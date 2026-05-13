from django.core.exceptions import PermissionDenied

class RoleRequiredMixin:
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']

class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['teacher']

class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['student']

class AdminOrTeacherMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'teacher']
