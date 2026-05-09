import { RefObject } from 'react';
import { Message } from '../types';
import MessageBubble from './MessageBubble';

interface Props {
  messages: Message[];
  loading: boolean;
  messagesEndRef: RefObject<HTMLDivElement>;
  onMore: () => void;
}

export default function ChatWindow({ messages, loading, messagesEndRef, onMore }: Props) {
  return (
    <div style={styles.container}>
      {messages.length === 0 && (
        <div style={styles.placeholder}>
          <div style={styles.icon}>🍜</div>
          <div style={styles.title}>FoodTrace 美食追踪</div>
          <div style={styles.hint}>
            粘贴抖音/小红书的分享文案或截图<br />
            我会提取其中的美食店铺和菜品<br />
            问一句「成都春熙路有什么好吃的」试试吧
          </div>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onMore={onMore} loading={loading} />
      ))}
      {loading && (
        <div style={styles.typing}>
          <span style={styles.dot}>●</span>
          <span style={{ ...styles.dot, animationDelay: '0.2s' }}>●</span>
          <span style={{ ...styles.dot, animationDelay: '0.4s' }}>●</span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 12px',
  },
  placeholder: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#aaa',
    textAlign: 'center',
  },
  icon: { fontSize: 48, marginBottom: 16 },
  title: { fontSize: 20, fontWeight: 600, color: '#333', marginBottom: 12 },
  hint: { fontSize: 14, lineHeight: 1.8 },
  typing: {
    display: 'flex',
    gap: 4,
    padding: '8px 12px',
  },
  dot: {
    fontSize: 8,
    color: '#ccc',
    animation: 'blink 1.4s infinite',
  },
};
