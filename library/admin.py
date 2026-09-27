from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'uploaded_by', 'is_public', 'created_at')
	list_filter = ('category', 'is_public', 'created_at')
	search_fields = ('title', 'description', 'uploaded_by__email')
	date_hierarchy = 'created_at'
