import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const p = new PrismaClient();
async function main() {
  const u = await p.user.findUnique({ where: { username: 'admin' } });
  if (!u) { console.log('no admin found, creating...');
    const hash = await bcrypt.hash('admin123456', 12);
    await p.user.create({ data: { username: 'admin', email: 'admin@example.com', passwordHash: hash, nickname: '管理员', isAdmin: true, status: 'active', gender: 'male' } });
    console.log('admin created');
  } else {
    const hash = await bcrypt.hash('admin123456', 12);
    await p.user.update({ where: { id: u.id }, data: { passwordHash: hash, isAdmin: true, status: 'active' } });
    console.log('admin password reset, email:', u.email);
  }
  await p.$disconnect();
}
main();
