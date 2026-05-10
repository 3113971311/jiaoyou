import type { FastifyInstance } from 'fastify';
import * as paymentService from './payment.service';
import { authenticate } from '../../middleware/authenticate';

export default async function paymentRoutes(fastify: FastifyInstance) {
  fastify.post('/api/cards/redeem', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { code } = request.body as any;
    return paymentService.redeemCard(userId, code);
  });

  fastify.get('/api/vip/status', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    return paymentService.getVipStatus(userId);
  });

  fastify.get('/api/vip/history', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { page, limit } = request.query as any;
    return paymentService.getVipHistory(userId, Number(page) || 1, Number(limit) || 10);
  });
}
