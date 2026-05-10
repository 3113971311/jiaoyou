import { PrismaClient } from '@prisma/client';
import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';

const prisma = new PrismaClient();

export default fp(async function prismaPlugin(fastify: FastifyInstance) {
  await prisma.$connect();
  fastify.decorate('prisma', prisma);
  fastify.addHook('onClose', async () => {
    await prisma.$disconnect();
  });
});

export { prisma };
