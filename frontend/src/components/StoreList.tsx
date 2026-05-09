import { Store } from '../types';
import StoreCard from './StoreCard';

interface Props {
  stores: Store[];
  hasMore?: boolean;
  totalRemaining?: number;
  onMore?: () => void;
  loading?: boolean;
}

export default function StoreList({ stores, hasMore, totalRemaining, onMore, loading }: Props) {
  if (stores.length === 0) return null;

  return (
    <div style={styles.container}>
      {stores.map((store, i) => (
        <StoreCard key={store.id} store={store} index={i + 1} />
      ))}
      {hasMore && onMore && (
        <button style={styles.moreBtn} onClick={onMore} disabled={loading}>
          {loading ? '加载中...' : `还有 ${totalRemaining ?? '?'} 家，点击查看更多 →`}
        </button>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { marginTop: 8 },
  moreBtn: {
    display: 'block',
    width: '100%',
    padding: '10px 0',
    background: 'transparent',
    border: '1px dashed #ddd',
    borderRadius: 8,
    color: '#888',
    fontSize: 13,
    cursor: 'pointer',
    textAlign: 'center',
  },
};
