from django import forms
from .models import ContactMessage
from students.models import Student
from courses.models import Course

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Full Name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email Address',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (e.g. 0712 345 678)',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What is your inquiry about?',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your message or inquiry here...',
                'required': True,
            }),
        }


class EnrollmentForm(forms.ModelForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        empty_label="-- Select Driving Course / License Category --",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'id_number', 'date_of_birth', 'gender', 'course',
            'preferred_schedule', 'preferred_branch', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712 345 678', 'required': True}),
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport Number', 'required': True}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'preferred_schedule': forms.Select(attrs={'class': 'form-select'}),
            'preferred_branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main Campus Nairobi / Westlands / Thika Road'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any prior driving experience, questions, or medical notes?'}),
        }

    def save(self, commit=True):
        student = super().save(commit=False)
        student.status = 'pending'
        if commit:
            student.save()
        return student
