import { Store } from '../types';

interface Props {
  store: Store;
  index?: number;
}

export default function StoreCard({ store, index }: Props) {
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        {index !== undefined && <span style={styles.rank}>{index}.</span>}
        <div style={styles.info}>
          <div style={styles.nameRow}>
            <span style={styles.name}>{store.name}</span>
            {store.category && <span style={styles.category}>{store.category}</span>}
          </div>
          <div style={styles.location}>
            📍 {store.location}
            {store.address ? ` · ${store.address}` : ''}
            {store._distance_km != null && (
              <span style={styles.distance}> {(store._distance_km).toFixed(1)}km</span>
            )}
          </div>
        </div>
      </div>
      {store.description && <div style={styles.desc}>{store.description}</div>}
      {store.dishes.length > 0 && (
        <div style={styles.dishes}>
          {store.dishes.map((d) => (
            <span key={d.id} style={styles.dishTag} title={d.description || undefined}>
              {d.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: '14px 16px',
    marginBottom: 10,
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    border: '1px solid #f0f0f0',
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
  },
  rank: {
    fontSize: 16,
    fontWeight: 700,
    color: '#ff6b35',
    minWidth: 24,
    lineHeight: '22px',
  },
  info: { flex: 1 },
  nameRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  name: { fontSize: 16, fontWeight: 600, color: '#1a1a1a' },
  category: {
    fontSize: 11,
    color: '#ff6b35',
    background: '#fff3ed',
    padding: '2px 6px',
    borderRadius: 4,
  },
  location: { fontSize: 13, color: '#888' },
  distance: { color: '#4a90d9', fontWeight: 500 },
  desc: { fontSize: 13, color: '#555', marginTop: 8, lineHeight: 1.5 },
  dishes: { display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  dishTag: {
    fontSize: 12,
    color: '#333',
    background: '#f7f7f7',
    padding: '4px 10px',
    borderRadius: 20,
    border: '1px solid #eee',
  },
};
