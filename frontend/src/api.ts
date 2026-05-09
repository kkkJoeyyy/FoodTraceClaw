import { Store } from './types';

const BASE_URL = '/api';

export interface SSECallback {
  onStatus?: (text: string) => void;
  onToken?: (text: string) => void;
  onText?: (text: string) => void;
  onDone?: (data: {
    intent: string;
    reply: string;
    stores: Store[];
    all_stores?: Store[];
    total?: number;
    has_more?: boolean;
    total_remaining?: number;
  }) => void;
  onError?: (error: string) => void;
}

export async function sendMessageStream(
  message: string,
  sessionId: string,
  images: string[] = [],
  callbacks: SSECallback
): Promise<void> {
  try {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId, images }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            switch (data.type) {
              case 'status':
                callbacks.onStatus?.(data.text);
                break;
              case 'token':
                callbacks.onToken?.(data.text);
                break;
              case 'text':
                callbacks.onText?.(data.text);
                break;
              case 'done':
                callbacks.onDone?.(data);
                break;
            }
          } catch {
            // Skip parse errors for partial chunks
          }
        }
      }
    }
  } catch (e) {
    callbacks.onError?.(e instanceof Error ? e.message : 'Unknown error');
  }
}

export async function fetchStores(page = 1, location = '') {
  const params = new URLSearchParams({ page: String(page), location });
  const res = await fetch(`${BASE_URL}/stores?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function deleteStore(id: number) {
  const res = await fetch(`${BASE_URL}/stores/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${BASE_URL}/stats`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
