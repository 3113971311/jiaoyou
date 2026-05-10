import type { FastifyInstance } from 'fastify';
import { updateProfileBody } from './user.schema';
import * as userService from './user.service';
import { authenticate } from '../../middleware/authenticate';

export default async function userRoutes(fastify: FastifyInstance) {
  // 查看用户资料
  fastify.get('/api/users/:id', { preHandler: [authenticate] }, async (request, reply) => {
    const { id } = request.params as any;
    return userService.getUserById(id);
  });

  // 修改个人资料
  fastify.put('/api/users/profile', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const data = updateProfileBody.parse(request.body);
    return userService.updateProfile(userId, data);
  });

  // 上传头像
  fastify.post('/api/users/avatar', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const file = await request.file();

    if (!file) {
      return { statusCode: 400, error: '请选择文件' };
    }

    const buffer = await file.toBuffer();
    return userService.uploadAvatar(fastify, userId, buffer, file.mimetype);
  });
}
