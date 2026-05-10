import { io } from '../../plugins/socketio';
import * as chatService from './chat.service';
import { prisma } from '../../plugins/prisma';

export function setupChatGateway() {
  io.on('connection', (socket) => {
    const userId = (socket as any).userId;

    // 发送消息
    socket.on('chat:send', async (data: {
      conversationId: string;
      content?: string;
      contentType?: string;
      imageUrl?: string;
      tempId?: string;
    }, callback) => {
      try {
        const message = await chatService.sendMessage(
          data.conversationId,
          userId,
          data.content,
          data.contentType || 'text',
          data.imageUrl,
        );

        // 发送给会话中的所有人
        io.to(`conversation:${data.conversationId}`).emit('chat:message', {
          ...message,
          senderId: userId,
        });

        if (callback) callback({ success: true, tempId: data.tempId, message });
      } catch (e: any) {
        if (callback) callback({ success: false, error: e.message });
      }
    });

    // 正在输入
    socket.on('chat:typing', (data: { conversationId: string; isTyping: boolean }) => {
      socket.to(`conversation:${data.conversationId}`).emit('chat:typing', {
        userId,
        conversationId: data.conversationId,
        isTyping: data.isTyping,
      });
    });

    // 标记已读
    socket.on('chat:read', async (data: { conversationId: string; messageIds: string[] }) => {
      await chatService.markRead(data.conversationId, userId, data.messageIds);
      socket.to(`conversation:${data.conversationId}`).emit('chat:read', {
        conversationId: data.conversationId,
        readBy: userId,
        messageIds: data.messageIds,
      });
    });

    // 加入会话房间
    socket.on('chat:join', (conversationId: string) => {
      socket.join(`conversation:${conversationId}`);
    });
  });
}
