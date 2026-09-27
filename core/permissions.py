from functools import wraps

from django.core.exceptions import PermissionDenied


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            if not request.user.is_superuser and request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def permissions_required(*permissions):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            if not request.user.is_superuser and not all(request.user.has_perm(permission) for permission in permissions):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator