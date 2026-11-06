from django.contrib import admin
from .models import Watchlist

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'media_type', 'tmdb_id', 'watched', 'added_at')
    list_filter = ('media_type', 'watched', 'added_at')
    search_fields = ('title', 'user__username', 'tmdb_id')
    date_hierarchy = 'added_at'
    ordering = ('-added_at',)
    list_editable = ('watched',)
