from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		MEMBER = 'member', 'Membre'
		SECRETARY = 'secretary', 'Secrétaire'
		TREASURER = 'treasurer', 'Trésorier'
		PRESIDENT = 'president', 'Président'
		ADMIN = 'admin', 'Administrateur'

	email = models.EmailField('adresse e-mail', unique=True)
	role = models.CharField('rôle', max_length=20, choices=Role.choices, default=Role.MEMBER)
	email_verified = models.BooleanField('adresse vérifiée', default=False)

	class Meta:
		ordering = ['last_name', 'first_name', 'username']

	def __str__(self):
		return self.get_full_name() or self.username


class StudentProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	photo = models.ImageField('photo de profil', upload_to='profiles/%Y/%m/', blank=True)
	university = models.CharField('université', max_length=180, blank=True)
	faculty = models.CharField('faculté', max_length=180, blank=True)
	study_year = models.CharField('promotion', max_length=80, blank=True)
	hometown = models.CharField('territoire ou ville d’origine', max_length=120, blank=True)
	phone = models.CharField('téléphone', max_length=30, blank=True)
	bio = models.TextField('présentation', max_length=500, blank=True)
	joined_at = models.DateTimeField('date d’adhésion', auto_now_add=True)

	class Meta:
		verbose_name = 'profil étudiant'
		verbose_name_plural = 'profils étudiants'

	def __str__(self):
		return f'Profil de {self.user}'


class ExecutiveMember(models.Model):
	user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='executive_position')
	title = models.CharField('fonction', max_length=120)
	term_start = models.DateField('début du mandat')
	term_end = models.DateField('fin du mandat', null=True, blank=True)
	biography = models.TextField('biographie', blank=True)
	display_order = models.PositiveSmallIntegerField(default=0)
	is_public = models.BooleanField('fiche publique', default=True)

	class Meta:
		ordering = ['display_order', 'title']
		verbose_name = 'membre du bureau exécutif'
		verbose_name_plural = 'bureau exécutif'

	def __str__(self):
		return f'{self.title} - {self.user}'

# Create your models here.
