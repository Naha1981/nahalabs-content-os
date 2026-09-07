// Asset storage for the Video Factory — generated images/audio live under
// public/generated/<projectId>/ and are served as static files in dev.

import fs from 'node:fs/promises'
import path from 'node:path'

export const GENERATED_ROOT = path.join(process.cwd(), 'public', 'generated')

export async function ensureProjectDir(projectId: string): Promise<string> {
  const dir = path.join(GENERATED_ROOT, projectId)
  await fs.mkdir(dir, { recursive: true })
  return dir
}

export async function saveAsset(
  projectId: string,
  filename: string,
  buffer: Buffer
): Promise<string> {
  await ensureProjectDir(projectId)
  const filePath = path.join(GENERATED_ROOT, projectId, filename)
  await fs.writeFile(filePath, buffer)
  return `/generated/${projectId}/${filename}`
}

export async function removeProjectAssets(projectId: string): Promise<void> {
  await fs.rm(path.join(GENERATED_ROOT, projectId), { recursive: true, force: true })
}

export async function readAssetBuffer(publicUrl: string): Promise<Buffer> {
  const rel = publicUrl.replace(/^\/+/, '')
  const filePath = path.join(process.cwd(), 'public', rel)
  return fs.readFile(filePath)
}
