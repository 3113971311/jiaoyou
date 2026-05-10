import type { FastifyInstance } from 'fastify';
import * as modService from './moderation.service';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';

export default async function moderationRoutes(fastify: FastifyInstance) {
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // 审核队列列表
  fastify.get('/api/admin/review-queue', adminAuth, async (request) => {
    const { status, imageType, page, limit } = request.query as any;
    return modService.getReviewQueue(status, imageType, Number(page) || 1, Number(limit) || 20);
  });

  // 单条审核详情
  fastify.get('/api/admin/review-queue/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    return modService.getReviewItem(id);
  });

  // 通过单张
  fastify.post('/api/admin/review-queue/:id/approve', adminAuth, async (request) => {
    const reviewerId = (request.user as any).sub;
    const { id } = request.params as any;
    return modService.approveImage(fastify, id, reviewerId);
  });

  // 拒绝单张
  fastify.post('/api/admin/review-queue/:id/reject', adminAuth, async (request) => {
    const reviewerId = (request.user as any).sub;
    const { id } = request.params as any;
    const { comment } = request.body as any;
    return modService.rejectImage(fastify, id, reviewerId, comment);
  });

  // 批量审核
  fastify.post('/api/admin/review-queue/batch', adminAuth, async (request) => {
    const reviewerId = (request.user as any).sub;
    const { ids, action } = request.body as any;
    return modService.batchReview(fastify, ids, action, reviewerId);
  });

  // 批量删除（仅已拒绝的）
  fastify.post('/api/admin/review-queue/batch-delete', adminAuth, async (request) => {
    const { ids } = request.body as any;
    return modService.batchDelete(fastify, ids);
  });
}
