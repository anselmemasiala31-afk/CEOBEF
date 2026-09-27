from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from accounts.models import User
from community.models import Notification
from core.permissions import permissions_required
from .forms import ContributionForm
from .models import Contribution


@login_required
def contribution_list(request):
    can_manage = request.user.has_perm('finance.view_all_contributions')
    contributions = Contribution.objects.select_related('member', 'recorded_by')
    if not can_manage:
        contributions = contributions.filter(member=request.user)
    totals = contributions.filter(status=Contribution.Status.PAID).values('currency').annotate(total=Sum('amount'))
    page = Paginator(contributions, 25).get_page(request.GET.get('page'))
    return render(request, 'finance/list.html', {'page': page, 'totals': totals, 'can_manage': can_manage})


@login_required
@permissions_required('finance.add_contribution')
def contribution_record(request):
    form = ContributionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        contribution = form.save(commit=False)
        contribution.recorded_by = request.user
        if contribution.status == Contribution.Status.PAID and not contribution.paid_at:
            from django.utils import timezone

            contribution.paid_at = timezone.now()
        contribution.save()
        Notification.objects.create(
            user=contribution.member,
            category=Notification.Category.CONTRIBUTION,
            title='Mise à jour de votre cotisation',
            body=f'{contribution.get_status_display()} · {contribution.amount} {contribution.currency} · {contribution.period}',
            url='/cotisations/',
        )
        if contribution.member.email_verified:
            send_mail(
                'Mise à jour de votre cotisation CEOBEF',
                f'Votre cotisation pour {contribution.period} est au statut : {contribution.get_status_display()}. Montant : {contribution.amount} {contribution.currency}.',
                None,
                [contribution.member.email],
                fail_silently=True,
            )
        messages.success(request, 'La cotisation a été enregistrée.')
        return redirect('finance:list')
    return render(request, 'finance/form.html', {'form': form})


@login_required
def download_receipt(request, pk):
    contribution = get_object_or_404(Contribution, pk=pk)
    can_manage = request.user.has_perm('finance.view_all_contributions')
    if contribution.member_id != request.user.pk and not can_manage:
        raise Http404
    if not contribution.receipt:
        raise Http404
    try:
        return FileResponse(contribution.receipt.open('rb'), as_attachment=True, filename=contribution.receipt.name.rsplit('/', 1)[-1])
    except (OSError, ValueError) as error:
        raise Http404 from error
