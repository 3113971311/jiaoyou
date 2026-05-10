import { prisma } from '../../plugins/prisma';
import { io } from '../../plugins/socketio';
import { notFound, forbidden } from '../../utils/errors';
import { filterText, checkText } from '../../utils/sensitive';

// 获取会话列表
export async function getConversations(userId: string, cursor?: string, limit: number = 20) {
  const convs = await prisma.conversation.findMany({
    where: {
      OR: [{ user1Id: userId }, { user2Id: userId }],
      ...(cursor ? { id: { lt: cursor } } : {}),
    },
    take: limit + 1,
    orderBy: { lastMessageAt: { sort: 'desc', nulls: 'last' } },
    include: {
      messages: { take: 1, orderBy: { createdAt: 'desc' } },
    },
  });

  const hasMore = convs.length > limit;
  if (hasMore) convs.pop();

  // 获取对方用户信息
  const list = await Promise.all(
    convs.map(async (c) => {
      const otherId = c.user1Id === userId ? c.user2Id : c.user1Id;
      const other = await prisma.user.findUnique({
        where: { id: otherId },
        select: { id: true, username: true, nickname: true, avatarUrl: true },
      });
      return {
        id: c.id,
        otherUser: other,
        lastMessage: c.messages[0] || null,
        lastMessageAt: c.lastMessageAt,
      };
    }),
  );

  return { list, nextCursor: hasMore ? convs[convs.length - 1]?.id : null };
}

// 获取消息历史
export async function getMessages(conversationId: string, userId: string, before?: string, limit: number = 30) {
  // 验证用户属于此会话
  const conv = await prisma.conversation.findUnique({ where: { id: conversationId } });
  if (!conv || (conv.user1Id !== userId && conv.user2Id !== userId)) {
    throw forbidden('无权访问此会话');
  }

  const messages = await prisma.message.findMany({
    where: {
      conversationId,
      ...(before ? { id: { lt: before } } : {}),
    },
    take: limit + 1,
    orderBy: { createdAt: 'desc' },
  });

  const hasMore = messages.length > limit;
  if (hasMore) messages.pop();

  return {
    list: messages.reverse(), // 返回正序
    nextCursor: hasMore ? messages[0]?.id : null,
  };
}

// 发送消息（通过 WebSocket 调用）
export async function sendMessage(
  conversationId: string,
  senderId: string,
  content: string | undefined,
  contentType: string = 'text',
  imageUrl?: string,
) {
  // 敏感词过滤（仅文本）
  let filteredContent = content;
  if (content && contentType === 'text') {
    const { hit, level } = checkText(content);
    if (level === 'block') {
      throw forbidden('消息包含违规内容，无法发送');
    }
    if (hit) {
      filteredContent = filterText(content);
    }
  }

  const message = await prisma.message.create({
    data: {
      conversationId,
      senderId,
      content: filteredContent,
      contentType,
      imageUrl,
      status: 'sent',
    },
  });

  // 更新会话最后消息时间
  await prisma.conversation.update({
    where: { id: conversationId },
    data: { lastMessageAt: new Date() },
  });

  return message;
}

// 标记已读
export async function markRead(conversationId: string, userId: string, messageIds: string[]) {
  await prisma.message.updateMany({
    where: {
      id: { in: messageIds },
      conversationId,
      senderId: { not: userId },
    },
    data: { status: 'read' },
  });
}

// 获取或创建会话
export async function getOrCreateConversation(user1Id: string, user2Id: string) {
  // 检查黑名单
  const blocked = await prisma.blacklist.findFirst({
    where: {
      OR: [
        { blockerId: user1Id, blockedId: user2Id },
        { blockerId: user2Id, blockedId: user1Id },
      ],
    },
  });
  if (blocked) throw forbidden('无法与对方聊天');

  const [a, b] = user1Id < user2Id ? [user1Id, user2Id] : [user2Id, user1Id];

  let conv = await prisma.conversation.findUnique({
    where: { user1Id_user2Id: { user1Id: a, user2Id: b } },
  });

  if (!conv) {
    conv = await prisma.conversation.create({
      data: { user1Id: a, user2Id: b },
    });
  }

  return conv;
}
