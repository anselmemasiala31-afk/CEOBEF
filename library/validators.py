from pathlib import Path

from django.core.exceptions import ValidationError


ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'}
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024


def validate_document_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError('Type de fichier non autorisé.')
    if uploaded_file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError('Le fichier ne peut pas dépasser 20 Mo.')
    if extension == '.pdf':
        header = uploaded_file.read(5)
        uploaded_file.seek(0)
        if header != b'%PDF-':
            raise ValidationError('Le contenu du fichier ne correspond pas à un document PDF.')