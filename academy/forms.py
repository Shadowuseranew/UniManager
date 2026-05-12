from django import forms
from .models import Timetable, Subject, Classroom, Group, Payment, Exam, StudyMaterial, Notification, Semester, Faculty
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
            'faculty': forms.Select(attrs={
                'class': 'form-select',
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

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'description', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(role='student')
        self.fields['student'].label = "Talaba"
        self.fields['amount'].label = "Summa"

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['subject', 'group', 'exam_type', 'date', 'start_time', 'end_time', 'max_score']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['subject', 'title', 'file']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['recipient', 'title', 'message']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipient'].queryset = User.objects.all()

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

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'academic_year', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 2025-2026 Bahorgi semestr'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }