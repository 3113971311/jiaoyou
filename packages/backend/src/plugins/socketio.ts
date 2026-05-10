import { Server as SocketServer } from 'socket.io';
import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';

let io: SocketServer;

export default fp(async function socketioPlugin(fastify: FastifyInstance) {
  io = new SocketServer(fastify.server, {
    cors: { origin: '*' },
    transports: ['websocket', 'polling'],
  });

  io.use(async (socket, next) => {
    const token = socket.handshake.auth.token;
    if (!token) return next(new Error('未提供认证 token'));
    try {
      const jwt = fastify.jwt;
      const payload = jwt.verify(token);
      (socket as any).userId = (payload as any).sub;
      next();
    } catch {
      next(new Error('token 无效'));
    }
  });

  io.on('connection', (socket) => {
    const userId = (socket as any).userId;
    fastify.log.info(`WS 连接: user ${userId}`);
    socket.join(`user:${userId}`);
    socket.on('chat:join', (conversationId: string) => {
      socket.join(`conversation:${conversationId}`);
    });
    socket.on('disconnect', () => {
      fastify.log.info(`WS 断开: user ${userId}`);
    });
  });

  fastify.decorate('io', io);
  fastify.addHook('onClose', () => io.close());
});

export { io };
