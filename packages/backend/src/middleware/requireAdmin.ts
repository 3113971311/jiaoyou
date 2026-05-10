import type { FastifyRequest, FastifyReply } from 'fastify';
import { prisma } from '../plugins/prisma';

export async function requireAdmin(request: FastifyRequest, reply: FastifyReply) {
  const userId = (request.user as any).sub;

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { isAdmin: true },
  });

  if (!user?.isAdmin) {
    return reply.status(403).send({ error: '需要管理员权限' });
  }
}
