from django.contrib import admin
from .models import Feed

@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'problem')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
    ordering = ('-created_at',)