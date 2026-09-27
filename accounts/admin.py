from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ExecutiveMember, StudentProfile, User


class StudentProfileInline(admin.StackedInline):
	model = StudentProfile
	can_delete = False
	extra = 0


@admin.register(User)
class CEOBEFUserAdmin(UserAdmin):
	inlines = [StudentProfileInline]
	list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'email_verified', 'is_active')
	list_filter = ('role', 'email_verified', 'is_active', 'is_staff')
	search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__university')
	fieldsets = UserAdmin.fieldsets + (('Communauté CEOBEF', {'fields': ('role', 'email_verified')}),)
	add_fieldsets = UserAdmin.add_fieldsets + (('Communauté CEOBEF', {'fields': ('email', 'first_name', 'last_name', 'role')}),)
	actions = ('export_members_csv',)

	@admin.action(description='Exporter les membres sélectionnés (CSV)')
	def export_members_csv(self, request, queryset):
		import csv

		from django.http import HttpResponse

		response = HttpResponse(content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = 'attachment; filename="ceobef-membres.csv"'
		response.write('\ufeff')
		writer = csv.writer(response)
		writer.writerow(['Identifiant', 'Prénom', 'Nom', 'E-mail', 'Rôle', 'Adresse vérifiée', 'Université'])
		for member in queryset.select_related('profile').iterator():
			writer.writerow([member.username, member.first_name, member.last_name, member.email, member.get_role_display(), member.email_verified, member.profile.university])
		return response


@admin.register(ExecutiveMember)
class ExecutiveMemberAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'term_start', 'term_end', 'is_public')
	list_filter = ('is_public', 'term_start')
	search_fields = ('title', 'user__first_name', 'user__last_name', 'user__email')
	autocomplete_fields = ('user',)
