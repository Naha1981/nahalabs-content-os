export type ApiMode = 'demo' | 'live';

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? '';
export const apiMode: ApiMode = process.env.NEXT_PUBLIC_DEMO_MODE === 'false' ? 'live' : 'demo';

export async function apiFetch<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  if (apiMode === 'demo') throw new Error('Demo mode: live API calls are disabled.');
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
    cache: 'no-store',
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body || response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function checkApiHealth(): Promise<boolean> {
  if (!baseUrl) return false;
  try {
    const response = await fetch(`${baseUrl}/healthz`, { cache: 'no-store' });
    return response.ok;
  } catch {
    return false;
  }
}
