from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
    )
    list_editable = ('is_published',)
    search_fields = ('title',)
    list_filter = ('is_published', 'category', 'location')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published')
    list_editable = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published')
    list_editable = ('is_published',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created_at')
