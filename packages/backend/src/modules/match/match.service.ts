import { prisma } from '../../plugins/prisma';
import { io } from '../../plugins/socketio';
import { badRequest, tooMany } from '../../utils/errors';
import { reverseGeocode } from '../../utils/geocode';

export async function startMatch(
  userId: string,
  scope: 'city' | 'province',
  latitude: number,
  longitude: number,
  preferGender?: string,
) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { gender: true, vipExpiresAt: true },
  });

  if (!user?.vipExpiresAt || user.vipExpiresAt < new Date()) {
    throw badRequest('需要 VIP 会员才能使用匹配功能');
  }

  // 每日上限检查
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayCount = await prisma.matchDailyCount.aggregate({
    where: { userId, date: today },
    _sum: { count: true },
  });
  if ((todayCount._sum.count || 0) >= 5) {
    throw tooMany('今日匹配次数已用完（5次/天）');
  }

  // 检查是否已在队列中
  const existing = await prisma.matchQueue.findFirst({
    where: { userId, status: 'waiting', expiresAt: { gt: new Date() } },
  });
  if (existing) {
    throw badRequest('你已在匹配队列中');
  }

  // 逆地理编码解析城市/省份
  const { city, province } = await reverseGeocode(latitude, longitude);
  const locationStr = [city, province].filter(Boolean).join(', ');
  // 更新用户定位信息
  if (locationStr) {
    await prisma.user.update({ where: { id: userId }, data: { location: locationStr } });
  }
  const effectiveGender = preferGender || (user.gender === 'male' ? 'female' : 'male');

  // 创建匹配队列记录
  const expiresAt = new Date(Date.now() + 12 * 60 * 60 * 1000); // 12小时
  const queueEntry = await prisma.matchQueue.create({
    data: {
      userId,
      scope,
      city,
      province,
      latitude,
      longitude,
      preferGender: effectiveGender,
      expiresAt,
    },
  });

  // 尝试立即匹配
  const matchResult = await tryMatch(userId, queueEntry.id, scope, city, province, effectiveGender, user.gender!);

  return matchResult || { message: '已进入匹配队列，等待配对...', queueId: queueEntry.id };
}

async function tryMatch(
  userId: string,
  queueId: string,
  scope: string,
  city: string,
  province: string,
  preferGender: string,
  userGender: string,
) {
  const candidates = await prisma.matchQueue.findMany({
    where: {
      userId: { not: userId },
      status: 'waiting',
      expiresAt: { gt: new Date() },
      preferGender: userGender, // 对方的期望性别 = 我的性别
      ...(scope === 'city' ? { city } : { province }),
    },
    orderBy: { createdAt: 'asc' },
    include: { user: { select: { gender: true } } },
  });

  // 筛选：我的期望性别 = 对方性别
  const valid = candidates.filter((c) => c.user.gender === preferGender);

  if (valid.length > 0) {
    const matched = valid[0]; // 先到先得

    // 创建会话
    const [a, b] = userId < matched.userId ? [userId, matched.userId] : [matched.userId, userId];
    const conversation = await prisma.conversation.upsert({
      where: { user1Id_user2Id: { user1Id: a, user2Id: b } },
      create: { user1Id: a, user2Id: b },
      update: {},
    });

    // 更新双方队列状态
    const now = new Date();
    await Promise.all([
      prisma.matchQueue.update({
        where: { id: queueId },
        data: { status: 'matched', matchedWith: matched.userId, matchedAt: now },
      }),
      prisma.matchQueue.update({
        where: { id: matched.id },
        data: { status: 'matched', matchedWith: userId, matchedAt: now },
      }),
    ]);

    // 更新每日计数
    await prisma.matchDailyCount.upsert({
      where: { userId_date: { userId, date: new Date().toISOString().slice(0, 10) } },
      create: { userId, date: new Date(), count: 1 },
      update: { count: { increment: 1 } },
    });

    // WebSocket 通知双方
    const notification = {
      type: 'match_success',
      title: '配对成功',
      content: '你们配对成功，开始聊天吧！',
      conversationId: conversation.id,
    };

    io.to(`user:${userId}`).emit('notification', notification);
    io.to(`user:${matched.userId}`).emit('notification', notification);

    // 发送系统消息
    await prisma.message.create({
      data: {
        conversationId: conversation.id,
        senderId: userId,
        content: '你们配对成功，开始聊天吧！',
        contentType: 'text',
      },
    });

    // 写通知记录
    await Promise.all([
      prisma.notification.create({
        data: {
          userId,
          type: 'match_success',
          title: '配对成功',
          content: '你们配对成功，开始聊天吧！',
          relatedId: matched.userId,
        },
      }),
      prisma.notification.create({
        data: {
          userId: matched.userId,
          type: 'match_success',
          title: '配对成功',
          content: '你们配对成功，开始聊天吧！',
          relatedId: userId,
        },
      }),
    ]);

    return {
      matched: true,
      conversationId: conversation.id,
      matchedUser: { id: matched.userId },
    };
  }

  return null;
}

export async function cancelMatch(userId: string) {
  const result = await prisma.matchQueue.updateMany({
    where: { userId, status: 'waiting', expiresAt: { gt: new Date() } },
    data: { status: 'cancelled' },
  });
  return { message: '已取消匹配' };
}

export async function getMatchStatus(userId: string) {
  const active = await prisma.matchQueue.findFirst({
    where: {
      userId,
      status: { in: ['waiting', 'matched'] },
      OR: [
        { status: 'waiting', expiresAt: { gt: new Date() } },
        { status: 'matched' },
      ],
    },
    orderBy: { createdAt: 'desc' },
    include: {
      matched: {
        select: { id: true, username: true, nickname: true, avatarUrl: true },
      },
    },
  });

  return {
    isMatching: active?.status === 'waiting' || false,
    isMatched: active?.status === 'matched' || false,
    matchedUser: active?.matched || null,
    expiresAt: active?.expiresAt || null,
  };
}

export async function getMatchHistory(userId: string, page: number = 1, limit: number = 10) {
  const [items, total] = await Promise.all([
    prisma.matchQueue.findMany({
      where: { userId },
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: {
        matched: {
          select: { id: true, username: true, nickname: true, avatarUrl: true },
        },
      },
    }),
    prisma.matchQueue.count({ where: { userId } }),
  ]);

  return { items, total, page, limit };
}

// 定时任务：清理过期匹配
export async function cleanupExpiredMatches() {
  const result = await prisma.matchQueue.updateMany({
    where: {
      status: 'waiting',
      expiresAt: { lt: new Date() },
    },
    data: { status: 'expired' },
  });
  return { cleaned: result.count };
}
