import { prisma } from '../../plugins/prisma';
import { memStore as redis } from '../../plugins/redis';
import { badRequest, tooMany } from '../../utils/errors';
import { hashCardCode, normalizeCardCode } from '../../utils/card-code';

export async function redeemCard(userId: string, code: string) {
  const normalized = normalizeCardCode(code);
  const codeHash = hashCardCode(code);

  // 限流检查
  const ipKey = `card:rate:user:${userId}`;
  const attempts = await redis.incr(ipKey);
  if (attempts === 1) await redis.expire(ipKey, 60);
  if (attempts > 3) {
    throw tooMany('操作频繁，请1分钟后再试');
  }

  // 查找卡密
  const card = await prisma.card.findFirst({ where: { codeHash } });
  if (!card) {
    // 记录失败次数
    const failKey = `card:fail:${userId}`;
    const fails = await redis.incr(failKey);
    if (fails === 1) await redis.expire(failKey, 3600);
    if (fails > 20) {
      throw badRequest('兑换失败次数过多，请1小时后再试');
    }
    throw badRequest('无效的卡密');
  }

  if (card.status !== 'unused') {
    throw badRequest('该卡密已被使用');
  }

  if (card.expiresAt < new Date()) {
    throw badRequest('该卡密已过期');
  }

  // 事务：兑换
  const result = await prisma.$transaction(async (tx) => {
    // 乐观锁更新卡密状态
    const updated = await tx.card.updateMany({
      where: { id: card.id, status: 'unused' },
      data: { status: 'used', usedBy: userId, usedAt: new Date() },
    });

    if (updated.count === 0) {
      throw badRequest('该卡密已被使用');
    }

    // 获取用户当前 VIP 状态
    const user = await tx.user.findUnique({
      where: { id: userId },
      select: { vipExpiresAt: true },
    });

    // 计算新的 VIP 到期时间
    const now = new Date();
    const base = user?.vipExpiresAt && user.vipExpiresAt > now ? user.vipExpiresAt : now;
    const newExpiry = new Date(base.getTime() + card.denominationDays * 24 * 60 * 60 * 1000);

    // 更新用户 VIP
    await tx.user.update({
      where: { id: userId },
      data: { vipExpiresAt: newExpiry },
    });

    // 写入订单
    await tx.vipOrder.create({
      data: {
        userId,
        cardId: card.id,
        days: card.denominationDays,
        orderType: 'card_redeem',
        vipBefore: user?.vipExpiresAt || null,
        vipAfter: newExpiry,
      },
    });

    return { days: card.denominationDays, vipExpiresAt: newExpiry.toISOString() };
  });

  return { success: true, ...result };
}

export async function getVipStatus(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { vipExpiresAt: true },
  });

  const now = new Date();
  const isVip = user?.vipExpiresAt ? user.vipExpiresAt > now : false;
  const daysRemaining = isVip
    ? Math.ceil((user!.vipExpiresAt!.getTime() - now.getTime()) / (24 * 60 * 60 * 1000))
    : 0;

  return { isVip, expiresAt: user?.vipExpiresAt || null, daysRemaining };
}

export async function getVipHistory(userId: string, page: number = 1, limit: number = 10) {
  const [items, total] = await Promise.all([
    prisma.vipOrder.findMany({
      where: { userId },
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.vipOrder.count({ where: { userId } }),
  ]);
  return { items, total, page, limit };
}
