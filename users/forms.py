from django import forms
from .models import User, TeacherProfile
from academy.models import Group

class BaseUserForm(forms.ModelForm):
    """Barcha foydalanuvchilar uchun umumiy maydonlar"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Parol"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        return super().save(commit=commit)

class AdminAddForm(BaseUserForm):
    """Admin qo'shish formasi"""
    class Meta(BaseUserForm.Meta):
        fields = BaseUserForm.Meta.fields

class TeacherAddForm(BaseUserForm):
    """O'qituvchi qo'shish formasi"""
    specialization = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Mutaxassislik"
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="O'qituvchi haqida"
    )

    class Meta(BaseUserForm.Meta):
        fields = BaseUserForm.Meta.fields + ['specialization', 'bio']

class StudentAddForm(BaseUserForm):
    """Talaba qo'shish formasi"""
    course = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
        label="Kurs"
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'style': 'height: 150px;'}),
        label="Guruhlarni tanlang"
    )
    parent = forms.ModelChoiceField(
        queryset=User.objects.filter(role='parent'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Ota-ona"
    )

    class Meta(BaseUserForm.Meta):
        fields = BaseUserForm.Meta.fields + ['course', 'groups', 'parent']

class ParentAddForm(BaseUserForm):
    class Meta(BaseUserForm.Meta):
        fields = BaseUserForm.Meta.fields

class UserCreationForm(StudentAddForm):
    """Eski viewlar bilan moslikni ta'minlash uchun (vaqtincha)"""
    role = forms.ChoiceField(choices=User.USER_ROLES, widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta(StudentAddForm.Meta):
        fields = StudentAddForm.Meta.fields + ['role']