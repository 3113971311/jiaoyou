import Fastify from 'fastify';
import cors from '@fastify/cors';
import multipart from '@fastify/multipart';
import fastifyStatic from '@fastify/static';
import path from 'path';

import { config } from './config';

import prismaPlugin from './plugins/prisma';
import redisPlugin from './plugins/redis';
import mailerPlugin from './plugins/mailer';
import storagePlugin from './plugins/storage';
import authPlugin from './plugins/auth';
import socketioPlugin from './plugins/socketio';

const fastify = Fastify({ logger: true });

async function start() {
  // ---- 基础插件 ----
  await fastify.register(cors, { origin: config.CORS_ORIGIN, credentials: true });
  await fastify.register(multipart, { limits: { fileSize: 10 * 1024 * 1024 } });

  // ---- 核心插件 ----
  await fastify.register(prismaPlugin);
  await fastify.register(redisPlugin);
  await fastify.register(mailerPlugin);
  await fastify.register(storagePlugin);
  await fastify.register(authPlugin);
  await fastify.register(socketioPlugin);

  // ---- 静态文件 ----
  // 上传文件的公开目录
  const publicDir = path.resolve(__dirname, '../../../data/storage/public');
  await fastify.register(fastifyStatic, {
    root: publicDir,
    prefix: '/public/',
    decorateReply: false,
  });

  // 前端 SPA（生产环境）
  const userDist = path.resolve(__dirname, '../../user-app/dist');
  const adminDist = path.resolve(__dirname, '../../admin-app/dist');
  await fastify.register(fastifyStatic, { root: adminDist, prefix: '/admin/', decorateReply: false });
  fastify.setNotFoundHandler((request, reply) => {
    if (request.url.startsWith('/admin')) return reply.sendFile('index.html', adminDist);
    if (!request.url.startsWith('/api') && !request.url.startsWith('/socket.io') && !request.url.startsWith('/public')) {
      return reply.sendFile('index.html', userDist);
    }
    reply.status(404).send({ error: 'Not Found' });
  });

  // ---- 健康检查 ----
  fastify.get('/api/health', async () => ({ status: 'ok', timestamp: new Date().toISOString() }));

  // ---- 路由 ----
  await fastify.register(import('./modules/auth/auth.routes'));
  await fastify.register(import('./modules/user/user.routes'));
  await fastify.register(import('./modules/user/user.admin.routes'));
  await fastify.register(import('./modules/follow/follow.routes'));
  await fastify.register(import('./modules/moment/moment.routes'));
  await fastify.register(import('./modules/moderation/moderation.routes'));
  await fastify.register(import('./modules/moderation/moderation.image'));
  await fastify.register(import('./modules/filter/filter.routes'));
  await fastify.register(import('./modules/site-config/site-config.routes'));
  await fastify.register(import('./modules/chat/chat.routes'));
  await fastify.register(import('./modules/chat/chat.upload'));
  await fastify.register(import('./modules/match/match.routes'));
  await fastify.register(import('./modules/match/geocode.routes'));
  await fastify.register(import('./modules/payment/payment.routes'));
  await fastify.register(import('./modules/payment/payment.buy'));
  await fastify.register(import('./modules/card/card.routes'));
  await fastify.register(import('./modules/report/report.routes'));
  await fastify.register(import('./modules/notification/notification.routes'));
  await fastify.register(import('./modules/dashboard/dashboard.routes'));
  await fastify.register(import('./modules/feedback/feedback.routes'));

  // ---- 聊天网关 ----
  const { setupChatGateway } = await import('./modules/chat/chat.gateway');
  setupChatGateway();

  // ---- 敏感词库 ----
  const { loadSensitiveWords } = await import('./utils/sensitive');
  await loadSensitiveWords();

  // ---- 启动 ----
  try {
    await fastify.listen({ port: config.APP_PORT, host: config.APP_HOST });
    fastify.log.info(`✅ 服务已启动: http://localhost:${config.APP_PORT}`);
    fastify.log.info(`📁 文件存储: ${publicDir}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

start();
