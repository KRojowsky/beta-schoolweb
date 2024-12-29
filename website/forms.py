from django.forms import ModelForm, ImageField
from .models import (Room, Lesson, User, Topic, Message, Course, LessonCorrection, Resign, Availability, Report,
                     BankInformation, NewStudents)
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta, datetime

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~USER-CREATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


class MyUserCreationForm(UserCreationForm):
    usable_password = None
    username = forms.CharField(
        max_length=10,
        label=_("Nazwa użytkownika (maks. 10 znaków)"),
        validators=[MaxLengthValidator(limit_value=10, message=_("Nazwa użytkownika nie może przekraczać 10 znaków."))],
        help_text=_("Maksymalnie 10 znaków."),
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

    # Dodane pole wyboru poziomu
    level = forms.ChoiceField(choices=Room.LEVEL_CHOICES, widget=forms.Select, required=True)


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
        validators=[MaxLengthValidator(limit_value=10, message="Nazwa użytkownika nie może przekraczać 10 znaków.")]
    )

    class Meta:
        model = User
        labels = {
            'avatar': 'Zdjęcie profilowe',
            'username': 'Nazwa użytkownika(maks. 10 znaków)',
            'email': 'Email',
            'bio': 'Bio',
            'interests': 'Zainteresowania'
        }
        fields = ['avatar', 'username', 'email', 'bio', 'interests']

    bio = forms.CharField(widget=forms.Textarea, required=False)


class PostFormCreate(forms.ModelForm):
    event_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Data',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PostFormCreate, self).__init__(*args, **kwargs)

        if user:
            self.fields['course'].queryset = Course.objects.filter(teacher=user)
            # Nadpisz pole 'course' aby wyświetlało 'name' kursu
            self.fields['course'].label_from_instance = lambda obj: f"{obj.name}"  # Wyświetlanie nazwy kursu

    def clean_event_datetime(self):
        event_datetime = self.cleaned_data['event_datetime']
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if event_datetime <= minimum_datetime:
            raise ValidationError("Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")

        return event_datetime

    class Meta:
        model = Lesson
        fields = ['title', 'description', 'course', 'event_datetime']


class PostFormEdit(forms.ModelForm):
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


class RoomMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'image', 'file']


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~TUTORING-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
class WriterDataForm(forms.ModelForm):
    user_type = forms.ChoiceField(
        choices=[('teacher', 'Korepetytor'), ('student', 'Uczeń')],
        label="Wybierz rolę"
    )

    class Meta:
        model = User
        fields = ['phone_number', 'level', 'subject']

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
    terms_and_privacy = forms.BooleanField(required=True, label="Akceptuję regulamin i politykę prywatności")
    age_confirmation = forms.BooleanField(required=True, label="Potwierdzam ukończenie 18 lat")
    referral_code_input = forms.CharField(
        max_length=10,
        required=False,
        label="Kod polecenia",
        help_text="Jeśli masz kod polecenia, wpisz go tutaj. Uczniowie muszą podać kod innego ucznia, nauczyciele - kod innego nauczyciela."
    )

    class Meta:
        model = User
        fields = ['role', 'first_name', 'last_name', 'username', 'email', 'phone_number', 'subject', 'level',
                  'referral_code_input', 'password1', 'password2']


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


class BankInformationForm(forms.ModelForm):
    expiration_month = forms.ChoiceField(label='Miesiąc', choices=[])
    expiration_year = forms.ChoiceField(label='Rok', choices=[])

    class Meta:
        model = BankInformation
        fields = ['card_number', 'cvv', 'cardholder_name', 'expiration_month', 'expiration_year']
        labels = {
            'card_number': 'Numer karty',
            'cvv': 'CVV',
            'cardholder_name': 'Imię i nazwisko',
        }
        widgets = {
            'card_number': forms.TextInput(attrs={
                'maxlength': '16',
                'placeholder': '16-cyfrowy numer karty',
            }),
            'cvv': forms.TextInput(attrs={
                'maxlength': '3',
                'placeholder': 'CVV',
            }),
            'cardholder_name': forms.TextInput(attrs={'placeholder': 'Imię i nazwisko właściciela'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        self.fields['expiration_month'].choices = [(i, f'{i:02}') for i in range(1, 13)]  # Months 1 to 12
        self.fields['expiration_year'].choices = [(year, year) for year in range(current_year, current_year + 6)]  # Current year to 5 years ahead

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('expiration_month')
        year = cleaned_data.get('expiration_year')

        if month and year:
            # Create the expiration date with the first day of the month
            cleaned_data['expiration_date'] = f'{year}-{month}-01'  # Format YYYY-MM-DD
        return cleaned_data


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


class ResignationForm(forms.ModelForm):
    course_info = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Nazwa kursu, imie i nazwisko ucznia/ów, numeru telefonu/ów, przedmiot, częstotliwość zajęć, dodatkowe informacje itd.'}))
    rating = forms.ChoiceField(choices=Resign.RATING_CHOICES, label='Ocena platformy SchoolWeb', required=True)
    consider_return = forms.ChoiceField(choices=Resign.RETURN_OPTIONS, label='Czy rozważasz powrót na SchoolWeb', required=True)
    reason_details = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Podaj dodatkowe informacje dotyczące powodu rezygnacji/przerwy'}),required=False)

    class Meta:
        model = Resign
        fields = ['email', 'reason', 'start_date', 'end_date', 'course_info', 'rating', 'consider_return', 'reason_details']


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