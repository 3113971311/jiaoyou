import type { FastifyInstance } from 'fastify';
import {
  registerBody,
  loginBody,
  refreshBody,
  sendCodeBody,
  resetPasswordBody,
  changePasswordBody,
} from './auth.schema';
import * as authService from './auth.service';
import { authenticate } from '../../middleware/authenticate';

export default async function authRoutes(fastify: FastifyInstance) {
  // 发送邮箱验证码
  fastify.post('/api/auth/send-verify-code', async (request, reply) => {
    const { email, purpose } = sendCodeBody.parse(request.body);
    const result = await authService.sendVerificationCode(email, purpose);
    return result;
  });

  // 注册
  fastify.post('/api/auth/register', async (request, reply) => {
    const data = registerBody.parse(request.body);
    const result = await authService.register(data);
    return result;
  });

  // 登录
  fastify.post('/api/auth/login', async (request, reply) => {
    const { account, password } = loginBody.parse(request.body);
    const result = await authService.login(account, password);
    return result;
  });

  // 刷新 token
  fastify.post('/api/auth/refresh', async (request, reply) => {
    const { refreshToken } = refreshBody.parse(request.body);
    const result = await authService.refreshTokens(refreshToken);
    return result;
  });

  // 登出
  fastify.post('/api/auth/logout', async (request, reply) => {
    const { refreshToken } = request.body as any;
    if (refreshToken) {
      await authService.logout(refreshToken);
    }
    return { message: '已登出' };
  });

  // 忘记密码 → 发送验证码（使用 send-verify-code 接口，purpose=reset_password）
  fastify.post('/api/auth/reset-password', async (request, reply) => {
    const { email, code, newPassword } = resetPasswordBody.parse(request.body);
    const result = await authService.resetPassword(email, code, newPassword);
    return result;
  });

  // 获取当前用户
  fastify.get('/api/auth/me', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    return authService.getMe(userId);
  });

  // 修改密码（需登录）
  fastify.put('/api/auth/password', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { oldPassword, newPassword } = changePasswordBody.parse(request.body);
    return authService.changePassword(userId, oldPassword, newPassword);
  });
}
