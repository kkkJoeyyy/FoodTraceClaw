export interface Dish {
  id: number;
  store_id: number;
  name: string;
  description: string;
}

export interface Store {
  id: number;
  name: string;
  location: string;
  address: string;
  lat: number | null;
  lon: number | null;
  description: string;
  category: string;
  source_type: string;
  created_at: string;
  dishes: Dish[];
  _distance_km?: number | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  stores?: Store[];
  allStores?: Store[];      // ALL stores from query (for local pagination)
  total?: number;
  visibleCount?: number;     // how many currently shown
  has_more?: boolean;
  total_remaining?: number;
  image?: string;
  timestamp: Date;
}
