import logging
from movies import tmdb
from recommendations.models import MoodHistory

logger = logging.getLogger(__name__)

MOOD_DEFINITIONS = {
    'happy': {
        'slug': 'happy',
        'name': 'Happy',
        'emoji': '😄',
        'icon': 'smile',
        'tagline': 'Uplifting Spirits & Good Times',
        'description': 'Laugh-out-loud comedies, vibrant animation, and wholesome family adventures designed to elevate your mood.',
        'genre_ids': [35, 16, 10751],  # Comedy, Animation, Family
        'primary_genres': ['Comedy', 'Animation', 'Family'],
        'color': '#10B981',
        'gradient': 'linear-gradient(135deg, #10B981, #059669)',
        'min_rating': 6.8,
    },
    'sad': {
        'slug': 'sad',
        'name': 'Sad',
        'emoji': '🥺',
        'icon': 'frown',
        'tagline': 'Emotional Catharsis & Deep Reflection',
        'description': 'Heartfelt dramas, moving romances, and poignant inspirational stories that help you process emotions and find catharsis.',
        'genre_ids': [18, 10749],  # Drama, Romance
        'primary_genres': ['Drama', 'Romance'],
        'color': '#3B82F6',
        'gradient': 'linear-gradient(135deg, #3B82F6, #1D4ED8)',
        'min_rating': 7.0,
    },
    'relaxed': {
        'slug': 'relaxed',
        'name': 'Relaxed',
        'emoji': '☕',
        'icon': 'coffee',
        'tagline': 'Peaceful Viewing & Calm Escapes',
        'description': 'Soothing nature documentaries, gentle romances, and cozy lighthearted films to help you unwind and decompress.',
        'genre_ids': [99, 10749, 35],  # Documentary, Romance, Light Comedy
        'primary_genres': ['Documentary', 'Romance', 'Comedy'],
        'color': '#06B6D4',
        'gradient': 'linear-gradient(135deg, #06B6D4, #0E7490)',
        'min_rating': 6.9,
    },
    'stressed': {
        'slug': 'stressed',
        'name': 'Stressed',
        'emoji': '🧘',
        'icon': 'zap-off',
        'tagline': 'Stress-Busting Fun & Easy Escapism',
        'description': 'Fun-filled comedies, exciting adventures, and colorful animations to turn off overthinking and wash away stress.',
        'genre_ids': [35, 12, 16, 10751],  # Comedy, Adventure, Animation, Family
        'primary_genres': ['Comedy', 'Adventure', 'Animation'],
        'color': '#F59E0B',
        'gradient': 'linear-gradient(135deg, #F59E0B, #D97706)',
        'min_rating': 6.7,
    },
    'adventurous': {
        'slug': 'adventurous',
        'name': 'Adventurous',
        'emoji': '🚀',
        'icon': 'compass',
        'tagline': 'Epic Quests & Thrilling Horizons',
        'description': 'Adrenaline-pumping action, fantastical journeys, and mind-expanding science fiction that ignite your sense of wonder.',
        'genre_ids': [28, 12, 878, 14],  # Action, Adventure, Sci-Fi, Fantasy
        'primary_genres': ['Action', 'Adventure', 'Science Fiction', 'Fantasy'],
        'color': '#EC4899',
        'gradient': 'linear-gradient(135deg, #EC4899, #BE185D)',
        'min_rating': 7.0,
    },
    'romantic': {
        'slug': 'romantic',
        'name': 'Romantic',
        'emoji': '💖',
        'icon': 'heart',
        'tagline': 'Love Stories & Sparkling Chemistry',
        'description': 'Charming rom-coms, passionate relationship sagas, and warm emotional connections that celebrate the magic of love.',
        'genre_ids': [10749, 35, 18],  # Romance, Comedy, Drama
        'primary_genres': ['Romance', 'Comedy', 'Drama'],
        'color': '#8B5CF6',
        'gradient': 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
        'min_rating': 6.9,
    },
}


class MoodRecommendationEngine:
    """
    Intelligent rule-based recommendation engine matching emotional states
    to cinematic themes, genres, and quality ratings.
    """

    @classmethod
    def get_mood_config(cls, mood_slug):
        mood_key = (mood_slug or '').lower().strip()
        return MOOD_DEFINITIONS.get(mood_key)

    @classmethod
    def record_mood_history(cls, user, mood_slug):
        """
        Record user's mood selection for authenticated accounts.
        """
        if user and user.is_authenticated and mood_slug in MOOD_DEFINITIONS:
            try:
                MoodHistory.objects.create(user=user, selected_mood=mood_slug)
            except Exception as e:
                logger.error(f"Failed to record mood history: {e}")

    @classmethod
    def recommend(cls, mood_slug, user=None, genre_filter=None, sort_by="popularity.desc", page=1, record=True):
        """
        Main recommendation pipeline:
        1. Validates emotional state.
        2. Resolves TMDB genre mapping.
        3. Queries TMDB /discover/movie using pipe '|' (OR logic).
        4. Deduplicates results.
        5. Computes multi-factor relevance score.
        6. Records user mood history if authenticated.
        """
        mood_key = (mood_slug or '').lower().strip()
        config = MOOD_DEFINITIONS.get(mood_key)
        if not config:
            mood_key = 'happy'
            config = MOOD_DEFINITIONS['happy']

        if record and user and user.is_authenticated:
            cls.record_mood_history(user, mood_key)

        genre_ids = config['genre_ids']
        if genre_filter:
            try:
                g_id = int(genre_filter)
                genre_ids = [g_id]
            except (ValueError, TypeError):
                pass

        # Query TMDB discover with OR genre logic
        candidates = tmdb.discover_movies_by_genre(
            genre_ids=genre_ids,
            sort_by=sort_by if sort_by != 'relevance' else 'popularity.desc',
            page=page,
            min_vote_average=config.get('min_rating', 6.5)
        )

        # Deduplicate
        seen_ids = set()
        unique_candidates = []
        for item in candidates:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_candidates.append(item)

        # Relevance scoring algorithm
        target_genre_set = set(config['genre_ids'])
        for item in unique_candidates:
            item_genres = set(item.get('genre_ids', []))
            genre_overlap = len(target_genre_set & item_genres)
            vote_avg = item.get('vote_average', 0.0)
            pop = min(item.get('popularity', 0.0), 100.0)

            # Combined weighted score:
            # - 40% genre affinity
            # - 35% user rating
            # - 25% popularity
            affinity_score = (genre_overlap / max(len(target_genre_set), 1)) * 40.0
            rating_score = (vote_avg / 10.0) * 35.0
            pop_score = (pop / 100.0) * 25.0
            item['relevance_score'] = round(affinity_score + rating_score + pop_score, 1)

        # Apply secondary sort if relevance requested
        if sort_by == 'relevance':
            unique_candidates.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return {
            'mood': config,
            'recommendations': unique_candidates,
            'total_found': len(unique_candidates),
            'available_genres': [
                {'id': gid, 'name': tmdb.GENRE_MAP.get(gid, f"Genre {gid}")}
                for gid in config['genre_ids']
            ],
            'selected_genre': int(genre_filter) if genre_filter and str(genre_filter).isdigit() else None,
            'sort_by': sort_by,
        }
