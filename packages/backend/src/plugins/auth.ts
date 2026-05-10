import fjwt from '@fastify/jwt';
import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';
import { config } from '../config';

export default fp(async function authPlugin(fastify: FastifyInstance) {
  fastify.register(fjwt, {
    secret: config.JWT_ACCESS_SECRET,
    sign: { expiresIn: config.JWT_ACCESS_TTL },
  });

  // 签名 refresh token
  fastify.decorate('signRefresh', (payload: object) => {
    return (fastify.jwt as any).sign(payload, {
      secret: config.JWT_REFRESH_SECRET,
      expiresIn: config.JWT_REFRESH_TTL,
    });
  });

  // 验证 refresh token
  fastify.decorate('verifyRefresh', (token: string) => {
    return (fastify.jwt as any).verify(token, { secret: config.JWT_REFRESH_SECRET });
  });
});
