import { PrismaClient } from '@prisma/client';
import { Transporter } from 'nodemailer';
import { Server as SocketServer } from 'socket.io';
import { memStore } from './plugins/redis';

declare module 'fastify' {
  interface FastifyInstance {
    prisma: PrismaClient;
    redis: typeof memStore;
    mailer: Transporter;
    io: SocketServer;
    storage: {
      storage: import('./plugins/storage').LocalStorage;
      stagingPath: (type: string, userId: string, filename: string) => string;
      publicPath: (type: string, userId: string, filename: string) => string;
      thumbPath: (type: string, userId: string, filename: string) => string;
      client: {
        putObject: (bucket: string, path: string, buffer: Buffer) => Promise<void>;
        removeObject: (bucket: string, path: string) => Promise<void>;
        copyObject: (bucket: string, dest: string, source: string) => Promise<void>;
      };
      bucket: string;
    };
    signRefresh: (payload: object) => string;
    verifyRefresh: (token: string) => any;
  }
}

export {};
