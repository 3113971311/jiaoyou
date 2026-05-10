import crypto from 'crypto';
import { config } from '../config';

const CHARSET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // 30 chars, no 0/O/1/I/L

export function generateCardCode(): string {
  const chars: string[] = [];
  while (chars.length < 16) {
    const byte = crypto.randomBytes(1)[0];
    if (byte < 240) { // 240 = 30 * 8, 避免取模偏差
      chars.push(CHARSET[byte % 30]);
    }
  }
  // 格式: XXXX-XXXX-XXXX-XXXX
  return `${chars.slice(0, 4).join('')}-${chars.slice(4, 8).join('')}-${chars.slice(8, 12).join('')}-${chars.slice(12, 16).join('')}`;
}

export function hashCardCode(code: string): string {
  const normalized = code.replace(/-/g, '').toUpperCase();
  return crypto.createHash('sha256').update(config.CARD_PEPPER + normalized).digest('hex');
}

export function normalizeCardCode(code: string): string {
  return code.replace(/-/g, '').toUpperCase();
}
