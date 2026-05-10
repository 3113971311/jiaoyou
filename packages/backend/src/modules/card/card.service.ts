import { prisma } from '../../plugins/prisma';
import { generateCardCode, hashCardCode } from '../../utils/card-code';

export async function generateBatch(
  generatedBy: string,
  batchName: string,
  denominationDays: number,
  expireDays: number,
  quantity: number,
  note?: string,
) {
  const batch = await prisma.cardBatch.create({
    data: { batchName, denominationDays, expireDays, quantity, generatedBy, note },
  });

  const codes: string[] = [];
  const expiresAt = new Date(Date.now() + expireDays * 24 * 60 * 60 * 1000);

  // 批量生成卡密
  for (let i = 0; i < quantity; i++) {
    const code = generateCardCode();
    codes.push(code);

    await prisma.card.create({
      data: {
        batchId: batch.id,
        cardCode: code,
        codeHash: hashCardCode(code),
        denominationDays,
        expiresAt,
      },
    });
  }

  return {
    batchId: batch.id,
    batchName: batch.batchName,
    quantity: batch.quantity,
    denominationDays,
    expireDays,
    codes, // 仅在生成时返回明文，之后只能通过导出获取
  };
}

export async function listBatches(page: number = 1, limit: number = 20) {
  const [items, total] = await Promise.all([
    prisma.cardBatch.findMany({
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: {
        _count: { select: { cards: true } },
        cards: {
          where: {},
          select: { status: true },
        },
      },
    }),
    prisma.cardBatch.count(),
  ]);

  const list = items.map((b) => {
    const used = b.cards.filter((c) => c.status === 'used').length;
    const expired = b.cards.filter((c) => c.status === 'expired').length;
    const unused = b.cards.filter((c) => c.status === 'unused').length;
    return {
      id: b.id,
      batchName: b.batchName,
      denominationDays: b.denominationDays,
      expireDays: b.expireDays,
      quantity: b.quantity,
      used,
      unused,
      expired,
      createdAt: b.createdAt,
    };
  });

  return { items: list, total, page, limit };
}

export async function getBatchDetail(batchId: string, page: number = 1, limit: number = 30, status?: string) {
  const batch = await prisma.cardBatch.findUnique({ where: { id: batchId } });
  if (!batch) throw new Error('批次不存在');

  const where: any = { batchId };
  if (status) where.status = status;

  const [items, total] = await Promise.all([
    prisma.card.findMany({
      where,
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'asc' },
      select: {
        id: true,
        cardCode: true, // 返回明文（掩码处理）
        denominationDays: true,
        status: true,
        usedBy: true,
        usedAt: true,
        expiresAt: true,
        createdAt: true,
      },
    }),
    prisma.card.count({ where }),
  ]);

  // 详情页返回完整卡密（不掩码），方便站长复制
  return { batch, items, total, page, limit };
}

export async function exportBatch(batchId: string) {
  const batch = await prisma.cardBatch.findUnique({ where: { id: batchId } });
  if (!batch) throw new Error('批次不存在');

  const cards = await prisma.card.findMany({
    where: { batchId },
    orderBy: { createdAt: 'asc' },
    select: {
      cardCode: true,
      denominationDays: true,
      status: true,
      expiresAt: true,
    },
  });

  // 生成 CSV
  const header = '卡密,面值(天),状态,过期时间\n';
  const rows = cards
    .map((c) => `${c.cardCode},${c.denominationDays},${c.status},${c.expiresAt?.toISOString() || ''}`)
    .join('\n');

  return {
    batchName: batch.batchName,
    csvContent: header + rows,
  };
}

// 定时清理过期卡密
export async function cleanupExpiredCards() {
  const result = await prisma.card.updateMany({
    where: {
      status: 'unused',
      expiresAt: { lt: new Date() },
    },
    data: { status: 'expired' },
  });
  return { cleaned: result.count };
}
