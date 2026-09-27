from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Contribution(models.Model):
	class Status(models.TextChoices):
		PENDING = 'pending', 'En attente'
		PAID = 'paid', 'Payée'
		REJECTED = 'rejected', 'Refusée'

	member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='contributions')
	amount = models.DecimalField('montant', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
	currency = models.CharField('devise', max_length=3, default='USD')
	reference = models.CharField('référence', max_length=80, blank=True)
	period = models.CharField('période', max_length=30)
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
	receipt = models.FileField(upload_to='receipts/%Y/%m/', blank=True)
	recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_contributions', null=True, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		permissions = [('view_all_contributions', 'Peut consulter toutes les cotisations')]
		indexes = [models.Index(fields=['member', 'status', '-created_at'])]

	def __str__(self):
		return f'{self.amount} {self.currency} - {self.member}'

# Create your models here.
