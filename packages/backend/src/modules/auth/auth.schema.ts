import { z } from 'zod';

export const registerBody = z.object({
  username: z
    .string()
    .min(3, '用户名至少3个字符')
    .max(20, '用户名最多20个字符')
    .regex(/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, '用户名只能包含字母、数字、下划线和中文'),
  email: z.string().email('邮箱格式不正确'),
  password: z.string().min(6, '密码至少6位').max(50, '密码最多50位'),
  code: z.string().length(6, '验证码为6位数字'),
});

export const loginBody = z.object({
  account: z.string().min(1, '请输入用户名或邮箱'),
  password: z.string().min(1, '请输入密码'),
});

export const refreshBody = z.object({
  refreshToken: z.string().min(1),
});

export const sendCodeBody = z.object({
  email: z.string().email('邮箱格式不正确'),
  purpose: z.enum(['register', 'reset_password']),
});

export const resetPasswordBody = z.object({
  email: z.string().email(),
  code: z.string().length(6),
  newPassword: z.string().min(6, '密码至少6位'),
});

export const changePasswordBody = z.object({
  oldPassword: z.string().min(1),
  newPassword: z.string().min(6, '密码至少6位'),
});
