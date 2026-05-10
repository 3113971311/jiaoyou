import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';
import { loadSensitiveWords } from '../../utils/sensitive';

export default async function filterRoutes(fastify: FastifyInstance) {
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // 敏感词列表
  fastify.get('/api/admin/sensitive-words', adminAuth, async () => {
    return prisma.sensitiveWord.findMany({ orderBy: { createdAt: 'desc' } });
  });

  // 添加敏感词
  fastify.post('/api/admin/sensitive-words', adminAuth, async (request) => {
    const { word, level } = request.body as any;
    const result = await prisma.sensitiveWord.create({
      data: { word, level: level || 'replace', createdBy: (request.user as any).sub },
    });
    await loadSensitiveWords(); // 刷新缓存
    return result;
  });

  // 删除敏感词
  fastify.delete('/api/admin/sensitive-words/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    await prisma.sensitiveWord.delete({ where: { id } });
    await loadSensitiveWords(); // 刷新缓存
    return { message: '已删除' };
  });
}
