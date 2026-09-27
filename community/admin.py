from django.contrib import admin

from .models import Announcement, Comment, GalleryAlbum, GalleryPhoto, Notification


class CommentInline(admin.TabularInline):
	model = Comment
	extra = 0
	readonly_fields = ('author', 'body', 'created_at')
	can_delete = False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'author', 'published', 'created_at')
	list_filter = ('category', 'published', 'created_at')
	search_fields = ('title', 'body', 'author__email')
	date_hierarchy = 'created_at'
	inlines = [CommentInline]


class GalleryPhotoInline(admin.TabularInline):
	model = GalleryPhoto
	extra = 1


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
	list_display = ('title', 'year', 'event', 'created_by')
	list_filter = ('year',)
	search_fields = ('title',)
	inlines = [GalleryPhotoInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'user', 'created_at', 'read_at')
	list_filter = ('category', 'created_at', 'read_at')
	search_fields = ('title', 'user__email', 'body')
	date_hierarchy = 'created_at'
