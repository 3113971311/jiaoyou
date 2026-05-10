import type { FastifyInstance } from 'fastify';
import bcrypt from 'bcrypt';
import { prisma } from '../../plugins/prisma';
import { authenticate } from '../../middleware/authenticate';
import { requireAdmin } from '../../middleware/requireAdmin';
import { badRequest } from '../../utils/errors';

export default async function userAdminRoutes(fastify: FastifyInstance) {
  const adminAuth = { preHandler: [authenticate, requireAdmin] };

  // 用户列表（支持搜索和分页）
  fastify.get('/api/admin/users', adminAuth, async (request) => {
    const { search, status, page, limit } = request.query as any;
    const where: any = {};
    if (search) {
      where.OR = [
        { username: { contains: search } },
        { email: { contains: search } },
        { nickname: { contains: search } },
      ];
    }
    if (status && status !== 'all') where.status = status;
    else if (!status) where.status = { not: 'deleted' }; // 默认排除已删除, 'all'显示全部

    const [items, total] = await Promise.all([
      prisma.user.findMany({
        where,
        skip: (Number(page) - 1 || 0) * (Number(limit) || 20),
        take: Number(limit) || 20,
        orderBy: { createdAt: 'desc' },
        select: {
          id: true, username: true, email: true, nickname: true,
          gender: true, avatarUrl: true, location: true, vipExpiresAt: true,
          isAdmin: true, status: true, warningCount: true, createdAt: true,
        },
      }),
      prisma.user.count({ where }),
    ]);
    return { items, total };
  });

  // 创建用户
  fastify.post('/api/admin/users', adminAuth, async (request, reply) => {
    const { username, email, password, nickname, gender, isAdmin, vipDays } = request.body as any;
    if (!username || !email || !password) {
      throw badRequest('用户名、邮箱、密码为必填项');
    }
    const existing = await prisma.user.findFirst({
      where: { OR: [{ username }, { email }] },
    });
    if (existing) throw badRequest('用户名或邮箱已存在');

    const passwordHash = await bcrypt.hash(password, 12);
    const vipExpiresAt = vipDays ? new Date(Date.now() + vipDays * 24 * 60 * 60 * 1000) : null;

    const user = await prisma.user.create({
      data: {
        username, email, passwordHash,
        nickname: nickname || username, gender: gender || null,
        isAdmin: !!isAdmin, vipExpiresAt,
      },
      select: { id: true, username: true, email: true, nickname: true, isAdmin: true, vipExpiresAt: true },
    });

    if (vipDays) {
      await prisma.vipOrder.create({
        data: {
          userId: user.id, days: vipDays, orderType: 'admin_grant',
          vipBefore: null, vipAfter: user.vipExpiresAt,
        },
      });
    }

    return user;
  });

  // 编辑用户
  fastify.put('/api/admin/users/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    const { username, email, password, nickname, gender, isAdmin, vipExpiresAt } = request.body as any;

    const data: any = {};
    if (username !== undefined) data.username = username;
    if (email !== undefined) data.email = email;
    if (nickname !== undefined) data.nickname = nickname;
    if (gender !== undefined) data.gender = gender;
    if (isAdmin !== undefined) data.isAdmin = isAdmin;
    if (vipExpiresAt !== undefined) data.vipExpiresAt = vipExpiresAt ? new Date(vipExpiresAt) : null;
    if (password) data.passwordHash = await bcrypt.hash(password, 12);

    const user = await prisma.user.update({
      where: { id },
      data,
      select: { id: true, username: true, email: true, nickname: true, isAdmin: true, vipExpiresAt: true, status: true },
    });
    return user;
  });

  // 移除VIP
  fastify.post('/api/admin/users/:id/remove-vip', adminAuth, async (request) => {
    const { id } = request.params as any;
    await prisma.user.update({ where: { id }, data: { vipExpiresAt: null } });
    return { message: 'VIP已移除' };
  });

  // 删除用户（软删除）
  fastify.delete('/api/admin/users/:id', adminAuth, async (request) => {
    const { id } = request.params as any;
    await prisma.user.update({
      where: { id },
      data: { status: 'deleted' },
    });
    return { message: '已删除' };
  });
}
