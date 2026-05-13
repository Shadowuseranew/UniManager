from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, TeacherProfile
from academy.models import Student

PROFILE_REGISTRY = {
    'student': {
        'model': Student,
        'field': 'student_profile',
        'defaults': lambda user: {
            'student_id': f"ST-{user.username}",
            'phone_number': user.phone_number or '',
        },
    },
    'teacher': {
        'model': TeacherProfile,
        'field': 'teacher_profile',
        'defaults': lambda user: {'specialization': ''},
    },
}

@receiver(post_save, sender=User)
def handle_user_profiles(sender, instance, created, **kwargs):
    config = PROFILE_REGISTRY.get(instance.role)
    if not config:
        return

    if created:
        config['model'].objects.create(
            user=instance, **config['defaults'](instance)
        )
    elif hasattr(instance, config['field']):
        getattr(instance, config['field']).save()