// ===== MusicLab Shared Types =====

// --- Auth ---
export interface User {
	id: number;
	username: string;
	lastfm_username: string | null;
}

export interface LoginRequest {
	username: string;
	password: string;
}

export interface LoginResponse {
	user: User;
	message: string;
}

// --- Last.fm Profile ---
export interface LastfmProfile {
	username: string;
	playcount: number;
	artist_count: number;
	top_artists: TopArtist[];
	top_tags: string[];
	top_genres: Array<{ name: string; count: number }>;
	recent_tracks: RecentTrack[];
	updated_at: string;
}

export interface TopArtist {
	name: string;
	playcount: number;
	url: string;
	image_url?: string;
}

export interface RecentTrack {
	name: string;
	artist: string;
	album?: string;
	played_at?: string;
	image_url?: string;
}

// --- Discovery ---
export interface DiscoveryCard {
	id: string;
	artist_name: string;
	genre_tags: string[];
	era: string;
	ai_blurb: string;
	why_it_matches: string;
	lastfm_listeners?: number | null;
	lastfm_playcount?: number | null;
	mb_data?: Record<string, any> | null;
	discogs_data?: Record<string, any> | null;
	already_in_lidarr: boolean;
}

export interface DiscoveryBatch {
	id: string;
	cards: DiscoveryCard[];
	created_at: string;
}

// --- Lidarr ---
export interface LidarrArtist {
	id: number;
	artistName: string;
	foreignArtistId: string;
	overview?: string;
	qualityProfileId: number;
	rootFolderPath: string;
	monitored: boolean;
	images?: ArtistImage[];
}

export interface ArtistImage {
	coverType: string;
	url: string;
}

export interface AddArtistRequest {
	artistName: string;
	foreignArtistId: string;
	qualityProfileId: number;
	rootFolderPath: string;
	monitored?: boolean;
}

export interface QualityProfile {
	id: number;
	name: string;
}

export interface RootFolder {
	id: number;
	path: string;
	freeSpace?: number;
}

// --- Chat ---
export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp?: string;
}

export interface MemoryBlock {
	summary: string;
	key_facts: string[];
	updated_at: string;
}

// --- Settings ---
export interface AppSettings {
	lastfm_username: string;
	lidarr_url: string;
	lidarr_api_key: string;
	llm_provider: 'openai' | 'anthropic' | 'ollama';
	llm_api_key: string;
	llm_model: string;
	theme: 'light' | 'dark';
}

// --- API ---
export interface ApiError {
	detail: string;
	status: number;
}
