import bcrypt from 'bcrypt';
import crypto from 'crypto';
import jwtLib from 'jsonwebtoken';
import { prisma } from '../../plugins/prisma';
import { memStore as redis } from '../../plugins/redis';
import { getTransporter, createTransporter } from '../../plugins/mailer';
import { config } from '../../config';
import { AppError, badRequest, unauthorized, forbidden, tooMany } from '../../utils/errors';

// ============================================================
// 邮箱验证码
// ============================================================

export async function sendVerificationCode(email: string, purpose: 'register' | 'reset_password') {
  // 1. 先做业务校验（不消耗限流次数）
  if (purpose === 'register') {
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) throw badRequest('该邮箱已被注册');
  }
  if (purpose === 'reset_password') {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) throw badRequest('该邮箱未注册');
  }

  // 2. 检查邮件服务是否已配置
  const { transporter, configured } = await getTransporter();
  if (!configured) {
    throw badRequest('邮件服务未配置，请联系管理员');
  }

  // 3. 限流：同一邮箱 60 秒内不可重复发送（仅在前面都通过后才锁定）
  const rateKey = `email:ratelimit:${email}:${purpose}`;
  const canSend = await redis.set(rateKey, '1', 'NX', 60);
  if (!canSend) {
    throw tooMany('验证码已发送，请60秒后再试');
  }

  // 4. 生成验证码并发送
  const code = String(Math.floor(100000 + Math.random() * 900000));
  await redis.set(`email:code:${purpose}:${email}`, code, 'EX', 300);

  const purposeText = purpose === 'register' ? '注册' : '重置密码';
  // 获取发件人地址（必须和SMTP登录用户一致）
  const smtpUserCfg = await prisma.siteConfig.findUnique({ where: { configKey: 'smtp_user' } });
  const fromAddress = smtpUserCfg?.configValue || config.SMTP_USER;
  try {
    await transporter.sendMail({
      from: `"交友平台" <${fromAddress}>`,
      to: email,
      subject: `【交友平台】${purposeText}验证码`,
      text: `您的${purposeText}验证码为：${code}，5分钟内有效。`,
      html: `<p>您的<strong>${purposeText}</strong>验证码为：</p><h2>${code}</h2><p>5分钟内有效。</p>`,
    });
  } catch (err: any) {
    // 发送失败 → 清除验证码（限流保留，前端倒计时同步）
    await redis.del(`email:code:${purpose}:${email}`);
    throw badRequest('邮件发送失败: ' + (err.message || '未知错误'));
  }

  return { message: '验证码已发送' };
}

// ============================================================
// 注册
// ============================================================

export async function register(data: {
  username: string;
  email: string;
  password: string;
  code: string;
}) {
  // 验证码校验
  const storedCode = await redis.get(`email:code:register:${data.email}`);
  if (!storedCode || storedCode !== data.code) {
    throw badRequest('验证码错误或已过期');
  }

  // 检查用户名唯一
  const existingUser = await prisma.user.findUnique({ where: { username: data.username } });
  if (existingUser) {
    throw badRequest('用户名已被注册');
  }

  // 删除验证码
  await redis.del(`email:code:register:${data.email}`);

  // 创建用户
  const passwordHash = await bcrypt.hash(data.password, 12);
  const user = await prisma.user.create({
    data: {
      username: data.username,
      email: data.email,
      passwordHash,
      nickname: data.username,
    },
  });

  return generateTokenPair(user.id);
}

// ============================================================
// 登录
// ============================================================

export async function login(account: string, password: string) {
  // 支持用户名或邮箱登录
  const user = await prisma.user.findFirst({
    where: {
      OR: [{ username: account }, { email: account }],
    },
  });

  if (!user) {
    throw unauthorized('用户名或密码错误');
  }

  if (user.status === 'banned' || user.status === 'deleted') {
    throw forbidden('账号已被封禁或删除');
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    throw unauthorized('用户名或密码错误');
  }

  return generateTokenPair(user.id);
}

// ============================================================
// Token 生成
// ============================================================

async function generateTokenPair(userId: string) {
  const accessToken = jwtLib.sign(
    { sub: userId, type: 'access' },
    config.JWT_ACCESS_SECRET,
    { expiresIn: config.JWT_ACCESS_TTL as any },
  );

  const family = crypto.randomUUID();
  const refreshToken = jwtLib.sign(
    { sub: userId, type: 'refresh', family },
    config.JWT_REFRESH_SECRET,
    { expiresIn: config.JWT_REFRESH_TTL as any },
  );

  // 存 refresh token hash
  const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7天后

  await prisma.refreshToken.create({
    data: {
      userId,
      tokenHash,
      family,
      expiresAt,
    },
  });

  return { accessToken, refreshToken };
}

// ============================================================
// 刷新 Token
// ============================================================

export async function refreshTokens(refreshToken: string) {
  let payload: any;
  try {
    payload = jwtLib.verify(refreshToken, config.JWT_REFRESH_SECRET);
  } catch {
    throw unauthorized('refresh token 无效或已过期');
  }

  const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
  const stored = await prisma.refreshToken.findUnique({ where: { tokenHash } });

  if (!stored || stored.revoked) {
    // Token 已被使用过 → 整个 family 泄露，全部撤销
    if (stored) {
      await prisma.refreshToken.updateMany({
        where: { family: stored.family },
        data: { revoked: true },
      });
    }
    throw unauthorized('refresh token 已被使用，请重新登录');
  }

  // 撤销旧 token
  await prisma.refreshToken.update({
    where: { id: stored.id },
    data: { revoked: true },
  });

  // 生成新 token pair
  const newAccessToken = jwtLib.sign(
    { sub: payload.sub, type: 'access' },
    config.JWT_ACCESS_SECRET,
    { expiresIn: config.JWT_ACCESS_TTL as any },
  );

  const newRefreshToken = jwtLib.sign(
    { sub: payload.sub, type: 'refresh', family: stored.family },
    config.JWT_REFRESH_SECRET,
    { expiresIn: config.JWT_REFRESH_TTL as any },
  );

  const newTokenHash = crypto.createHash('sha256').update(newRefreshToken).digest('hex');
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  await prisma.refreshToken.create({
    data: {
      userId: payload.sub,
      tokenHash: newTokenHash,
      family: stored.family,
      expiresAt,
    },
  });

  return { accessToken: newAccessToken, refreshToken: newRefreshToken };
}

// ============================================================
// 登出
// ============================================================

export async function logout(refreshToken: string) {
  const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
  await prisma.refreshToken.updateMany({
    where: { tokenHash },
    data: { revoked: true },
  });
}

// ============================================================
// 重置密码
// ============================================================

export async function resetPassword(email: string, code: string, newPassword: string) {
  const storedCode = await redis.get(`email:code:reset_password:${email}`);
  if (!storedCode || storedCode !== code) {
    throw badRequest('验证码错误或已过期');
  }

  const passwordHash = await bcrypt.hash(newPassword, 12);
  await prisma.user.update({
    where: { email },
    data: { passwordHash },
  });

  await redis.del(`email:code:reset_password:${email}`);

  // 撤销该用户所有 refresh token（强制所有设备重新登录）
  await prisma.refreshToken.updateMany({
    where: { user: { email } },
    data: { revoked: true },
  });

  return { message: '密码重置成功' };
}

// ============================================================
// 修改密码
// ============================================================

export async function changePassword(userId: string, oldPassword: string, newPassword: string) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw unauthorized();

  const valid = await bcrypt.compare(oldPassword, user.passwordHash);
  if (!valid) {
    throw badRequest('原密码错误');
  }

  const passwordHash = await bcrypt.hash(newPassword, 12);
  await prisma.user.update({ where: { id: userId }, data: { passwordHash } });

  return { message: '密码修改成功' };
}

// ============================================================
// 获取当前用户
// ============================================================

export async function getMe(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      username: true,
      email: true,
      nickname: true,
      avatarUrl: true,
      gender: true,
      birthday: true,
      bio: true,
      location: true,
      vipExpiresAt: true,
      isAdmin: true,
      status: true,
      createdAt: true,
    },
  });

  if (!user) throw unauthorized();
  return user;
}
