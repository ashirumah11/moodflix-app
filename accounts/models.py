from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Profile model extending Django User with entertainment preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio about your movie tastes")
    preferred_genres = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Comma-separated preferred genre IDs or names"
    )
    preferred_moods = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Comma-separated preferred moods (e.g. happy, adventurous)"
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_preferred_moods_list(self):
        if not self.preferred_moods:
            return []
        return [m.strip() for m in self.preferred_moods.split(',') if m.strip()]

    def get_preferred_genres_list(self):
        if not self.preferred_genres:
            return []
        return [g.strip() for g in self.preferred_genres.split(',') if g.strip()]


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
