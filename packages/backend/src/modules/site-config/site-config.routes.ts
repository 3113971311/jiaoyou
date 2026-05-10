import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { memStore as redis } from '../../plugins/redis';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';
import { createTransporter } from '../../plugins/mailer';

const CACHE_KEY = 'site:configs';
const CACHE_TTL = 3600; // 1小时

export default async function siteConfigRoutes(fastify: FastifyInstance) {
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // 公开接口：获取配置项（支持 ?keys=key1,key2 批量获取）
  fastify.get('/api/site-config', async (request) => {
    const { keys } = request.query as any;

    // 尝试从缓存获取
    const cached = await redis.get(CACHE_KEY);
    let configs: Record<string, any>;

    if (cached) {
      configs = JSON.parse(cached);
    } else {
      const all = await prisma.siteConfig.findMany();
      configs = {};
      for (const c of all) {
        configs[c.configKey] = { value: c.configValue, type: c.valueType };
      }
      await redis.set(CACHE_KEY, JSON.stringify(configs), 'EX', CACHE_TTL);
    }

    // 如果指定了 keys，只返回这些
    if (keys) {
      const keyList = (keys as string).split(',').map((k: string) => k.trim());
      const filtered: Record<string, any> = {};
      for (const k of keyList) {
        if (configs[k]) filtered[k] = configs[k];
      }
      return filtered;
    }

    return configs;
  });

  // 管理端：配置列表
  fastify.get('/api/admin/site-configs', adminAuth, async () => {
    return prisma.siteConfig.findMany();
  });

  // 管理端：编辑配置项
  fastify.put('/api/admin/site-configs/:key', adminAuth, async (request) => {
    const { key } = request.params as any;
    const { value, type, description } = request.body as any;
    const userId = (request.user as any).sub;

    const result = await prisma.siteConfig.upsert({
      where: { configKey: key },
      update: {
        configValue: value,
        valueType: type,
        description,
        updatedBy: userId,
        updatedAt: new Date(),
      },
      create: {
        configKey: key,
        configValue: value,
        valueType: type || 'text',
        description,
        updatedBy: userId,
      },
    });

    // 刷新缓存
    await redis.del(CACHE_KEY);

    // 如果修改的是 SMTP 相关配置，重新创建邮件发送器
    if (key.startsWith('smtp_')) {
      await createTransporter();
      fastify.log.info('SMTP 配置已更新');
    }

    return result;
  });
}
