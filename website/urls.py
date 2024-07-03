from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'schoolweb'

urlpatterns = [
    # KNOWLEDGE ZONE
    path('', views.home, name="home"),
    path('zostan-korepetytorem/', views.become_tutor, name="become-tutor"),
    path('faq/', views.faq, name="faq"),
    path('regulamin/', views.statute, name="statute"),
    path('kontakt/', views.contact, name='contact'),
    path('przedmioty/', views.subjects, name='subjects'),

    path('wiadomość/', views.user_message, name='user-message'),

    path('logowanie-strefa-wiedzy/', views.loginPage, name="login"),
    path('wylogowywanie-strefa-wiedzy/', views.logoutUser, name="logout"),
    path('rejestracja-strefa-wiedzy/', views.registerPage, name="register"),

    path('strefa-wiedzy/', views.knowledge_zone, name="knowledge_zone"),

    path('room/<str:pk>/', views.room, name="room"),
    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    path('profile/<str:pk>/', views.userProfile, name="user-profile"),
    path('update-user/', views.updateUser, name="update-user"),

    path('topics/', views.topicsPage, name="topics"),
    path('activity/', views.activityPage, name="activity"),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="knowledge-zone/password_reset.html"), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="knowledge-zone/password_reset_sent.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="knowledge-zone/password_reset_form.html"), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="knowledge-zone/password_reset_done.html"), name='password_reset_complete'),


    # TUTORING ZONE
    path('zaczynaj/', views.lessonsHome, name="lessons-home"),
    path('logowanie-strefa-korepetycji/', views.lessonsLogin, name="lessonsLogin"),

    path('nowy-uczen/', views.newStudent, name='newStudent'),
    path('uczen-aplikuj/', views.applyStudent, name="applyStudent"),

    path('nowy-korepetytor/', views.newTeacher, name='newTeacher'),
    path('korepetytor-aplikuj/', views.applyTeacher, name="applyTeacher"),



    path('like-room/<int:pk>/', views.like_room, name='like-room'),

    path('toggle-like/<int:message_id>/', views.toggle_like, name='toggle-like'),
    path('get_likes/<int:message_id>/', views.get_likes, name='get_likes'),
    path('get_room_likes/<int:room_id>/', views.get_room_likes, name='get_room_likes'),
    path('toggle-like-room/<int:room_id>/', views.toggle_like_room, name='toggle_like_room'),

    path('courses-students/', views.courses_studentsPage, name="courses_students"),
    path('courses-teachers/', views.courses_teachersPage, name="courses_teachers"),
    path('activity-lesson/', views.activity_lessonPage, name="activity-lesson"),

    path('lessons-logout/', views.lessonsLogout, name="lessonsLogout"),

    path('lesson_feedback/<int:pk>/', views.lesson_feedback, name='lesson_feedback'),
    path('lesson/<str:pk>/', views.lesson, name="lesson"),
    path('lesson-profile/<str:pk>/', views.lessonProfile, name="lesson-profile"),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('resignation/', views.resignation, name='resignation'),

    path('student-page/', views.studentPage, name="studentPage"),
    path('teacher-page/', views.teacherPage, name="teacherPage"),
    path('create-loader/', views.coursesLoader, name="coursesLoader"),
    path('no-lessons/', views.noLessons, name="noLessons"),

    path('create-lesson/', views.createLesson, name='createLesson'),
    path('update-lesson/', views.updateLesson, name='updateLesson'),
    path('update-lesson/<str:pk>/', views.updateLesson, name='updateLesson'),
    path('delete-lesson/<str:pk>/', views.deleteLesson, name='deleteLesson'),
    path('delete-lesson-message/<str:pk>/', views.deleteLessonMessage, name='deleteLessonMessage'),

    path('update-user-lessons/', views.updateUserLessons, name="update-user-lessons"),

    path('lobby/<str:pk>/', views.Lobby, name='lobby'),
    path('converse/', views.converse, name='converse'),
    path('get_token/', views.getToken),
    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('lesson_correction/<int:pk>/', views.lesson_correction, name='lessonCorrection'),
    path('manage_availability/', views.manage_availability, name='manage_availability'),
    path('get_availability/<str:selected_date>/', views.get_availability, name='get_availability'),
    path('success/', views.success_page, name='success_page'),
]
