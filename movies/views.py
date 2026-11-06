from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, Http404
from . import tmdb
from . import services
from watchlist.models import Watchlist

def _is_ajax(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '')
    )


def _get_nonnegative_float(value, default=0.0):
    """Parse optional rating filters without turning malformed query strings into 500s."""
    try:
        return max(float(value), 0.0)
    except (TypeError, ValueError):
        return default


def home_view(request):
    """
    Renders the MoodFlix cinematic homepage with real TMDB sections.
    """
    data = services.get_home_page_data(request.user)
    return render(request, 'home/index.html', data)


def movie_trailer_view(request, media_type, tmdb_id):
    """
    JSON API endpoint to fetch official YouTube trailer information on demand.
    Powers the modal player across movie cards, discover, search, and detail pages.
    """
    if media_type not in ('movie', 'tv'):
        return JsonResponse({'status': 'error', 'has_trailer': False, 'message': 'Invalid media type.'}, status=400)

    try:
        tmdb_id_int = int(tmdb_id)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'has_trailer': False, 'message': 'Invalid title ID.'}, status=400)

    trailer_info = tmdb.get_trailer(tmdb_id_int, media_type)
    if trailer_info and trailer_info.get('key'):
        return JsonResponse({
            'status': 'success',
            'has_trailer': True,
            'key': trailer_info['key'],
            'embed_url': trailer_info['embed_url'],
            'watch_url': trailer_info['watch_url'],
            'name': trailer_info.get('name', 'Official Trailer'),
        })
    else:
        return JsonResponse({
            'status': 'not_found',
            'has_trailer': False,
            'message': 'Sorry, no trailer is currently available for this movie.',
        })


def discover_view(request):
    """
    Browse and discover movies with advanced genre, rating, and sort filters.
    Supports Popular, Top Rated, Now Playing in Theaters, and Upcoming.
    """
    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort', 'popularity.desc')
    media_type = request.GET.get('type', 'movie')
    min_rating = _get_nonnegative_float(request.GET.get('rating', 0.0))
    page_num = request.GET.get('page', 1)

    genres = tmdb.get_movie_genres()

    if media_type == 'tv':
        if sort_by == 'vote_average.desc':
            items = tmdb.get_top_rated_tv(page=page_num)
        else:
            items = tmdb.get_popular_tv(page=page_num)
    else:
        if genre_id:
            items = tmdb.discover_movies_by_genre(genre_id, sort_by=sort_by, page=page_num, min_vote_average=min_rating)
        elif sort_by == 'vote_average.desc':
            items = tmdb.get_top_rated_movies(page=page_num)
        elif sort_by == 'now_playing':
            items = tmdb.get_now_playing_movies(page=page_num)
        elif sort_by == 'upcoming':
            items = tmdb.get_upcoming_movies(page=page_num)
        else:
            items = tmdb.get_popular_movies(page=page_num)

    # Attach watchlist annotations
    services.attach_watchlist_status(request.user, items)

    # Apply pagination (12 per page)
    paginator = Paginator(items, 12)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'page_obj': page_obj,
        'genres': genres,
        'selected_genre': int(genre_id) if genre_id and str(genre_id).isdigit() else None,
        'selected_sort': sort_by,
        'selected_media': media_type,
        'selected_rating': min_rating,
    }
    return render(request, 'movies/discover.html', context)


def trending_view(request):
    """
    Display current trending movies and TV shows across the world.
    """
    time_window = request.GET.get('window', 'day')
    if time_window not in ('day', 'week'):
        time_window = 'day'

    trending_movies = tmdb.get_trending_movies(time_window=time_window)
    trending_tv = tmdb.get_popular_tv()

    services.attach_watchlist_status(request.user, trending_movies)
    services.attach_watchlist_status(request.user, trending_tv)

    context = {
        'trending_movies': trending_movies,
        'trending_tv': trending_tv,
        'time_window': time_window,
    }
    return render(request, 'movies/trending.html', context)


def search_view(request):
    """
    Search movies and TV shows by keyword with dynamic filters.
    Uses TMDB's dedicated endpoints (/search/movie, /search/tv, /search/multi).
    """
    query = request.GET.get('q', '').strip()
    genre_id = request.GET.get('genre')
    media_type = request.GET.get('type', 'all')
    min_rating = _get_nonnegative_float(request.GET.get('rating', 0.0))
    year = request.GET.get('year')
    page_num = request.GET.get('page', 1)

    results = []
    if query:
        if media_type == 'movie':
            raw_results = tmdb.search_movies(query, page=page_num)
        elif media_type == 'tv':
            raw_results = tmdb.search_tv(query, page=page_num)
        else:
            raw_results = tmdb.search_multi(query, page=page_num)

        results = services.filter_content(
            raw_results,
            genre_id=genre_id,
            min_rating=min_rating,
            release_year=year,
            media_type=media_type
        )
        services.attach_watchlist_status(request.user, results)

    # If AJAX live search preview requested
    if _is_ajax(request):
        return JsonResponse({
            'query': query,
            'count': len(results),
            'results': results[:8]  # Quick preview for live search dropdown
        })

    paginator = Paginator(results, 12)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    genres = tmdb.get_movie_genres()

    context = {
        'query': query,
        'page_obj': page_obj,
        'genres': genres,
        'selected_genre': int(genre_id) if genre_id and str(genre_id).isdigit() else None,
        'selected_media': media_type,
        'selected_rating': min_rating,
        'selected_year': year,
        'total_results': len(results),
    }
    return render(request, 'movies/search.html', context)


def movie_detail_view(request, tmdb_id):
    """
    Detailed information page for a specific movie using TMDB metadata.
    """
    movie = tmdb.get_movie_details(tmdb_id)
    if not movie:
        raise Http404("Movie not found.")

    services.attach_watchlist_status(request.user, [movie])
    if 'similar' in movie and movie['similar']:
        services.attach_watchlist_status(request.user, movie['similar'])

    in_watchlist = movie.get('in_watchlist', False)
    is_watched = movie.get('is_watched', False)

    context = {
        'movie': movie,
        'in_watchlist': in_watchlist,
        'is_watched': is_watched,
    }
    return render(request, 'movies/detail.html', context)


def tv_detail_view(request, tmdb_id):
    """
    Detailed information page for a specific TV show using TMDB metadata.
    """
    tv_show = tmdb.get_tv_details(tmdb_id)
    if not tv_show:
        raise Http404("TV show not found.")

    services.attach_watchlist_status(request.user, [tv_show])
    if 'similar' in tv_show and tv_show['similar']:
        services.attach_watchlist_status(request.user, tv_show['similar'])

    in_watchlist = tv_show.get('in_watchlist', False)
    is_watched = tv_show.get('is_watched', False)

    context = {
        'tv': tv_show,
        'in_watchlist': in_watchlist,
        'is_watched': is_watched,
    }
    return render(request, 'movies/tv_detail.html', context)
