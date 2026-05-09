import { useChat } from './hooks/useChat';
import ChatWindow from './components/ChatWindow';
import InputArea from './components/InputArea';

export default function App() {
  const { messages, loading, send, showMore, messagesEndRef } = useChat();

  return (
    <div style={styles.app}>
      <div style={styles.header}>
        <span style={styles.logo}>🍜</span>
        <span style={styles.title}>FoodTrace</span>
      </div>
      <ChatWindow
        messages={messages}
        loading={loading}
        messagesEndRef={messagesEndRef}
        onMore={showMore}
      />
      <InputArea onSend={send} disabled={loading} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    display: 'flex',
    flexDirection: 'column',
    height: '100dvh',
    maxWidth: 640,
    margin: '0 auto',
    background: '#fafafa',
  },
  header: {
    padding: '12px 16px',
    background: '#fff',
    borderBottom: '1px solid #eee',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  logo: { fontSize: 20 },
  title: { fontSize: 16, fontWeight: 700, color: '#ff6b35' },
};
