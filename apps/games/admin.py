from django.contrib import admin
from .models import SecretWordPack, SecretCategory, SecretWord

@admin.register(SecretWordPack)
class SecretWordPackAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class SecretWordInline(admin.TabularInline):
    model = SecretWord
    extra = 1
    fields = ('english_name', 'arabic_name', 'difficulty', 'weight', 'popularity', 'is_active')

@admin.register(SecretCategory)
class SecretCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'pack', 'is_active')
    list_filter = ('pack', 'is_active')
    search_fields = ('name',)
    inlines = [SecretWordInline]

@admin.register(SecretWord)
class SecretWordAdmin(admin.ModelAdmin):
    list_display = ('english_name', 'arabic_name', 'category', 'difficulty', 'weight', 'popularity', 'is_active')
    list_filter = ('category__pack', 'category', 'difficulty', 'is_active')
    search_fields = ('english_name', 'arabic_name', 'tags')
    readonly_fields = ('popularity', 'last_used_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'english_name', 'arabic_name', 'is_active')
        }),
        ('Classification', {
            'fields': ('difficulty', 'tags')
        }),
        ('Engine Metrics', {
            'fields': ('weight', 'popularity', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )
