from django.forms import ModelForm, ImageField
from .models import Room, Post, User, NewStudent, NewTeacher, Course, LessonCorrection, Resign, Availability
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class MyUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=10,
        label=_("Nazwa użytkownika (maks. 10 znaków)"),
        validators=[MaxLengthValidator(limit_value=10, message=_("Nazwa użytkownika nie może przekraczać 10 znaków."))],
        help_text=_("Maksymalnie 10 znaków."),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class NewTeacherForm(forms.ModelForm):
    class Meta:
        model = NewTeacher

        labels = {
            'name': 'Imie i nazwisko korepetytora',
            'phone_number': 'Numer telefonu',
            'school': 'Najwyższy osiągnięty stopień edukacji',
            'subject': 'Wybierz podstawowy przedmiot, z którego chcesz udzielać korepetycji',
            'age_language': 'Czy masz ukończone 18 lat i znasz język polski na poziomie ojczystym?',
        }

        fields = ['name', 'phone_number', 'school', 'subject', 'age_language']


class ApplyTeacherForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        validators=[MaxLengthValidator(limit_value=10, message=_("Nazwa użytkownika nie może przekraczać 10 znaków."))],
        label=_("Nazwa użytkownika (będzie używana w 'Strefie Wiedzy')")
    )

    class Meta:
        model = User

        labels = {
            'username': 'Nazwa użytkownika (będzie używana w "Strefie Wiedzy")',
            'email': 'Email',
        }

        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class NewStudentForm(forms.ModelForm):
    class Meta:
        model = NewStudent

        labels = {
            'name': 'Imie i nazwisko ucznia',
            'phone_number': 'Numer telefonu',
            'subject': 'Wybierz podstawowy przedmiot, z którego chcesz otrzymywać korepetycje',
            'school': 'Aktualny stopień edukacji',
            'level': 'Wybierz rodzaj zajęć',
        }

        fields = ['name', 'phone_number', 'subject', 'school', 'level']


class ApplyStudentForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        validators=[MaxLengthValidator(limit_value=10, message=_("Nazwa użytkownika nie może przekraczać 10 znaków."))],
        label=_("Nazwa użytkownika (będzie używana w 'Strefie Wiedzy')")
    )

    class Meta:
        model = User

        labels = {
            'username': 'Nazwa użytkownika (będzie używana w "Strefie Wiedzy")',
            'email': 'Email'
        }

        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']

    image = ImageField(required=False)


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
        }
        fields = ['avatar', 'username', 'email', 'bio']

    bio = forms.CharField(widget=forms.Textarea, required=False)


class PostFormCreate(forms.ModelForm):
    event_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Data',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    def clean_event_datetime(self):
        event_datetime = self.cleaned_data['event_datetime']
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if event_datetime <= minimum_datetime:
            raise ValidationError("Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")

        return event_datetime

    class Meta:
        model = Post
        fields = ['title', 'description', 'course', 'event_datetime']


class PostFormEdit(forms.ModelForm):
    event_datetime = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Data',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Post
        fields = ['title', 'description', 'event_datetime']

    def clean_event_datetime(self):
        event_datetime = self.cleaned_data['event_datetime']
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if event_datetime <= minimum_datetime:
            raise ValidationError("Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")

        return event_datetime


class LessonFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        post_instance = kwargs.pop('post_instance')
        super(LessonFeedbackForm, self).__init__(*args, **kwargs)
        self.fields['attended_students'].queryset = post_instance.course.students.all()

    class Meta:
        model = Post
        fields = ['feedback', 'points', 'schoolweb_rating', 'attended_students', 'attended_teachers']

    attended_teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='Teachers'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Nauczyciele, którzy dołączyli'
    )

    attended_students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='Students'),
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
            self.fields['attended_students'].queryset = course.students.all()

    class Meta:
        model = LessonCorrection
        fields = ['attended_teachers', 'attended_students', 'feedback', 'lesson_image']

    attended_teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='Teachers'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Nauczyciele, którzy dołączyli',
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

    lesson_image = forms.ImageField(label='Zdjęcie lekcji', required=False)


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