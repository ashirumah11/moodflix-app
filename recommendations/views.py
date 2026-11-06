from django.shortcuts import render, redirect
from django.contrib import messages
from .engine import MoodRecommendationEngine, MOOD_DEFINITIONS
from .models import MoodHistory
from movies.services import attach_watchlist_status

def mood_selection_view(request):
    """
    Displays the interactive mood selection board.
    """
    recent_history = []
    if request.user.is_authenticated:
        recent_history = MoodHistory.objects.filter(user=request.user).order_by('-selected_at')[:6]

    context = {
        'moods': list(MOOD_DEFINITIONS.values()),
        'recent_history': recent_history,
    }
    return render(request, 'recommendations/mood_selection.html', context)


def mood_results_view(request, mood_slug):
    """
    Processes mood selection, runs recommendation engine, and returns results.
    Supports filtering by genre, sorting, and refreshing.
    """
    genre_filter = request.GET.get('genre')
    sort_by = request.GET.get('sort', 'relevance')
    refresh = request.GET.get('refresh') == '1'

    # Check validity of mood
    mood_slug = mood_slug.lower().strip()
    if mood_slug not in MOOD_DEFINITIONS:
        messages.warning(request, f"Mood '{mood_slug}' not recognized. Showing happy recommendations instead.")
        return redirect('recommendations:mood_results', mood_slug='happy')

    # Get recommendations
    results = MoodRecommendationEngine.recommend(
        mood_slug=mood_slug,
        user=request.user,
        genre_filter=genre_filter,
        sort_by=sort_by,
        record=not refresh  # Don't duplicate history record on quick refresh
    )

    # Attach watchlist status
    recommendations = attach_watchlist_status(request.user, results['recommendations'])

    context = {
        'mood': results['mood'],
        'recommendations': recommendations,
        'total_found': len(recommendations),
        'available_genres': results['available_genres'],
        'selected_genre': results['selected_genre'],
        'sort_by': sort_by,
        'all_moods': list(MOOD_DEFINITIONS.values()),
    }
    return render(request, 'recommendations/results.html', context)
