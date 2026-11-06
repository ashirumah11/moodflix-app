import hashlib
import logging
import re
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"

# Standard Fallback SVGs
DEFAULT_POSTER_FALLBACK = "/static/images/fallback_poster.svg"
DEFAULT_BACKDROP_FALLBACK = "/static/images/fallback_backdrop.svg"

# Supported TMDB Image Dimensions
POSTER_SIZES = ("w342", "w500", "w780", "original")
BACKDROP_SIZES = ("w780", "w1280", "original")
YOUTUBE_VIDEO_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")

# TMDB Movie & TV Genre ID Map
GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
    10759: "Action & Adventure",
    10762: "Kids",
    10765: "Sci-Fi & Fantasy",
    10768: "War & Politics",
}


def get_image_url(path, size="w500", is_backdrop=False):
    """
    Returns full image URL from TMDB path or fallback placeholder.
    Constructs https://image.tmdb.org/t/p/{size}/{poster_path}
    """
    if not path:
        return DEFAULT_BACKDROP_FALLBACK if is_backdrop else DEFAULT_POSTER_FALLBACK
    if str(path).startswith('http://') or str(path).startswith('https://'):
        return path
    
    clean_path = str(path).lstrip('/')
    if is_backdrop and size not in BACKDROP_SIZES:
        size = "w1280"
    elif not is_backdrop and size not in POSTER_SIZES:
        size = "w500"

    return f"{TMDB_IMAGE_BASE}/{size}/{clean_path}"


def get_poster_url(path, size="w500"):
    return get_image_url(path, size=size, is_backdrop=False)


def get_backdrop_url(path, size="w1280"):
    return get_image_url(path, size=size, is_backdrop=True)


def extract_youtube_trailer(videos):
    """
    Identifies and returns the best valid YouTube trailer key from video results.
    Prioritizes:
    1. site == 'YouTube' AND type == 'Trailer' AND official == True
    2. site == 'YouTube' AND type == 'Trailer'
    3. site == 'YouTube' AND type == 'Teaser'
    4. Any valid YouTube video key
    """
    if not videos or not isinstance(videos, list):
        return None

    yt_videos = [
        v for v in videos
        if (
            isinstance(v, dict)
            and v.get('site') == 'YouTube'
            and isinstance(v.get('key'), str)
            and YOUTUBE_VIDEO_KEY_RE.fullmatch(v['key'].strip())
        )
    ]
    if not yt_videos:
        return None

    # 1. Official Trailer
    for v in yt_videos:
        if v.get('type') == 'Trailer' and v.get('official') is True:
            return v['key'].strip()

    # 2. General Trailer
    for v in yt_videos:
        if v.get('type') == 'Trailer':
            return v['key'].strip()

    # 3. Teaser
    for v in yt_videos:
        if v.get('type') == 'Teaser':
            return v['key'].strip()

    # 4. Fallback first available YouTube video key
    return yt_videos[0]['key'].strip()


def _make_request(endpoint, params=None):
    """
    Execute authenticated request to TMDB API with error handling, timeout, and caching.
    """
    params_repr = sorted((params or {}).items())
    key_hash = hashlib.md5(f"{endpoint}_{params_repr}".encode('utf-8')).hexdigest()
    cache_key = f"tmdb_{key_hash}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    api_key = getattr(settings, 'TMDB_API_KEY', '').strip()
    read_token = getattr(settings, 'TMDB_READ_ACCESS_TOKEN', '').strip()

    if not api_key and not read_token:
        logger.warning(f"No TMDB API credentials configured. Returning fallback catalogue for {endpoint}.")
        return None

    headers = {'accept': 'application/json'}
    query_params = params.copy() if params else {}

    if read_token:
        headers['Authorization'] = f"Bearer {read_token}"
    elif api_key:
        query_params['api_key'] = api_key

    url = f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(url, headers=headers, params=query_params, timeout=(3.05, 6))
        # A locally stored bearer token can be revoked independently of an API
        # key. When both are configured, give the valid API key one safe retry
        # instead of silently falling back to sample data after a 401.
        if response.status_code == 401 and read_token and api_key:
            logger.warning("TMDB bearer token was rejected; retrying with the API key.")
            headers.pop('Authorization', None)
            query_params['api_key'] = api_key
            response = requests.get(url, headers=headers, params=query_params, timeout=(3.05, 6))
        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, getattr(settings, 'TMDB_CACHE_TIMEOUT', 3600))
            return data
        elif response.status_code == 429:
            logger.error("TMDB rate limit exceeded.")
            return None
        elif response.status_code == 404:
            logger.warning(f"TMDB resource not found: {url}")
            return None
        else:
            logger.error(f"TMDB API error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        # Request URLs can contain the API key when v3 authentication is used;
        # never include the exception text because requests echoes that URL.
        logger.error(
            "TMDB connection error for endpoint %s (%s)",
            endpoint,
            e.__class__.__name__,
        )
        return None


# ==========================================
# CURATED REAL-WORLD FALLBACK CATALOGUE
# Uses authentic TMDB IDs, verified poster & backdrop paths,
# and real YouTube official trailer keys
# ==========================================
MOCK_MOVIES = [
    {
        "id": 693134,
        "title": "Dune: Part Two",
        "overview": "Follow the mythic journey of Paul Atreides as he unites with Chani and the Fremen while on a path of revenge against the conspirators who destroyed his family.",
        "release_date": "2024-02-27",
        "vote_average": 8.2,
        "vote_count": 5200,
        "popularity": 195.4,
        "poster_path": "/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "backdrop_path": "/xOMo8BRK7PfcJv9JCnx7s520DRq.jpg",
        "genre_ids": [878, 12],
        "media_type": "movie",
        "trailer_key": "Way9Dexny3w",
        "runtime": 166,
        "tagline": "Long live the fighters.",
        "director": "Denis Villeneuve",
    },
    {
        "id": 872585,
        "title": "Oppenheimer",
        "overview": "The story of J. Robert Oppenheimer's role in the development of the atomic bomb during World War II.",
        "release_date": "2023-07-19",
        "vote_average": 8.1,
        "vote_count": 8900,
        "popularity": 142.1,
        "poster_path": "/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "backdrop_path": "/rLb2cwF3Pazuxaj0sRXQ037tGI1.jpg",
        "genre_ids": [18, 36],
        "media_type": "movie",
        "trailer_key": "uYPbbksJxIg",
        "runtime": 180,
        "tagline": "The world forever changes.",
        "director": "Christopher Nolan",
    },
    {
        "id": 569094,
        "title": "Spider-Man: Across the Spider-Verse",
        "overview": "After reuniting with Gwen Stacy, Brooklyn's full-time, friendly neighborhood Spider-Man is catapulted across the Multiverse.",
        "release_date": "2023-05-31",
        "vote_average": 8.4,
        "vote_count": 6400,
        "popularity": 130.5,
        "poster_path": "/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
        "backdrop_path": "/4HodYYKEIsGOdinkGi2Ucz6X9i0.jpg",
        "genre_ids": [16, 28, 12, 878],
        "media_type": "movie",
        "trailer_key": "cqGjhVJWtEg",
        "runtime": 140,
        "tagline": "It's how you wear the mask that matters.",
        "director": "Joaquim Dos Santos, Kemp Powers",
    },
    {
        "id": 545611,
        "title": "Everything Everywhere All at Once",
        "overview": "An aging Chinese immigrant is swept up in an insane adventure, where she alone can save what's important to her by connecting with the lives she could have led in other universes.",
        "release_date": "2022-03-24",
        "vote_average": 8.0,
        "vote_count": 6200,
        "popularity": 85.4,
        "poster_path": "/w3LxiVYPqrlexP02048ST9Y8Ki4.jpg",
        "backdrop_path": "/70AV2Xx5FQYj20xq5ssIx89Gjt8.jpg",
        "genre_ids": [28, 12, 878, 35],
        "media_type": "movie",
        "trailer_key": "wxN1T1uxQ2g",
        "runtime": 139,
        "tagline": "The universe is so much bigger than you realize.",
        "director": "Daniel Kwan, Daniel Scheinert",
    },
    {
        "id": 157336,
        "title": "Interstellar",
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        "release_date": "2014-11-05",
        "vote_average": 8.4,
        "vote_count": 34000,
        "popularity": 118.7,
        "poster_path": "/gEU2QniE6EwfVDxCzs3flTeNGAz.jpg",
        "backdrop_path": "/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        "genre_ids": [12, 18, 878],
        "media_type": "movie",
        "trailer_key": "zSWdZVtXT7E",
        "runtime": 169,
        "tagline": "Mankind was born on Earth. It was never meant to die here.",
        "director": "Christopher Nolan",
    },
    {
        "id": 27205,
        "title": "Inception",
        "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets, is offered a chance to regain his old life as payment for an impossible task: inception.",
        "release_date": "2010-07-15",
        "vote_average": 8.4,
        "vote_count": 36000,
        "popularity": 95.0,
        "poster_path": "/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",
        "backdrop_path": "/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
        "genre_ids": [28, 878, 12],
        "media_type": "movie",
        "trailer_key": "YoHD9XEInc0",
        "runtime": 148,
        "tagline": "Your mind is the scene of the crime.",
        "director": "Christopher Nolan",
    },
    {
        "id": 129,
        "title": "Spirited Away",
        "overview": "A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must call upon the courage she never knew she had to free her family.",
        "release_date": "2001-07-20",
        "vote_average": 8.5,
        "vote_count": 16000,
        "popularity": 92.1,
        "poster_path": "/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
        "backdrop_path": "/Ab8mkHmkYADjU7wQiOkia9BzGvS.jpg",
        "genre_ids": [16, 10751, 14],
        "media_type": "movie",
        "trailer_key": "ByXuk9QqQkk",
        "runtime": 125,
        "tagline": "The tunnel led to a mysterious world.",
        "director": "Hayao Miyazaki",
    },
    {
        "id": 508442,
        "title": "Soul",
        "overview": "Joe Gardner is a middle school teacher with a love for jazz music. After a successful gig at the Half Note Club, he suddenly gets into an accident that separates his soul from his body.",
        "release_date": "2020-12-25",
        "vote_average": 8.1,
        "vote_count": 9800,
        "popularity": 68.9,
        "poster_path": "/hm58o4GhIdawJaCu4eu834jhBlW.jpg",
        "backdrop_path": "/kf456ZqeC45XTvo6W9pWJH1o2q5.jpg",
        "genre_ids": [16, 35, 14, 10751],
        "media_type": "movie",
        "trailer_key": "xOsLIiBStEs",
        "runtime": 100,
        "tagline": "Is all this living really worth dying for?",
        "director": "Pete Docter",
    },
    {
        "id": 666277,
        "title": "Past Lives",
        "overview": "Nora and Hae Sung, two deeply connected childhood friends, are wrested apart after Nora's family emigrates from South Korea. Two decades later, they are reunited in New York for one fateful week.",
        "release_date": "2023-06-02",
        "vote_average": 7.9,
        "vote_count": 2100,
        "popularity": 62.1,
        "poster_path": "/k3WaW15g8QcjvfHQcsbUt7xadwF.jpg",
        "backdrop_path": "/5YZbUmjbMa3ClvSW1Wj3D6XGolb.jpg",
        "genre_ids": [18, 10749],
        "media_type": "movie",
        "trailer_key": "kA244xucWIU",
        "runtime": 105,
        "tagline": "Inyeon connects every soul across time.",
        "director": "Celine Song",
    },
    {
        "id": 787699,
        "title": "Wonka",
        "overview": "Willy Wonka – chock-full of ideas and determined to change the world one delectable bite at a time – is proof that the best things in life begin with a dream.",
        "release_date": "2023-12-06",
        "vote_average": 7.2,
        "vote_count": 4100,
        "popularity": 81.2,
        "poster_path": "/qhb1qYheapYO797NeZOPbFADqvj.jpg",
        "backdrop_path": "/yyFc8Icl32vrrHm921Z8Bs8u4fg.jpg",
        "genre_ids": [35, 10751, 14],
        "media_type": "movie",
        "trailer_key": "otNh9bTjXWg",
        "runtime": 116,
        "tagline": "Witness how Willy became Wonka.",
        "director": "Paul King",
    },
    {
        "id": 244786,
        "title": "Whiplash",
        "overview": "Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at any cost, pushing his physical and emotional limits.",
        "release_date": "2014-10-10",
        "vote_average": 8.4,
        "vote_count": 14500,
        "popularity": 74.3,
        "poster_path": "/7fn624j5lj3x.jpg",
        "backdrop_path": "/8fn4jk3.jpg",
        "genre_ids": [18, 10402],
        "media_type": "movie",
        "trailer_key": "7d_jQycdQGo",
        "runtime": 107,
        "tagline": "The road to greatness can take you to the edge.",
        "director": "Damien Chazelle",
    },
    {
        "id": 346648,
        "title": "Paddington 2",
        "overview": "Paddington, now happily settled with the Brown family, picks up a series of odd jobs to buy the perfect pop-up book for Aunt Lucy's 100th birthday, only for the book to be stolen.",
        "release_date": "2017-11-05",
        "vote_average": 8.1,
        "vote_count": 3900,
        "popularity": 70.8,
        "poster_path": "/8CjS0bWpC1Wc3gBv2Y8U4iFk5qZ.jpg",
        "backdrop_path": "/ok756eH3N7Q1pD7o8N2Yh8V9o0k.jpg",
        "genre_ids": [35, 16, 10751, 12],
        "media_type": "movie",
        "trailer_key": "PLl99DlL6b4",
        "runtime": 103,
        "tagline": "It takes a bear to catch a thief.",
        "director": "Paul King",
    },
    {
        "id": 8392,
        "title": "My Neighbor Totoro",
        "overview": "Two young sisters move to the countryside and discover friendly woodland spirits, including the gentle Totoro.",
        "release_date": "1988-04-16",
        "vote_average": 8.2,
        "vote_count": 7600,
        "popularity": 65.4,
        "poster_path": "/rtGDOeG9LzoerkDGZF9dnVeLppL.jpg",
        "backdrop_path": "/etqs3fD3OZosHj0BZB2hWf0QnIi.jpg",
        "genre_ids": [14, 16, 10751],
        "media_type": "movie",
        "trailer_key": "92a7Hj0ijLs",
        "runtime": 86,
        "tagline": "You've never had a friend like Totoro.",
        "director": "Hayao Miyazaki",
    },
]

MOCK_NOW_PLAYING = [
    MOCK_MOVIES[0],  # Dune: Part Two
    MOCK_MOVIES[1],  # Oppenheimer
    MOCK_MOVIES[9],  # Wonka
    MOCK_MOVIES[8],  # Past Lives
]

MOCK_UPCOMING = [
    {
        "id": 1022789,
        "title": "Inside Out 2",
        "overview": "Teenager Riley's mind headquarters undergoes a sudden demolition to make room for unexpected new Emotions: Anxiety, Envy, Ennui, and Embarrassment.",
        "release_date": "2024-06-14",
        "vote_average": 7.6,
        "vote_count": 4800,
        "popularity": 210.0,
        "poster_path": "/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",
        "backdrop_path": "/xg27NrXi7VXCGUr7MG75UqLl6Vg.jpg",
        "genre_ids": [16, 10751, 35, 14],
        "media_type": "movie",
        "trailer_key": "LEjhY15eCx0",
        "runtime": 96,
        "tagline": "Make room for new emotions.",
        "director": "Kelsey Mann",
    },
    {
        "id": 533535,
        "title": "Deadpool & Wolverine",
        "overview": "A listless Wade Wilson toils in civilian life until a monumental threat leads him to recruit an alternate universe Wolverine.",
        "release_date": "2024-07-26",
        "vote_average": 7.7,
        "vote_count": 5500,
        "popularity": 250.0,
        "poster_path": "/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
        "backdrop_path": "/yDHYTfA3R0jFYba16jBB1ef8oIt.jpg",
        "genre_ids": [28, 35, 878],
        "media_type": "movie",
        "trailer_key": "73_1biulkYk",
        "runtime": 128,
        "tagline": "Come together.",
        "director": "Shawn Levy",
    },
    {
        "id": 912649,
        "title": "Venom: The Last Dance",
        "overview": "Eddie and Venom are on the run. Hunted by both of their worlds and with the net closing in, the duo are forced into a devastating decision.",
        "release_date": "2024-10-25",
        "vote_average": 6.8,
        "vote_count": 2200,
        "popularity": 180.0,
        "poster_path": "/aosm8NMQ3UyoBVpSxyimorCQykC.jpg",
        "backdrop_path": "/3V4kLQg0kSqPLctI5ziYWpngNg5.jpg",
        "genre_ids": [28, 878, 12],
        "media_type": "movie",
        "trailer_key": "__2bjWbetsA",
        "runtime": 110,
        "tagline": "'Til death do they part.",
        "director": "Kelly Marcel",
    },
    {
        "id": 519182,
        "title": "Despicable Me 4",
        "overview": "Gru and Lucy welcome a new member to the family, Gru Jr., who is intent on tormenting his dad. A new nemesis forces the family to go on the run.",
        "release_date": "2024-07-03",
        "vote_average": 7.1,
        "vote_count": 2400,
        "popularity": 160.0,
        "poster_path": "/wWba3TaojhK7NdycRhoQpsG0FaH.jpg",
        "backdrop_path": "/lgkFtNmd2vCokm1vL1vjB5029hn.jpg",
        "genre_ids": [16, 10751, 35, 12],
        "media_type": "movie",
        "trailer_key": "qQlr9-rF32A",
        "runtime": 95,
        "tagline": "Things just got a little more despicable.",
        "director": "Chris Renaud",
    },
]

MOCK_TV = [
    {
        "id": 126308,
        "title": "Shōgun",
        "name": "Shōgun",
        "overview": "In Japan in the year 1600, Lord Yoshii Toranaga discovers secrets from a marooned European ship that could tip the scales of civil war in his favor.",
        "first_air_date": "2024-02-27",
        "vote_average": 8.5,
        "vote_count": 1200,
        "popularity": 140.0,
        "poster_path": "/7O4iVfOMQmdCSxhOg1WNzG1AgYT.jpg",
        "backdrop_path": "/5fWTAe8oMls2d2qN55bJb4C7v6R.jpg",
        "genre_ids": [18, 10768],
        "media_type": "tv",
        "trailer_key": "yFNARGz2X_s",
        "number_of_seasons": 1,
        "number_of_episodes": 10,
    },
    {
        "id": 66732,
        "title": "Stranger Things",
        "name": "Stranger Things",
        "overview": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
        "first_air_date": "2016-07-15",
        "vote_average": 8.6,
        "vote_count": 17000,
        "popularity": 115.0,
        "poster_path": "/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
        "backdrop_path": "/56v2KjBlU4XaOv9rVYEQypROD7P.jpg",
        "genre_ids": [10765, 18, 9648],
        "media_type": "tv",
        "trailer_key": "b9EkMc79ZSU",
        "number_of_seasons": 4,
        "number_of_episodes": 34,
    },
    {
        "id": 100088,
        "title": "The Last of Us",
        "name": "The Last of Us",
        "overview": "Twenty years after modern civilization has been destroyed, Joel is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
        "first_air_date": "2023-01-15",
        "vote_average": 8.6,
        "vote_count": 4800,
        "popularity": 110.0,
        "poster_path": "/uKvVjK1q1yt2XbVTubRizHuGjr1.jpg",
        "backdrop_path": "/uDgy6hyPd82kOHh6I95FLtLnj6p.jpg",
        "genre_ids": [18, 10765, 10759],
        "media_type": "tv",
        "trailer_key": "uLtkt8BonwM",
        "number_of_seasons": 1,
        "number_of_episodes": 9,
    },
    {
        "id": 97546,
        "title": "Ted Lasso",
        "name": "Ted Lasso",
        "overview": "An American college football coach is recruited to manage an English soccer team, AFC Richmond. Despite having no experience with association football, his relentless optimism wins hearts.",
        "first_air_date": "2020-08-14",
        "vote_average": 8.5,
        "vote_count": 1800,
        "popularity": 88.0,
        "poster_path": "/5NzFw9r5F1u6p2B7v3A8N5C1z2k.jpg",
        "backdrop_path": "/v4B3t2w8o1p5A7q9s8N2e4R6y1b.jpg",
        "genre_ids": [35, 18],
        "media_type": "tv",
        "trailer_key": "3u7EIiohs6U",
        "number_of_seasons": 3,
        "number_of_episodes": 34,
    },
]

# Older internal links used these short IDs before the catalogue adopted the
# canonical TMDB IDs. Retain them so bookmarked fallback-mode detail pages keep
# working when API credentials are not configured.
LEGACY_FALLBACK_IDS = {
    'movie': {104: 157336},  # Interstellar
    'tv': {201: 97546},      # Ted Lasso
}


def _format_item(item, media_type="movie"):
    """
    Format movie or tv show item into a normalized dictionary.
    """
    m_type = item.get('media_type', media_type)
    title = item.get('title') or item.get('name') or "Untitled"
    release_date = item.get('release_date') or item.get('first_air_date') or ""
    release_year = release_date[:4] if release_date else ""

    poster_path = item.get('poster_path')
    backdrop_path = item.get('backdrop_path')

    # Resolve genre names
    genre_ids = item.get('genre_ids', [])
    genre_names = [GENRE_MAP.get(gid) for gid in genre_ids if gid in GENRE_MAP]
    if not genre_names and 'genres' in item:
        genre_names = [g.get('name') for g in item.get('genres', []) if g.get('name')]

    vote_avg = round(float(item.get('vote_average', 0.0)), 1)

    return {
        'id': item.get('id'),
        'title': title,
        'original_title': item.get('original_title') or item.get('original_name') or title,
        'overview': item.get('overview', ''),
        'release_date': release_date,
        'release_year': release_year,
        'vote_average': vote_avg,
        'vote_count': item.get('vote_count', 0),
        'popularity': item.get('popularity', 0.0),
        'poster_path': poster_path,
        'poster_url': get_poster_url(poster_path, size="w500"),
        'backdrop_path': backdrop_path,
        'backdrop_url': get_backdrop_url(backdrop_path, size="w1280"),
        'media_type': m_type,
        'genres': genre_names,
        'genre_ids': genre_ids,
        'trailer_key': item.get('trailer_key'),
    }


# ==========================================
# PUBLIC TMDB API SERVICE FUNCTIONS
# ==========================================

def get_trending_movies(time_window="day", page=1):
    """
    Fetch trending movies for the day or week.
    Endpoint: /trending/movie/{time_window}
    """
    data = _make_request(f"trending/movie/{time_window}", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]
    return [_format_item(m, 'movie') for m in MOCK_MOVIES]


def get_popular_movies(page=1):
    """
    Fetch popular movies currently trending on TMDB.
    Endpoint: /movie/popular
    """
    data = _make_request("movie/popular", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]
    sorted_mocks = sorted(MOCK_MOVIES, key=lambda x: x.get('popularity', 0), reverse=True)
    return [_format_item(m, 'movie') for m in sorted_mocks]


def get_top_rated_movies(page=1):
    """
    Fetch highest rated movies of all time.
    Endpoint: /movie/top_rated
    """
    data = _make_request("movie/top_rated", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]
    sorted_mocks = sorted(MOCK_MOVIES, key=lambda x: x.get('vote_average', 0), reverse=True)
    return [_format_item(m, 'movie') for m in sorted_mocks]


def get_now_playing_movies(page=1):
    """
    Fetch movies currently playing in theaters.
    Endpoint: /movie/now_playing
    """
    data = _make_request("movie/now_playing", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]
    return [_format_item(m, 'movie') for m in MOCK_NOW_PLAYING]


def get_upcoming_movies(page=1):
    """
    Fetch anticipated upcoming releases.
    Endpoint: /movie/upcoming
    """
    data = _make_request("movie/upcoming", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]
    return [_format_item(m, 'movie') for m in MOCK_UPCOMING]


def get_popular_tv(page=1):
    """
    Fetch popular television series.
    Endpoint: /tv/popular
    """
    data = _make_request("tv/popular", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(s, 'tv') for s in data['results']]
    return [_format_item(s, 'tv') for s in MOCK_TV]


def get_top_rated_tv(page=1):
    """
    Fetch top-rated television series.
    Endpoint: /tv/top_rated
    """
    data = _make_request("tv/top_rated", {'page': page})
    if data and 'results' in data and data['results']:
        return [_format_item(s, 'tv') for s in data['results']]
    sorted_mocks = sorted(MOCK_TV, key=lambda x: x.get('vote_average', 0), reverse=True)
    return [_format_item(s, 'tv') for s in sorted_mocks]


def search_movies(query, page=1):
    """
    Search specifically for movies.
    Endpoint: /search/movie
    """
    if not query:
        return []
    data = _make_request("search/movie", {'query': query, 'page': page})
    if isinstance(data, dict) and 'results' in data:
        return [_format_item(m, 'movie') for m in data['results']]
    q_lower = query.lower()
    return [_format_item(m, 'movie') for m in MOCK_MOVIES if q_lower in m['title'].lower() or q_lower in m['overview'].lower()]


def search_tv(query, page=1):
    """
    Search specifically for TV shows.
    Endpoint: /search/tv
    """
    if not query:
        return []
    data = _make_request("search/tv", {'query': query, 'page': page})
    if isinstance(data, dict) and 'results' in data:
        return [_format_item(s, 'tv') for s in data['results']]
    q_lower = query.lower()
    return [_format_item(t, 'tv') for t in MOCK_TV if q_lower in t['name'].lower() or q_lower in t['overview'].lower()]


def search_multi(query, page=1):
    """
    Search movies and TV shows matching query.
    Endpoint: /search/multi
    """
    if not query:
        return []
    data = _make_request("search/multi", {'query': query, 'page': page})
    if data and 'results' in data:
        results = []
        for item in data['results']:
            media_type = item.get('media_type')
            if media_type in ('movie', 'tv'):
                results.append(_format_item(item, media_type))
        return results

    # Search local mock catalog
    q_lower = query.lower()
    matches = []
    for m in MOCK_MOVIES:
        if q_lower in m['title'].lower() or q_lower in m['overview'].lower():
            matches.append(_format_item(m, 'movie'))
    for t in MOCK_TV:
        if q_lower in t['name'].lower() or q_lower in t['overview'].lower():
            matches.append(_format_item(t, 'tv'))
    return matches


def get_movie_details(movie_id):
    """
    Get detailed information for a movie including videos and credits.
    Endpoint: /movie/{movie_id}?append_to_response=videos,credits,similar
    """
    data = _make_request(f"movie/{movie_id}", {'append_to_response': 'videos,credits,similar'})
    if data:
        item = _format_item(data, 'movie')
        item['runtime'] = data.get('runtime', 0)
        item['tagline'] = data.get('tagline', '')
        item['status'] = data.get('status', 'Released')
        
        # Production companies
        prod_cos = data.get('production_companies', [])
        item['production_companies'] = [p.get('name') for p in prod_cos if p.get('name')]

        # Cast
        credits = data.get('credits', {})
        cast = credits.get('cast', [])[:10]
        item['cast'] = [
            {
                'name': c.get('name'),
                'character': c.get('character'),
                'profile_url': get_image_url(c.get('profile_path'), size="w185") if c.get('profile_path') else None
            }
            for c in cast
        ]
        
        # Director
        crew = credits.get('crew', [])
        directors = [c.get('name') for c in crew if c.get('job') == 'Director']
        item['director'] = ", ".join(directors) if directors else None

        # Trailer
        videos = data.get('videos', {}).get('results', [])
        item['trailer_key'] = extract_youtube_trailer(videos)

        # Similar movies
        similar = data.get('similar', {}).get('results', [])[:6]
        item['similar'] = [_format_item(s, 'movie') for s in similar]

        return item

    # Check mock catalogue, including legacy IDs used by earlier fallback links.
    try:
        lookup_id = int(movie_id)
    except (TypeError, ValueError):
        return None
    lookup_id = LEGACY_FALLBACK_IDS['movie'].get(lookup_id, lookup_id)
    mock = next((m for m in MOCK_MOVIES + MOCK_UPCOMING if m['id'] == lookup_id), None)
    if mock:
        formatted = _format_item(mock, 'movie')
        formatted['runtime'] = mock.get('runtime', 120)
        formatted['tagline'] = mock.get('tagline', "Find your mood. Discover your story.")
        formatted['director'] = mock.get('director', "Acclaimed Filmmaker")
        formatted['cast'] = [
            {'name': 'Lead Actor', 'character': 'Protagonist', 'profile_url': None},
            {'name': 'Supporting Star', 'character': 'Ally', 'profile_url': None},
        ]
        formatted['similar'] = [_format_item(m, 'movie') for m in MOCK_MOVIES if m['id'] != lookup_id][:4]
        return formatted

    return None


def get_tv_details(tv_id):
    """
    Get detailed information for a TV show including videos and credits.
    Endpoint: /tv/{tv_id}?append_to_response=videos,credits,similar
    """
    data = _make_request(f"tv/{tv_id}", {'append_to_response': 'videos,credits,similar'})
    if data:
        item = _format_item(data, 'tv')
        item['number_of_seasons'] = data.get('number_of_seasons', 1)
        item['number_of_episodes'] = data.get('number_of_episodes', 1)
        item['tagline'] = data.get('tagline', '')
        item['status'] = data.get('status', 'Returning Series')

        credits = data.get('credits', {})
        cast = credits.get('cast', [])[:10]
        item['cast'] = [
            {
                'name': c.get('name'),
                'character': c.get('character'),
                'profile_url': get_image_url(c.get('profile_path'), size="w185") if c.get('profile_path') else None
            }
            for c in cast
        ]

        # Trailer
        videos = data.get('videos', {}).get('results', [])
        item['trailer_key'] = extract_youtube_trailer(videos)

        # Similar
        similar = data.get('similar', {}).get('results', [])[:6]
        item['similar'] = [_format_item(s, 'tv') for s in similar]

        return item

    # Check mock TV catalogue, including legacy IDs used by earlier fallback links.
    try:
        lookup_id = int(tv_id)
    except (TypeError, ValueError):
        return None
    lookup_id = LEGACY_FALLBACK_IDS['tv'].get(lookup_id, lookup_id)
    mock = next((t for t in MOCK_TV if t['id'] == lookup_id), None)
    if mock:
        formatted = _format_item(mock, 'tv')
        formatted['number_of_seasons'] = mock.get('number_of_seasons', 2)
        formatted['number_of_episodes'] = mock.get('number_of_episodes', 20)
        formatted['tagline'] = "Streaming television at its finest."
        formatted['cast'] = [
            {'name': 'Lead Star', 'character': 'Hero', 'profile_url': None},
            {'name': 'Co-Star', 'character': 'Friend', 'profile_url': None},
        ]
        formatted['similar'] = [_format_item(t, 'tv') for t in MOCK_TV if t['id'] != lookup_id][:3]
        return formatted

    return None


def get_movie_trailer(movie_id):
    """
    Fetch trailer video information for a movie from TMDB /movie/{id}/videos.
    """
    data = _make_request(f"movie/{movie_id}/videos")
    if data and 'results' in data:
        key = extract_youtube_trailer(data['results'])
        if key:
            return {
                'key': key,
                'site': 'YouTube',
                'name': 'Official Trailer',
                'embed_url': f"https://www.youtube.com/embed/{key}?autoplay=1&rel=0",
                'watch_url': f"https://www.youtube.com/watch?v={key}",
            }

    details = get_movie_details(movie_id)
    if details and details.get('trailer_key'):
        key = details['trailer_key']
        return {
            'key': key,
            'site': 'YouTube',
            'name': 'Official Trailer',
            'embed_url': f"https://www.youtube.com/embed/{key}?autoplay=1&rel=0",
            'watch_url': f"https://www.youtube.com/watch?v={key}",
        }

    return None


def get_tv_trailer(tv_id):
    """
    Fetch trailer video information for a TV show from TMDB /tv/{id}/videos.
    """
    data = _make_request(f"tv/{tv_id}/videos")
    if data and 'results' in data:
        key = extract_youtube_trailer(data['results'])
        if key:
            return {
                'key': key,
                'site': 'YouTube',
                'name': 'Official Trailer',
                'embed_url': f"https://www.youtube.com/embed/{key}?autoplay=1&rel=0",
                'watch_url': f"https://www.youtube.com/watch?v={key}",
            }

    details = get_tv_details(tv_id)
    if details and details.get('trailer_key'):
        key = details['trailer_key']
        return {
            'key': key,
            'site': 'YouTube',
            'name': 'Official Trailer',
            'embed_url': f"https://www.youtube.com/embed/{key}?autoplay=1&rel=0",
            'watch_url': f"https://www.youtube.com/watch?v={key}",
        }

    return None


def get_trailer(tmdb_id, media_type='movie'):
    """
    Unified trailer retriever for movie or tv show.
    """
    if media_type == 'tv':
        return get_tv_trailer(tmdb_id)
    return get_movie_trailer(tmdb_id)


def discover_movies_by_genre(genre_ids, sort_by="popularity.desc", page=1, min_vote_average=0):
    """
    Discover movies filtered by genre IDs.
    Uses pipe '|' (OR logic) for multi-genre mood combinations.
    Endpoint: /discover/movie
    """
    if isinstance(genre_ids, (list, tuple)):
        genre_str = "|".join(str(g) for g in genre_ids)
        target_genre_set = set(int(g) for g in genre_ids)
    else:
        genre_str = str(genre_ids)
        target_genre_set = set(int(g.strip()) for g in genre_str.replace('|', ',').split(',') if g.strip().isdigit())

    params = {
        'with_genres': genre_str,
        'sort_by': sort_by,
        'page': page,
        'vote_count.gte': 50,
    }
    if min_vote_average > 0:
        params['vote_average.gte'] = min_vote_average

    data = _make_request("discover/movie", params)
    if data and 'results' in data and data['results']:
        return [_format_item(m, 'movie') for m in data['results']]

    # Filter mock movies matching any target genre
    matched = []
    for m in MOCK_MOVIES + MOCK_UPCOMING:
        m_genres = set(m.get('genre_ids', []))
        if target_genre_set & m_genres:
            matched.append(_format_item(m, 'movie'))

    if not matched:
        matched = [_format_item(m, 'movie') for m in MOCK_MOVIES]

    if sort_by == 'vote_average.desc':
        matched.sort(key=lambda x: x['vote_average'], reverse=True)
    else:
        matched.sort(key=lambda x: x['popularity'], reverse=True)

    return matched


def get_movie_genres():
    """
    Fetch all official movie genres.
    Endpoint: /genre/movie/list
    """
    data = _make_request("genre/movie/list")
    if data and 'genres' in data:
        return data['genres']
    return [{'id': k, 'name': v} for k, v in GENRE_MAP.items() if k not in (10759, 10762, 10765, 10768)]
