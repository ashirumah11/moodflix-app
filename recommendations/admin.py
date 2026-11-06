from django.contrib import admin
from .models import MoodHistory

@admin.register(MoodHistory)
class MoodHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'selected_mood', 'selected_at')
    list_filter = ('selected_mood', 'selected_at')
    search_fields = ('user__username', 'selected_mood')
    date_hierarchy = 'selected_at'
    ordering = ('-selected_at',)
