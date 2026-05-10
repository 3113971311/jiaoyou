import type { FastifyInstance } from 'fastify';
import { authenticate } from '../../middleware/authenticate';
import { forwardGeocode } from '../../utils/geocode';

export default async function geocodeRoutes(fastify: FastifyInstance) {
  fastify.get('/api/geocode/search', { preHandler: [authenticate] }, async (request) => {
    const { q } = request.query as any;
    if (!q) return { lat: null, lng: null };
    const result = await forwardGeocode(q);
    return result || { lat: null, lng: null };
  });
}
