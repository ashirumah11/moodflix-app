from django.db import models
from django.contrib.auth.models import User

class MoodHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_history')
    selected_mood = models.CharField(max_length=50, help_text="Selected mood e.g. happy, romantic")
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mood History"
        verbose_name_plural = "Mood Histories"
        ordering = ['-selected_at']
        indexes = [
            models.Index(fields=['user', '-selected_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.selected_mood.capitalize()} on {self.selected_at.strftime('%Y-%m-%d %H:%M')}"
