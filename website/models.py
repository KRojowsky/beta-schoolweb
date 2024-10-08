from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~WIDGET~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlatformMessage(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, validators=[RegexValidator(r'^\d{9}$', message='Numer telefonu musi składać się z 9 cyfr.')])
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~KNOWLEDGE-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True, )
    bio = models.TextField(null=True, default="Brak opisu")
    avatar = models.ImageField(upload_to='profile-pictures/', null=True, blank=True, default='profile-pictures/avatar.svg')

    lessons = models.IntegerField(default=0)
    lessons_intermediate = models.IntegerField(default=0)

    break_lessons = models.IntegerField(default=0)
    all_break_lessons = models.IntegerField(default=0)

    missed_lessons = models.IntegerField(default=0)
    all_missed_lessons = models.IntegerField(default=0)

    all_lessons = models.IntegerField(default=0)
    all_lessons_intermediate = models.IntegerField(default=0)
    phone_number = models.CharField(default='N/A', max_length=20)
    add_info = models.CharField(max_length=100, default="rola/przedmiot")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.pk:
            super(User, self).save(*args, **kwargs)

        is_student = self.groups.filter(name='Students').exists()

        if is_student:
            try:
                original_instance = User.objects.get(pk=self.pk)
                original_lessons = original_instance.lessons
            except User.DoesNotExist:
                original_lessons = 0

            if original_lessons != 0 and self.lessons == 0:
                if self.lessons == 0 and self.all_lessons > 0:
                    self.all_lessons += 1
                self.all_lessons += 0
            elif original_lessons > self.lessons:
                self.all_lessons += 1
        else:
            pass

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}' if self.first_name and self.last_name else self.username


class Topic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    svg_icon = models.FileField(upload_to='icons/', null=True, blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='room-images/', null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_rooms', blank=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name

    def preserve_user_on_delete(self):
        if self.host and self.host.deleted:
            self.host = None
            self.save()


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='message-images/', blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    file = models.FileField(upload_to='message-files/', blank=True, null=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]

    def toggle_like(self, user):
        if user in self.likes.all():
            self.likes.remove(user)
        else:
            self.likes.add(user)
        self.save()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~TUTORING-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Course(models.Model):
    COURSE_TYPE_CHOICES = (
        ('basic', 'Podstawowy'),
        ('intermediate', 'Rozszerzony'),
    )

    name = models.CharField(max_length=200)
    student = models.CharField(max_length=200, default="")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    students = models.ManyToManyField(User, related_name='courses_enrolled', blank=True)
    courseCreated = models.DateTimeField(auto_now_add=True)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default='basic')

    def get_lessons_with_feedback_count(self):
        return self.post_set.filter(feedback__isnull=False).count()

    class Meta:
        ordering = ['-courseCreated']

    def __str__(self):
        return self.student


class Report(models.Model):
    REPORT_REASONS = [
        ('SPAM', 'Spam'),
        ('INAPPROPRIATE', 'Nieodpowiednia treść'),
        ('HARASSMENT', 'Nękanie'),
        ('FALSE_INFO', 'Fałszywe informacje'),
        ('HATE_SPEECH', 'Mowa nienawiści'),
        ('VIOLENCE', 'Przemoc'),
        ('COPYRIGHT', 'Naruszenie praw autorskich'),
        ('OTHER', 'Inne'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Report by {self.reporter.username} on {self.room.name}'


class RoomMember(models.Model):
    name = models.CharField(max_length=200, default="Default Name")
    uid = models.CharField(max_length=200)
    room_name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


import random
import string

class Post(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='postParticipants', blank=True)
    postUpdated = models.DateTimeField(auto_now=True)
    postCreated = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='room-images/', null=True, blank=True)
    event_datetime = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    points = models.IntegerField(null=True, blank=True)
    schoolweb_rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], null=True, blank=True)
    clicked_users = models.ManyToManyField(User, related_name='clicked_posts', blank=True)
    attended_students = models.ManyToManyField(User, related_name='attended_students_lessons', blank=True)
    attended_teachers = models.ManyToManyField(User, related_name='attended_teachers_lessons', blank=True)
    feedback_submitted = models.BooleanField(default=False)
    invite_code = models.CharField(max_length=10, unique=True, blank=True)  # Nowe pole na kod zaproszenia

    def save(self, *args, **kwargs):
        # Generowanie unikalnego invite_code
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    def generate_invite_code(self):
        """Generuje unikalny kod zaproszenia."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    def add_click(self, user):
        if user not in self.clicked_users.all():
            self.clicked_users.add(user)
            self.click_count = self.clicked_users.count()
            self.save()

    def add_feedback(self, feedback_text):
        self.feedback = feedback_text
        self.save()

    class Meta:
        ordering = ['-postUpdated', '-postCreated']

    def __str__(self):
        return self.title



class CourseMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Post, on_delete=models.CASCADE)
    body = models.TextField()
    messageUpdated = models.DateTimeField(auto_now=True)
    messageCreated = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='message-images/', blank=True, null=True)
    file = models.FileField(upload_to='message-files/', blank=True, null=True)

    class Meta:
        ordering = ['-messageUpdated', '-messageCreated']

    def __str__(self):
        return self.body[0:50]


class NewTeacher(models.Model):
    SCHOOL_CHOICES = [
        ('podstawowa', 'Szkoła podstawowa'),
        ('średnia', 'Szkoła średnia'),
        ('maturalna', 'Klasa maturalna'),
        ('praktyki', 'Praktyki'),
        ('licencjat', 'Licencjat'),
        ('magister', 'Magister'),
        ('inżynier', 'Inżynier'),
        ('doktor', 'Doktor'),
    ]

    LANGUAGE = [
        ('tak', 'Tak'),
        ('nie', 'Nie'),
    ]

    name = models.CharField(max_length=50, null=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Numer telefonu musi byc w formacie: '999 999 999'. Maksymalnie 15 cyfr."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True)
    school = models.CharField(choices=SCHOOL_CHOICES, max_length=20, null=True)
    subject = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    age_language = models.CharField(choices=LANGUAGE, max_length=20, null=True)

    def __str__(self):
        return self.name


class NewStudent(models.Model):
    SCHOOL_CHOICES = [
        ('podstawowa', 'Szkoła podstawowa'),
        ('średnia', 'Szkoła średnia'),
        ('maturalna', 'Klasa maturalna'),
        ('wyższa', 'Szkoła wyższa'),
    ]

    LEVEL_CHOICES = [
        ('rozwijające', 'Rozwijające'),
        ('korygujące', 'Korygujące'),
    ]

    name = models.CharField(max_length=50, null=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Numer telefonu musi byc w formacie: '999 999 999'. Maksymalnie 15 cyfr."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True)
    subject = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    school = models.CharField(choices=SCHOOL_CHOICES, max_length=20, null=True)
    level = models.CharField(choices=LEVEL_CHOICES, max_length=20, null=True)

    def __str__(self):
        return self.name


class LessonCorrection(models.Model):
    lesson = models.ForeignKey(Post, on_delete=models.CASCADE, default="")
    feedback = models.TextField(null=True, blank=True, default="")
    attended_students = models.ManyToManyField(User, related_name='attended_students', blank=True)
    attended_teachers = models.ManyToManyField(User, related_name='attended_teachers', blank=True)
    lesson_image = models.ImageField(upload_to='lesson_images/', null=True, blank=True)


class Resign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()

    REASON_CHOICES = [
        ('Przerwa', 'Przerwa'),
        ('Rezygnacja', 'Rezygnacja'),
    ]
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    course_info = models.TextField(blank=True, null=True)

    RATING_CHOICES = [
        (1, 'Źle'),
        (2, 'Słabo'),
        (3, 'Przeciętnie'),
        (4, 'Dobrze'),
        (5, 'Fantastycznie'),
    ]
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)

    RETURN_OPTIONS = [
        ('Tak', 'Tak'),
        ('Nie', 'Nie'),
    ]
    consider_return = models.CharField(max_length=3, choices=RETURN_OPTIONS, blank=True, null=True)
    reason_details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Resignation - {self.email}'


class Availability(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    day = models.DateField()
    hour_6_7 = models.BooleanField(default=False)
    hour_7_8 = models.BooleanField(default=False)
    hour_8_9 = models.BooleanField(default=False)
    hour_9_10 = models.BooleanField(default=False)
    hour_10_11 = models.BooleanField(default=False)
    hour_11_12 = models.BooleanField(default=False)
    hour_12_13 = models.BooleanField(default=False)
    hour_13_14 = models.BooleanField(default=False)
    hour_14_15 = models.BooleanField(default=False)
    hour_15_16 = models.BooleanField(default=False)
    hour_16_17 = models.BooleanField(default=False)
    hour_17_18 = models.BooleanField(default=False)
    hour_18_19 = models.BooleanField(default=False)
    hour_19_20 = models.BooleanField(default=False)
    hour_20_21 = models.BooleanField(default=False)
    hour_21_22 = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.day}"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BLOG~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class BlogCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='blog-category-images/', blank=True, null=True)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(default="", null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    image = models.ImageField(upload_to='blog-list-images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name='blog_posts')
    is_new = models.BooleanField(default=False, verbose_name='Nowość')
    is_trending = models.BooleanField(default=False, verbose_name='Na czasie')
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def get_similar_posts(self):
        return BlogPost.objects.filter(category=self.category).exclude(id=self.id)

    def number_of_likes(self):
        return self.likes


class ContentBlock(models.Model):
    TEXT = 'text'
    IMAGE = 'image'

    BLOCK_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
    ]

    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='content_blocks')
    block_type = models.CharField(max_length=10, choices=BLOCK_TYPE_CHOICES)
    order = models.PositiveIntegerField()
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='blog-details-images/', blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Block {self.id} ({self.get_block_type_display()}) for {self.blog_post.title}"
