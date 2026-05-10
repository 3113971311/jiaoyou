import { prisma } from '../../plugins/prisma';
import { notFound } from '../../utils/errors';
import type { FastifyInstance } from 'fastify';

export async function getReviewQueue(
  status: string = 'pending',
  imageType?: string,
  page: number = 1,
  limit: number = 20,
) {
  const where: any = { status };
  if (imageType) where.imageType = imageType;

  const [items, total] = await Promise.all([
    prisma.reviewQueue.findMany({
      where,
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { submittedAt: 'asc' },
      include: {
        submitter: {
          select: { id: true, username: true, nickname: true },
        },
        reviewer: {
          select: { id: true, username: true },
        },
      },
    }),
    prisma.reviewQueue.count({ where }),
  ]);

  return { items, total, page, limit };
}

export async function getReviewItem(id: string) {
  const item = await prisma.reviewQueue.findUnique({
    where: { id },
    include: {
      submitter: {
        select: { id: true, username: true, nickname: true },
      },
    },
  });
  if (!item) throw notFound();
  return item;
}

export async function approveImage(
  fastify: FastifyInstance,
  id: string,
  reviewerId: string,
) {
  const item = await prisma.reviewQueue.findUnique({ where: { id } });
  if (!item) throw notFound();
  if (item.status !== 'pending') throw notFound('该图片已被处理');

  const storage = fastify.storage;

  // 从 staging 复制到 public
  const stagingPath = item.imageUrl.replace(/^\//, '');
  const publicPath = stagingPath.replace('staging/', 'public/');

  try {
    await storage.client.copyObject(storage.bucket, publicPath, stagingPath);
  } catch {
    // 重试一次
    await storage.client.copyObject(storage.bucket, publicPath, stagingPath);
  }

  const publicUrl = `/${publicPath}`;

  // 更新审核记录
  await prisma.reviewQueue.update({
    where: { id },
    data: {
      status: 'approved',
      reviewedBy: reviewerId,
      reviewedAt: new Date(),
    },
  });

  // 根据类型更新关联数据
  if (item.imageType === 'avatar') {
    await prisma.user.update({
      where: { id: item.relatedId! },
      data: { avatarUrl: publicUrl, avatarStaging: null },
    });
  } else if (item.imageType === 'moment') {
    // 更新 moment_image 的 public_url
    await prisma.momentImage.updateMany({
      where: {
        momentId: item.relatedId!,
        imageUrl: item.imageUrl,
      },
      data: { publicUrl, reviewStatus: 'approved' },
    });

    // 检查该动态的所有图片是否都审核完毕
    const pendingImages = await prisma.momentImage.count({
      where: { momentId: item.relatedId!, reviewStatus: 'pending' },
    });

    if (pendingImages === 0) {
      // 所有图片审核完毕，更新动态状态
      const moment = await prisma.moment.findUnique({
        where: { id: item.relatedId! },
        select: { userId: true },
      });

      await prisma.moment.update({
        where: { id: item.relatedId! },
        data: { status: 'approved' },
      });

      // 发送通知
      if (moment) {
        await prisma.notification.create({
          data: {
            userId: moment.userId,
            type: 'review_approved',
            title: '审核通过',
            content: '你的动态审核已通过',
            relatedId: item.relatedId!,
          },
        });
      }
    }
  }

  // 发送审核通过通知
  await prisma.notification.create({
    data: {
      userId: item.submittedBy,
      type: 'review_approved',
      title: '图片审核通过',
      content: item.imageType === 'avatar' ? '你的头像审核通过' : '你的图片审核通过',
      relatedId: item.relatedId,
    },
  });

  return { message: '已通过' };
}

export async function rejectImage(
  fastify: FastifyInstance,
  id: string,
  reviewerId: string,
  comment?: string,
) {
  const item = await prisma.reviewQueue.findUnique({ where: { id } });
  if (!item) throw notFound();
  if (item.status !== 'pending') throw notFound('该图片已被处理');

  // 删除 staging 图片
  const stagingPath = item.imageUrl.replace(/^\//, '');
  try {
    await fastify.storage.client.removeObject(fastify.storage.bucket, stagingPath);
    if (item.thumbnailUrl) {
      const thumbPath = item.thumbnailUrl.replace(/^\//, '');
      await fastify.storage.client.removeObject(fastify.storage.bucket, thumbPath);
    }
  } catch {
    // 忽略删除错误
  }

  // 更新审核记录
  await prisma.reviewQueue.update({
    where: { id },
    data: {
      status: 'rejected',
      reviewedBy: reviewerId,
      reviewComment: comment || '审核未通过',
      reviewedAt: new Date(),
    },
  });

  // 如果是 moment 图片，更新状态
  if (item.imageType === 'moment' && item.relatedId) {
    await prisma.momentImage.updateMany({
      where: { momentId: item.relatedId, imageUrl: item.imageUrl },
      data: { reviewStatus: 'rejected' },
    });

    // 检查是否需要将整个 moment 标记为 rejected
    const totalImages = await prisma.momentImage.count({
      where: { momentId: item.relatedId },
    });
    const rejectedImages = await prisma.momentImage.count({
      where: { momentId: item.relatedId, reviewStatus: 'rejected' },
    });

    if (totalImages === rejectedImages) {
      await prisma.moment.update({
        where: { id: item.relatedId },
        data: { status: 'rejected' },
      });
    }
  }

  // 发送通知
  await prisma.notification.create({
    data: {
      userId: item.submittedBy,
      type: 'review_rejected',
      title: '审核未通过',
      content: comment || '你的图片审核未通过',
      relatedId: item.relatedId,
    },
  });

  return { message: '已拒绝' };
}

export async function batchReview(
  fastify: FastifyInstance,
  ids: string[],
  action: 'approve' | 'reject',
  reviewerId: string,
) {
  const results = [];
  for (const id of ids) {
    try {
      if (action === 'approve') {
        results.push(await approveImage(fastify, id, reviewerId));
      } else {
        results.push(await rejectImage(fastify, id, reviewerId));
      }
    } catch (e: any) {
      results.push({ id, error: e.message });
    }
  }
  return { processed: results.length, results };
}

export async function batchDelete(fastify: FastifyInstance, ids: string[]) {
  let deleted = 0;
  for (const id of ids) {
    try {
      const item = await prisma.reviewQueue.findUnique({ where: { id } });
      if (!item) continue;
      // 删除暂存区图片
      const stagingPath = item.imageUrl.replace(/^\//, '');
      try { await fastify.storage.client.removeObject(fastify.storage.bucket, stagingPath); } catch {}
      if (item.thumbnailUrl) {
        const thumbPath = item.thumbnailUrl.replace(/^\//, '');
        try { await fastify.storage.client.removeObject(fastify.storage.bucket, thumbPath); } catch {}
      }
      // 删除审核记录
      await prisma.reviewQueue.delete({ where: { id } });
      deleted++;
    } catch {}
  }
  return { deleted };
}
