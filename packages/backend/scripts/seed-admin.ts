import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function seed() {
  const username = process.env.ADMIN_USERNAME || 'admin';
  const email = process.env.ADMIN_EMAIL || 'admin@example.com';
  const password = process.env.ADMIN_PASSWORD || 'admin123456';

  const passwordHash = await bcrypt.hash(password, 12);

  const admin = await prisma.user.upsert({
    where: { username },
    update: {},
    create: {
      username,
      email,
      passwordHash,
      nickname: '管理员',
      isAdmin: true,
      gender: 'male',
    },
  });

  console.log(`管理员账号已创建:`);
  console.log(`  用户名: ${admin.username}`);
  console.log(`  邮箱: ${admin.email}`);

  // 初始化默认 site_configs
  const defaults = [
    { key: 'announcement', value: '<p>欢迎来到交友平台！</p>', type: 'html', desc: '首页公告' },
    { key: 'about_us', value: '<p>关于我们</p>', type: 'html', desc: '关于我们' },
    { key: 'user_agreement', value: '<p>用户协议内容</p>', type: 'html', desc: '用户协议' },
    { key: 'privacy_policy', value: '<p>隐私政策内容</p>', type: 'html', desc: '隐私政策' },
    { key: 'chat_rules', value: '<p>请文明聊天</p>', type: 'html', desc: '聊天规范' },
    { key: 'register_welcome', value: '欢迎加入，请完善您的个人资料', type: 'text', desc: '注册欢迎语' },
    { key: 'vip_benefits', value: '[]', type: 'json', desc: 'VIP权益列表' },
    { key: 'home_banner', value: '{"images":[],"interval":3}', type: 'json', desc: '首页轮播图' },
    { key: 'smtp_host', value: 'smtp.qq.com', type: 'text', desc: 'SMTP服务器' },
    { key: 'smtp_port', value: '465', type: 'text', desc: 'SMTP端口' },
    { key: 'smtp_user', value: '', type: 'text', desc: '发件邮箱地址' },
    { key: 'smtp_pass', value: '', type: 'text', desc: '邮箱授权码' },
  ];

  for (const item of defaults) {
    await prisma.siteConfig.upsert({
      where: { configKey: item.key },
      update: {},
      create: {
        configKey: item.key,
        configValue: item.value,
        valueType: item.type,
        description: item.desc,
      },
    });
  }

  console.log(`已初始化 ${defaults.length} 个系统配置项`);

  await prisma.$disconnect();
}

seed().catch((e) => {
  console.error(e);
  process.exit(1);
});
