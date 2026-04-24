from django import forms
from .models import User
from academy.models import Group  # Guruhlarni olish uchun

from django import forms
from .models import User
from academy.models import Group

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Parol"
    )
    
    student_id = forms.CharField(
        max_length=20, 
        required=False, # Majburiy emas qilamiz, chunki admin yoki o'qituvchiga kerakmas bo'lishi mumkin
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: ST-2026-001'}),
        label="Talaba ID"
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'style': 'height: 150px;'}),
        label="Guruhlarni tanlang"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

def save(self, commit=True):
    # commit=False bilan bazaga yozishni vaqtincha to'xtatamiz
    user = super().save(commit=False)
    
    # Formadan parolni olamiz
    password = self.cleaned_data.get("password")
    
    if password:
        # Agar yangi parol yozilgan bo'lsa, uni shifrlab saqlaymiz
        user.set_password(password)
    
    # DIQQAT: Bu yerda boshqa set_password qatori bo'lmasligi kerak!
    
    if commit:
        user.save()
    return user