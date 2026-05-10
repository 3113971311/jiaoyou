import fs from 'fs/promises';
import path from 'path';
import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';

const BASE_DIR = path.resolve(__dirname, '../../../data/storage');
const STAGING_DIR = path.join(BASE_DIR, 'staging');
const PUBLIC_DIR = path.join(BASE_DIR, 'public');

class LocalStorage {
  async ensureDirs() {
    await fs.mkdir(STAGING_DIR, { recursive: true });
    await fs.mkdir(PUBLIC_DIR, { recursive: true });
    await fs.mkdir(path.join(STAGING_DIR, 'avatar'), { recursive: true });
    await fs.mkdir(path.join(STAGING_DIR, 'moment'), { recursive: true });
    await fs.mkdir(path.join(STAGING_DIR, 'thumb'), { recursive: true });
    await fs.mkdir(path.join(PUBLIC_DIR, 'avatar'), { recursive: true });
    await fs.mkdir(path.join(PUBLIC_DIR, 'moment'), { recursive: true });
    await fs.mkdir(path.join(PUBLIC_DIR, 'chat'), { recursive: true });
  }

  stagingPath(type: string, userId: string, filename: string) {
    return `staging/${type}/${userId}/${filename}`;
  }

  publicPath(type: string, userId: string, filename: string) {
    return `public/${type}/${userId}/${filename}`;
  }

  thumbPath(type: string, userId: string, filename: string) {
    return `staging/thumb/${type}/${userId}/${filename}`;
  }

  async putObject(relativePath: string, buffer: Buffer) {
    const fullPath = path.join(BASE_DIR, relativePath);
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    await fs.writeFile(fullPath, buffer);
  }

  async removeObject(relativePath: string) {
    const fullPath = path.join(BASE_DIR, relativePath);
    try {
      await fs.unlink(fullPath);
    } catch {}
  }

  async copyObject(sourcePath: string, destPath: string) {
    const fullSource = path.join(BASE_DIR, sourcePath);
    const fullDest = path.join(BASE_DIR, destPath);
    await fs.mkdir(path.dirname(fullDest), { recursive: true });
    await fs.copyFile(fullSource, fullDest);
  }
}

export const localStorage = new LocalStorage();

export default fp(async function storagePlugin(fastify: FastifyInstance) {
  await localStorage.ensureDirs();

  fastify.decorate('storage', {
    storage: localStorage,
    stagingPath: (type: string, userId: string, filename: string) =>
      localStorage.stagingPath(type, userId, filename),
    publicPath: (type: string, userId: string, filename: string) =>
      localStorage.publicPath(type, userId, filename),
    thumbPath: (type: string, userId: string, filename: string) =>
      localStorage.thumbPath(type, userId, filename),
    client: {
      putObject: async (_bucket: string, relativePath: string, buffer: Buffer) => {
        await localStorage.putObject(relativePath, buffer);
      },
      removeObject: async (_bucket: string, relativePath: string) => {
        await localStorage.removeObject(relativePath);
      },
      copyObject: async (_bucket: string, dest: string, source: string) => {
        // source is like "/bucket-name/staging/..."
        const srcPath = source.replace(/^\/[^/]+\//, '');
        await localStorage.copyObject(srcPath, dest);
      },
    },
    bucket: 'local',
  });

  fastify.log.info(`本地文件存储已就绪: ${BASE_DIR}`);
});
