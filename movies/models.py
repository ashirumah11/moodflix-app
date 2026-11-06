from django.db import models

# In accordance with architecture guidelines, external movie metadata is retrieved
# and cached on-demand from the TMDB API to prevent database bloat and ensure real-time accuracy.
# User-specific associations are stored in the Watchlist and MoodHistory models.
