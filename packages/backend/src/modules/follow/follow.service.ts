import { prisma } from '../../plugins/prisma';
import { badRequest } from '../../utils/errors';

export async function followUser(followerId: string, followedId: string) {
  if (followerId === followedId) {
    throw badRequest('不能关注自己');
  }

  const target = await prisma.user.findUnique({ where: { id: followedId } });
  if (!target) throw badRequest('用户不存在');

  // 检查是否已关注
  const existing = await prisma.follow.findUnique({
    where: { followerId_followedId: { followerId, followedId } },
  });
  if (existing) {
    return { message: '已关注', mutual: await isMutualFollow(followerId, followedId) };
  }

  await prisma.follow.create({
    data: { followerId, followedId },
  });

  const mutual = await isMutualFollow(followerId, followedId);

  // 如果形成互关，发送通知
  if (mutual) {
    await prisma.notification.create({
      data: {
        userId: followedId,
        type: 'follow_mutual',
        title: '互相关注',
        content: '你和对方互相关注了',
        relatedId: followerId,
      },
    });
    // 推送给对方
    const { io } = await import('../../plugins/socketio');
    io.to(`user:${followedId}`).emit('notification', {
      type: 'follow_mutual',
      title: '互相关注',
      content: '有人和你互相关注了',
    });
  } else {
    // 单向关注通知
    await prisma.notification.create({
      data: {
        userId: followedId,
        type: 'followed',
        title: '新粉丝',
        content: '有人关注了你',
        relatedId: followerId,
      },
    });
  }

  return { message: '关注成功', mutual };
}

export async function unfollowUser(followerId: string, followedId: string) {
  await prisma.follow.deleteMany({
    where: { followerId, followedId },
  });
  return { message: '已取消关注' };
}

export async function getFollowing(userId: string, cursor?: string, limit: number = 20) {
  const follows = await prisma.follow.findMany({
    where: { followerId: userId },
    take: limit + 1,
    ...(cursor ? { cursor: { id: cursor }, skip: 1 } : {}),
    orderBy: { createdAt: 'desc' },
    include: {
      followed: {
        select: {
          id: true,
          username: true,
          nickname: true,
          avatarUrl: true,
          gender: true,
        },
      },
    },
  });

  const hasMore = follows.length > limit;
  if (hasMore) follows.pop();

  return {
    list: follows.map((f) => f.followed),
    nextCursor: hasMore ? follows[follows.length - 1]?.id : null,
  };
}

export async function getFollowers(userId: string, cursor?: string, limit: number = 20) {
  const follows = await prisma.follow.findMany({
    where: { followedId: userId },
    take: limit + 1,
    ...(cursor ? { cursor: { id: cursor }, skip: 1 } : {}),
    orderBy: { createdAt: 'desc' },
    include: {
      follower: {
        select: {
          id: true,
          username: true,
          nickname: true,
          avatarUrl: true,
          gender: true,
        },
      },
    },
  });

  const hasMore = follows.length > limit;
  if (hasMore) follows.pop();

  return {
    list: follows.map((f) => f.follower),
    nextCursor: hasMore ? follows[follows.length - 1]?.id : null,
  };
}

export async function isMutualFollow(user1Id: string, user2Id: string): Promise<boolean> {
  const count = await prisma.follow.count({
    where: {
      OR: [
        { followerId: user1Id, followedId: user2Id },
        { followerId: user2Id, followedId: user1Id },
      ],
    },
  });
  return count === 2;
}

export async function checkFollowStatus(userId: string, targetId: string) {
  const [iFollow, theyFollow] = await Promise.all([
    prisma.follow.findUnique({
      where: { followerId_followedId: { followerId: userId, followedId: targetId } },
    }),
    prisma.follow.findUnique({
      where: { followerId_followedId: { followerId: targetId, followedId: userId } },
    }),
  ]);

  return {
    iFollow: !!iFollow,
    theyFollow: !!theyFollow,
    mutual: !!(iFollow && theyFollow),
  };
}
