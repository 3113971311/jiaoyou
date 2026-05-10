import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';

// 内存 KV 存储（替代 Redis），支持 TTL
class MemoryStore {
  private store = new Map<string, { value: any; expiresAt: number }>();
  private timers = new Map<string, NodeJS.Timeout>();

  async set(key: string, value: any, mode?: string, ttl?: number): Promise<'OK' | null> {
    // NX: 仅当 key 不存在时才设置
    if (mode === 'NX' && this.store.has(key)) {
      const item = this.store.get(key);
      if (item && Date.now() < item.expiresAt) return null;
    }
    // EX: 过期时间(秒)
    const actualTTL = mode === 'EX' ? ttl : (ttl ?? (mode ? undefined : undefined));
    const ttlSeconds = typeof actualTTL === 'number' ? actualTTL : undefined;
    this.store.set(key, { value, expiresAt: ttlSeconds ? Date.now() + ttlSeconds * 1000 : Infinity });

    // 清除旧定时器
    if (this.timers.has(key)) clearTimeout(this.timers.get(key)!);

    if (ttl) {
      this.timers.set(
        key,
        setTimeout(() => this.store.delete(key), ttl * 1000),
      );
    }
    return 'OK';
  }

  async get(key: string): Promise<any | null> {
    const item = this.store.get(key);
    if (!item) return null;
    if (Date.now() > item.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return item.value;
  }

  async del(key: string): Promise<number> {
    const existed = this.store.has(key);
    this.store.delete(key);
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key)!);
      this.timers.delete(key);
    }
    return existed ? 1 : 0;
  }

  async incr(key: string): Promise<number> {
    const item = this.store.get(key);
    if (!item || Date.now() > item.expiresAt) {
      this.store.set(key, { value: 1, expiresAt: Infinity });
      return 1;
    }
    item.value = Number(item.value) + 1;
    return item.value;
  }

  async expire(key: string, ttl: number): Promise<number> {
    const item = this.store.get(key);
    if (!item) return 0;
    item.expiresAt = Date.now() + ttl * 1000;
    if (this.timers.has(key)) clearTimeout(this.timers.get(key)!);
    this.timers.set(key, setTimeout(() => this.store.delete(key), ttl * 1000));
    return 1;
  }
}

export const memStore = new MemoryStore();

export default fp(async function redisPlugin(fastify: FastifyInstance) {
  fastify.decorate('redis', memStore);
  fastify.log.info('内存存储已就绪（轻量模式）');
});
