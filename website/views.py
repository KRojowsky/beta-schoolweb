from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.contrib.auth import authenticate, login, logout
from .models import (User, Room, Topic, Message, Course, Lesson, LessonStats, CourseMessage, PlatformMessage, BlogPost,
                     BlogCategory, BankInformation, LessonStats, TeachersEarning)
from .forms import (RoomForm, UserForm, MyUserCreationForm, PostFormCreate, PostFormEdit, LessonFeedbackForm,
                    LessonCorrectionForm, ResignationForm, ReportForm, RoomMessageForm,BankInformationForm,
                    ApplyUserForm, WriterDataForm)
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.urls import reverse
from django.http import JsonResponse
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from .forms import AvailabilityForm
from .models import Availability
from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from datetime import date

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~WIDGET~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def home(request):
    user_group = None

    if request.user.is_authenticated:
        if request.user.groups.exists():
            user_group = request.user.groups.first().name

    if user_group == 'Teachers':
        target_url = 'schoolweb:teacherPage'
    elif user_group == 'Students':
        target_url = 'schoolweb:studentPage'
    elif user_group in ['NewStudents', 'NewTeachers']:
        target_url = 'schoolweb:coursesLoader'
    elif user_group == 'Writer':
        target_url = 'schoolweb:applyUser'
    else:
        target_url = 'schoolweb:applyUser'

    return render(request, 'widget/main-view.html', {'target_url': target_url})


def become_tutor(request):
    return render(request, 'widget/become-tutor.html')


def faq(request):
    return render(request, 'widget/faq.html')


def statute(request):
    return render(request, 'widget/statute.html')


def contact(request):
    return render(request, 'widget/contact.html')


def subjects(request):
    return render(request, 'widget/subjects.html')


# SENDING EMAIL VIA PLATFORM CONTACT FORM

def user_message(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')

        PlatformMessage.objects.create(email=email, phone_number=phone_number, message=message)

    return render(request, 'base-widget.html')


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~KNOWLEDGE-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def loginPage(request):
    page = 'login'

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        next_url = request.POST.get('next') or reverse('schoolweb:knowledge_zone')

        user = User.objects.filter(email=email).first()

        if user is None:
            messages.error(request, 'Użytkownik nie istnieje')
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect(next_url)
            else:
                messages.error(request, 'Błędny Email lub Hasło')

    context = {'page': page}
    return render(request, 'knowledge-zone/login_register.html', context)


@login_required(login_url='schoolweb:login')
def logoutUser(request):
    logout(request)
    next_url = request.GET.get('next', 'schoolweb:knowledge_zone')
    return redirect(next_url)


def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username').lower()

            if check_user_exists_in_group(username):
                messages.error(request, 'Użytkownik już istnieje w grupie.')
                return redirect('schoolweb:registerPage')

            user = form.save(commit=False)
            user.username = username
            user.save()

            try:
                writers_group = Group.objects.get(name='Writers')
                user.groups.add(writers_group)
            except Group.DoesNotExist:
                messages.error(request, 'Grupa "Writers" nie istnieje.')
                return redirect('schoolweb:registerPage')
            except Exception as e:
                messages.error(request, f'Wystąpił błąd: {str(e)}')
                return redirect('schoolweb:registerPage')

            login(request, user)
            return redirect('schoolweb:knowledge_zone')
        else:
            error_messages = [error for errors in form.errors.values() for error in errors]
            for error in error_messages:
                messages.error(request, error)

    context = {'form': form}
    return render(request, 'knowledge-zone/login_register.html', context)


# CHECKING WHILE REGISTER IF USER EXISTS IN GROUP
def check_user_exists_in_group(username):
    try:
        user = User.objects.get(username=username)
        return user.groups.exists()
    except User.DoesNotExist:
        return False


def knowledge_zone(request):
    user_in_migrates = False

    if request.user.is_authenticated:
        user_in_migrates = request.user.groups.filter(name='Migrates').exists()

    q = request.GET.get('q', '')
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[:28]
    room_count = rooms.count()
    room_messages = Message.objects.order_by('-created')[:12]

    # Determine the redirect URL based on user group
    if request.user.is_authenticated:
        if request.user.groups.filter(name='NewTeachers').exists() or request.user.groups.filter(name='NewStudents').exists():
            user_redirect_url = reverse('schoolweb:coursesLoader')
        elif request.user.groups.filter(name='Teachers').exists():
            user_redirect_url = reverse('schoolweb:teacherPage')
        elif request.user.groups.filter(name='Students').exists():
            user_redirect_url = reverse('schoolweb:studentPage')
        elif request.user.groups.filter(name='Writers').exists():
            user_redirect_url = reverse('schoolweb:WriterToTutoringZone')
        else:
            user_redirect_url = reverse('schoolweb:applyUser')
    else:
        user_redirect_url = reverse('schoolweb:applyUser')

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
        'user_in_migrates': user_in_migrates,
        'user_redirect_url': user_redirect_url,  # Pass the full URL to the template
    }

    return render(request, 'knowledge-zone/knowledge-zone.html', context)


import logging

logger = logging.getLogger(__name__)


@login_required
def WriterToTutoringZone(request):
    # Upewnijmy się, że użytkownik jest w grupie 'Writers'
    if not request.user.groups.filter(name='Writers').exists():
        return redirect('schoolweb:knowledge_zone')

    if request.method == 'POST':
        form = WriterDataForm(request.POST, instance=request.user)
        if form.is_valid():
            # Zapisujemy dane użytkownika
            user = form.save(commit=False)

            # Pobieramy wybraną rolę
            user_type = form.cleaned_data['user_type']

            # Pobieramy odpowiednią grupę
            if user_type == 'teacher':
                new_group = Group.objects.get(name='NewTeachers')
            elif user_type == 'student':
                new_group = Group.objects.get(name='NewStudents')
            else:
                new_group = None

            # Usuwamy użytkownika z obecnych grup i przypisujemy do nowej
            if new_group:
                user.groups.clear()
                user.groups.add(new_group)

            # Zapisujemy zmiany w użytkowniku
            user.save()

            # Przekierowanie do kursów
            return redirect('schoolweb:coursesLoader')
    else:
        form = WriterDataForm(instance=request.user)

    return render(request, 'tutoring-zone/writer-to-tutoring-zone.html', {'form': form})


def room(request, pk):
    try:
        room = Room.objects.get(id=pk)
    except Room.DoesNotExist:
        return redirect('schoolweb:knowledge_zone')

    room_messages = room.message_set.all().order_by('created')
    participants = room.participants.all()

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')

        if body or image or file:
            message = Message.objects.create(
                user=request.user,
                room=room,
                body=body,
                image=image,
                file=file
            )
            room.participants.add(request.user)

            return redirect('schoolweb:room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'knowledge-zone/room.html', context)


@login_required(login_url='schoolweb:login')
def createRoom(request):
    form = RoomForm(request.POST or None, request.FILES or None)
    topics = Topic.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user

            # Handle image upload (if any)
            if 'image' in request.FILES:
                room.image.save(request.FILES['image'].name, request.FILES['image'])

            room.save()

            # Check if the user is in 'Teachers' group and has sufficient points
            if request.user.groups.filter(name='Teachers').exists() and request.user.points >= 1000:
                # Deduct 1000 points from the user
                request.user.points -= 1000
                request.user.save()

                # Add 50 zł bonus to both month_bonus and all_bonus for the user
                lesson_stats, created = LessonStats.objects.get_or_create(user=request.user)

                # Add 50 zł to both bonuses
                lesson_stats.month_bonus += 50  # Add to monthly bonus
                lesson_stats.all_bonus += 50  # Add to total bonus

                lesson_stats.save()

            # Check if the user is in the 'Student' group and their level
            if request.user.groups.filter(name='Students').exists() and request.user.points >= 1000:
                request.user.points -= 1000
                request.user.save()
                user_level = request.user.level

                lesson_stats, created = LessonStats.objects.get_or_create(user=request.user)

                if user_level == 'Podstawa':
                    lesson_stats.lessons += 1
                    lesson_stats.save()

                elif user_level == 'Rozszerzenie':
                    lesson_stats.lessons_intermediate += 1
                    lesson_stats.save()

            return redirect('schoolweb:knowledge_zone')

    context = {'form': form, 'topics': topics}
    return render(request, 'knowledge-zone/room_form.html', context)


@login_required(login_url='schoolweb:login')
def updateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        return HttpResponse('Operacja wzbroniona.')

    current_likes = room.likes.all()

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            updated_room = form.save(commit=False)
            updated_room.likes.set(current_likes)
            updated_room.save()
            return redirect('schoolweb:room', pk=room.id)
    else:
        form = RoomForm(instance=room)

    topics = Topic.objects.all()
    context = {'form': form, 'topics': topics}
    return render(request, 'knowledge-zone/room_form.html', context)


@login_required(login_url='schoolweb:login')
def reportRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.room = room
            report.reporter = request.user
            report.save()
            return redirect('schoolweb:knowledge_zone')
    else:
        form = ReportForm()
    return render(request, 'knowledge-zone/report-room.html', {'form': form, 'room': room})


@login_required(login_url='schoolweb:login')
def deleteRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        return HttpResponse('Operacja wzbroniona.')

    if request.method == 'POST':
        room.delete()
        return redirect('schoolweb:knowledge_zone')

    return render(request, 'knowledge-zone/delete.html', {'obj': room})


@login_required(login_url='schoolweb:login')
def deleteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user:
        return HttpResponse('Operacja wzbroniona.')

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    if request.method == 'POST':
        message.delete()

        lesson_url = request.session.get('lesson_url', '/')
        return redirect(lesson_url)

    return render(request, 'knowledge-zone/delete.html', {'obj': message})


@login_required(login_url='schoolweb:login')
def editRoomMessage(request, pk):
    message = get_object_or_404(Message, pk=pk)

    # Check if the user is the author of the message
    if request.user != message.user:
        return redirect('room', pk=message.room.pk)

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    if request.method == 'POST':
        form = RoomMessageForm(request.POST, request.FILES, instance=message)
        if form.is_valid():
            form.save()  # The points deduction and stats update will now happen in the model's save method

            # Redirect back to the lesson URL after saving
            lesson_url = request.session.get('lesson_url', '/')
            return redirect(lesson_url)
    else:
        form = RoomMessageForm(instance=message)

    return render(request, 'knowledge-zone/edit-message.html', {'form': form, 'message': message})


def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.hosted_rooms.all()  # Zamiast user.room_set.all()
    room_messages = user.messages.all()  # Zamiast user.message_set.all()
    topics = Topic.objects.all()

    # Determine the redirect URL based on user group
    if request.user.is_authenticated:
        if request.user.groups.filter(name='NewTeachers').exists() or request.user.groups.filter(name='NewStudents').exists():
            user_redirect_url = reverse('schoolweb:coursesLoader')
        elif request.user.groups.filter(name='Teachers').exists():
            user_redirect_url = reverse('schoolweb:teacherPage')
        elif request.user.groups.filter(name='Students').exists():
            user_redirect_url = reverse('schoolweb:studentPage')
        elif request.user.groups.filter(name='Writers').exists():
            user_redirect_url = reverse('schoolweb:WriterToTutoringZone')
        else:
            user_redirect_url = reverse('schoolweb:applyUser')
    else:
        user_redirect_url = reverse('schoolweb:applyUser')

    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
        'user_redirect_url': user_redirect_url,  # Pass the full URL to the template
    }
    return render(request, 'knowledge-zone/profile.html', context)


@login_required(login_url='schoolweb:login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('schoolweb:user-profile', pk=user.id)

    error_messages = [error for field, errors in form.errors.items() for error in errors]
    for error in error_messages:
        messages.error(request, error)

    return render(request, 'knowledge-zone/update-user.html', {'form': form})


def activityPage(request):
    try:
        room_messages = Message.objects.all()[:12]
    except Exception as e:
        room_messages = []

    return render(request, 'knowledge-zone/activity.html', {'room_messages': room_messages})


def topicsPage(request):
    q = request.GET.get('q', '')
    topics = Topic.objects.filter(Q(name__icontains=q))

    return render(request, 'knowledge-zone/topics.html', {'topics': topics})


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~TUTORING-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def applyUser(request):
    if request.method == 'POST':
        form = ApplyUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.phone_number = form.cleaned_data.get('phone_number')
            user.subject = form.cleaned_data.get('subject')
            user.level = form.cleaned_data.get('level')

            referral_code_input = form.cleaned_data.get('referral_code_input')
            role = form.cleaned_data.get('role')

            # Obsługa kodu polecenia
            if referral_code_input:
                referred_user = User.objects.filter(referral_code=referral_code_input).first()

                if referred_user:
                    if role == 'student' and referred_user.groups.filter(name="Students").exists():
                        user.referred_by = referral_code_input
                        lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)
                        if user.level == "Podstawa":
                            lesson_stats.lessons += 1
                        elif user.level == "Rozszerzenie":
                            lesson_stats.lessons_intermediate += 1
                        lesson_stats.save()
                    elif role == 'teacher' and referred_user.groups.filter(name="Teachers").exists():
                        user.referred_by = referral_code_input
                        lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)
                        lesson_stats.month_referral_bonus += 50  # Dodanie do miesięcznego bonusu
                        lesson_stats.all_referral_bonus += 50  # Dodanie do całkowitego bonusu
                        lesson_stats.save()
                    else:
                        form.add_error(
                            'referral_code_input',
                            'Kod polecenia jest nieprawidłowy lub należy do użytkownika spoza wymaganej grupy.'
                        )
                        return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})

            # Zapisanie użytkownika
            user.save()

            # Logowanie użytkownika
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)

                # Dodanie użytkownika do odpowiedniej grupy
                group_name = 'NewStudents' if role == 'student' else 'NewTeachers'
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    form.add_error(None, 'Nie znaleziono odpowiedniej grupy.')
                    return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})

                return redirect('schoolweb:coursesLoader')

            else:
                form.add_error(None, 'Błąd logowania, sprawdź dane.')

    else:
        form = ApplyUserForm()

    return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})


def coursesLoader(request):
    if not request.user.is_authenticated:
        return redirect('schoolweb:knowledge_zone')

    user_groups = request.user.groups.values_list('name', flat=True)

    if 'Teachers' in user_groups:
        return redirect('schoolweb:teacherPage')
    elif 'Student' in user_groups:
        return redirect('schoolweb:studentPage')
    elif 'NewStudents' in user_groups or 'NewTeachers' in user_groups:
        return render(request, 'tutoring-zone/user-creator.html')
    else:
        return redirect('schoolweb:knowledge_zone')


def noLessons(request):
    return render(request, 'tutoring-zone/no-lessons.html')


def change_user_group(user, new_group_name):
    try:
        new_group = Group.objects.get(name=new_group_name)
        user.groups.set([new_group])
        user.save()
        return True
    except Group.DoesNotExist:
        return False


def is_teacher(user):
    return user.groups.filter(name='Teachers').exists()


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def teacherPage(request):
    now = datetime.now() - timedelta(minutes=15)
    time_difference = timedelta(minutes=35)
    time_threshold = now - time_difference
    a = 0

    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)
    all_courses = Course.objects.all()

    upcoming_lessons = Lesson.objects.filter(
        Q(course__in=courses) & Q(event_datetime__gt=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('event_datetime')

    past_lessons = Lesson.objects.filter(
        Q(course__in=courses) & Q(event_datetime__lte=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('-event_datetime')

    lessons = list(upcoming_lessons) + list(past_lessons)

    post_count = len(lessons)
    lesson_messages = CourseMessage.objects.filter(room__in=lessons)

    context = {
        'lessons': lessons,
        'courses': courses,
        'post_count': post_count,
        'lesson_messages': lesson_messages,
        'all_courses': all_courses,
        'now': now,
        'time_threshold': time_threshold,
        'a': a,
        'teacher': teacher,
    }
    return render(request, 'tutoring-zone/teacher-view.html', context)


@login_required(login_url='schoolweb:login')
def lessonProfile(request, pk):
    user = get_object_or_404(User, id=pk)

    lesson_stats = getattr(user, 'lesson_stats', None)

    if not lesson_stats:
        lesson_stats = LessonStats.objects.create(user=user)

    month_earnings = (
        60 * lesson_stats.lessons_intermediate +
        40 * lesson_stats.lessons +
        20 * lesson_stats.break_lessons -
        50 * lesson_stats.missed_lessons +
        lesson_stats.month_bonus
    )
    all_earnings = (
        60 * lesson_stats.all_lessons_intermediate +
        40 * lesson_stats.all_lessons +
        20 * lesson_stats.all_break_lessons -
        50 * lesson_stats.all_missed_lessons +
        lesson_stats.all_bonus
    )

    logged_in_user = request.user
    is_teacher = logged_in_user.groups.filter(name='Teachers').exists()
    is_student = logged_in_user.groups.filter(name='Students').exists()

    # Set templates and determine accessible users
    if is_teacher:
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        courses_component = 'tutoring-zone/courses-component-teachers.html'
        courses = Course.objects.filter(teacher=logged_in_user)
        accessible_users = User.objects.filter(groups__name='Students', courses_enrolled__in=courses)
    elif is_student:
        navbar_template = 'tutoring-zone/nav-student-view.html'
        courses_component = 'tutoring-zone/courses-component-students.html'
        courses = Course.objects.filter(students=logged_in_user)
        accessible_users = User.objects.filter(
            Q(groups__name='Students', courses_enrolled__in=courses) |
            Q(groups__name='Teachers', courses_taught__in=courses)
        ).distinct()
    else:
        navbar_template = ''
        courses_component = ''
        courses = []
        accessible_users = []

    # Profile accessibility check
    is_accessible_profile = (
        logged_in_user == user or
        (is_teacher and user in accessible_users) or
        (is_student and user in accessible_users)
    )

    if not is_accessible_profile:
        return render(request, 'tutoring-zone/lesson-no-exists.html')

    # Fetch user's lessons and messages
    lessons = user.lesson_set.all()
    lesson_messages = user.coursemessage_set.all()

    context = {
        'user': user,
        'lessons': lessons,
        'lesson_messages': lesson_messages,
        'package': lesson_stats.lessons,
        'all_package': lesson_stats.all_lessons,
        'courses': courses,
        'navbar_template': navbar_template,
        'courses_component': courses_component,
        'month_earnings': month_earnings,
        'all_earnings': all_earnings,
        'is_teacher': is_teacher,
        'lesson_stats': lesson_stats,
    }

    return render(request, 'tutoring-zone/lesson-profile.html', context)


@login_required(login_url='login')
def bankInformation(request):
    bank_info = BankInformation.objects.filter(user=request.user).first()

    is_editing = request.GET.get('edit') == 'true'

    if request.method == 'POST':
        if not bank_info:
            bank_info = BankInformation(user=request.user)

        form = BankInformationForm(request.POST, instance=bank_info)

        if form.is_valid():
            form.save()
            return redirect('schoolweb:bank_information')
    else:
        form = BankInformationForm(instance=bank_info) if is_editing else None

    context = {
        'form': form,
        'bank_info': bank_info,
        'is_editing': is_editing,
    }
    return render(request, 'tutoring-zone/bank-informations.html', context)


@login_required(login_url='login')
def Teachersearnings(request):
    user_earnings = TeachersEarning.objects.filter(user=request.user).order_by('-year', '-month')

    context = {
        'user_earnings': user_earnings
    }

    return render(request, 'tutoring-zone/earnings-pdf.html', context)


@login_required(login_url='login')
def updateUserLessons(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('schoolweb:lesson-profile', pk=user.id)

    navbar_template = 'tutoring-zone/nav-teacher-view.html'
    error_messages = [error for field, errors in form.errors.items() for error in errors]
    for error in error_messages:
        messages.error(request, error)

    context = {'navbar_template': navbar_template, 'form': form}

    return render(request, 'tutoring-zone/update-user-lessons.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def createLesson(request):
    initial_data = {'host': request.user}
    form = PostFormCreate(user=request.user, initial=initial_data)
    current_date = timezone.now().strftime('%Y-%m-%dT%H:%M')

    if request.method == 'POST':
        form = PostFormCreate(request.POST, user=request.user, initial=initial_data)
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if form.is_valid():
            post = form.save(commit=False)
            post.host = request.user

            overlapping_lessons = Lesson.objects.filter(
                course__teacher=request.user,
                event_datetime__gte=post.event_datetime - timedelta(minutes=50),
                event_datetime__lte=post.event_datetime + timedelta(minutes=50)
            )

            students_in_course = post.course.students.all()
            student_has_lessons = True
            students_without_lessons = []

            for student in students_in_course:
                if post.course.course_type == 'basic' and student.lesson_stats.lessons <= 0:
                    student_has_lessons = False
                    students_without_lessons.append(student)
                elif post.course.course_type == 'intermediate' and student.lesson_stats.lessons_intermediate <= 0:
                    student_has_lessons = False
                    students_without_lessons.append(student)

            if not student_has_lessons:
                students_names = ', '.join(
                    [f"{student.first_name} {student.last_name}" for student in students_without_lessons])
                messages.error(request, f"Następujący studenci nie mają dostępnych lekcji: {students_names}.")
            elif overlapping_lessons.exists():
                messages.error(request, "W wybranym terminie istnieje już inna lekcja.")
            elif post.event_datetime <= minimum_datetime:
                messages.error(request, "Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")
            else:
                post.save()

                for student in students_in_course:
                    lesson_stats = student.lesson_stats
                    if post.course.course_type == 'basic':
                        lesson_stats.lessons -= 1
                    elif post.course.course_type == 'intermediate':
                        lesson_stats.lessons_intermediate -= 1
                    lesson_stats.save()

                messages.success(request, "Lekcja została pomyślnie utworzona.")
                return redirect('schoolweb:teacherPage')

    return render(request, 'tutoring-zone/create-lesson.html', {'form': form, 'current_date': current_date})


def courses_teachersPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    courses = Course.objects.filter(name__icontains=q)
    return render(request, 'tutoring-zone/courses-teachers.html', {'courses': courses})


def activity_lessonPage(request):
    lesson_messages = CourseMessage.objects.all()[0:12]
    return render(request, 'tutoring-zone/activity-lesson.html', {'lesson_messages': lesson_messages})


@login_required(login_url='login')
def lesson(request, pk):
    lesson = get_object_or_404(Lesson, id=pk)
    lesson_messages = lesson.coursemessage_set.order_by('-messageCreated')
    participants = lesson.participants.all()

    user = request.user
    course = lesson.course

    if user != course.teacher and user not in course.students.all():
        return redirect('access_denied')

    if request.method == 'POST':
        message = CourseMessage.objects.create(
            user=request.user,
            room=lesson,
            body=request.POST.get('body'),
            image=request.FILES.get('image'),
            file=request.FILES.get('file')
        )
        lesson.participants.add(request.user)

        message.save()
        return redirect('schoolweb:lesson', pk=lesson.id)

    navbar_template = ''
    back_link = ''

    if user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        back_link = reverse('schoolweb:teacherPage')
    elif user.groups.filter(name='Students').exists():
        navbar_template = 'tutoring-zone/nav-student-view.html'
        back_link = reverse('schoolweb:studentPage')

    context = {
        'lesson': lesson,
        'lesson_messages': lesson_messages,
        'participants': participants,
        'navbar_template': navbar_template,
        'back_link': back_link
    }
    return render(request, 'tutoring-zone/lesson.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def updateLesson(request, pk):
    post = get_object_or_404(Lesson, id=pk)

    if request.user != post.host:
        return HttpResponse('Brak dostępu')

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    time_difference = post.event_datetime - timezone.now()
    can_edit = time_difference.total_seconds() > 900

    if request.method == 'POST':
        form = PostFormEdit(request.POST, instance=post)
        if form.is_valid() and can_edit:
            overlapping_lessons = Lesson.objects.filter(
                course__teacher=request.user,
                event_datetime__gte=form.cleaned_data['event_datetime'] - timedelta(minutes=50),
                event_datetime__lte=form.cleaned_data['event_datetime'] + timedelta(minutes=50)
            ).exclude(id=pk)

            if overlapping_lessons.exists():
                form.add_error('event_datetime', "W wybranym terminie już istnieje inna lekcja.")
            else:
                form.save()
                lesson_url = request.session.get('lesson_url', '/')
                return redirect(lesson_url)
    else:
        form = PostFormEdit(instance=post)

    context = {'form': form, 'can_edit': can_edit}
    return render(request, 'tutoring-zone/update-lesson.html', context)


@login_required(login_url='login')
def deleteLessonMessage(request, pk):
    message = get_object_or_404(CourseMessage, id=pk)

    if request.user != message.user:
        return HttpResponse('Brak dostępu')


    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    if request.method == 'POST':
        message.delete()

        lesson_url = request.session.get('lesson_url', '/')
        return redirect(lesson_url)

    user = request.user

    if user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
    elif user.groups.filter(name='Students').exists():
        navbar_template = 'tutoring-zone/nav-student-view.html'

    context = {'obj': message, 'navbar_template': navbar_template}
    return render(request, 'tutoring-zone/delete-lesson-message.html', context)


@login_required(login_url='login')
def editLessonMessage(request, pk):
    message = get_object_or_404(CourseMessage, id=pk)

    if request.user != message.user:
        return redirect('lesson', pk=message.room.pk)

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    if request.method == 'POST':
        form = RoomMessageForm(request.POST, request.FILES, instance=message)
        if form.is_valid():
            form.save()
            lesson_url = request.session.get('lesson_url', '/')
            return redirect(lesson_url)
    else:
        form = RoomMessageForm(instance=message)

    return render(request, 'tutoring-zone/edit-lesson-message.html', {'form': form, 'message': message})


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def lessonFeedback(request, pk):
    lesson = get_object_or_404(Lesson, id=pk)
    user = request.user

    if user != lesson.course.teacher:
        return redirect('access_denied')

    if lesson.feedback_submitted:
        return redirect('schoolweb:teacherPage')

    if request.method == 'POST':
        form = LessonFeedbackForm(request.POST, instance=lesson, post_instance=lesson)
        if form.is_valid():
            lesson_feedback_instance = form.save(commit=False)
            lesson_feedback_instance.lesson = lesson
            lesson_feedback_instance.save()

            lesson.attended_students.set(form.cleaned_data['attended_students'])
            lesson.attended_teachers.set(form.cleaned_data['attended_teachers'])
            lesson.save()

            lesson.feedback_submitted = True
            lesson.save()

            if user.groups.filter(name='Teachers').exists():
                lesson_stats = user.lesson_stats  # Pobierz powiązany obiekt LessonStats

                if lesson.clicked_users.count() > 1:
                    if lesson.course.course_type == 'basic':
                        lesson_stats.lessons += 1
                        lesson_stats.all_lessons += 1
                    elif lesson.course.course_type == 'intermediate':
                        lesson_stats.lessons_intermediate += 1
                        lesson_stats.all_lessons_intermediate += 1
                elif lesson.clicked_users.count() == 1:
                    lesson_stats.break_lessons += 1
                    lesson_stats.all_break_lessons += 1
                elif lesson.clicked_users.count() == 0:
                    lesson_stats.missed_lessons += 1
                    lesson_stats.all_missed_lessons += 1

                lesson_stats.save()  # Zapisz zmiany w LessonStats

            return redirect('schoolweb:teacherPage')

    else:
        form = LessonFeedbackForm(instance=lesson, post_instance=lesson)

    context = {
        'lesson': lesson,
        'form': form,
    }

    return render(request, 'tutoring-zone/lesson-feedback.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def lessonCorrection(request, pk):
    lesson = get_object_or_404(Lesson, id=pk)
    user = request.user

    if user != lesson.course.teacher:
        return redirect('access_denied')

    form = LessonCorrectionForm(course=lesson.course)

    if request.method == 'POST':
        form = LessonCorrectionForm(request.POST, request.FILES, course=lesson.course)
        if form.is_valid():
            lesson_correction_instance = form.save(commit=False)
            lesson_correction_instance.lesson = lesson
            lesson_correction_instance.save()
            form.save_m2m()

            return redirect('schoolweb:teacherPage')

    context = {'form': form, 'lesson': lesson}
    return render(request, 'tutoring-zone/lesson-correction.html', context)


def successPage(request):
    return render(request, 'tutoring-zone/success-page.html')


def check_user_group(username):
    try:
        user = User.objects.get(username=username)
        if user.groups.exists():
            user_groups = user.groups.all()
            return True, user_groups
        else:
            return False, []
    except User.DoesNotExist:
        return False, []


def like_room(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.user.is_authenticated:
        if request.user in room.likes.all():
            room.likes.remove(request.user)
        else:
            room.likes.add(request.user)

    return redirect('room', pk=room.id)


def toggle_like(request, message_id):
    if request.method == 'POST' and request.user.is_authenticated:
        message = Message.objects.get(pk=message_id)
        message.toggle_like(request.user)
        likes_count = message.likes.count()
        return JsonResponse({'likes_count': likes_count})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def toggle_like_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    user = request.user

    if user in room.likes.all():
        room.likes.remove(user)
        liked = False
    else:
        room.likes.add(user)
        liked = True

    return JsonResponse({'liked': liked, 'likes_count': room.likes.count()})


def get_room_likes(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    liked_users = room.likes.all()

    liked_users_data = [
        {'id': user.id, 'username': user.username, 'avatar': user.avatar.url}
        for user in liked_users
    ]

    return JsonResponse({'liked_users': liked_users_data})


def get_likes(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    liked_users = message.likes.all()

    liked_users_data = [
        {'id': user.id, 'username': user.username, 'avatar': user.avatar.url}
        for user in liked_users
    ]

    return JsonResponse({'liked_users': liked_users_data})


def courses_studentsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    courses = Course.objects.filter(name__icontains=q)
    return render(request, 'website/courses-students.html', {'courses': courses})


def is_student(user):
    return user.groups.filter(name='Students').exists()


@user_passes_test(is_student, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def studentPage(request):
    now = datetime.now() - timedelta(minutes=15)
    time_difference = timedelta(minutes=35)
    time_threshold = now - time_difference

    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    student = request.user
    courses = Course.objects.filter(students=student)
    teachers = User.objects.filter(groups__name='Teachers', courses_taught__in=courses)
    other_students = User.objects.filter(groups__name='Students', courses_enrolled__in=courses).exclude(id=student.id)
    all_courses = Course.objects.all()

    upcoming_lessons = Lesson.objects.filter(
        Q(course__in=courses) & Q(event_datetime__gt=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('event_datetime')

    past_lessons = Lesson.objects.filter(
        Q(course__in=courses) & Q(event_datetime__lte=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('-event_datetime')

    lessons = list(upcoming_lessons) + list(past_lessons)

    post_count = len(lessons)
    lesson_messages = CourseMessage.objects.filter(Q(room__in=lessons))

    context = {
        'lessons': lessons,
        'courses': courses,
        'post_count': post_count,
        'lesson_messages': lesson_messages,
        'all_courses': all_courses,
        'now': now,
        'time_threshold': time_threshold,
        'teachers': teachers,
    }
    return render(request, 'tutoring-zone/student-view.html', context)


def access_denied(request):
    return render(request, 'website/lesson-no-exists.html')


@user_passes_test(is_teacher, login_url='schoolweb:login')
@login_required(login_url='schoolweb:login')
def resignation(request):
    if request.method == 'POST':
        form = ResignationForm(request.POST)
        if form.is_valid():
            resignation = form.save(commit=False)
            resignation.user = request.user
            resignation.save()
            return redirect('schoolweb:success-page')
    else:
        form = ResignationForm()

    return render(request, 'tutoring-zone/resignation.html', {'form': form})


@login_required
def manage_availability(request):
    user = request.user

    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            day = form.cleaned_data['day']

            existing_availability = Availability.objects.filter(user=user, day=day).first()

            if existing_availability:
                form = AvailabilityForm(request.POST, instance=existing_availability)
            else:
                form = AvailabilityForm(request.POST)

            availability = form.save(commit=False)
            availability.user = user
            availability.save()

            return redirect('schoolweb:manage_availability')
    else:
        form = AvailabilityForm()

    user_availability = Availability.objects.filter(user=user)

    return render(request, 'tutoring-zone/manage-availability.html',
                  {'form': form, 'user_availability': user_availability})


def get_availability(request, selected_date):
    user = request.user
    selected_availability = Availability.objects.filter(user=user, day=selected_date).first()

    if selected_availability:
        availability_data = {
            'hour_6_7': selected_availability.hour_6_7,
            'hour_7_8': selected_availability.hour_7_8,
            'hour_8_9': selected_availability.hour_8_9,
            'hour_9_10': selected_availability.hour_9_10,
            'hour_10_11': selected_availability.hour_10_11,
            'hour_11_12': selected_availability.hour_11_12,
            'hour_12_13': selected_availability.hour_12_13,
            'hour_13_14': selected_availability.hour_13_14,
            'hour_14_15': selected_availability.hour_14_15,
            'hour_15_16': selected_availability.hour_15_16,
            'hour_16_17': selected_availability.hour_16_17,
            'hour_17_18': selected_availability.hour_17_18,
            'hour_18_19': selected_availability.hour_18_19,
            'hour_19_20': selected_availability.hour_19_20,
            'hour_20_21': selected_availability.hour_20_21,
            'hour_21_22': selected_availability.hour_21_22,
        }
    else:
        availability_data = {}

    return JsonResponse(availability_data)


def Lobby(request):
    return render(request, 'website/lobby1.html')


def converse(request):
    user = request.user
    room_code = request.GET.get('room')

    post = get_object_or_404(Lesson, invite_code=room_code)

    if user not in post.clicked_users.all():
        post.add_click(user)

    context = {
        'user': user,
        'post': post,
    }

    return render(request, 'website/room2.html', context)


@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, **kwargs):
    Room.objects.filter(host=instance).update(host=None)


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BLOG~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def get_blog_context():
    categories = BlogCategory.objects.all()
    years = BlogPost.objects.dates('created_at', 'year').distinct()
    months = BlogPost.objects.dates('created_at', 'month').distinct()
    days = BlogPost.objects.dates('created_at', 'day').distinct()

    return {
        'categories': categories,
        'years': years,
        'months': months,
        'days': days,
    }


def blog_post_list(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    new = request.GET.get('new')
    trending = request.GET.get('trending')

    blog_posts = BlogPost.objects.all()

    if category_id:
        category = get_object_or_404(BlogCategory, id=category_id)
        blog_posts = blog_posts.filter(category=category)

    if query:
        blog_posts = blog_posts.filter(Q(title__icontains=query))

    if year:
        blog_posts = blog_posts.filter(created_at__year=year)

    if month:
        blog_posts = blog_posts.filter(created_at__month=month)

    if day:
        blog_posts = blog_posts.filter(created_at__day=day)

    if new:
        blog_posts = blog_posts.filter(is_new=True)

    if trending:
        blog_posts = blog_posts.filter(is_trending=True)

    blog_posts = blog_posts.order_by('-created_at')

    page = request.GET.get('page', 1)
    paginator = Paginator(blog_posts, 12)
    blog_posts = paginator.get_page(page)

    context = get_blog_context()
    context.update({
        'blog_posts': blog_posts,
    })

    return render(request, 'blog/blog-post-list.html', context)


def blog_post_detail(request, slug, id):
    post = get_object_or_404(BlogPost, slug=slug, id=id)
    post.increment_views()
    content_blocks = post.content_blocks.all()
    similar_posts = post.get_similar_posts().order_by('-created_at')[:4]

    liked_posts = request.COOKIES.get('liked_posts', '')
    liked = str(post.id) in liked_posts.split(',')

    context = get_blog_context()
    context.update({
        'post': post,
        'content_blocks': content_blocks,
        'similar_posts': similar_posts,
        'liked': liked,
    })

    return render(request, 'blog/blog-post-detail.html', context)


def like_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    liked_posts = request.COOKIES.get('liked_posts', '')
    liked_posts_list = liked_posts.split(',')

    if str(pk) in liked_posts_list:
        liked_posts_list.remove(str(pk))
        post.likes -= 1
        liked = False
    else:
        liked_posts_list.append(str(pk))
        post.likes += 1
        liked = True

    post.save()
    response = JsonResponse({'likes': post.likes, 'liked': liked})
    response.set_cookie('liked_posts', ','.join(liked_posts_list))
    return response
