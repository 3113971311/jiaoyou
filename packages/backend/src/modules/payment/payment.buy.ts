import type { FastifyInstance } from 'fastify';
import { prisma } from '../../plugins/prisma';
import { authenticate } from '../../middleware/authenticate';
import { getTransporter } from '../../plugins/mailer';
import { generateCardCode, hashCardCode } from '../../utils/card-code';
import { badRequest } from '../../utils/errors';

const PLANS: Record<number, number> = { 7: 9.9, 30: 29.9, 90: 69.9, 180: 119.9, 360: 199.9 };

export default async function cardBuyRoutes(fastify: FastifyInstance) {
  fastify.post('/api/cards/buy', { preHandler: [authenticate] }, async (request) => {
    const userId = (request.user as any).sub;
    const { days, email } = request.body as any;

    if (!PLANS[days]) throw badRequest('无效的套餐');
    if (!email) throw badRequest('请填写邮箱');

    // 生成一张卡密（面值=选择的天数，销毁天数=365天）
    const code = generateCardCode();
    const codeHash = hashCardCode(code);
    const expiresAt = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000);

    // 创建批次（单张卡密自动批次）
    const batch = await prisma.cardBatch.create({
      data: { batchName: `用户购买-${days}天`, denominationDays: days, expireDays: 365, quantity: 1, generatedBy: userId, note: `用户购买，邮箱: ${email}` },
    });

    await prisma.card.create({
      data: { batchId: batch.id, cardCode: code, codeHash, denominationDays: days, expiresAt },
    });

    // 发送邮件
    const { transporter, configured } = await getTransporter();
    if (!configured) throw badRequest('邮件服务未配置，请联系站长');

    const smtpUserCfg = await prisma.siteConfig.findUnique({ where: { configKey: 'smtp_user' } });
    const fromAddress = smtpUserCfg?.configValue || '';

    try {
      await transporter.sendMail({
        from: `"交友平台" <${fromAddress}>`,
        to: email,
        subject: '您购买的VIP卡密',
        html: `
          <h3>感谢购买！</h3>
          <p>您的VIP卡密为：</p>
          <h2 style="color:#1989fa">${code}</h2>
          <p>面值：<strong>${days}天VIP</strong></p>
          <p>使用方法：登录平台 → VIP会员 → 输入卡密兑换</p>
          <p>卡密有效期：${expiresAt.toLocaleDateString()} 之前使用</p>
          <hr>
          <p style="color:#999;font-size:12px">如有疑问请联系站长</p>
        `,
      });
    } catch (err: any) {
      // 邮件发送失败则删除卡片
      await prisma.card.delete({ where: { cardCode: code } });
      throw badRequest('邮件发送失败: ' + (err.message || '未知错误'));
    }

    return { message: '购买成功，卡密已发送至您的邮箱', days, email };
  });
}
