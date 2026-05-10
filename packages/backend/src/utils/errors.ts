export class AppError extends Error {
  constructor(
    public statusCode: number,
    message: string,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export function badRequest(message: string) {
  return new AppError(400, message);
}

export function unauthorized(message: string = '未登录或 token 已过期') {
  return new AppError(401, message);
}

export function forbidden(message: string = '权限不足') {
  return new AppError(403, message);
}

export function notFound(message: string = '资源不存在') {
  return new AppError(404, message);
}

export function tooMany(message: string = '操作过于频繁，请稍后再试') {
  return new AppError(429, message);
}
