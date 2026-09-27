from django.contrib import admin

from .models import Event, EventRSVP


class EventRSVPInline(admin.TabularInline):
	model = EventRSVP
	extra = 0
	autocomplete_fields = ('user',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('title', 'starts_at', 'location', 'status', 'participant_total', 'created_by')
	list_filter = ('status', 'starts_at')
	search_fields = ('title', 'summary', 'location')
	prepopulated_fields = {'slug': ('title',)}
	date_hierarchy = 'starts_at'
	inlines = [EventRSVPInline]

	@admin.display(description='Participants')
	def participant_total(self, obj):
		return obj.rsvps.filter(status=EventRSVP.Status.GOING).count()


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
	list_display = ('event', 'user', 'status', 'updated_at')
	list_filter = ('status', 'event')
	search_fields = ('event__title', 'user__email', 'user__last_name')
