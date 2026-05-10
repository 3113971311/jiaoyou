import { prisma } from '../../plugins/prisma';
import { badRequest, notFound, forbidden } from '../../utils/errors';
import { processImage, ALLOWED_MIME_TYPES, MAX_FILE_SIZE } from '../../utils/image';
import type { FastifyInstance } from 'fastify';

// ============================================================
// 创建动态
// ============================================================

export async function createMoment(
  fastify: FastifyInstance,
  userId: string,
  contentText: string | undefined,
  files: Array<{ buffer: Buffer; mimeType: string }> = [],
) {
  // 每日上限检查
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const todayCount = await prisma.moment.count({
    where: { userId, createdAt: { gte: today } },
  });
  if (todayCount >= 3) {
    throw badRequest('今日发布次数已用完（3条/天）');
  }

  // 检查是否有图片
  const hasImages = files.length > 0;
  const initialStatus = hasImages ? 'pending_review' : 'approved';

  const moment = await prisma.moment.create({
    data: {
      userId,
      contentText,
      status: initialStatus,
    },
  });

  // 处理图片
  if (hasImages) {
    const storage = fastify.storage;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      if (!ALLOWED_MIME_TYPES.includes(file.mimeType)) {
        throw badRequest('仅支持 JPG、PNG、WebP 格式');
      }
      if (file.buffer.length > MAX_FILE_SIZE) {
        throw badRequest('图片大小不能超过 10MB');
      }

      const { buffer, thumbBuffer, filename, thumbFilename } = await processImage(file.buffer);

      // 上传到暂存区
      const stagingPath = storage.stagingPath('moment', userId, filename);
      await storage.client.putObject(storage.bucket, stagingPath, buffer);

      let thumbStagingPath: string | undefined;
      if (thumbBuffer && thumbFilename) {
        thumbStagingPath = storage.thumbPath('moment', userId, thumbFilename);
        await storage.client.putObject(storage.bucket, thumbStagingPath, thumbBuffer);
      }

      const imageUrl = `/${stagingPath}`;
      const thumbnailUrl = thumbStagingPath ? `/${thumbStagingPath}` : null;

      // 创建 moment_image
      await prisma.momentImage.create({
        data: {
          momentId: moment.id,
          imageUrl,
          thumbnailUrl,
          sortOrder: i,
        },
      });

      // 写入审核队列
      await prisma.reviewQueue.create({
        data: {
          imageUrl,
          thumbnailUrl,
          imageType: 'moment',
          relatedId: moment.id,
          submittedBy: userId,
        },
      });
    }
  }

  return {
    id: moment.id,
    status: moment.status,
    message: hasImages ? '动态已提交，图片审核通过后可见' : '动态发布成功',
  };
}

// ============================================================
// 动态流（仅互关用户的已审核动态）
// ============================================================

export async function getFeed(userId: string, cursor?: string, limit: number = 20) {
  // 找到所有互关的用户 ID
  const mutualFollows = await prisma.follow.findMany({
    where: {
      followerId: userId,
      followed: { followerRelations: { some: { followerId: userId } } },
    },
    select: { followedId: true },
  });

  const mutualIds = mutualFollows.map((f) => f.followedId);
  // 加上自己
  const visibleUserIds = [userId, ...mutualIds];

  const moments = await prisma.moment.findMany({
    where: {
      userId: { in: visibleUserIds },
      status: 'approved',
      ...(cursor ? { id: { lt: cursor } } : {}),
    },
    take: limit + 1,
    orderBy: { createdAt: 'desc' },
    include: {
      user: {
        select: { id: true, username: true, nickname: true, avatarUrl: true },
      },
      images: {
        where: { reviewStatus: 'approved' },
        select: { publicUrl: true, thumbnailUrl: true },
        orderBy: { sortOrder: 'asc' },
      },
      _count: { select: { likes: true, comments: true } },
    },
  });

  const hasMore = moments.length > limit;
  if (hasMore) moments.pop();

  return {
    list: moments.map((m) => ({
      id: m.id,
      user: m.user,
      contentText: m.contentText,
      images: m.images.map((img) => ({
        url: img.publicUrl || img.thumbnailUrl,
        thumb: img.thumbnailUrl,
      })),
      likeCount: m._count.likes,
      commentCount: m._count.comments,
      createdAt: m.createdAt,
    })),
    nextCursor: hasMore ? moments[moments.length - 1]?.id : null,
  };
}

// ============================================================
// 获取单条动态
// ============================================================

export async function getMoment(momentId: string, userId: string) {
  const moment = await prisma.moment.findUnique({
    where: { id: momentId },
    include: {
      user: {
        select: { id: true, username: true, nickname: true, avatarUrl: true },
      },
      images: { orderBy: { sortOrder: 'asc' } },
      _count: { select: { likes: true, comments: true } },
    },
  });

  if (!moment) throw notFound('动态不存在');

  // 可见性判断：自己的 OR 互关的
  if (moment.userId !== userId) {
    if (moment.status !== 'approved') throw notFound('动态不存在');
    const mutual = await prisma.follow.count({
      where: {
        followerId: userId,
        followedId: moment.userId,
      },
    });
    const reverseMutual = await prisma.follow.count({
      where: {
        followerId: moment.userId,
        followedId: userId,
      },
    });
    if (mutual === 0 || reverseMutual === 0) {
      throw forbidden('需要互相关注才能查看动态');
    }
  }

  return { ...moment, likeCount: moment._count.likes, commentCount: moment._count.comments, _count: undefined };
}

// ============================================================
// 删除动态
// ============================================================

export async function deleteMoment(momentId: string, userId: string) {
  const moment = await prisma.moment.findUnique({ where: { id: momentId } });
  if (!moment) throw notFound();
  if (moment.userId !== userId) throw forbidden('只能删除自己的动态');

  await prisma.moment.delete({ where: { id: momentId } });
  return { message: '已删除' };
}

// ============================================================
// 点赞/取消
// ============================================================

export async function toggleLike(momentId: string, userId: string) {
  const existing = await prisma.momentLike.findUnique({
    where: { momentId_userId: { momentId, userId } },
  });

  if (existing) {
    await prisma.momentLike.delete({ where: { id: existing.id } });
    const count = await prisma.momentLike.count({ where: { momentId } });
    return { liked: false, likeCount: count };
  }

  await prisma.momentLike.create({ data: { momentId, userId } });
  const count = await prisma.momentLike.count({ where: { momentId } });

  // 通知动态作者
  const moment = await prisma.moment.findUnique({ where: { id: momentId }, select: { userId: true } });
  if (moment && moment.userId !== userId) {
    await prisma.notification.create({
      data: {
        userId: moment.userId,
        type: 'moment_liked',
        title: '新的赞',
        content: '有人赞了你的动态',
        relatedId: momentId,
      },
    });
  }

  return { liked: true, likeCount: count };
}

// ============================================================
// 评论
// ============================================================

export async function addComment(momentId: string, userId: string, content: string) {
  const comment = await prisma.momentComment.create({
    data: { momentId, userId, content },
    include: {
      user: { select: { id: true, username: true, nickname: true, avatarUrl: true } },
    },
  });

  // 通知动态作者
  const moment = await prisma.moment.findUnique({ where: { id: momentId }, select: { userId: true } });
  if (moment && moment.userId !== userId) {
    await prisma.notification.create({
      data: {
        userId: moment.userId,
        type: 'moment_commented',
        title: '新的评论',
        content: content.slice(0, 100),
        relatedId: momentId,
      },
    });
  }

  return comment;
}

export async function getComments(momentId: string, cursor?: string, limit: number = 20) {
  const comments = await prisma.momentComment.findMany({
    where: { momentId, ...(cursor ? { id: { lt: cursor } } : {}) },
    take: limit + 1,
    orderBy: { createdAt: 'asc' },
    include: {
      user: { select: { id: true, username: true, nickname: true, avatarUrl: true } },
    },
  });

  const hasMore = comments.length > limit;
  if (hasMore) comments.pop();

  return {
    list: comments,
    nextCursor: hasMore ? comments[comments.length - 1]?.id : null,
  };
}
