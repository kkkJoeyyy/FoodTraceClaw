import { useState, useCallback, useRef, useEffect } from 'react';
import { Message, Store } from '../types';
import { sendMessageStream } from '../api';

const PAGE_SIZE = 5;

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

function getSessionId(): string {
  let sid = localStorage.getItem('foodtrace_session');
  if (!sid) {
    sid = generateId();
    localStorage.setItem('foodtrace_session', sid);
  }
  return sid;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState<string>('');
  const sessionId = useRef(getSessionId());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, statusText, scrollToBottom]);

  const send = useCallback(async (text: string, images: string[] = []) => {
    if (!text.trim() && images.length === 0) return;

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: text,
      image: images[0] || undefined,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setStatusText('');

    const assistantId = generateId();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    await sendMessageStream(text, sessionId.current, images, {
      onStatus: (statusText) => {
        setStatusText(statusText);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: statusText } : m
          )
        );
      },
      onToken: (token) => {
        setStatusText('');
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === assistantId) {
              const newContent = m.content + token;
              return { ...m, content: newContent };
            }
            return m;
          })
        );
      },
      onText: (text) => {
        setStatusText('');
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: text } : m
          )
        );
      },
      onDone: (data) => {
        setStatusText('');
        const allStores = data.all_stores || data.stores || [];
        const total = data.total ?? allStores.length;
        const initialVisible = Math.min(PAGE_SIZE, allStores.length);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: data.reply,
                  stores: allStores.slice(0, initialVisible),
                  allStores: allStores,
                  total: total,
                  visibleCount: initialVisible,
                }
              : m
          )
        );
      },
      onError: (error) => {
        setStatusText('');
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `发送失败：${error}` }
              : m
          )
        );
      },
    });

    setLoading(false);
  }, []);

  /** Show more stores for the last query message (local pagination, no API call). */
  const showMore = useCallback(() => {
    setMessages((prev) => {
      // Find the most recent assistant message with allStores
      const updated = [...prev];
      for (let i = updated.length - 1; i >= 0; i--) {
        const m = updated[i];
        if (m.role === 'assistant' && m.allStores && m.allStores.length > 0) {
          const currentVisible = m.visibleCount ?? PAGE_SIZE;
          const newVisible = currentVisible + PAGE_SIZE;
          if (newVisible >= m.allStores.length) {
            // Show all remaining + exhausted message
            updated[i] = {
              ...m,
              stores: m.allStores,
              visibleCount: m.allStores.length,
              content: m.content + '\n\n已经竭尽数据库了！',
            };
          } else {
            updated[i] = {
              ...m,
              stores: m.allStores.slice(0, newVisible),
              visibleCount: newVisible,
            };
          }
          return updated;
        }
      }
      return prev;
    });
  }, []);

  return { messages, loading, statusText, send, showMore, messagesEndRef };
}
