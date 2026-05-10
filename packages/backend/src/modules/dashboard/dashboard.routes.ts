import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';

export default async function dashboardRoutes(fastify: FastifyInstance) {
  fastify.get(
    '/api/admin/dashboard',
    { preHandler: [authenticate, requireAdmin] },
    async () => {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

      const [
        totalUsers, todayNewUsers, activeVip, todayMatches,
        pendingReviews, todayMoments, pendingReports, bannedUsers,
        latestMoments, latestMatches, latestUsers,
      ] = await Promise.all([
        prisma.user.count({ where: { status: { not: 'deleted' } } }),
        prisma.user.count({ where: { createdAt: { gte: today }, status: { not: 'deleted' } } }),
        prisma.user.count({ where: { vipExpiresAt: { gt: now } } }),
        prisma.matchQueue.count({ where: { status: 'matched', matchedAt: { gte: today } } }),
        prisma.reviewQueue.count({ where: { status: 'pending' } }),
        prisma.moment.count({ where: { createdAt: { gte: today } } }),
        prisma.report.count({ where: { status: 'pending' } }),
        prisma.user.count({ where: { status: 'banned' } }),

        // 实时动态
        prisma.moment.findMany({
          where: { status: 'approved' },
          take: 5, orderBy: { createdAt: 'desc' },
          select: { id: true, contentText: true, createdAt: true,
            user: { select: { username: true, nickname: true } } },
        }),

        prisma.matchQueue.findMany({
          where: { status: 'matched' },
          take: 5, orderBy: { matchedAt: 'desc' },
          select: { id: true, matchedAt: true, scope: true,
            user: { select: { username: true, nickname: true } },
            matched: { select: { username: true, nickname: true } } },
        }),

        prisma.user.findMany({
          where: { status: { not: 'deleted' } },
          take: 5, orderBy: { createdAt: 'desc' },
          select: { id: true, username: true, nickname: true, createdAt: true },
        }),
      ]);

      return {
        totalUsers, todayNewUsers, activeVip, todayMatches,
        pendingReviews, todayMoments, pendingReports, bannedUsers,
        latestMoments: latestMoments.map(m => ({ id: m.id, text: m.contentText?.slice(0, 60) || '(图片)', user: m.user.nickname || m.user.username, time: m.createdAt })),
        latestMatches: latestMatches.map(m => ({ id: m.id, user1: m.user.nickname || m.user.username, user2: m.matched?.nickname || m.matched?.username, scope: m.scope, time: m.matchedAt })),
        latestUsers: latestUsers.map(u => ({ id: u.id, username: u.username, nickname: u.nickname, time: u.createdAt })),
      };
    },
  );
}
