from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_preferred_moods')

    def get_preferred_moods(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.preferred_moods
        return "-"
    get_preferred_moods.short_description = 'Preferred Moods'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_moods', 'preferred_genres', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'preferred_moods', 'preferred_genres')
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
