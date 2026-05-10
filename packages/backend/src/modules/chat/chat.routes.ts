import type { FastifyInstance } from 'fastify';
import * as chatService from './chat.service';
import { authenticate } from '../../middleware/authenticate';
import { requireVIP } from '../../middleware/requireVIP';
import { requireAdmin } from '../../middleware/requireAdmin';
import { prisma } from '../../plugins/prisma';

export default async function chatRoutes(fastify: FastifyInstance) {
  const vipAuth = { preHandler: [authenticate, requireVIP] };
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // ---- 用户端 ----

  // 会话列表
  fastify.get('/api/conversations', vipAuth, async (request) => {
    const userId = (request.user as any).sub;
    const { cursor, limit } = request.query as any;
    return chatService.getConversations(userId, cursor, Number(limit) || 20);
  });

  // 消息历史
  fastify.get('/api/conversations/:id/messages', vipAuth, async (request) => {
    const userId = (request.user as any).sub;
    const { id } = request.params as any;
    const { before, limit } = request.query as any;
    return chatService.getMessages(id, userId, before, Number(limit) || 30);
  });

  // 创建/获取会话
  fastify.post('/api/conversations', vipAuth, async (request) => {
    const userId = (request.user as any).sub;
    const { targetUserId } = request.body as any;
    return chatService.getOrCreateConversation(userId, targetUserId);
  });

  // ---- 管理端聊天监控 ----

  fastify.get('/api/admin/chats', adminAuth, async (request) => {
    const { search } = request.query as any;
    const where: any = {};
    if (search) {
      where.OR = [
        { user1: { username: { contains: search } } },
        { user2: { username: { contains: search } } },
      ];
    }
    return prisma.conversation.findMany({
      where,
      take: 50,
      orderBy: { lastMessageAt: { sort: 'desc', nulls: 'last' } },
      include: {
        user1: { select: { id: true, username: true, nickname: true } },
        user2: { select: { id: true, username: true, nickname: true } },
        _count: { select: { messages: true } },
      },
    });
  });

  fastify.get('/api/admin/chats/:id/messages', adminAuth, async (request) => {
    const { id } = request.params as any;
    const { before, limit } = request.query as any;
    const messages = await prisma.message.findMany({
      where: { conversationId: id, ...(before ? { id: { lt: before } } : {}) },
      take: Number(limit) || 50,
      orderBy: { createdAt: 'desc' },
      include: {
        sender: { select: { id: true, username: true, nickname: true } },
      },
    });
    return messages.reverse();
  });
}
