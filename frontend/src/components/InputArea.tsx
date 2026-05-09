import { useState, useRef, useCallback, KeyboardEvent, ClipboardEvent } from 'react';

interface Props {
  onSend: (text: string, images: string[]) => void;
  disabled?: boolean;
}

export default function InputArea({ onSend, disabled }: Props) {
  const [text, setText] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    if (!text.trim() && images.length === 0) return;
    onSend(text, images);
    setText('');
    setImages([]);
    textareaRef.current?.focus();
  }, [text, images, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handlePaste = useCallback((e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (!file) continue;
        const reader = new FileReader();
        reader.onload = () => {
          setImages((prev) => [...prev, reader.result as string]);
        };
        reader.readAsDataURL(file);
      }
    }
  }, []);

  const removeImage = (i: number) => {
    setImages((prev) => prev.filter((_, idx) => idx !== i));
  };

  return (
    <div style={styles.container}>
      {images.length > 0 && (
        <div style={styles.imagePreview}>
          {images.map((img, i) => (
            <div key={i} style={styles.imgWrap}>
              <img src={img} alt={`preview-${i}`} style={styles.img} />
              <button style={styles.removeBtn} onClick={() => removeImage(i)}>✕</button>
            </div>
          ))}
        </div>
      )}
      <div style={styles.inputRow}>
        <textarea
          ref={textareaRef}
          style={styles.textarea}
          placeholder="粘贴分享文案或输入查询..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          rows={1}
          disabled={disabled}
        />
        <button style={styles.sendBtn} onClick={handleSend} disabled={disabled || (!text.trim() && images.length === 0)}>
          发送
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    borderTop: '1px solid #eee',
    padding: '10px 16px',
    background: '#fff',
  },
  imagePreview: {
    display: 'flex',
    gap: 8,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
  imgWrap: {
    position: 'relative',
  },
  img: {
    width: 60,
    height: 60,
    objectFit: 'cover',
    borderRadius: 8,
    border: '1px solid #eee',
  },
  removeBtn: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 20,
    height: 20,
    borderRadius: '50%',
    border: 'none',
    background: '#333',
    color: '#fff',
    fontSize: 10,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  inputRow: {
    display: 'flex',
    gap: 8,
    alignItems: 'flex-end',
  },
  textarea: {
    flex: 1,
    border: '1px solid #e0e0e0',
    borderRadius: 8,
    padding: '8px 12px',
    fontSize: 14,
    lineHeight: 1.5,
    resize: 'none',
    outline: 'none',
    fontFamily: 'inherit',
    maxHeight: 100,
  },
  sendBtn: {
    padding: '8px 20px',
    background: '#ff6b35',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    height: 38,
  },
};
