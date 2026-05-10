import sharp from 'sharp';
import path from 'path';
import crypto from 'crypto';

export async function processImage(
  buffer: Buffer,
  options: { thumbnail?: boolean } = {},
) {
  const { thumbnail = true } = options;

  // 剥离 EXIF 元数据
  let image = sharp(buffer, { failOnError: false }).rotate();

  const metadata = await image.metadata();
  const ext = metadata.format === 'png' ? 'png' : 'jpeg';

  // 原图处理：限制最大 1920px 宽度，jpeg 质量 85
  const processed = await image
    .resize(1920, 1920, { fit: 'inside', withoutEnlargement: true })
    .jpeg({ quality: 85 })
    .toBuffer();

  let thumbBuffer: Buffer | undefined;
  if (thumbnail) {
    // 缩略图：300x300，jpeg 质量 70
    thumbBuffer = await sharp(processed)
      .resize(300, 300, { fit: 'cover' })
      .jpeg({ quality: 70 })
      .toBuffer();
  }

  // 生成唯一文件名
  const filename = `${crypto.randomUUID()}.${ext}`;
  const thumbFilename = thumbnail ? `${crypto.randomUUID()}_thumb.jpg` : undefined;

  return {
    buffer: processed,
    thumbBuffer,
    filename,
    thumbFilename,
    mimeType: 'image/jpeg',
  };
}

export const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
