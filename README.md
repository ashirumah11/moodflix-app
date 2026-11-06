# 🎬 MoodFlix

> **Find Your Mood. Discover Your Movie.**
> A modern, cinematic Django-only movie and television discovery platform matching emotional states to curated entertainment.

---

## 🌟 Overview

Traditional streaming services and movie databases organize cinema by static genres, release years, or algorithmic popularity. **MoodFlix** flips the script by introducing **emotional discovery**:

1. Users select how they feel right now:
   - 😄 **Happy** (Uplifting comedies, animation, feel-good family cinema)
   - 🥺 **Sad** (Cathartic dramas, heartfelt romances, inspirational journeys)
   - ☕ **Relaxed** (Soothing documentaries, gentle light comedies, peaceful stories)
   - 🧘 **Stressed** (Pure escapism, stress-busting adventures, vibrant humor)
   - 🚀 **Adventurous** (High-octane action, epic fantasy, mind-bending sci-fi)
   - 💖 **Romantic** (Passionate romances, sparkling chemistry, relationship sagas)
2. The **MoodFlix Recommendation Engine** validates the mood, calculates TMDB genre affinities, evaluates quality thresholds, and ranks titles using a multi-factor relevance scoring formula.
3. Users explore cinematic details, stream official YouTube trailers, and save content into their personal **Watchlist** (with real-time watched/unwatched tracking).

---

## 🏗️ Architecture & Philosophy

MoodFlix is engineered strictly as a **Django-only server-side rendered (SSR)** web application:
- **No separate Node.js / React / Next.js / Vue / Vite build systems.**
- Clean, semantic **HTML5** and **CSS3** utilizing custom CSS variables for a cinematic dark theme (`#0B0B10`, `#15151F`, `#1D1D2A`, with `#8B5CF6` and `#EC4899` gradients).
- Lightweight, unobtrusive **Vanilla JavaScript** (dynamic modal player, AJAX watchlist toggling, debounced live search preview, smooth carousel scrolling).
- **Graceful degradation**: Every core feature (watchlist, search, recommendations, filters, authentication) operates via standard HTTP GET and POST requests even if JavaScript is completely disabled.

---

## 📁 Project Directory Structure

```text
moodflix/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                      # Project core configuration
│   ├── settings.py              # Environment variables, caching, apps, database
│   ├── urls.py                  # Root URL configuration
│   ├── context_processors.py    # Global moods, watchlist counters & status
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                    # Authentication, profiles & preferences
│   ├── models.py                # UserProfile model & signal receivers
│   ├── views.py                 # Register, login, logout, profile & edit views
│   ├── forms.py                 # Registration, login, and preference forms
│   ├── urls.py                  # Accounts URL routing & password reset views
│   ├── admin.py                 # Custom user & profile admin configuration
│   └── tests.py                 # Accounts unit & integration tests
│
├── movies/                      # Movie discovery, detail & TMDB integration
│   ├── tmdb.py                  # Direct TMDB API client with caching & fallback
│   ├── services.py              # Homepage assembler, search & watchlist annotator
│   ├── views.py                 # Home, discover, trending, search & detail views
│   ├── urls.py                  # Movie routes
│   └── tests.py                 # Movie & TMDB unit tests
│
├── recommendations/             # Mood recommendation engine
│   ├── engine.py                # Multi-factor rule-based recommendation logic
│   ├── models.py                # MoodHistory model for authenticated users
│   ├── views.py                 # Mood selection & recommendation results views
│   ├── urls.py                  # Mood routes
│   ├── admin.py                 # Admin registration for MoodHistory
│   └── tests.py                 # Recommendation engine tests
│
├── watchlist/                   # User watchlist & watched tracking
│   ├── models.py                # Watchlist model with unique user constraints
│   ├── views.py                 # Watchlist index, AJAX toggle, watched toggle, remove
│   ├── urls.py                  # Watchlist routes
│   ├── admin.py                 # Admin registration for Watchlist
│   └── tests.py                 # User data isolation & watchlist tests
│
├── templates/                   # Django server-rendered HTML templates
│   ├── base.html                # Base cinematic layout with fonts, modal & header
│   ├── includes/
│   │   ├── navbar.html          # Responsive navigation & real-time badge
│   │   ├── footer.html          # Cinematic footer & TMDB attribution
│   │   ├── messages.html        # Dismissible toast alert framework
│   │   └── movie_card.html      # Reusable movie & TV show card partial
│   ├── home/index.html          # Hero section, mood grid, trending & carousels
│   ├── recommendations/
│   │   ├── mood_selection.html  # Interactive mood discovery board
│   │   └── results.html         # Curated recommendations & sub-filters
│   ├── movies/
│   │   ├── discover.html        # Multi-attribute discovery catalog
│   │   ├── trending.html        # Trending cinema & TV shows
│   │   ├── search.html          # Live search with debounced dropdown & filters
│   │   ├── detail.html          # Movie detail, cast, trailer player & similar
│   │   └── tv_detail.html       # TV series detail, seasons, episodes & cast
│   ├── accounts/
│   │   ├── login.html           # Authentication sign-in form
│   │   ├── register.html        # Account creation with validation
│   │   ├── profile.html         # User profile, preferences & mood history
│   │   ├── profile_edit.html    # Profile & mood preference editor
│   │   └── password_*.html      # Secure password reset & change templates
│   └── watchlist/index.html     # User watchlist with status tabs (Watched/Want)
│
└── static/
    ├── css/
    │   ├── main.css             # Design tokens, variables & typography
    │   ├── components.css       # Cards, badges, buttons, modals, alerts & navbar
    │   ├── home.css             # Hero spotlight, mood cards & carousels
    │   ├── movies.css           # Details layout, video player, filters & search
    │   └── responsive.css       # Mobile & tablet layout adaptations
    ├── js/
    │   ├── main.js              # Navbar scroll, mobile menu, toast & modal player
    │   ├── mood.js              # Mood card interactive animations
    │   ├── watchlist.js         # AJAX watchlist toggle & badge update
    │   └── search.js            # Debounced live search preview dropdown
    └── images/
        ├── fallback_poster.svg  # Crisp vector placeholder for missing posters
        └── fallback_backdrop.svg# Crisp vector placeholder for missing backdrops
```

---

## ⚙️ Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Git

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone <repository-url>
cd moodflix-app

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` as needed:
```env
DEBUG=True
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# (Optional) The Movie Database API Credentials
# Get a free key at https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_READ_ACCESS_TOKEN=your_bearer_token_here
```
> **Note:** If no TMDB API credentials are provided, MoodFlix automatically and seamlessly activates its **curated fallback catalogue**. All pages, trailers, mood recommendations, search, and details remain 100% interactive and functional without errors!

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create an Administrator Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run the Local Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Running the Test Suite

The project includes unit and integration tests covering authentication, user isolation, recommendation algorithms, TMDB fallback resilience, and watchlist operations.

To run the full test suite:
```bash
python manage.py test
```

To run app-specific tests:
```bash
python manage.py test accounts
python manage.py test movies
python manage.py test recommendations
python manage.py test watchlist
```

---

## 🛡️ Security & Performance Highlights

- **User Isolation**: Watchlist items and mood history are scoped strictly to individual authenticated users. A user cannot view, edit, mark as watched, or delete another user's watchlist item.
- **CSRF Protection**: All POST endpoints (login, register, profile update, watchlist toggling, watched state changes) strictly enforce Django CSRF tokens.
- **API Caching**: TMDB requests are cached using Django's caching framework (`LocMemCache` locally, easily swappable with Redis/Memcached) using MD5 hashed keys to prevent repeated network overhead.
- **Safe External Integration**: HTTP calls to external APIs enforce strict connection and read timeouts (`timeout=(3.05, 6)`).
- **PostgreSQL Ready**: SQLite3 is configured for local MVP ease; production environments can switch to PostgreSQL simply by defining the `DATABASE_URL` environment variable.
- **Production Asset Serving**: Configured with WhiteNoise for compressed, fingerprinted static asset delivery with zero external CDN dependency.

---

## 📄 License
MIT License. Built for movie lovers.

