import type { FastifyInstance } from 'fastify';
import fs from 'fs/promises';
import path from 'path';
import jwtLib from 'jsonwebtoken';
import { config } from '../../config';
import { prisma } from '../../plugins/prisma';

// 管理端查看暂存区图片（审核用）
// 使用 token query 参数鉴权，因为 <img> 标签不带 Authorization header
export default async function imagePreviewRoutes(fastify: FastifyInstance) {
  fastify.get('/api/admin/image-preview', async (request, reply) => {
    const { path: imgPath, token } = request.query as any;

    // token 鉴权
    if (!token) return reply.status(401).send({ error: 'missing token' });
    try {
      const payload = jwtLib.verify(token, config.JWT_ACCESS_SECRET) as any;
      const user = await prisma.user.findUnique({ where: { id: payload.sub } });
      if (!user?.isAdmin) return reply.status(403).send({ error: 'not admin' });
    } catch {
      return reply.status(401).send({ error: 'invalid token' });
    }

    if (!imgPath) return reply.status(400).send({ error: 'missing path' });

    // 安全检查：只允许访问 staging 目录
    const safe = imgPath.replace(/\\/g, '/').replace(/\.\./g, '');
    const fullPath = path.resolve(__dirname, '../../../../../data/storage', safe.replace(/^\//, ''));

    try {
      const buf = await fs.readFile(fullPath);
      const ext = path.extname(fullPath).toLowerCase();
      const mime = ext === '.png' ? 'image/png' : ext === '.webp' ? 'image/webp' : 'image/jpeg';
      reply.header('Content-Type', mime);
      reply.header('Cache-Control', 'private, max-age=60');
      return reply.send(buf);
    } catch {
      return reply.status(404).send({ error: 'image not found' });
    }
  });
}
