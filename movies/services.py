from . import tmdb
from watchlist.models import Watchlist

def attach_watchlist_status(user, items):
    """
    Annotate a list of movie/TV dicts with the user's watchlist state.
    Efficiently queries the database once.
    """
    if not user or not user.is_authenticated or not items:
        for item in items:
            item['in_watchlist'] = False
            item['is_watched'] = False
        return items

    # Collect TMDB IDs
    item_ids = [item['id'] for item in items if 'id' in item and item['id'] is not None]
    
    saved_items = Watchlist.objects.filter(
        user=user,
        tmdb_id__in=item_ids
    ).values('tmdb_id', 'media_type', 'watched', 'id')

    saved_map = {(entry['tmdb_id'], entry['media_type']): entry for entry in saved_items}

    for item in items:
        key = (item.get('id'), item.get('media_type', 'movie'))
        if key in saved_map:
            item['in_watchlist'] = True
            item['is_watched'] = saved_map[key]['watched']
            item['watchlist_id'] = saved_map[key]['id']
        else:
            item['in_watchlist'] = False
            item['is_watched'] = False
            item['watchlist_id'] = None

    return items


def get_home_page_data(user=None):
    """
    Retrieve and assemble all data needed for the rich cinematic homepage:
    - Hero movie with official trailer attached
    - Trending Movies
    - Now Playing Movies (In Theaters)
    - Popular Movies
    - Top Rated Movies
    - Upcoming Releases
    - Popular TV Series
    """
    trending = tmdb.get_trending_movies(time_window="day")
    now_playing = tmdb.get_now_playing_movies()
    popular = tmdb.get_popular_movies()
    top_rated = tmdb.get_top_rated_movies()
    upcoming = tmdb.get_upcoming_movies()
    popular_tv = tmdb.get_popular_tv()

    # Select hero movie: find one with a valid backdrop
    hero_candidates = [m for m in trending if m.get('backdrop_path')] or trending or popular
    hero_movie = hero_candidates[0] if hero_candidates else None

    # Fetch official trailer for hero movie
    if hero_movie:
        media_type = hero_movie.get('media_type', 'movie')
        trailer_info = tmdb.get_trailer(hero_movie['id'], media_type)
        if trailer_info:
            hero_movie['trailer_key'] = trailer_info.get('key')
            hero_movie['trailer_url'] = trailer_info.get('watch_url')

    # Attach watchlist status
    if user and user.is_authenticated:
        for collection in (trending, now_playing, popular, top_rated, upcoming, popular_tv):
            attach_watchlist_status(user, collection)
        if hero_movie:
            attach_watchlist_status(user, [hero_movie])

    return {
        'hero_movie': hero_movie,
        'trending_movies': trending[:10],
        'now_playing_movies': now_playing[:10],
        'popular_movies': popular[:10],
        'top_rated_movies': top_rated[:10],
        'upcoming_movies': upcoming[:10],
        'popular_tv': popular_tv[:10],
    }


def filter_content(items, query=None, genre_id=None, min_rating=0.0, release_year=None, media_type=None):
    """
    Apply multi-attribute filtering to a list of movie/TV items.
    """
    results = list(items)

    if query:
        q_lower = query.lower()
        results = [
            it for it in results
            if q_lower in it.get('title', '').lower() or q_lower in it.get('overview', '').lower()
        ]

    if media_type and media_type != 'all':
        results = [it for it in results if it.get('media_type') == media_type]

    if genre_id:
        try:
            gid = int(genre_id)
            results = [it for it in results if gid in it.get('genre_ids', [])]
        except (ValueError, TypeError):
            pass

    if min_rating and float(min_rating) > 0:
        results = [it for it in results if float(it.get('vote_average', 0)) >= float(min_rating)]

    if release_year:
        results = [it for it in results if str(it.get('release_year', '')) == str(release_year)]

    return results
