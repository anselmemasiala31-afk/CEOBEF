from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from community.models import Notification
from community.services import notify_users
from core.permissions import permissions_required
from .forms import DocumentForm
from .models import Document


@login_required
def document_list(request):
    documents = Document.objects.select_related('uploaded_by')
    if not request.user.has_perm('library.download_document'):
        documents = documents.filter(is_public=True)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    if query:
        documents = documents.filter(title__icontains=query) | documents.filter(description__icontains=query)
    if category:
        documents = documents.filter(category=category)
    page = Paginator(documents.distinct(), 20).get_page(request.GET.get('page'))
    return render(request, 'library/list.html', {'page': page, 'query': query, 'categories': Document.Category.choices, 'selected_category': category})


@login_required
@permissions_required('library.add_document')
def document_upload(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        document = form.save(commit=False)
        document.uploaded_by = request.user
        document.original_name = document.file.name
        document.save()
        notify_users(
            User.objects.filter(is_active=True).exclude(pk=request.user.pk).values_list('id', flat=True),
            category=Notification.Category.DOCUMENT,
            title=f'Nouveau document : {document.title}',
            body=document.description[:280],
            url='/documents/',
        )
        messages.success(request, 'Le document a été ajouté à la bibliothèque.')
        return redirect('library:list')
    return render(request, 'library/form.html', {'form': form})


@login_required
def document_download(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not document.is_public and not request.user.has_perm('library.download_document'):
        raise Http404
    try:
        return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.original_name or document.file.name.rsplit('/', 1)[-1])
    except OSError as error:
        raise Http404 from error
