from django.contrib import admin
from .models import Blog, Category

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title','id', 'feature_image_display', 'content_snippet', 'display_categories')
    search_fields = ('title', 'content')
    list_filter = ('category',)

    def feature_image_display(self, obj):
        if obj.feature_image:
            return obj.feature_image.url
        return "-"
    feature_image_display.short_description = 'Feature Image'

    def content_snippet(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_snippet.short_description = 'Content Snippet'

    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.category.all()])
    display_categories.short_description = 'Categories'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
