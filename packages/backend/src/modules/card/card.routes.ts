import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import * as cardService from './card.service';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';

export default async function cardRoutes(fastify: FastifyInstance) {
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  fastify.post('/api/admin/cards/generate', adminAuth, async (request) => {
    const userId = (request.user as any).sub;
    const { batchName, denominationDays, expireDays, quantity, note } = request.body as any;
    return cardService.generateBatch(userId, batchName, denominationDays, expireDays || 7, quantity, note);
  });

  fastify.get('/api/admin/cards/batches', adminAuth, async (request) => {
    const { page, limit } = request.query as any;
    return cardService.listBatches(Number(page) || 1, Number(limit) || 20);
  });

  fastify.get('/api/admin/cards/batches/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    const { page, limit, status } = request.query as any;
    return cardService.getBatchDetail(id, Number(page) || 1, Number(limit) || 30, status as string | undefined);
  });

  // 删除单张卡密
  fastify.delete('/api/admin/cards/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    await prisma.card.delete({ where: { id } });
    return { message: '已删除' };
  });

  fastify.get('/api/admin/cards/batches/:id/export', adminAuth, async (request, reply) => {
    const { id } = request.params as any;
    const data = await cardService.exportBatch(id);
    reply.header('Content-Type', 'text/csv; charset=utf-8');
    reply.header('Content-Disposition', `attachment; filename="${data.batchName}.csv"`);
    return data.csvContent;
  });
}
