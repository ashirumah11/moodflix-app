from django.db import models
from django.contrib.auth.models import User

class Watchlist(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('movie', 'Movie'),
        ('tv', 'TV Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    tmdb_id = models.IntegerField(help_text="TMDB ID of the movie or TV show")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='movie')
    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    backdrop_path = models.CharField(max_length=255, blank=True, null=True)
    vote_average = models.FloatField(default=0.0)
    release_date = models.CharField(max_length=50, blank=True, null=True)
    watched = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Watchlist Item"
        verbose_name_plural = "Watchlist Items"
        ordering = ['-added_at']
        unique_together = ('user', 'tmdb_id', 'media_type')
        indexes = [
            models.Index(fields=['user', 'watched']),
            models.Index(fields=['user', 'tmdb_id', 'media_type']),
        ]

    def __str__(self):
        status = "Watched" if self.watched else "Want to Watch"
        return f"{self.title} ({self.media_type}) - {self.user.username} [{status}]"
