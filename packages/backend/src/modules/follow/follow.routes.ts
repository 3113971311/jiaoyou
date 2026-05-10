import type { FastifyInstance } from 'fastify';
import * as followService from './follow.service';
import { authenticate } from '../../middleware/authenticate';
import { requireVIP } from '../../middleware/requireVIP';

export default async function followRoutes(fastify: FastifyInstance) {
  // 关注用户
  fastify.post(
    '/api/follow/:userId',
    { preHandler: [authenticate, requireVIP] },
    async (request) => {
      const followerId = (request.user as any).sub;
      const { userId } = request.params as any;
      return followService.followUser(followerId, userId);
    },
  );

  // 取消关注
  fastify.delete(
    '/api/follow/:userId',
    { preHandler: [authenticate, requireVIP] },
    async (request) => {
      const followerId = (request.user as any).sub;
      const { userId } = request.params as any;
      return followService.unfollowUser(followerId, userId);
    },
  );

  // 我的关注列表
  fastify.get(
    '/api/follow/following',
    { preHandler: [authenticate] },
    async (request) => {
      const userId = (request.user as any).sub;
      const { cursor, limit } = request.query as any;
      return followService.getFollowing(userId, cursor, Number(limit) || 20);
    },
  );

  // 我的粉丝列表
  fastify.get(
    '/api/follow/followers',
    { preHandler: [authenticate] },
    async (request) => {
      const userId = (request.user as any).sub;
      const { cursor, limit } = request.query as any;
      return followService.getFollowers(userId, cursor, Number(limit) || 20);
    },
  );

  // 检查与某用户的关注关系
  fastify.get(
    '/api/follow/status/:userId',
    { preHandler: [authenticate] },
    async (request) => {
      const userId = (request.user as any).sub;
      const { userId: targetId } = request.params as any;
      return followService.checkFollowStatus(userId, targetId);
    },
  );
}
