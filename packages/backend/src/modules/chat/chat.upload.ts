import type { FastifyInstance } from 'fastify';
import { authenticate } from '../../middleware/authenticate';
import { processImage, ALLOWED_MIME_TYPES, MAX_FILE_SIZE } from '../../utils/image';
import { badRequest } from '../../utils/errors';

export default async function chatUploadRoutes(fastify: FastifyInstance) {
  fastify.post('/api/upload/chat-image', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const file = await request.file();
    if (!file) throw badRequest('请选择文件');
    if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) throw badRequest('仅支持 JPG/PNG/WebP');

    const buffer = await file.toBuffer();
    if (buffer.length > MAX_FILE_SIZE) throw badRequest('图片不能超过10MB');

    const { buffer: processed, filename } = await processImage(buffer, { thumbnail: false });

    // 聊天图片直接存公开区（免审）
    const publicPath = fastify.storage.publicPath('chat', userId, filename);
    await fastify.storage.client.putObject(fastify.storage.bucket, publicPath, processed);

    return { url: `/${publicPath}` };
  });
}
