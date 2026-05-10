import { z } from 'zod';

export const updateProfileBody = z.object({
  nickname: z.string().max(50).optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  birthday: z.string().optional(), // ISO date string
  bio: z.string().max(500).optional(),
  location: z.string().max(100).optional(),
});
