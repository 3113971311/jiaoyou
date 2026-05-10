import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { io } from '../../plugins/socketio';
import { authenticate } from '../../middleware/authenticate';
import { requireVIP } from '../../middleware/requireVIP';
import { requireAdmin } from '../../middleware/requireAdmin';

export default async function reportRoutes(fastify: FastifyInstance) {
  const auth = { preHandler: [authenticate] };
  const vipAuth = { preHandler: [authenticate, requireVIP] };
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // ---- 举报 ----
  fastify.post('/api/reports', vipAuth, async (request) => {
    const reporterId = (request.user as any).sub;
    const { targetType, targetId, reason } = request.body as any;
    return prisma.report.create({
      data: { reporterId, targetType, targetId, reason },
    });
  });

  // ---- 管理端举报处理 ----
  fastify.get('/api/admin/reports', adminAuth, async (request) => {
    const { status, page, limit } = request.query as any;
    const where: any = {};
    if (status) where.status = status;

    const [items, total] = await Promise.all([
      prisma.report.findMany({
        where,
        skip: (Number(page) - 1 || 0) * Number(limit) || 0,
        take: Number(limit) || 20,
        orderBy: { createdAt: 'desc' },
        include: {
          reporter: { select: { id: true, username: true } },
        },
      }),
      prisma.report.count({ where }),
    ]);
    return { items, total };
  });

  fastify.post('/api/admin/reports/:id/handle', adminAuth, async (request) => {
    const handledBy = (request.user as any).sub;
    const { id } = request.params as any;
    const { action, result } = request.body as any;
    return prisma.report.update({
      where: { id },
      data: { status: action === 'dismiss' ? 'dismissed' : 'handled', handledBy, result, handledAt: new Date() },
    });
  });

  // ---- 警告 ----
  fastify.post('/api/admin/users/:id/warn', adminAuth, async (request) => {
    const warnedBy = (request.user as any).sub;
    const { id } = request.params as any;
    const { reason, relatedChatImageUrl } = request.body as any;

    await prisma.warning.create({
      data: { userId: id, warnedBy, reason, relatedChatImageUrl },
    });

    // 累计警告次数
    const warnCount = await prisma.warning.count({ where: { userId: id } });

    // 3次警告自动封号
    if (warnCount >= 3) {
      await prisma.user.update({
        where: { id },
        data: { status: 'banned' },
      });

      // 通知用户
      await prisma.notification.create({
        data: {
          userId: id,
          type: 'banned',
          title: '账号已被封禁',
          content: '因多次违规，你的账号已被封禁',
        },
      });

      io.to(`user:${id}`).emit('notification', {
        type: 'banned',
        title: '账号已被封禁',
        content: '因多次违规，你的账号已被封禁',
      });

      return { warningCount: warnCount, banned: true };
    }

    // 推送警告通知
    await prisma.notification.create({
      data: {
        userId: id,
        type: 'warning',
        title: '收到警告',
        content: reason,
      },
    });

    io.to(`user:${id}`).emit('notification', {
      type: 'warning',
      title: '收到警告',
      content: reason,
    });

    return { warningCount: warnCount };
  });

  fastify.get('/api/admin/users/:id/warnings', adminAuth, async (request) => {
    const { id } = request.params as any;
    return prisma.warning.findMany({
      where: { userId: id },
      orderBy: { createdAt: 'desc' },
    });
  });

  // ---- 黑名单 ----
  fastify.post('/api/blacklist/:userId', vipAuth, async (request) => {
    const blockerId = (request.user as any).sub;
    const { userId } = request.params as any;

    // 拉黑时自动解除互关
    await prisma.follow.deleteMany({
      where: {
        OR: [
          { followerId: blockerId, followedId: userId },
          { followerId: userId, followedId: blockerId },
        ],
      },
    });

    return prisma.blacklist.upsert({
      where: { blockerId_blockedId: { blockerId, blockedId: userId } },
      create: { blockerId, blockedId: userId },
      update: {},
    });
  });

  fastify.delete('/api/blacklist/:userId', auth, async (request) => {
    const blockerId = (request.user as any).sub;
    const { userId } = request.params as any;
    await prisma.blacklist.deleteMany({ where: { blockerId, blockedId: userId } });
    return { message: '已解除拉黑' };
  });

  fastify.get('/api/blacklist', auth, async (request) => {
    const userId = (request.user as any).sub;
    return prisma.blacklist.findMany({
      where: { blockerId: userId },
      include: {
        blocked: { select: { id: true, username: true, nickname: true, avatarUrl: true } },
      },
    });
  });
}
