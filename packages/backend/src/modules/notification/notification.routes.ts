import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { authenticate } from '../../middleware/authenticate';

export default async function notificationRoutes(fastify: FastifyInstance) {
  const auth = { preHandler: [authenticate] };

  // 通知列表
  fastify.get('/api/notifications', auth, async (request) => {
    const userId = (request.user as any).sub;
    const { cursor, limit } = request.query as any;

    const items = await prisma.notification.findMany({
      where: {
        userId,
        ...(cursor ? { id: { lt: cursor } } : {}),
      },
      take: Number(limit) || 30,
      orderBy: { createdAt: 'desc' },
    });

    // 未读计数
    const unreadCount = await prisma.notification.count({
      where: { userId, isRead: false },
    });

    return { items, unreadCount, nextCursor: items.length > 0 ? items[items.length - 1].id : null };
  });

  // 标记已读
  fastify.put('/api/notifications/:id/read', auth, async (request) => {
    const { id } = request.params as any;
    await prisma.notification.update({
      where: { id },
      data: { isRead: true },
    });
    return { message: '已读' };
  });

  // 全部已读
  fastify.put('/api/notifications/read-all', auth, async (request) => {
    const userId = (request.user as any).sub;
    await prisma.notification.updateMany({
      where: { userId, isRead: false },
      data: { isRead: true },
    });
    return { message: '全部已读' };
  });
}
