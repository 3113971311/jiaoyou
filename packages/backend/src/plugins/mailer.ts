import nodemailer from 'nodemailer';
import fp from 'fastify-plugin';
import type { FastifyInstance } from 'fastify';
import { prisma } from './prisma';

let transporter: nodemailer.Transporter;

async function getSmtpConfig() {
  const keys = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass'];
  const configs = await prisma.siteConfig.findMany({
    where: { configKey: { in: keys } },
  });
  const map: Record<string, string> = {};
  for (const c of configs) map[c.configKey] = c.configValue;
  return {
    host: map.smtp_host || 'smtp.qq.com',
    port: parseInt(map.smtp_port || '465'),
    user: map.smtp_user || '',
    pass: map.smtp_pass || '',
  };
}

export async function createTransporter() {
  const cfg = await getSmtpConfig();
  transporter = nodemailer.createTransport({
    host: cfg.host,
    port: cfg.port,
    secure: true,
    auth: { user: cfg.user, pass: cfg.pass },
  });
  return { transporter, configured: !!cfg.user };
}

export async function getTransporter() {
  if (!transporter) {
    const result = await createTransporter();
    return result;
  }
  return { transporter, configured: true };
}

export default fp(async function mailerPlugin(fastify: FastifyInstance) {
  try {
    const { transporter: t, configured } = await createTransporter();
    if (!configured) {
      fastify.log.warn('SMTP 未配置，邮件功能不可用。请在管理后台→系统设置中填写发件邮箱和授权码');
    } else {
      await t.verify();
      fastify.log.info('SMTP 邮件服务已连接');
    }
  } catch {
    fastify.log.warn('SMTP 连接失败，请检查邮箱配置');
  }

  // mailer 通过 getTransporter() 动态获取，不挂载到 fastify 实例
});
