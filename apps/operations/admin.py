from django.contrib import admin
from .models import FeatureFlag, FeatureSegment

class FeatureSegmentInline(admin.TabularInline):
    model = FeatureSegment
    extra = 1
    fields = ('segment_type', 'segment_value')

@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('flag_key', 'is_global_enabled', 'description', 'created_at')
    list_filter = ('is_global_enabled',)
    search_fields = ('flag_key', 'description')
    inlines = [FeatureSegmentInline]
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('flag_key', 'description')
        }),
        ('State', {
            'fields': ('is_global_enabled',)
        }),
    )
