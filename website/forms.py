from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import ContactMessage
from students.models import Student
from students.validators import validate_age_18_plus
from courses.models import Course, Branch


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
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True).order_by('order', 'name'),
        empty_label="-- Select Training Branch --",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_branch', 'required': True})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True).order_by('order', 'name'),
        empty_label="-- Select Driving Course / Category --",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course', 'required': True})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True})
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'id_number', 'date_of_birth', 'gender', 'branch', 'course',
            'preferred_schedule', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712 345 678', 'required': True}),
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport Number', 'required': True}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'preferred_schedule': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any prior driving experience, questions, or medical notes?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True).order_by('order', 'name')
        self.fields['course'].queryset = Course.objects.filter(is_active=True).order_by('order', 'name')
        today = date.today()
        try:
            max_dob = today.replace(year=today.year - 18)
        except ValueError:
            max_dob = today.replace(year=today.year - 18, month=2, day=28)
        self.fields['date_of_birth'].widget.attrs['max'] = max_dob.isoformat()

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            raise ValidationError("Date of birth is required.")
        validate_age_18_plus(dob)
        return dob

    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get('branch')
        course = cleaned_data.get('course')
        email = (cleaned_data.get('email') or '').strip()
        id_number = (cleaned_data.get('id_number') or '').strip()
        if branch and not branch.is_active:
            self.add_error('branch', "Selected branch is not active.")
        if branch and course:
            if course.branches.exists() and not course.branches.filter(pk=branch.pk).exists():
                self.add_error('course', f"'{course.name}' is not offered at {branch.name}.")
        if course and (email or id_number):
            from django.db.models import Q
            active_statuses = ['PENDING_APPROVAL', 'pending', 'APPROVED', 'approved', 'enrolled']
            q = Q()
            if email:
                q |= Q(email__iexact=email)
            if id_number:
                q |= Q(id_number__iexact=id_number)
            dup_qs = Student.objects.filter(q, course=course, status__in=active_statuses)
            if self.instance and self.instance.pk:
                dup_qs = dup_qs.exclude(pk=self.instance.pk)
            if dup_qs.exists():
                self.add_error('course', "This student is already enrolled in this course.")
        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)
        student.status = 'PENDING_APPROVAL'
        if student.branch:
            student.preferred_branch = student.branch.name
        if commit:
            student.save()
        return student
