import { z } from 'zod';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

const envSchema = z.object({
  DATABASE_URL: z.string().default('file:./dev.db'),
  JWT_ACCESS_SECRET: z.string().default('dev-access-secret'),
  JWT_REFRESH_SECRET: z.string().default('dev-refresh-secret'),
  JWT_ACCESS_TTL: z.string().default('15m'),
  JWT_REFRESH_TTL: z.string().default('7d'),
  CARD_PEPPER: z.string().default('dev-card-pepper'),
  SMTP_HOST: z.string().default('smtp.qq.com'),
  SMTP_PORT: z.coerce.number().default(465),
  SMTP_USER: z.string().default(''),
  SMTP_PASS: z.string().default(''),
  AMAP_API_KEY: z.string().optional(),
  APP_PORT: z.coerce.number().default(3000),
  APP_HOST: z.string().default('0.0.0.0'),
  CORS_ORIGIN: z.string().default('http://localhost:5173'),
});

export const config = envSchema.parse(process.env);
export type Config = z.infer<typeof envSchema>;
