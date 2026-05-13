def base_template(request):
    if not request.user.is_authenticated:
        return {'base_template': 'base.html'}
    role_map = {
        'admin': 'admin_base.html',
        'teacher': 'teacher_base.html',
        'student': 'student_base.html',
    }
    return {'base_template': role_map.get(request.user.role, 'base.html')}
