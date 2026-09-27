from django.contrib import admin

from .models import Contribution


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
	list_display = ('member', 'period', 'amount', 'currency', 'status', 'paid_at', 'recorded_by')
	list_filter = ('status', 'currency', 'period', 'paid_at')
	search_fields = ('member__email', 'member__last_name', 'reference')
	date_hierarchy = 'created_at'
	autocomplete_fields = ('member', 'recorded_by')
