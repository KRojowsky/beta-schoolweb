from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import (User, Room, Topic, Message, Course, Post, CourseMessage, PlatformMessage, Report, BlogPost,
                     BlogCategory)
from .forms import (RoomForm, UserForm, MyUserCreationForm, ApplyTeacherForm, ApplyStudentForm, NewStudentForm,
                    NewTeacherForm, PostFormCreate, PostFormEdit, LessonFeedbackForm, LessonCorrectionForm,
                    ResignationForm, ReportForm, RoomMessageForm)
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from agora_token_builder import RtcTokenBuilder
import random
import time
from datetime import datetime
from django.utils import timezone
import json
from datetime import timedelta
from .forms import AvailabilityForm
from .models import Availability
from django.core.paginator import Paginator

'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~WIDGET~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def home(request):
    user_in_migrates = False

    if request.user.is_authenticated:
        user_in_migrates = request.user.groups.filter(name='Migrates').exists()

    context = {
        'user_in_migrates': user_in_migrates,
    }

    return render(request, 'widget/main-view.html', context)


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

    if request.user.is_authenticated:
        return redirect('schoolweb:knowledge_zone')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        user = User.objects.filter(email=email).first()

        if user is None:
            messages.error(request, 'Użytkownik nie istnieje')
        else:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('schoolweb:knowledge_zone')
            else:
                messages.error(request, 'Błędny Email lub Hasło')

    context = {'page': page}
    return render(request, 'knowledge-zone/login_register.html', context)


@login_required(login_url='schoolweb:login')
def logoutUser(request):
    logout(request)
    return redirect('schoolweb:knowledge_zone')


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

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
        'user_in_migrates': user_in_migrates,  # Przekazanie informacji do szablonu
    }

    return render(request, 'knowledge-zone/knowledge-zone.html', context)


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

            if 'image' in request.FILES:
                room.image.save(request.FILES['image'].name, request.FILES['image'])

            room.save()
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

    if request.method == 'POST':
        message.delete()
        return redirect('schoolweb:knowledge_zone')

    return render(request, 'knowledge-zone/delete.html', {'obj': message})


@login_required(login_url='login')
def editRoomMessage(request, pk):
    message = get_object_or_404(Message, pk=pk)

    if request.user != message.user:
        return redirect('room', pk=message.room.pk)

    if request.method == 'POST':
        form = RoomMessageForm(request.POST, request.FILES, instance=message)
        if form.is_valid():
            form.save()
            return redirect('schoolweb:room', pk=message.room.pk)
    else:
        form = RoomMessageForm(instance=message)

    return render(request, 'knowledge-zone/edit-message.html', {'form': form, 'message': message})


def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
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


def lessonsHome(request):
    user = request.user

    if user.groups.filter(name='Teachers').exists():
        return redirect('schoolweb:teacherPage')

    if user.groups.filter(name='Students').exists():
        return redirect('schoolweb:studentPage')

    if user.groups.filter(name='NewStudents').exists():
        return redirect('schoolweb:coursesLoader')

    if user.groups.filter(name='NewTeachers').exists():
        return redirect('schoolweb:coursesLoader')

    return render(request, 'tutoring-zone/lessons-home.html')


def newStudent(request):
    if request.method == 'POST':
        form = NewStudentForm(request.POST)
        if form.is_valid():
            form.save()

            if request.user.is_authenticated:
                change_user_group(request.user, 'NewStudents')
                return redirect(reverse('schoolweb:coursesLoader'))
            else:
                return redirect(reverse('schoolweb:applyStudent'))
    else:
        form = NewStudentForm()

    context = {'form': form}
    return render(request, 'tutoring-zone/new-student.html', context)


def applyStudent(request):
    if request.method == 'POST':
        form = ApplyStudentForm(request.POST)
        if form.is_valid():
            user = form.save()

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)

                group = Group.objects.get(name='NewStudents')
                user.groups.add(group)

                return redirect('schoolweb:lessonsLogin')
    else:
        form = ApplyStudentForm()

    return render(request, 'tutoring-zone/apply-students.html', {'form': form})


def newTeacher(request):
    if request.method == 'POST':
        form = NewTeacherForm(request.POST)
        if form.is_valid():
            form.save()

            if request.user.is_authenticated:
                change_user_group(request.user, 'NewStudents')
                return redirect(reverse('schoolweb:coursesLoader'))
            else:
                return redirect(reverse('schoolweb:applyTeacher'))
    else:
        form = NewTeacherForm()

    context = {'form': form}
    return render(request, 'tutoring-zone/new-teacher.html', context)


def applyTeacher(request):
    if request.method == 'POST':
        form = ApplyTeacherForm(request.POST)
        if form.is_valid():
            user = form.save()

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)

                group = Group.objects.get(name='NewTeachers')
                user.groups.add(group)

                return redirect('schoolweb:lessonsLogin')
    else:
        form = ApplyTeacherForm()

    return render(request, 'tutoring-zone/apply-teacher.html', {'form': form})


def coursesLoader(request):
    return render(request, 'tutoring-zone/user-creator.html')


def noLessons(request):
    return render(request, 'tutoring-zone/no-lessons.html')


def lessonsLogin(request):
    page = 'lessonsLogin'

    if request.user.groups.filter(name__in=['NewStudents', 'NewTeachers']).exists():
        return redirect('schoolweb:coursesLoader')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Użytkownik nie istnieje')
            return redirect('schoolweb:lessonsLogin')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            user_groups = set(user.groups.values_list('name', flat=True))

            if 'Teachers' in user_groups:
                login(request, user)
                return redirect('schoolweb:teacherPage')
            elif 'Students' in user_groups:
                login(request, user)
                return redirect('schoolweb:studentPage')
            elif 'Writers' in user_groups:
                change_user_group(user, 'Migrates')
                login(request, user)
                return redirect('schoolweb:coursesLoader')
            elif user_groups & {'NONE', 'Migrates', 'NewStudents', 'NewTeachers'}:
                login(request, user)
                return redirect('schoolweb:coursesLoader')
        else:
            messages.error(request, 'Błędny Email lub Hasło')

    context = {'page': page}
    return render(request, 'tutoring-zone/login_register_lessons.html', context)


def change_user_group(user, new_group_name):
    try:
        new_group = Group.objects.get(name=new_group_name)
        user.groups.set([new_group])
        user.save()
        return True
    except Group.DoesNotExist:
        return False


def lessonsRegister(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            user.groups.add(Group.objects.get(name='NONE'))
            return redirect('lessonsLogin')
        else:
            messages.error(request, 'Wystąpił błąd podczas próby rejestracji.')

    context = {'form': form}
    return render(request, 'website/login_register_lessons.html', context)


def lessonsLogout(request):
    logout(request)
    return redirect('schoolweb:knowledge_zone')


def is_teacher(user):
    return user.groups.filter(name='Teachers').exists()


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def teacherPage(request):
    now = datetime.now() - timedelta(minutes=15)
    time_difference = timedelta(minutes=35)
    time_threshold = now - time_difference
    a = 0

    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    teacher = request.user
    courses = Course.objects.filter(teacher=teacher)
    all_courses = Course.objects.all()

    upcoming_lessons = Post.objects.filter(
        Q(course__in=courses) & Q(event_datetime__gt=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('event_datetime')

    past_lessons = Post.objects.filter(
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


@login_required(login_url='lessonsLogin')
def lessonProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    lessons = user.post_set.all()
    lesson_messages = user.coursemessage_set.all()
    package = user.lessons
    all_package = user.all_lessons
    month_earnings = 60 * user.lessons_intermediate + 40 * user.lessons + 20 * user.break_lessons - 50 * user.missed_lessons
    all_earnings = 60 * user.all_lessons_intermediate + 40 * user.all_lessons + 20 * user.all_break_lessons - 50 * user.all_missed_lessons

    logged_in_user = request.user

    is_teacher = logged_in_user.groups.filter(name='Teachers').exists()

    if logged_in_user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        courses_component = 'tutoring-zone/courses-component-teachers.html'
        courses = Course.objects.filter(teacher=logged_in_user)
        accessible_users = User.objects.filter(groups__name='Students', courses_enrolled__in=courses)
    elif logged_in_user.groups.filter(name='Students').exists():
        navbar_template = 'tutoring-zone/nav-student-view.html'
        courses_component = 'tutoring-zone/courses-component-students.html'
        courses = Course.objects.filter(students=logged_in_user)
        accessible_users = (
            User.objects
            .filter(
                Q(groups__name='Students', courses_enrolled__in=courses) |
                Q(groups__name='Teachers', courses_taught__in=courses)
            )
            .distinct()
        )

    is_accessible_profile = (
            logged_in_user == user or
            (is_teacher and user in accessible_users) or
            (logged_in_user.groups.filter(name='Students').exists() and user in accessible_users)
    )

    if not is_accessible_profile:
        return render(request, 'tutoring-zone/lesson-no-exists.html')

    context = {
        'user': user,
        'lessons': lessons,
        'lesson_messages': lesson_messages,
        'package': package,
        'all_package': all_package,
        'courses': courses,
        'navbar_template': navbar_template,
        'courses_component': courses_component,
        'month_earnings': month_earnings,
        'all_earnings': all_earnings,
        'is_teacher': is_teacher,
    }

    return render(request, 'tutoring-zone/lesson-profile.html', context)


@login_required(login_url='lessonsLogin')
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


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def createLesson(request):
    initial_data = {'host': request.user}
    form = PostFormCreate(user=request.user, initial=initial_data)  # Przekazujemy użytkownika do formularza
    current_date = timezone.now().strftime('%Y-%m-%dT%H:%M')

    if request.method == 'POST':
        form = PostFormCreate(request.POST, user=request.user, initial=initial_data)
        minimum_datetime = timezone.now() + timedelta(minutes=15)

        if form.is_valid():
            post = form.save(commit=False)
            post.host = request.user

            overlapping_lessons = Post.objects.filter(
                course__teacher=request.user,
                event_datetime__gte=post.event_datetime - timedelta(minutes=50),
                event_datetime__lte=post.event_datetime + timedelta(minutes=50)
            )

            students_in_course = post.course.students.all()
            student_has_lessons = True

            for student in students_in_course:
                if post.course.course_type == 'basic':
                    if student.lessons <= 0:
                        student_has_lessons = False
                        break
                elif post.course.course_type == 'intermediate':
                    if student.lessons_intermediate <= 0:
                        student_has_lessons = False
                        break

            if not student_has_lessons:
                messages.error(request, "Jeden lub więcej studentów nie ma dostępnych lekcji w tym kursie.")
            elif overlapping_lessons.exists():
                messages.error(request, "W wybranym terminie istnieje już inna lekcja.")
            elif post.event_datetime <= minimum_datetime:
                messages.error(request, "Wybierz datę i godzinę co najmniej 15 minut od teraźniejszego czasu.")
            else:
                post.save()

                for student in students_in_course:
                    if post.course.course_type == 'basic':
                        student.lessons -= 1
                    elif post.course.course_type == 'intermediate':
                        student.lessons_intermediate -= 1
                    student.save()

                return redirect('schoolweb:teacherPage')

    return render(request, 'tutoring-zone/create-lesson.html', {'form': form, 'current_date': current_date})


def courses_teachersPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    courses = Course.objects.filter(name__icontains=q)
    return render(request, 'tutoring-zone/courses-teachers.html', {'courses': courses})


def activity_lessonPage(request):
    lesson_messages = CourseMessage.objects.all()[0:12]
    return render(request, 'tutoring-zone/activity-lesson.html', {'lesson_messages': lesson_messages})


@login_required(login_url='lessonsLogin')
def lesson(request, pk):
    lesson = get_object_or_404(Post, id=pk)
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


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def updateLesson(request, pk):
    post = get_object_or_404(Post, id=pk)

    if request.user != post.host:
        return HttpResponse('Brak dostępu')

    time_difference = post.event_datetime - timezone.now()
    can_edit = time_difference.total_seconds() > 900

    if request.method == 'POST':
        form = PostFormEdit(request.POST, instance=post)
        if form.is_valid() and can_edit:
            overlapping_lessons = Post.objects.filter(
                course__teacher=request.user,
                event_datetime__gte=form.cleaned_data['event_datetime'] - timedelta(minutes=50),
                event_datetime__lte=form.cleaned_data['event_datetime'] + timedelta(minutes=50)
            ).exclude(id=pk)

            if overlapping_lessons.exists():
                form.add_error('event_datetime', "W wybranym terminie już istnieje inna lekcja.")
            else:
                form.save()
                return redirect('schoolweb:teacherPage')
    else:
        form = PostFormEdit(instance=post)

    context = {'form': form, 'can_edit': can_edit}
    return render(request, 'tutoring-zone/update-lesson.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def deleteLesson(request, pk):
    post = Post.objects.get(id=pk)

    if request.method == 'POST':
        post.delete()
        return redirect('schoolweb:teacherPage')

    user = request.user

    if user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        back_link = reverse('schoolweb:teacherPage')

    elif user.groups.filter(name='Students').exists():
        navbar_template = 'tutoring-zone/nav-student-view.html'
        back_link = reverse('schoolweb:studentPage')

    context = {'obj': post, 'navbar_template': navbar_template, 'back_link': back_link}
    return render(request, 'tutoring-zone/delete-lessons.html', context)


@login_required(login_url='lessonsLogin')
def deleteLessonMessage(request, pk):
    message = CourseMessage.objects.get(id=pk)
    if request.user != message.user:
        return HttpResponse('Brak dostępu')
    if request.method == 'POST':
        message.delete()
        return redirect('schoolweb:teacherPage')

    user = request.user

    if user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'

    elif user.groups.filter(name='Students').exists():
        navbar_template = 'tutoring-zone/nav-student-view.html'

    context = {'obj': message, 'navbar_template': navbar_template}
    return render(request, 'tutoring-zone/delete-lessons.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def lessonFeedback(request, pk):
    lesson = get_object_or_404(Post, id=pk)
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
                if lesson.clicked_users.count() > 1:
                    if lesson.course.course_type == 'basic':
                        user.lessons += 1
                        user.all_lessons += 1
                    elif lesson.course.course_type == 'intermediate':
                        user.lessons_intermediate += 1
                        user.all_lessons_intermediate += 1
                    user.save()
                elif lesson.clicked_users.count() == 1:
                    user.break_lessons += 1
                    user.all_break_lessons += 1
                    user.save()
                elif lesson.clicked_users.count() == 0:
                    user.missed_lessons += 1
                    user.all_missed_lessons += 1
                    user.save()

            return redirect('schoolweb:teacherPage')

    else:
        form = LessonFeedbackForm(instance=lesson, post_instance=lesson)

    context = {
        'lesson': lesson,
        'form': form,
    }

    return render(request, 'tutoring-zone/lesson-feedback.html', context)


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
def lessonCorrection(request, pk):
    lesson = get_object_or_404(Post, id=pk)
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


@user_passes_test(is_student, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
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

    upcoming_lessons = Post.objects.filter(
        Q(course__in=courses) & Q(event_datetime__gt=now) & (Q(course__name=q) | Q(title__icontains=q))
    ).order_by('event_datetime')

    past_lessons = Post.objects.filter(
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


@user_passes_test(is_teacher, login_url='schoolweb:lessonsLogin')
@login_required(login_url='schoolweb:lessonsLogin')
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

    post = get_object_or_404(Post, invite_code=room_code)

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
