from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'schoolweb'

urlpatterns = [
    # WIDGET
    path('', views.home, name="home"),

    path('zostan-korepetytorem/', views.become_tutor, name="become-tutor"),
    path('faq/', views.faq, name="faq"),
    path('regulamin/', views.statute, name="statute"),
    path('kontakt/', views.contact, name='contact'),
    path('przedmioty/', views.subjects, name='subjects'),

    path('wiadomosc/', views.user_message, name='user-message'),


    # KNOWLEDGE ZONE
    path('logowanie-strefa-wiedzy/', views.loginPage, name="login"),
    path('wylogowywanie-strefa-wiedzy/', views.logoutUser, name="logout"),
    path('rejestracja-strefa-wiedzy/', views.registerPage, name="register"),

    path('strefa-wiedzy/', views.knowledge_zone, name="knowledge_zone"),

    path('post/<int:pk>/zgłos/', views.reportRoom, name='report-room'),

    path('post/<str:pk>/', views.room, name="room"),
    path('utworz-post/', views.createRoom, name="create-room"),
    path('edytuj-post/<str:pk>/', views.updateRoom, name="update-room"),
    path('usun-post/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('usun-komentarz/<str:pk>/', views.deleteMessage, name="delete-message"),
    path('edytuj-komentarz/<int:pk>/', views.editRoomMessage, name='edit-message'),


    path('profil/<str:pk>/', views.userProfile, name="user-profile"),
    path('edytuj-uzytkownika/', views.updateUser, name="update-user"),

    path('tematy/', views.topicsPage, name="topics"),
    path('aktywnosc/', views.activityPage, name="activity"),

    # TUTORING ZONE
    path('zaczynaj/', views.lessonsHome, name="lessons-home"),
    path('logowanie-strefa-korepetycji/', views.lessonsLogin, name="lessonsLogin"),

    path('nowy-uczen/', views.newStudent, name='newStudent'),
    path('uczen-aplikuj/', views.applyStudent, name="applyStudent"),

    path('nowy-korepetytor/', views.newTeacher, name='newTeacher'),
    path('korepetytor-aplikuj/', views.applyTeacher, name="applyTeacher"),

    path('create-loader/', views.coursesLoader, name="coursesLoader"),

    path('strefa-korepetycji-korepetytor/', views.teacherPage, name="teacherPage"),
    path('strefa-korepetycji-korepetytor-uczen/', views.studentPage, name="studentPage"),

    path('lesson-profile/<str:pk>/', views.lessonProfile, name="lesson-profile"),
    path('update-user-lessons/', views.updateUserLessons, name="update-user-lessons"),

    path('courses-teachers/', views.courses_teachersPage, name="courses-teachers"),

    path('create-lesson/', views.createLesson, name='create-lesson'),
    path('activity-lesson/', views.activity_lessonPage, name="activity-lesson"),

    path('lessons-logout/', views.lessonsLogout, name="lessonsLogout"),

    path('lesson/<str:pk>/', views.lesson, name="lesson"),
    path('update-lesson/', views.updateLesson, name='updateLesson'),
    path('update-lesson/<str:pk>/', views.updateLesson, name='updateLesson'),

    path('delete-lesson/<str:pk>/', views.deleteLesson, name='delete-lesson'),
    path('delete-lesson-message/<str:pk>/', views.deleteLessonMessage, name='delete-lesson-message'),

    path('lesson-feedback/<int:pk>/', views.lessonFeedback, name='lesson-feedback'),
    path('lesson-correction/<int:pk>/', views.lessonCorrection, name='lesson-correction'),

    path('resignation/', views.resignation, name='resignation'),

    path('success/', views.successPage, name='success-page'),







    path('like-room/<int:pk>/', views.like_room, name='like-room'),

    path('toggle-like/<int:message_id>/', views.toggle_like, name='toggle-like'),
    path('get_likes/<int:message_id>/', views.get_likes, name='get_likes'),
    path('get_room_likes/<int:room_id>/', views.get_room_likes, name='get_room_likes'),
    path('toggle-like-room/<int:room_id>/', views.toggle_like_room, name='toggle_like_room'),

    path('courses-students/', views.courses_studentsPage, name="courses_students"),

    path('access-denied/', views.access_denied, name='access_denied'),

    path('lobby/<str:pk>/', views.Lobby, name='lobby'),
    path('converse/', views.converse, name='converse'),
    path('get_token/', views.getToken),
    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('dostępność/', views.manage_availability, name='manage_availability'),
    path('get_availability/<str:selected_date>/', views.get_availability, name='get_availability'),

    # BLOG
    path('blog/', views.blog_post_list, name='blog_post_list'),
    path('post/<slug:slug>/<int:id>/', views.blog_post_detail, name='blog_post_detail'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
]
