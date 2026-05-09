import { Message } from '../types';
import StoreList from './StoreList';

interface Props {
  message: Message;
  onMore?: () => void;
  loading?: boolean;
}

export default function MessageBubble({ message, onMore, loading }: Props) {
  const isUser = message.role === 'user';
  const allCount = message.allStores?.length ?? 0;
  const visible = message.visibleCount ?? 0;
  const hasMore = allCount > visible;
  const remaining = allCount - visible;

  return (
    <div style={{ ...styles.wrapper, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      {!isUser && <div style={styles.avatar}>🍜</div>}
      <div style={styles.content}>
        <div style={{
          ...styles.bubble,
          ...(isUser ? styles.userBubble : styles.assistantBubble),
        }}>
          {message.image && (
            <img src={message.image} alt="shared" style={styles.image} />
          )}
          {message.content && <div style={styles.text}>{message.content}</div>}
        </div>
        {message.stores && message.stores.length > 0 && (
          <StoreList
            stores={message.stores}
            hasMore={hasMore}
            totalRemaining={remaining}
            onMore={onMore}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    marginBottom: 16,
    padding: '0 4px',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    background: '#ff6b35',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 16,
    marginRight: 8,
    flexShrink: 0,
  },
  content: {
    maxWidth: '85%',
    minWidth: 0,
  },
  bubble: {
    borderRadius: 12,
    padding: '10px 14px',
    display: 'inline-block',
    wordBreak: 'break-word',
  },
  userBubble: {
    background: '#ff6b35',
    color: '#fff',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    background: '#f5f5f5',
    color: '#1a1a1a',
    borderBottomLeftRadius: 4,
  },
  text: {
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
  },
  image: {
    maxWidth: 240,
    maxHeight: 240,
    borderRadius: 8,
    marginBottom: 6,
    display: 'block',
  },
};
