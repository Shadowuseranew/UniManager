from django import forms
from .models import Timetable, Subject, Lesson, Classroom, Group
from users.models import User

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'credits']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        # 'room' o'rniga 'classroom' ishlatamiz
        fields = ['subject', 'teacher', 'classroom', 'day', 'start_time', 'end_time', 'group_name']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'classroom': forms.Select(attrs={'class': 'form-select'}), # Bu endi Select (ForeignKey bo'lgani uchun)
            'group_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: IF-21'}),
        }

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        # Modelingizdagi maydon nomlari bilan bir xil bo'lishi shart
        fields = ['number', 'capacity', 'room_type'] 
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 302'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sig\'imi'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'number': 'Xona raqami',
            'capacity': 'Sig\'imi',
            'room_type': 'Xona turi',
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        # Barcha kerakli maydonlarni ro'yxatga olamiz
        fields = ['name', 'faculty', 'course_number', 'teacher', 'subjects']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Masalan: IF-21'
            }),
            'faculty': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Masalan: Kompyuter injiniringi'
            }),
            'course_number': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 4
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subjects': forms.SelectMultiple(attrs={
                'class': 'form-control', 
                'style': 'height: 150px;',
                'help_text': 'Bir nechta fanni tanlash uchun Ctrl tugmasini bosib turing'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. Faqat 'teacher' rolidagi foydalanuvchilarni tanlash imkonini beramiz
        self.fields['teacher'].queryset = User.objects.filter(role='teacher')
        
        # 2. Maydonlarga chiroyli nomlar (labels) beramiz
        self.fields['teacher'].label = "Guruh rahbari (Kurator)"
        self.fields['subjects'].label = "Ushbu guruh o'qiydigan fanlar"

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        # DIQQAT: Bu yerga 'group' maydonini qo'shishingiz shart
        fields = ['group', 'subject', 'teacher', 'day_of_week', 'start_time', 'end_time', 'classroom']
        
        widgets = {
            # Guruh tanlash (Select) vidjetini qo'shing
            'group': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'classroom': forms.Select(attrs={'class': 'form-select'}), # Xonani ham Select qiling
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }