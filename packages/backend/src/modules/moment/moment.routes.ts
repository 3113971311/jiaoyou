import type { FastifyInstance } from 'fastify';
import * as momentService from './moment.service';
import { authenticate } from '../../middleware/authenticate';
import { requireVIP } from '../../middleware/requireVIP';

export default async function momentRoutes(fastify: FastifyInstance) {
  // 发布动态
  fastify.post('/api/moments', { preHandler: [authenticate, requireVIP] }, async (request) => {
    const userId = (request.user as any).sub;
    const parts = request.parts();
    let contentText: string | undefined;
    const files: Array<{ buffer: Buffer; mimeType: string }> = [];

    for await (const part of parts) {
      if (part.type === 'field' && part.fieldname === 'content_text') {
        contentText = (part as any).value;
      } else if (part.type === 'file') {
        const buffer = await (part as any).toBuffer();
        files.push({ buffer, mimeType: (part as any).mimetype });
      }
    }

    if (!contentText && files.length === 0) {
      return { statusCode: 400, error: '动态内容不能为空' };
    }

    return momentService.createMoment(fastify, userId, contentText, files);
  });

  // 动态流
  fastify.get('/api/moments', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { cursor, limit } = request.query as any;
    return momentService.getFeed(userId, cursor, Number(limit) || 20);
  });

  // 单条动态
  fastify.get('/api/moments/:id', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { id } = request.params as any;
    return momentService.getMoment(id, userId);
  });

  // 删除动态
  fastify.delete('/api/moments/:id', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { id } = request.params as any;
    return momentService.deleteMoment(id, userId);
  });

  // 点赞/取消
  fastify.post('/api/moments/:id/like', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { id } = request.params as any;
    return momentService.toggleLike(id, userId);
  });

  // 评论
  fastify.post('/api/moments/:id/comments', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { id } = request.params as any;
    const { content } = request.body as any;
    if (!content) return { statusCode: 400, error: '评论内容不能为空' };
    return momentService.addComment(id, userId, content);
  });

  // 评论列表
  fastify.get('/api/moments/:id/comments', { preHandler: [authenticate] }, async (request) => {
    const { id } = request.params as any;
    const { cursor, limit } = request.query as any;
    return momentService.getComments(id, cursor, Number(limit) || 20);
  });
}
