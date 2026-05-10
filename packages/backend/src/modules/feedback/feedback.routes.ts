import type { FastifyInstance } from 'fastify';
import { authenticate } from '../../middleware/authenticate';
import { getTransporter } from '../../plugins/mailer';
import { prisma } from '../../plugins/prisma';

export default async function feedbackRoutes(fastify: FastifyInstance) {
  fastify.post('/api/feedback', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { title, content, contact } = request.body as any;

    const user = await prisma.user.findUnique({ where: { id: userId } });

    // 获取管理员邮箱
    const smtpUser = await prisma.siteConfig.findUnique({ where: { configKey: 'smtp_user' } });
    const adminEmail = smtpUser?.configValue;

    // 如果有配置邮箱，发送邮件通知站长
    if (adminEmail) {
      try {
        const { transporter, configured } = await getTransporter();
        if (configured) {
          await transporter.sendMail({
            from: `"交友平台" <${adminEmail}>`,
            to: adminEmail,
            subject: `【用户反馈】${title}`,
            html: `
              <h3>用户反馈</h3>
              <p><strong>反馈用户：</strong>${user?.username} (${user?.nickname || '-'})</p>
              <p><strong>标题：</strong>${title}</p>
              <p><strong>详细描述：</strong></p>
              <pre>${content}</pre>
              <p><strong>联系方式：</strong>${contact || '未提供'}</p>
            `,
          });
        }
      } catch {}
    }

    return { message: '反馈已提交' };
  });
}
