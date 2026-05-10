import type { FastifyInstance } from 'fastify';
import * as matchService from './match.service';
import { authenticate } from '../../middleware/authenticate';
import { requireVIP } from '../../middleware/requireVIP';

export default async function matchRoutes(fastify: FastifyInstance) {
  const vipAuth = { preHandler: [authenticate, requireVIP] };

  fastify.post('/api/match/start', vipAuth, async (request) => {
    const userId = (request.user as any).sub;
    const { scope, latitude, longitude, preferGender } = request.body as any;
    return matchService.startMatch(userId, scope, latitude, longitude, preferGender);
  });

  fastify.post('/api/match/cancel', vipAuth, async (request) => {
    const userId = (request.user as any).sub;
    return matchService.cancelMatch(userId);
  });

  fastify.get('/api/match/status', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    return matchService.getMatchStatus(userId);
  });

  fastify.get('/api/match/history', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { page, limit } = request.query as any;
    return matchService.getMatchHistory(userId, Number(page) || 1, Number(limit) || 10);
  });
}
