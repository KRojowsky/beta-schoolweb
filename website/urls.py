from django.urls import path
from . import views

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
    path('strefa-wiedzy/post/<int:pk>/zgłos/', views.reportRoom, name='report-room'),
    path('strefa-wiedzy/post/<str:pk>/', views.room, name="room"),
    path('strefa-wiedzy/utworz-post/', views.createRoom, name="create-room"),
    path('strefa-wiedzy/edytuj-post/<str:pk>/', views.updateRoom, name="update-room"),
    path('strefa-wiedzy/usun-post/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('strefa-wiedzy/usun-komentarz/<str:pk>/', views.deleteMessage, name="delete-message"),
    path('strefa-wiedzy/edytuj-komentarz/<int:pk>/', views.editRoomMessage, name='edit-message'),
    path('strefa-wiedzy/profil-strefa-wiedzy/<str:pk>/', views.userProfile, name="user-profile"),
    path('strefa-wiedzy/edytuj-uzytkownika-strefa-wiedzy/', views.updateUser, name="update-user"),
    path('strefa-wiedzy/tematy/', views.topicsPage, name="topics"),
    path('strefa-wiedzy/aktywnosc/', views.activityPage, name="activity"),

    # BLOG
    path('blog/', views.blog_post_list, name='blog-post-list'),
    path('post/<slug:slug>/<int:id>/', views.blog_post_detail, name='blog-post-detail'),
    path('post/<int:pk>/like/', views.like_post, name='like-post'),

    # TUTORING ZONE
    path('rejestracja-strefa-korepetycji/', views.applyUser, name="applyUser"),
    path('dolacz-strefa-korepetycji', views.WriterToTutoringZone, name="WriterToTutoringZone"),
    path('tworzenie-konta/', views.coursesLoader, name="coursesLoader"),
    path('zdobadz-ucznia/', views.newStudent, name='new_students'),
    path('strefa-korepetycji-korepetytor/', views.teacherPage, name="teacherPage"),
    path('strefa-korepetycji-uczen/', views.studentPage, name="studentPage"),
    path('profil-strefa-korepetycji/<str:pk>/', views.lessonProfile, name="lesson-profile"),
    path('informacje-bankowe/', views.bankInformation, name='bank_information'),
    path('pdf-dochody/', views.Teachersearnings, name='earnings_pdf'),
    path('edytuj-uzytkownika-strefa-korepetycji/', views.updateUserLessons, name="update-user-lessons"),
    path('kursy-korepetytor/', views.courses_teachersPage, name="courses-teachers"),
    path('utworz-lekcje/', views.createLesson, name='create-lesson'),
    path('znajdz-korepetycje/', views.findTutor, name='find_tutor'),
    path('aktywnosci-strefa-korepetycji/', views.activity_lessonPage, name="activity-lesson"),
    path('lekcja/<str:pk>/', views.lesson, name="lesson"),
    path('edytuj-lekcje/<str:pk>/', views.updateLesson, name='updateLesson'),
    path('usun-komentarz-lekcji/<str:pk>/', views.deleteLessonMessage, name='delete-lesson-message'),
    path('edytuj-komentarz-lekcji/<str:pk>/', views.editLessonMessage, name='edit-lesson-message'),
    path('feedback-lekcji/<int:pk>/', views.lessonFeedback, name='lesson-feedback'),
    path('poprawka-lekcji/<int:pk>/', views.lessonCorrection, name='lesson-correction'),
    path('rezygnacja/', views.resignation, name='resignation'),
    path('success/', views.successPage, name='success-page'),
    path('like-room/<int:pk>/', views.like_room, name='like-room'),
    path('toggle-like/<int:message_id>/', views.toggle_like, name='toggle-like'),
    path('get_likes/<int:message_id>/', views.get_likes, name='get_likes'),
    path('get_room_likes/<int:room_id>/', views.get_room_likes, name='get_room_likes'),
    path('toggle-like-room/<int:room_id>/', views.toggle_like_room, name='toggle_like_room'),
    path('courses-students/', views.courses_studentsPage, name="courses_students"),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('converse', views.converse, name='converse'),
    path('dostępność/', views.manage_availability, name='manage_availability'),
    path('get_availability/<str:selected_date>/', views.get_availability, name='get_availability'),
]
