import type { FastifyRequest, FastifyReply } from 'fastify';
import { prisma } from '../plugins/prisma';

export async function requireVIP(request: FastifyRequest, reply: FastifyReply) {
  const userId = (request.user as any).sub;

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { vipExpiresAt: true, isAdmin: true },
  });

  // 管理员免VIP限制
  if (user?.isAdmin) return;

  if (!user || !user.vipExpiresAt || user.vipExpiresAt < new Date()) {
    return reply.status(403).send({ error: '此功能需要 VIP 会员，请先充值' });
  }
}
