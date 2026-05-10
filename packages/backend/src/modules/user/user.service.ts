import { prisma } from '../../plugins/prisma';
import { notFound, badRequest } from '../../utils/errors';
import { processImage, ALLOWED_MIME_TYPES, MAX_FILE_SIZE } from '../../utils/image';
import type { FastifyInstance } from 'fastify';

export async function getUserById(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      username: true,
      nickname: true,
      avatarUrl: true,
      avatarStaging: true,
      gender: true,
      birthday: true,
      bio: true,
      location: true,
      status: true,
      vipExpiresAt: true,
      createdAt: true,
      // 关注数
      _count: {
        select: {
          followerRelations: true,
          followedRelations: true,
          moments: { where: { status: 'approved' } },
        },
      },
    },
  });

  if (!user || user.status === 'banned') throw notFound('用户不存在');

  const isVip = user.vipExpiresAt ? user.vipExpiresAt > new Date() : false;

  return {
    ...user,
    isVip,
    followerCount: user._count.followerRelations,
    followingCount: user._count.followedRelations,
    momentCount: user._count.moments,
    _count: undefined,
  };
}

export async function updateProfile(
  userId: string,
  data: {
    nickname?: string;
    gender?: string;
    birthday?: string;
    bio?: string;
    location?: string;
  },
) {
  const updateData: any = {};

  if (data.nickname !== undefined) updateData.nickname = data.nickname;
  if (data.gender !== undefined) updateData.gender = data.gender;
  if (data.birthday !== undefined) updateData.birthday = new Date(data.birthday);
  if (data.bio !== undefined) updateData.bio = data.bio;
  if (data.location !== undefined) updateData.location = data.location;

  const user = await prisma.user.update({
    where: { id: userId },
    data: updateData,
  });

  return { message: '资料已更新' };
}

export async function uploadAvatar(
  fastify: FastifyInstance,
  userId: string,
  fileBuffer: Buffer,
  mimeType: string,
) {
  if (!ALLOWED_MIME_TYPES.includes(mimeType)) {
    throw badRequest('仅支持 JPG、PNG、WebP 格式');
  }
  if (fileBuffer.length > MAX_FILE_SIZE) {
    throw badRequest('图片大小不能超过 10MB');
  }

  // 处理图片
  const { buffer, thumbBuffer, filename, thumbFilename } = await processImage(fileBuffer);

  const storage = fastify.storage;

  // 上传原图到暂存区
  const stagingPath = storage.stagingPath('avatar', userId, filename);
  await storage.client.putObject(storage.bucket, stagingPath, buffer);

  // 上传缩略图
  let thumbStagingPath: string | undefined;
  if (thumbBuffer && thumbFilename) {
    thumbStagingPath = storage.thumbPath('avatar', userId, thumbFilename);
    await storage.client.putObject(storage.bucket, thumbStagingPath, thumbBuffer);
  }

  // 生成可访问的 URL（staging 区，仅供管理员审核用）
  const imageUrl = `/${stagingPath}`;
  const thumbnailUrl = thumbStagingPath ? `/${thumbStagingPath}` : undefined;

  // 更新用户头像暂存 URL
  await prisma.user.update({
    where: { id: userId },
    data: { avatarStaging: imageUrl },
  });

  // 写入审核队列
  await prisma.reviewQueue.create({
    data: {
      imageUrl,
      thumbnailUrl,
      imageType: 'avatar',
      relatedId: userId,
      submittedBy: userId,
      status: 'pending',
    },
  });

  return {
    message: '头像已上传，等待审核',
    stagingUrl: imageUrl,
    status: 'pending_review',
  };
}
