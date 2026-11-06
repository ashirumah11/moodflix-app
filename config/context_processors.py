from datetime import datetime
from django.conf import settings

def moodflix_context(request):
    """
    Global template context processor for MoodFlix.
    Provides watchlist count, mood definitions, and environment status.
    """
    watchlist_count = 0
    if request.user.is_authenticated:
        try:
            from watchlist.models import Watchlist
            watchlist_count = Watchlist.objects.filter(user=request.user).count()
        except Exception:
            watchlist_count = 0

    moods = [
        {
            'slug': 'happy',
            'name': 'Happy',
            'emoji': '😄',
            'icon': 'smile',
            'description': 'Uplifting comedies, feel-good animation & cheerful vibes',
            'color': '#10B981',
            'gradient': 'linear-gradient(135deg, #10B981, #059669)',
        },
        {
            'slug': 'sad',
            'name': 'Sad',
            'emoji': '🥺',
            'icon': 'frown',
            'description': 'Heartfelt dramas, emotional journeys & deep catharsis',
            'color': '#3B82F6',
            'gradient': 'linear-gradient(135deg, #3B82F6, #1D4ED8)',
        },
        {
            'slug': 'relaxed',
            'name': 'Relaxed',
            'emoji': '☕',
            'icon': 'coffee',
            'description': 'Soothing documentaries, gentle romances & chill stories',
            'color': '#06B6D4',
            'gradient': 'linear-gradient(135deg, #06B6D4, #0E7490)',
        },
        {
            'slug': 'stressed',
            'name': 'Stressed',
            'emoji': '🧘',
            'icon': 'zap-off',
            'description': 'Lighthearted escapism, pure fun & stress-melting laughter',
            'color': '#F59E0B',
            'gradient': 'linear-gradient(135deg, #F59E0B, #D97706)',
        },
        {
            'slug': 'adventurous',
            'name': 'Adventurous',
            'emoji': '🚀',
            'icon': 'compass',
            'description': 'Thrilling action, epic fantasy & mind-bending sci-fi',
            'color': '#EC4899',
            'gradient': 'linear-gradient(135deg, #EC4899, #BE185D)',
        },
        {
            'slug': 'romantic',
            'name': 'Romantic',
            'emoji': '💖',
            'icon': 'heart',
            'description': 'Passionate tales, swoon-worthy chemistry & love stories',
            'color': '#8B5CF6',
            'gradient': 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
        },
    ]

    return {
        'watchlist_count': watchlist_count,
        'global_moods': moods,
        'current_year': datetime.now().year,
        'tmdb_configured': bool(settings.TMDB_API_KEY or settings.TMDB_READ_ACCESS_TOKEN),
        'debug': settings.DEBUG,
    }
