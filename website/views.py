from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Sum
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from .models import (User, Room, Topic, Message, Course, Lesson, LessonStats, CourseMessage, PlatformMessage, BlogPost,
                     BlogCategory, LessonStats, TeachersEarning, NewStudents)
from .forms import (RoomForm, UserForm, MyUserCreationForm, LessonFormCreate, LessonFormEdit, LessonFeedbackForm,
                    LessonCorrectionForm, ResignationForm, ReportForm, RoomMessageForm,
                    ApplyUserForm, WriterDataForm, NewStudentForm)
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.urls import reverse, NoReverseMatch
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
from django.core.exceptions import PermissionDenied
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.messages import get_messages
from django.contrib.auth import get_user
import html
from django.views.decorators.http import require_POST
from django.conf import settings
import requests
from django.http import HttpResponseForbidden



'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''

def get_target_url(user):
    if user.is_authenticated:
        group_obj = user.groups.first()
        if group_obj:
            group = group_obj.name
            return {
                'Teachers': 'schoolweb:teacherPage',
                'Students': 'schoolweb:studentPage',
                'NewStudents': 'schoolweb:coursesLoader',
                'NewTeachers': 'schoolweb:coursesLoader',
                'Writers': 'schoolweb:WriterToTutoringZone'
            }.get(group, 'schoolweb:applyUser')
    return 'schoolweb:applyUser'


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~WIDGET~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def home(request):
    target_url = get_target_url(request.user)
    return render(request, 'widget/main-view.html', {'target_url': target_url})


def become_tutor(request):
    target_url = get_target_url(request.user)
    return render(request, 'widget/become-tutor.html', {'target_url': target_url})


def faq(request):
    target_url = get_target_url(request.user)
    return render(request, 'widget/faq.html', {'target_url': target_url})


def contact(request):
    target_url = get_target_url(request.user)
    return render(request, 'widget/contact.html', {'target_url': target_url})


def subjects(request):
    target_url = get_target_url(request.user)
    return render(request, 'widget/subjects.html', {'target_url': target_url})


def verify_recaptcha(token):
    secret_key = settings.RECAPTCHA_SECRET_KEY
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': secret_key,
            'response': token
        }
    )
    result = response.json()
    return result.get('success', False)


@require_POST
def user_message(request):
    email = request.POST.get('email', '').strip()
    phone_number = request.POST.get('phone_number', '').strip()
    message = request.POST.get('message', '').strip()
    recaptcha_token = request.POST.get('g-recaptcha-response')

    if not email or not message:
        return JsonResponse({'status': 'error', 'message': 'Email i wiadomość są wymagane.'}, status=400)

    if '@' not in email:
        return JsonResponse({'status': 'error', 'message': 'Nieprawidłowy adres email.'}, status=400)

    if not recaptcha_token or not verify_recaptcha(recaptcha_token):
        return JsonResponse({'status': 'error', 'message': 'Weryfikacja reCAPTCHA nie powiodła się.'}, status=400)

    email = html.escape(email)
    phone_number = html.escape(phone_number)
    message = html.escape(message)

    try:
        PlatformMessage.objects.create(
            email=email,
            phone_number=phone_number,
            message=message
        )
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Wystąpił problem podczas wysyłania wiadomości.'
        }, status=500)

    return JsonResponse({'status': 'success', 'message': 'Wiadomość została wysłana!'})


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


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~KNOWLEDGE-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''


def loginPage(request):
    messages.get_messages(request)

    if request.method == 'POST':
        recaptcha_token = request.POST.get('g-recaptcha-response')
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            messages.error(request, 'Weryfikacja reCAPTCHA nie powiodła się. Spróbuj ponownie.')
            return render(request, 'knowledge-zone/login_register.html', {'page': 'login'})

        email = request.POST.get('email', '').lower()
        password = request.POST.get('password', '')

        try:
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('schoolweb:knowledge_zone')
        except NoReverseMatch:
            next_url = reverse('home')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, 'Błędny Email lub Hasło')

    return render(request, 'knowledge-zone/login_register.html', {'page': 'login'})


@login_required(login_url='schoolweb:login')
def logoutUser(request):
    logout(request)
    next_url = request.GET.get('next', 'schoolweb:knowledge_zone')
    return redirect(next_url)


def session_timeout(request):
    logout(request)
    messages.error(request, "Zostałeś automatycznie wylogowany z powodu braku aktywności.")
    return redirect('schoolweb:login')


def registerPage(request):
    messages.get_messages(request)

    if request.method == 'POST':
        recaptcha_token = request.POST.get('g-recaptcha-response')
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            messages.error(request, 'Weryfikacja reCAPTCHA nie powiodła się. Spróbuj ponownie.')
            return redirect('schoolweb:register')

        if not request.POST.get('accept_terms'):
            messages.error(request, 'Musisz zaakceptować regulamin i politykę prywatności.')
            return redirect('schoolweb:register')

        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()

            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Użytkownik o podanej nazwie już istnieje.')
            else:
                try:
                    with transaction.atomic():
                        user = form.save(commit=False)
                        user.username = username
                        user.save()

                        writers_group = Group.objects.get(name='Writers')
                        user.groups.add(writers_group)

                    login(request, user)
                    messages.success(request, 'Rejestracja zakończona pomyślnie!')
                    return redirect('schoolweb:knowledge_zone')

                except Exception as e:
                    form.add_error(None, f'Wystąpił błąd podczas rejestracji: {str(e)}')

    else:
        form = MyUserCreationForm()

    return render(request, 'knowledge-zone/login_register.html', {'form': form, 'page': 'register'})


def knowledge_zone(request):
    q = request.GET.get('q', '').strip()
    level_filter = request.GET.get('level', '').strip()

    rooms = Room.objects.all()

    if q:
        rooms = rooms.filter(
            Q(topic__name__icontains=q) |
            Q(name__icontains=q) |
            Q(description__icontains=q)
        )

    if level_filter:
        rooms = rooms.filter(level=level_filter)

    topics = Topic.objects.all()[:30]
    room_count = rooms.count()
    room_messages = Message.objects.order_by('-created')[:12]

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

    print(user_redirect_url)

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
        'user_redirect_url': user_redirect_url,
        'current_q': q,
        'current_level': level_filter,
    }

    return render(request, 'knowledge-zone/knowledge-zone.html', context)


def room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room_messages = room.message_set.select_related('user').all().order_by('created')
    participants = room.participants.all()

    similar_rooms = Room.objects.filter(
        topic=room.topic,
        level=room.level
    ).exclude(id=room.id)[:4]

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')

        if body or image or file:
            Message.objects.create(
                user=request.user,
                room=room,
                body=body,
                image=image,
                file=file
            )
            room.participants.add(request.user)
            messages.success(request, 'Komentarz został dodany pomyślnie!')
            return redirect('schoolweb:room', pk=room.id)

    if request.user.groups.filter(name='Teachers').exists():
        user_redirect_url = reverse('schoolweb:teacherPage')
    elif request.user.groups.filter(name='Students').exists():
        user_redirect_url = reverse('schoolweb:studentPage')
    else:
        user_redirect_url = reverse('schoolweb:applyUser')

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
        'user_redirect_url': user_redirect_url,
        'similar_rooms': similar_rooms,
    }
    return render(request, 'knowledge-zone/room.html', context)


@login_required(login_url='schoolweb:login')
@transaction.atomic
def createRoom(request):
    form = RoomForm(request.POST or None, request.FILES or None)
    topics = Topic.objects.all()

    if request.method == 'POST' and form.is_valid():
        room = form.save(commit=False)
        room.host = request.user

        if request.POST.get('image_clear') == 'on':
            room.image = None

        room.save()

        messages.success(request, 'Post został pomyślnie utworzony!')
        return redirect('schoolweb:knowledge_zone')

    context = {'form': form, 'topics': topics}
    return render(request, 'knowledge-zone/room_form.html', context)


@login_required(login_url='schoolweb:login')
@transaction.atomic
def updateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        messages.error(request, 'Nie masz uprawnień do edycji tego postu.')
        return redirect('schoolweb:knowledge_zone')

    current_likes = room.likes.all()

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            updated_room = form.save(commit=False)

            if request.POST.get('image_clear') == 'on':
                if updated_room.image:
                    updated_room.image.delete(save=False)
                updated_room.image = None

            updated_room.likes.set(current_likes)
            updated_room.save()
            messages.success(request, 'Post został pomyślnie zaktualizowany!')
            return redirect('schoolweb:room', pk=room.id)
        else:
            messages.error(request, 'Wystąpił błąd podczas aktualizacji postu.')
    else:
        form = RoomForm(instance=room)

    topics = Topic.objects.all()
    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'knowledge-zone/room_form.html', context)


@login_required(login_url='schoolweb:login')
def reportRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if room.host == request.user:
        messages.error(request, 'Nie możesz zgłosić własnego posta.')
        return redirect('schoolweb:knowledge_zone')

    if room.reports.filter(reporter=request.user).exists():
        messages.warning(request, 'Ten post został już przez Ciebie zgłoszony.')
        return redirect('schoolweb:knowledge_zone')

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.room = room
            report.reporter = request.user
            report.save()
            messages.success(request, 'Dziękujemy za zgłoszenie! Zajmiemy się sprawą wkrótce.')
            return redirect('schoolweb:knowledge_zone')
        else:
            messages.error(request, 'Wystąpił błąd podczas wysyłania zgłoszenia. Spróbuj ponownie.')
    else:
        form = ReportForm()

    return render(request, 'knowledge-zone/report-room.html', {'form': form, 'room': room})


@login_required(login_url='schoolweb:login')
def deleteRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        messages.error(request, 'Nie masz uprawnień do usunięcia tego postu.')
        return redirect('schoolweb:knowledge_zone')

    if request.method == 'GET':
        previous_url = request.META.get('HTTP_REFERER', '/')
        request.session['lesson_url'] = previous_url

    if request.method == 'POST':
        try:
            room.delete()
            messages.success(request, 'Post został pomyślnie usunięty.')
        except Exception as e:
            messages.error(request, f'Wystąpił błąd podczas usuwania postu: {str(e)}')

        return redirect(reverse('schoolweb:knowledge_zone'))

    return render(request, 'knowledge-zone/delete.html', {
        'obj': room,
        'lesson_url': request.session.get('lesson_url', reverse('schoolweb:knowledge_zone'))
    })


@login_required(login_url='schoolweb:login')
def deleteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user:
        raise PermissionDenied('Operacja wzbroniona.')

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER', '/')
        request.session['lesson_url'] = lesson_url
    else:
        lesson_url = request.session.get('lesson_url', '/')

    if request.method == 'POST':
        try:
            message.delete()
            messages.success(request, 'Komentarz został poprawnie usunięty.')
        except Exception as e:
            messages.error(request, f'Wystąpił błąd podczas usuwania wiadomości: {str(e)}')
        return redirect(lesson_url)

    return render(request, 'knowledge-zone/delete.html', {
        'obj': message,
        'lesson_url': lesson_url,
    })


@login_required(login_url='schoolweb:login')
def editRoomMessage(request, pk):
    message = get_object_or_404(Message, pk=pk)

    if request.user != message.user:
        messages.error(request, 'Nie możesz edytować tej wiadomości.')
        return redirect('schoolweb:room', pk=message.room.pk)

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        if lesson_url:
            request.session['lesson_url'] = lesson_url

    form = RoomMessageForm(request.POST or None, request.FILES or None, instance=message)

    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)

        if request.POST.get('image_clear') == 'on':
            message.image.delete(save=False)
            message.image = None

        if request.POST.get('file_clear') == 'on':
            message.file.delete(save=False)
            message.file = None

        is_empty = (
            not message.body.strip() and
            not message.image and
            not message.file
        )

        if is_empty:
            message.delete()
            messages.info(request, 'Komentarz został usunięty, ponieważ był pusty.')
        else:
            message.save()
            messages.success(request, 'Komentarz został zaktualizowany.')

        next_url = request.POST.get('next') or request.session.get('lesson_url', '/')
        return redirect(next_url)

    lesson_url = request.session.get('lesson_url', '/')

    return render(request, 'knowledge-zone/edit-message.html', {
        'form': form,
        'message': message,
        'lesson_url': lesson_url,
    })


@login_required(login_url='schoolweb:login')
def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    logged_in_user = request.user

    rooms = user.hosted_rooms.all()
    room_messages = user.messages.all()
    topics = Topic.objects.all()
    user_posts = user.hosted_rooms.all()
    lessons = user.lesson_set.all()
    lesson_messages = user.coursemessage_set.all()

    lesson_stats, _ = LessonStats.objects.get_or_create(user=user)

    month_earnings = (
        lesson_stats.intermediate_lesson_rate * lesson_stats.lessons_intermediate +
        lesson_stats.basic_lesson_rate * lesson_stats.lessons +
        20 * lesson_stats.break_lessons -
        50 * lesson_stats.missed_lessons +
        lesson_stats.month_bonus +
        lesson_stats.month_referral_bonus
    )
    all_earnings = (
        lesson_stats.intermediate_lesson_rate * lesson_stats.all_lessons_intermediate +
        lesson_stats.basic_lesson_rate * lesson_stats.all_lessons +
        20 * lesson_stats.all_break_lessons -
        50 * lesson_stats.all_missed_lessons +
        lesson_stats.all_bonus +
        lesson_stats.all_referral_bonus
    )

    is_teacher = logged_in_user.groups.filter(name='Teachers').exists()
    is_student = logged_in_user.groups.filter(name='Students').exists()

    if is_teacher:
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        courses_component = 'tutoring-zone/courses-component-teachers.html'
        user_redirect_url = reverse('schoolweb:teacherPage')
    elif is_student:
        navbar_template = 'tutoring-zone/nav-student-view.html'
        courses_component = 'tutoring-zone/courses-component-students.html'
        user_redirect_url = reverse('schoolweb:studentPage')
    else:
        navbar_template = 'knowledge-zone/nav-no-search.html'
        courses_component = ''
        user_redirect_url = reverse('schoolweb:WriterToTutoringZone')

    if logged_in_user == user:
        profile_user_courses = Course.objects.filter(teacher=user) | Course.objects.filter(students=user)
        is_course_teacher_of_user = False
    elif is_teacher:
        profile_user_courses = Course.objects.filter(teacher=logged_in_user, students=user)
        is_course_teacher_of_user = profile_user_courses.exists()
    else:
        profile_user_courses = Course.objects.none()
        is_course_teacher_of_user = False

    teacher_data = {
        "month_earnings": month_earnings,
        "all_earnings": all_earnings,
        "month_bonus": lesson_stats.month_bonus,
        "all_bonus": lesson_stats.all_bonus,
        "month_referral_bonus": lesson_stats.month_referral_bonus,
        "all_referral_bonus": lesson_stats.all_referral_bonus,
        "lessons": lesson_stats.lessons,
        "lessons_intermediate": lesson_stats.lessons_intermediate,
        "break_lessons": lesson_stats.break_lessons,
        "missed_lessons": lesson_stats.missed_lessons,
        "all_lessons": lesson_stats.all_lessons,
        "all_lessons_intermediate": lesson_stats.all_lessons_intermediate,
        "all_break_lessons": lesson_stats.all_break_lessons,
        "all_missed_lessons": lesson_stats.all_missed_lessons,
    }

    context = {
        'user': user,
        'logged_in_user': logged_in_user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
        'lessons': lessons,
        'lesson_messages': lesson_messages,
        'user_posts': user_posts,
        'package': lesson_stats.lessons,
        'all_package': lesson_stats.all_lessons,
        'courses': profile_user_courses,
        'navbar_template': navbar_template,
        'courses_component': courses_component,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'month_earnings': month_earnings,
        'all_earnings': all_earnings,
        'teacher_data': teacher_data,
        'is_course_teacher_of_user': is_course_teacher_of_user,
        'user_redirect_url': user_redirect_url,
    }

    return render(request, 'knowledge-zone/profile.html', context)


@login_required(login_url='schoolweb:login')
def updateUser(request):
    user = request.user

    if request.method == 'POST':
        if request.POST.get('avatar_clear') == 'on':
            if user.avatar:
                try:
                    user.avatar.delete(save=False)
                except Exception:
                    pass
            user.avatar = None
            user.save()
            messages.success(request, "Zdjęcie profilowe zostało usunięte.")
            return redirect('schoolweb:user-profile', pk=user.id)

        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, "Twój profil został zaktualizowany.")
            return redirect('schoolweb:user-profile', pk=user.id)

        error_messages = [error for field, errors in form.errors.items() for error in errors]
        for error in error_messages:
            messages.error(request, error)

    else:
        form = UserForm(instance=user)

    return render(request, 'knowledge-zone/update-user.html', {'form': form, 'user': user})


def activityPage(request):
    room_messages = Message.objects.select_related('user', 'room')[:12]
    return render(request, 'knowledge-zone/activity.html', {'room_messages': room_messages})


def topicsPage(request):
    q = request.GET.get('q', '')
    topics = Topic.objects.filter(Q(name__icontains=q))

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

    return render(request, 'knowledge-zone/topics.html', {
        'topics': topics,
        'user_redirect_url': user_redirect_url
    })


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

    liked_users_data = []
    for user in liked_users:
        if user.avatar and hasattr(user.avatar, 'url'):
            avatar_url = user.avatar.url
        else:
            avatar_url = '/static/img/profile-pictures/avatar.svg'

        liked_users_data.append({
            'id': user.id,
            'username': user.username,
            'avatar': avatar_url,
        })

    return JsonResponse({'liked_users': liked_users_data})



def get_likes(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    liked_users = message.likes.all()

    liked_users_data = []
    for user in liked_users:
        if user.avatar and hasattr(user.avatar, 'url'):
            avatar_url = user.avatar.url
        else:
            avatar_url = '/static/img/profile-pictures/avatar.svg'

        liked_users_data.append({
            'id': user.id,
            'username': user.username,
            'avatar': avatar_url,
        })

    return JsonResponse({'liked_users': liked_users_data})


'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~TUTORING-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''

@login_required(login_url='schoolweb:login')
def WriterToTutoringZone(request):
    if not request.user.groups.filter(name='Writers').exists():
        return redirect('schoolweb:knowledge_zone')

    if request.method == 'POST':
        form = WriterDataForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            notes = form.cleaned_data.get('notes')
            user_type = form.cleaned_data['user_type']
            referral_code_input = form.cleaned_data.get('referral_code_input')

            if referral_code_input:
                referred_user = User.objects.filter(referral_code=referral_code_input).first()

                if referred_user:
                    if user_type in ['student', 'teacher']:
                        if referred_user.groups.filter(name="Teachers").exists():
                            user.referred_by = referral_code_input
                            lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)
                            lesson_stats.month_referral_bonus += 50
                            lesson_stats.all_referral_bonus += 50
                            lesson_stats.save()

                        elif referred_user.groups.filter(name="Students").exists():
                            user.referred_by = referral_code_input
                            lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)

                            if referred_user.level == "Podstawa":
                                lesson_stats.lessons += 1
                            elif referred_user.level == "Rozszerzenie":
                                lesson_stats.lessons_intermediate += 1
                            lesson_stats.save()
                    else:
                        form.add_error(
                            'referral_code_input',
                            'Kod polecenia jest nieprawidłowy lub należy do użytkownika spoza wymaganej grupy.'
                        )
                        return render(request, 'tutoring-zone/writer-to-tutoring-zone.html', {'form': form})
                else:
                    form.add_error('referral_code_input', 'Kod polecenia nie istnieje.')
                    return render(request, 'tutoring-zone/writer-to-tutoring-zone.html', {'form': form})

            new_group = None

            if user_type == 'student':
                NewStudents.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'subject': user.subject,
                        'level': user.level,
                        'notes': notes,
                        'is_selected': False,
                        'is_new': True,
                        'user': user
                    }
                )

            if user_type == 'teacher':
                new_group = Group.objects.get(name='NewTeachers')
            elif user_type == 'student':
                new_group = Group.objects.get(name='NewStudents')

            if new_group and not request.user.groups.filter(id=new_group.id).exists():
                request.user.groups.clear()
                request.user.groups.add(new_group)

            user.save()

            return redirect('schoolweb:coursesLoader')
    else:
        form = WriterDataForm(instance=request.user)

    return render(request, 'tutoring-zone/writer-to-tutoring-zone.html', {'form': form})


def applyUser(request):
    if request.method == 'POST':
        recaptcha_token = request.POST.get('g-recaptcha-response')
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            form = ApplyUserForm(request.POST)
            form.add_error(None, 'Weryfikacja reCAPTCHA nie powiodła się. Spróbuj ponownie.')
            return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})

        form = ApplyUserForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.phone_number = form.cleaned_data.get('phone_number')
            user.subject = form.cleaned_data.get('subject')
            user.level = form.cleaned_data.get('level')

            notes = form.cleaned_data.get('notes')
            referral_code_input = form.cleaned_data.get('referral_code_input')
            role = form.cleaned_data.get('role')

            if referral_code_input:
                referred_user = User.objects.filter(referral_code=referral_code_input).first()

                if referred_user:
                    if referred_user.email == user.email:
                        form.add_error('referral_code_input', 'Nie możesz użyć własnego kodu polecenia.')
                        return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})

                if referred_user:
                    if role in ['student', 'teacher']:
                        if referred_user.groups.filter(name="Teachers").exists():
                            user.referred_by = referral_code_input
                            lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)
                            lesson_stats.month_referral_bonus += 50
                            lesson_stats.all_referral_bonus += 50
                            lesson_stats.save()

                        elif referred_user.groups.filter(name="Students").exists():
                            user.referred_by = referral_code_input
                            lesson_stats, created = LessonStats.objects.get_or_create(user=referred_user)

                            if referred_user.level == "Podstawa":
                                lesson_stats.lessons += 1
                            elif referred_user.level == "Rozszerzenie":
                                lesson_stats.lessons_intermediate += 1
                            lesson_stats.save()
                    else:
                        form.add_error(
                            'referral_code_input',
                            'Kod polecenia jest nieprawidłowy lub należy do użytkownika spoza wymaganej grupy.'
                        )
                        return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})
                else:
                    form.add_error('referral_code_input', 'Kod polecenia nie istnieje.')
                    return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})

            user.save()

            if role == 'student':
                NewStudents.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'subject': user.subject,
                        'level': user.level,
                        'notes': notes,
                        'is_selected': False,
                        'is_new': True,
                        'user': user
                    }
                )

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)

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
            form.add_error(None, 'Formularz jest niepoprawny.')

    else:
        form = ApplyUserForm()

    return render(request, 'tutoring-zone/application-tutoring-zone.html', {'form': form})


@login_required(login_url='schoolweb:knowledge_zone')
def coursesLoader(request):
    user_groups = set(request.user.groups.values_list('name', flat=True))

    if 'Teachers' in user_groups:
        return redirect('schoolweb:teacherPage')
    elif 'Students' in user_groups:
        return redirect('schoolweb:studentPage')
    elif 'NewStudents' in user_groups or 'NewTeachers' in user_groups:
        return render(request, 'tutoring-zone/user-creator.html')

    return redirect('schoolweb:knowledge_zone')

'''~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~ '''

@login_required(login_url='schoolweb:login')
def newStudent(request):
    if not request.user.groups.filter(name='Teachers').exists():
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if not student_id:
            return redirect('schoolweb:new_students')

        student = get_object_or_404(NewStudents, id=student_id)

        if student.is_selected:
            messages.error(request, "Ten uczeń został już wybrany przez innego nauczyciela.")
            return redirect('schoolweb:new_students')

        with transaction.atomic():
            student.is_selected = True
            student.save()

            teacher = request.user
            course_type = 'basic' if student.level == 'Podstawa' else 'intermediate'

            new_course = Course.objects.create(
                name=f"{student.first_name} {student.last_name}",
                subject=student.subject,
                teacher=teacher,
                course_type=course_type,
            )

            if student.user:
                new_course.students.add(student.user)

        return redirect('schoolweb:new_students')

    students = NewStudents.objects.filter(is_selected=False)
    context = {'students': students}
    return render(request, 'tutoring-zone/students-list.html', context)


def is_teacher(user):
    return user.groups.filter(name='Teachers').exists()


@login_required(login_url='schoolweb:login')
def teacherPage(request):
    if not is_teacher(request.user):
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

    now = datetime.now()
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    teacher = request.user

    courses = Course.objects.filter(teacher=teacher)
    all_courses = Course.objects.all()

    upcoming_lessons = Lesson.objects.filter(
        Q(event_datetime__gt=now) &
        (Q(course__name=q) | Q(title__icontains=q)) &
        Q(host=teacher)
    ).order_by('event_datetime')

    past_lessons = Lesson.objects.filter(
        Q(event_datetime__lte=now) &
        (Q(course__name=q) | Q(title__icontains=q)) &
        Q(host=teacher)
    ).order_by('-event_datetime')

    lessons = list(upcoming_lessons) + list(past_lessons)

    for lesson in lessons:
        event = lesson.event_datetime
        feedback_sent = lesson.feedback_submitted
        correction_sent = lesson.lessoncorrection_set.exists()

        # Przedziały czasowe względem teraz
        time_until = (event - now).total_seconds()
        time_since = (now - event).total_seconds()

        # Czasowe flagi do użycia w HTML
        lesson.lock_before_join = time_until > 15 * 60  # przed 15 min przed
        lesson.can_join = 0 <= time_until <= 15 * 60 or 0 <= time_since <= 10 * 60  # od 15 min przed do 10 min po
        lesson.lock_after_join = 10 * 60 < time_since < 50 * 60  # od 10 min po do 50 min po
        lesson.can_feedback = time_since >= 50 * 60 and not feedback_sent
        lesson.can_refresh = time_since >= 50 * 60 and feedback_sent and not correction_sent
        lesson.lock_only = time_since >= 50 * 60 and feedback_sent and correction_sent  # po 50 min i wszystko już wysłane
        print(lesson.id, feedback_sent, correction_sent, lesson.can_feedback, lesson.can_refresh, lesson.lock_only)

    post_count = len(lessons)
    lesson_messages = CourseMessage.objects.filter(room__in=lessons)

    if request.user.groups.filter(name='Teachers').exists():
        user_redirect_url = reverse('schoolweb:teacherPage')
    elif request.user.groups.filter(name='Students').exists():
        user_redirect_url = reverse('schoolweb:studentPage')
    else:
        user_redirect_url = reverse('schoolweb:login')

    context = {
        'lessons': lessons,
        'courses': courses,
        'post_count': post_count,
        'lesson_messages': lesson_messages,
        'all_courses': all_courses,
        'now': now,
        'time_threshold': now,
        'teacher': teacher,
        'user_redirect_url': user_redirect_url,
    }

    return render(request, 'tutoring-zone/teacher-view.html', context)


def is_student(user):
    return user.groups.filter(name='Students').exists()


@login_required(login_url='schoolweb:login')
@user_passes_test(is_student, login_url='schoolweb:login')
def studentPage(request):
    now = datetime.now()
    q = request.GET.get('q', '')
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

    for lesson in lessons:
        event = lesson.event_datetime
        time_until = (event - now).total_seconds()
        time_since = (now - event).total_seconds()

        # Flagi czasowe tylko dla studenta
        lesson.lock_before_join = time_until > 15 * 60
        lesson.can_join = 0 <= time_until <= 15 * 60 or 0 <= time_since <= 10 * 60
        lesson.lock_after_join = time_since > 10 * 60

    post_count = len(lessons)
    lesson_messages = CourseMessage.objects.filter(Q(room__in=lessons))
    new_student = NewStudents.objects.filter(email=student.email).first()

    if request.user.groups.filter(name='Teachers').exists():
        user_redirect_url = reverse('schoolweb:teacherPage')
    elif request.user.groups.filter(name='Students').exists():
        user_redirect_url = reverse('schoolweb:studentPage')

    context = {
        'lessons': lessons,
        'courses': courses,
        'post_count': post_count,
        'lesson_messages': lesson_messages,
        'all_courses': all_courses,
        'now': now,
        'time_threshold': now,
        'teachers': teachers,
        'new_student': new_student,
        'user_redirect_url': user_redirect_url,
    }
    return render(request, 'tutoring-zone/student-view.html', context)


@login_required(login_url='schoolweb:login')
def coursesTutoringZone(request):
    user = request.user
    q = request.GET.get('q', '')

    if user.groups.filter(name='Teachers').exists():
        courses = Course.objects.filter(name__icontains=q, teacher=user)
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
        user_redirect_url = reverse('schoolweb:teacherPage')
        user_group = 'teacher'
    elif user.groups.filter(name='Students').exists():
        courses = Course.objects.filter(name__icontains=q, students=user)
        navbar_template = 'tutoring-zone/nav-student-view.html'
        user_redirect_url = reverse('schoolweb:studentPage')
        user_group = 'student'
    else:
        courses = Course.objects.none()
        navbar_template = 'tutoring-zone/nav-no-search.html'
        user_redirect_url = request.META.get('HTTP_REFERER', reverse('schoolweb:applyUser'))
        user_group = None

    return render(request, 'tutoring-zone/courses-tutoring-zone.html', {
        'courses': courses,
        'navbar_template': navbar_template,
        'user_redirect_url': user_redirect_url,
        'show_search': False,
        'user_group': user_group,
    })


@login_required(login_url='schoolweb:login')
def activityTutoringZone(request):
    lesson_messages = CourseMessage.objects.all()[:12]

    user_redirect_url = request.META.get('HTTP_REFERER', reverse('schoolweb:applyUser'))

    if request.user.groups.filter(name='Teachers').exists():
        user_redirect_url = reverse('schoolweb:teacherPage')
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
    elif request.user.groups.filter(name='Students').exists():
        user_redirect_url = reverse('schoolweb:studentPage')
        navbar_template = 'tutoring-zone/nav-student-view.html'
    else:
        navbar_template = 'tutoring-zone/nav-no-search.html'

    return render(request, 'tutoring-zone/activity-tutoring-zone.html', {
        'lesson_messages': lesson_messages,
        'user_redirect_url': user_redirect_url,
        'show_search': False,
        'navbar_template': navbar_template,
    })


@login_required(login_url='schoolweb:login')
def Teachersearnings(request):
    if not request.user.groups.filter(name='Teachers').exists():
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

    user_earnings = TeachersEarning.objects.filter(user=request.user).order_by('-year', '-month')

    context = {
        'user_earnings': user_earnings,
        'navbar_template': 'tutoring-zone/nav-teacher-view.html',
        'show_search': False,
    }

    return render(request, 'tutoring-zone/earnings-pdf.html', context)


@login_required(login_url='schoolweb:login')
def generate_pdf(request, month, year):
    if not request.user.groups.filter(name='Teachers').exists():
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

    lessons = Lesson.objects.filter(
        host=request.user,
        event_datetime__month=month,
        event_datetime__year=year
    )

    aggregate_earnings = lessons.aggregate(total_payment=Sum('payment'))['total_payment'] or 0

    lesson_stats = LessonStats.objects.filter(user=request.user).first()

    month_bonus = lesson_stats.month_bonus if lesson_stats else 0
    month_referral_bonus = lesson_stats.month_referral_bonus if lesson_stats else 0
    total_earnings = aggregate_earnings + month_bonus + month_referral_bonus

    context = {
        'lessons': lessons,
        'month': month,
        'year': year,
        'aggregate_earnings': aggregate_earnings,
        'month_bonus': month_bonus,
        'month_referral_bonus': month_referral_bonus,
        'total_earnings': total_earnings
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="lessons_{month}_{year}.pdf"'

    template_path = 'tutoring-zone/earnings-pdf-template.html'
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



@login_required(login_url='schoolweb:login')
def resignation(request):
    user = request.user
    is_teacher = user.groups.filter(name='Teachers').exists()

    if request.method == 'POST':
        form = ResignationForm(request.POST, is_teacher=is_teacher)
        if form.is_valid():
            resignation = form.save(commit=False)
            resignation.user = request.user
            resignation.email = request.user.email

            reason = form.cleaned_data.get('reason') if is_teacher else 'Rezygnacja'
            if reason == 'Przerwa':
                resignation.start_date = form.cleaned_data.get('pause_start_date')
                resignation.end_date = form.cleaned_data.get('pause_end_date')
            elif reason == 'Rezygnacja':
                resignation.end_date = form.cleaned_data.get('resignation_date')

            resignation.save()
            messages.success(request, "Twoja rezygnacja została przyjęta.")
            return redirect('schoolweb:user-profile', request.user.pk)
    else:
        form = ResignationForm(is_teacher=is_teacher)

    return render(request, 'tutoring-zone/resignation.html', {
        'form': form,
        'is_teacher': is_teacher
    })


@login_required(login_url='schoolweb:login')
def lesson(request, pk):
    lesson = get_object_or_404(Lesson, id=pk)
    lesson_messages = lesson.coursemessage_set.order_by('-messageCreated')
    participants = lesson.participants.all()

    user = request.user
    course = lesson.course

    if user != course.teacher and user not in course.students.all():
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

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


@login_required(login_url='schoolweb:login')
def createLesson(request):
    if not request.user.groups.filter(name='Teachers').exists():
        return HttpResponseForbidden("Nie masz uprawnień do tej akcji.")

    initial_data = {'host': request.user}
    form = LessonFormCreate(user=request.user, initial=initial_data)
    current_date = timezone.now().strftime('%Y-%m-%dT%H:%M')

    storage = get_messages(request)
    for _ in storage:
        pass

    if request.method == 'POST':
        form = LessonFormCreate(request.POST, user=request.user, initial=initial_data)
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

    return render(request, 'tutoring-zone/create-lesson.html', {
        'form': form,
        'current_date': current_date,
        'show_search': False,
    })


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
        form = LessonFormEdit(request.POST, instance=post)
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
        form = LessonFormEdit(instance=post)

    context = {
        'form': form,
        'can_edit': can_edit,
        'show_search': False,
    }
    return render(request, 'tutoring-zone/update-lesson.html', context)


@login_required(login_url='schoolweb:login')
def findTutor(request):
    if request.method == 'POST':
        form = NewStudentForm(request.POST)
        if form.is_valid():
            new_student = form.save(commit=False)
            new_student.user = request.user
            new_student.email = request.user.email
            new_student.first_name = request.user.first_name
            new_student.last_name = request.user.last_name
            new_student.save()
            messages.success(request, "Dane zostały pomyślnie zapisane.")
            return redirect('schoolweb:studentPage')
        else:
            messages.error(request, "Proszę poprawić błędy w formularzu.")
    else:
        form = NewStudentForm()

    return render(request, 'tutoring-zone/find-tutor.html', {'form': form})


@login_required(login_url='schoolweb:login')
def deleteLessonMessage(request, pk):
    message = get_object_or_404(CourseMessage, id=pk)

    if request.user != message.user:
        return HttpResponse('Brak dostępu', status=403)

    if request.method == 'GET':
        lesson_url = request.META.get('HTTP_REFERER')
        request.session['lesson_url'] = lesson_url

    elif request.method == 'POST':
        message.delete()
        messages.success(request, "Wiadomość została pomyślnie usunięta.")
        lesson_url = request.session.pop('lesson_url', '/')
        return redirect(lesson_url)

    if request.user.groups.filter(name='Teachers').exists():
        navbar_template = 'tutoring-zone/nav-teacher-view.html'
    else:
        navbar_template = 'tutoring-zone/nav-student-view.html'

    context = {'obj': message, 'navbar_template': navbar_template}
    return render(request, 'tutoring-zone/delete-lesson-message.html', context)


@login_required(login_url='schoolweb:login')
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
            messages.success(request, "Komentarz został pomyślnie zaktualizowany.")
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
        return redirect('schoolweb:access_denied')

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
                lesson_stats = user.lesson_stats

                clicked_count = lesson.clicked_users.count()

                # Logika ustalania wynagrodzenia
                if clicked_count == 0:
                    lesson.payment = -50
                    lesson_stats.missed_lessons += 1
                    lesson_stats.all_missed_lessons += 1
                elif clicked_count == 1:
                    single_user = lesson.clicked_users.first()
                    if single_user.groups.filter(name='Students').exists():
                        lesson.payment = -50
                        lesson_stats.missed_lessons += 1
                        lesson_stats.all_missed_lessons += 1
                    elif single_user.groups.filter(name='Teachers').exists():
                        lesson.payment = 20
                        lesson_stats.break_lessons += 1
                        lesson_stats.all_break_lessons += 1
                elif clicked_count > 1:
                    includes_teacher = lesson.clicked_users.filter(groups__name='Teachers').exists()
                    if includes_teacher:
                        if lesson.course.course_type == 'basic':
                            lesson_stats.lessons += 1
                            lesson_stats.all_lessons += 1
                            lesson.payment = 50
                        elif lesson.course.course_type == 'intermediate':
                            lesson_stats.lessons_intermediate += 1
                            lesson_stats.all_lessons_intermediate += 1
                            lesson.payment = 70
                    else:
                        lesson.payment = -50
                        lesson_stats.missed_lessons += 1
                        lesson_stats.all_missed_lessons += 1

                lesson_stats.save()
                lesson.save()

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
    user = get_user(request)
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

