from django.contrib import admin

from .models import Conversation, Message, MessageReadReceipt, PresenceConnection


class MessageInline(admin.TabularInline):
	model = Message
	extra = 0
	readonly_fields = ('sender', 'content', 'attachment_name', 'created_at')
	show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
	list_display = ('id', 'kind', 'title', 'official', 'created_by', 'updated_at')
	list_filter = ('kind', 'official', 'created_at')
	search_fields = ('title', 'participants__email', 'participants__last_name')
	filter_horizontal = ('participants',)
	inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'conversation', 'sender', 'created_at', 'has_attachment')
	list_filter = ('created_at',)
	search_fields = ('content', 'sender__email', 'conversation__title')
	readonly_fields = ('conversation', 'sender', 'content', 'attachment_name', 'created_at')

	@admin.display(boolean=True, description='Pièce jointe')
	def has_attachment(self, obj):
		return bool(obj.attachment)


@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
	list_display = ('message', 'user', 'read_at')
	list_filter = ('read_at',)
	search_fields = ('user__email', 'message__content')


@admin.register(PresenceConnection)
class PresenceConnectionAdmin(admin.ModelAdmin):
	list_display = ('user', 'channel_name', 'connected_at', 'last_seen')
	list_filter = ('connected_at', 'last_seen')
	search_fields = ('user__email', 'channel_name')
	readonly_fields = ('user', 'channel_name', 'connected_at', 'last_seen')
