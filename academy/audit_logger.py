from .models import AuditLog

def log_action(request, action, model_name, obj=None, details=''):
    user = request.user if request.user.is_authenticated else None
    ip = request.META.get('REMOTE_ADDR', '')
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=obj.pk if obj else None,
        object_repr=str(obj)[:255] if obj else '',
        details=details,
        ip_address=ip,
    )
