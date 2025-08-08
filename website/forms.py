from django.forms import ModelForm, ImageField
from .models import (Room, Lesson, User, Topic, Message, Course, LessonCorrection, Resign, Availability, Report, NewStudents)
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta, datetime
import re

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~USER-CREATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''

def validate_username_length(value):
    if len(value) > 10:
        raise ValidationError(_("Nazwa użytkownika nie może przekraczać 10 znaków."))


class MyUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label=_("Nazwa użytkownika (maks. 10 znaków)"),
        validators=[validate_username_length],
        help_text=_("Maksymalnie 10 znaków."),
    )
    first_name = forms.CharField(
        required=True,
        label=_("Imię"),
        max_length=30
    )
    last_name = forms.CharField(
        required=True,
        label=_("Nazwisko"),
        max_length=30
    )
    email = forms.EmailField(
        required=True,
        label=_("E-mail")
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~KNOWLEDGE-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']

    level = forms.ChoiceField(choices=Room.LEVEL_CHOICES, widget=forms.Select, required=True)


class RoomMessageForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Wpisz treść wiadomości...',
            'rows': 4
        }),
        required=False,
        label='Treść komentarza'
    )

    image_clear = forms.BooleanField(
        required=False,
        initial=False,
        label='Usuń obraz'
    )

    class Meta:
        model = Message
        fields = ['body', 'image', 'file']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance or not self.instance.image:
            self.fields['image_clear'].widget = forms.HiddenInput()

        # Całkowicie usuń automatyczny opis i checkbox Django
        self.fields['image'].widget.initial_text = ''
        self.fields['image'].widget.clear_checkbox_label = ''
        self.fields['image'].widget.input_text = 'Zmień obraz'
        self.fields['image'].widget.template_name = 'knowledge-zone/custom_clearable_file_input.html'

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('image_clear'):
            cleaned_data['image'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Jeśli obraz ma zostać usunięty — usuń plik i wartość
        if self.cleaned_data.get('image_clear') and instance.image:
            instance.image.delete(save=False)
            instance.image = None

        if commit:
            instance.save()
        return instance


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserForm(forms.ModelForm):
    username = forms.CharField(
        validators=[MaxLengthValidator(10, message="Nazwa użytkownika nie może przekraczać 10 znaków.")]
    )
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['avatar', 'username', 'email', 'bio', 'interests']
        labels = {
            'avatar': 'Zdjęcie profilowe',
            'username': 'Nazwa użytkownika (maks. 10 znaków)',
            'email': 'Email',
            'bio': 'Bio',
            'interests': 'Zainteresowania'
        }

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~TUTORING-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


class WriterDataForm(forms.ModelForm):
    user_type = forms.ChoiceField(
        choices=[('teacher', 'Korepetytor'), ('student', 'Uczeń')],
        label="Wybierz rolę"
    )
    referral_code_input = forms.CharField(
        max_length=10,
        required=False,
        label="Kod polecenia",
    )

    notes = forms.CharField(required=False, label="Dodatkowe uwagi", widget=forms.Textarea(attrs={
            'placeholder': 'Możesz tutaj wpisać dodatkowe informacje, np. tematy, które chciałbyś przerobić, swoje potrzeby edukacyjne, oczekiwania względem korepetycji lub inne istotne uwagi.',
            'rows': 4
        })
    )

    age_confirmation = forms.BooleanField(required=True, label="Potwierdzam ukończenie 18 lat lub zgoda została wyrażona przez opiekuna prawnego.")


    class Meta:
        model = User
        fields = ['phone_number', 'level', 'subject']
        labels = {
            'phone_number': 'Numer telefonu',
            'level': 'Poziom nauki',
            'subject': 'Wybierz przedmiot',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['subject'].required = True
        self.fields['level'].required = True

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        if not phone_number or phone_number == 'N/A':
            raise forms.ValidationError("Numer telefonu jest wymagany.")

        if len(phone_number) != 9 or not re.match(r'^\d{9}$', phone_number):
            raise forms.ValidationError("Numer telefonu musi zawierać dokładnie 9 cyfr.")

        return phone_number

    def clean_user_type(self):
        user_type = self.cleaned_data.get('user_type')
        if user_type not in ['teacher', 'student']:
            raise forms.ValidationError("Wybierz prawidłową rolę.")
        return user_type


class ApplyUserForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', 'Uczeń'),
        ('teacher', 'Korepetytor'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label="Wybierz rolę")
    phone_number = forms.CharField(max_length=20, required=True, label="Numer telefonu")
    subject = forms.ModelChoiceField(queryset=Topic.objects.all(), label="Wybierz przedmiot", required=False)
    level = forms.ChoiceField(choices=User.LEVEL_CHOICES, required=True, label="Poziom zajęć", initial="podstawa")
    notes = forms.CharField(required=False, label="Dodatkowe uwagi",widget=forms.Textarea(attrs={
            'placeholder': 'Możesz tutaj wpisać dodatkowe informacje, np. tematy, które chciałbyś przerobić, swoje potrzeby edukacyjne, oczekiwania względem korepetycji lub inne istotne uwagi.',
            'rows': 4,
        })
    )
    terms_and_privacy = forms.BooleanField(required=True)
    age_confirmation = forms.BooleanField(required=True, label="Potwierdzam ukończenie 18 lat lub zgoda została wyrażona przez opiekuna prawnego.")
    referral_code_input = forms.CharField(
        max_length=10,
        required=False,
        label="Kod polecenia",
    )

    username = forms.CharField(
        max_length=10,
        label="Nazwa użytkownika (maks. 10 znaków)",
        validators=[MaxLengthValidator(10, message="Nazwa użytkownika nie może mieć więcej niż 10 znaków.")],
    )

    class Meta:
        model = User
        fields = ['role', 'first_name', 'last_name', 'username', 'email', 'phone_number', 'subject', 'level',
                  'referral_code_input', 'password1', 'password2']



class ResignationForm(forms.ModelForm):
    pause_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'resignation_start_date'}), required=False
    )
    pause_end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'resignation_end_date'}), required=False
    )
    resignation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'last_day'}), required=False
    )

    course_info = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Nazwa kursu, imię i nazwisko ucznia/ów...'}), required=False
    )
    rating = forms.ChoiceField(choices=Resign.RATING_CHOICES, label='Ocena platformy SchoolWeb', required=True)
    consider_return = forms.ChoiceField(choices=Resign.RETURN_OPTIONS, label='Czy rozważasz powrót na SchoolWeb?', required=True)
    reason_details = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Dodatkowe informacje'}), required=False
    )

    class Meta:
        model = Resign
        fields = ['reason', 'course_info', 'rating', 'consider_return', 'reason_details']

    def __init__(self, *args, **kwargs):
        is_teacher = kwargs.pop('is_teacher', False)
        super().__init__(*args, **kwargs)

        if not is_teacher:
            del self.fields['reason']
            del self.fields['course_info']



class LessonFormCreate(forms.ModelForm):
    event_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Data',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LessonFormCreate, self).__init__(*args, **kwargs)

        if user:
            self.fields['course'].queryset = Course.objects.filter(teacher=user)
            self.fields['course'].label_from_instance = lambda obj: f"{obj.name}"

    def clean_event_datetime(self):
        event_datetime = self.cleaned_data['event_datetime']
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if event_datetime <= minimum_datetime:
            raise ValidationError("Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")

        return event_datetime

    class Meta:
        model = Lesson
        fields = ['title', 'description', 'course', 'event_datetime']


class LessonFormEdit(forms.ModelForm):
    event_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Data',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Lesson
        fields = ['title', 'description', 'event_datetime']

    def clean_event_datetime(self):
        event_datetime = self.cleaned_data['event_datetime']
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if event_datetime <= minimum_datetime:
            raise ValidationError("Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")

        return event_datetime


class NewStudentForm(forms.ModelForm):
    class Meta:
        model = NewStudents
        fields = ['subject', 'level']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class LessonFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        post_instance = kwargs.pop('post_instance')
        super(LessonFeedbackForm, self).__init__(*args, **kwargs)

        self.fields['attended_teachers'].queryset = User.objects.filter(
            courses_taught=post_instance.course
        )

        self.fields['attended_students'].queryset = post_instance.course.students.all()

    class Meta:
        model = Lesson
        fields = ['feedback', 'points', 'schoolweb_rating', 'attended_students', 'attended_teachers']

    attended_teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Nauczyciele, którzy dołączyli'
    )

    attended_students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Uczniowie, którzy dołączyli'
    )

    feedback = forms.CharField(
        label='Dodatkowe informacje na temat lekcji:',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False,
        initial="-",
    )


class LessonCorrectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super(LessonCorrectionForm, self).__init__(*args, **kwargs)

        if course:
            self.fields['attended_teachers'].queryset = User.objects.filter(
                courses_taught=course
            )

            self.fields['attended_students'].queryset = course.students.all()

    class Meta:
        model = LessonCorrection
        fields = ['attended_teachers', 'attended_students', 'feedback', 'lesson_image']

    attended_teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Nauczyciele, którzy dołączyli'
    )

    attended_students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Uczniowie, którzy dołączyli'
    )

    feedback = forms.CharField(
        label='Dodatkowe informacje:',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )

    lesson_image = forms.ImageField(
        label='Zdjęcie lekcji',
        required=False
    )


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['day', 'hour_6_7', 'hour_7_8', 'hour_8_9', 'hour_9_10', 'hour_10_11', 'hour_11_12',
                  'hour_12_13', 'hour_13_14', 'hour_14_15', 'hour_15_16', 'hour_16_17', 'hour_17_18',
                  'hour_18_19', 'hour_19_20', 'hour_20_21', 'hour_21_22']

    def __init__(self, *args, **kwargs):
        super(AvailabilityForm, self).__init__(*args, **kwargs)
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        seven_days_later = tomorrow + timezone.timedelta(days=7)
        self.fields['day'].widget = forms.DateInput(attrs={'type': 'date', 'min': tomorrow.date(), 'max': seven_days_later.date()})
