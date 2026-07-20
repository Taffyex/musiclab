// ===== MusicLab Shared Types =====

// --- Auth ---
export interface User {
	id: number;
	username: string;
	lastfm_username: string | null;
	llm_provider?: string;
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
	top_tags: Array<{ name: string; count: number }>;
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
	timestamp?: number;
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

// --- Explore ---
export interface Genre { id: number; name: string; slug: string; source: string; style_count: number; }
export interface Style { id: number; name: string; slug: string; genre_id: number; genre_name: string; }
export interface GenreTree { genre: Genre; styles: Style[]; }

export interface ArtistSummary {
	id: number; name: string; slug: string; image_url: string;
	lastfm_listeners: number | null; lastfm_playcount: number | null;
	genres: string[]; styles: string[];
	already_in_lidarr: boolean;
}

export interface ArtistDetail extends ArtistSummary {
	bio: string; discogs_profile: string; country: string;
	begin_date: string; end_date: string; artist_type: string;
	mb_tags: string[]; mb_relations: MBRelation[];
	releases: ReleaseDetail[]; similar_artists: ArtistSummary[];
	lidarr_artist: Record<string, any> | null;
}

export interface ReleaseDetail {
	id: number; title: string; year: number | null;
	release_type: string; label: string; format: string;
	cover_url: string; genres: string[]; styles: string[];
	credits: Credit[];
}

export interface Credit {
	id: number; entity_name: string; entity_slug: string;
	role: string; entity_type: string;
}

export interface CreditEntity {
	name: string; slug: string; entity_type: string;
	roles: string[]; release_count: number;
	releases: ReleaseWithArtist[];
}

export interface ReleaseWithArtist {
	release_id: number; title: string; year: number | null;
	artist_name: string; artist_slug: string; role: string; cover_url: string;
}

export interface MBRelation {
	type: string; direction: string; target_name: string;
	target_mbid: string; begin: string; end: string;
}

export interface ExploreFilters {
	genre?: string; style?: string; decade?: string;
	sort_by: 'listeners' | 'scrobbles' | 'name';
	sort_order: 'asc' | 'desc';
	page: number; per_page: number;
}

export interface FavoriteItem {
	entity_type: 'artist' | 'genre' | 'style';
	entity_id: number;
	name: string;
	slug: string;
	image_url?: string;
}

export interface UserFavorites {
	artists: FavoriteItem[];
	genres: FavoriteItem[];
	styles: FavoriteItem[];
}
