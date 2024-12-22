from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import RegexValidator
import random
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~WIDGET~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlatformMessage(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, validators=[RegexValidator(r'^\d{9}$', message='Numer telefonu musi składać się z 9 cyfr.')])
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Wiadomości z Platformy'
        verbose_name_plural = 'Wiadomości z Platformy'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~KNOWLEDGE-ZONE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Topic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    svg_icon = models.FileField(upload_to='icons/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kategorie - Strefa Wiedzy'
        verbose_name_plural = 'Kategorie - Strefa Wiedzy'


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True, default="Brak opisu")
    interests = models.TextField(null=True, blank=True, default="Brak zainteresowań")
    avatar = models.ImageField(upload_to='profile-pictures/', null=True, blank=True, default='profile-pictures/avatar.svg')
    phone_number = models.CharField(default='N/A', max_length=20)
    subject = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    points = models.IntegerField(default=0)

    LEVEL_CHOICES = [
        ('Podstawa', 'Podstawa'),
        ('Rozszerzenie', 'Rozszerzenie'),
    ]
    level = models.CharField(
        max_length=50,
        choices=LEVEL_CHOICES,
        blank=True,
        verbose_name="Poziom"
    )

    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)  # New field
    referred_by = models.CharField(max_length=10, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_referral_code(self):
        """Generate a unique 10-character alphanumeric referral code."""
        length = 10
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def save(self, *args, **kwargs):
        if not self.referral_code:  # Generate referral code if not set
            self.referral_code = self.generate_referral_code()

        super().save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return f'{self.first_name} {self.last_name}' if self.first_name and self.last_name else self.username


class LessonStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="lesson_stats")
    lessons = models.IntegerField(default=0)
    lessons_intermediate = models.IntegerField(default=0)

    break_lessons = models.IntegerField(default=0)
    all_break_lessons = models.IntegerField(default=0)

    missed_lessons = models.IntegerField(default=0)
    all_missed_lessons = models.IntegerField(default=0)

    all_lessons = models.IntegerField(default=0)
    all_lessons_intermediate = models.IntegerField(default=0)

    month_bonus = models.IntegerField(default=0)
    all_bonus = models.IntegerField(default=0)

    month_referral_bonus = models.IntegerField(default=0)
    all_referral_bonus = models.IntegerField(default=0)

    def update_all_lessons(self):
        try:
            original_instance = LessonStats.objects.get(pk=self.pk)
            original_lessons = original_instance.lessons
        except LessonStats.DoesNotExist:
            original_lessons = 0

        if original_lessons != 0 and self.lessons == 0:
            if self.all_lessons > 0:
                self.all_lessons += 1
        elif original_lessons > self.lessons:
            self.all_lessons += 1

    @property
    def month_earnings(self):
        if self.user.groups.filter(name='Teachers').exists():
            return (
                60 * self.lessons_intermediate +
                40 * self.lessons +
                20 * self.break_lessons -
                50 * self.missed_lessons +
                self.month_bonus + self.month_referral_bonus
            )
        return -1

    @property
    def all_earnings(self):
        if self.user.groups.filter(name='Teachers').exists():
            return (
                60 * self.all_lessons_intermediate +
                40 * self.all_lessons +
                20 * self.all_break_lessons -
                50 * self.all_missed_lessons +
                self.all_bonus + self.all_referral_bonus
            )
        return -1

    def save(self, *args, **kwargs):
        self.update_all_lessons()
        super(LessonStats, self).save(*args, **kwargs)

    def __str__(self):
        return (
            f"LessonStats for {self.user} | "
            f"Monthly Earnings: {self.month_earnings} | "
            f"Total Earnings: {self.all_earnings}"
        )

    class Meta:
        verbose_name = 'Lekcje - statystyki'
        verbose_name_plural = 'Lekcje - statystyki'



class BankInformation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_information')
    card_number = models.CharField(max_length=16, unique=True)
    cvv = models.CharField(max_length=3)
    cardholder_name = models.CharField(max_length=100)
    expiration_date = models.DateField()

    def __str__(self):
        return f'{self.cardholder_name} - {self.card_number}'


    class Meta:
        verbose_name = 'Informacje bankowe'
        verbose_name_plural = 'Informacje bankowe'


class TeachersEarning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    monthly_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_added = models.DateTimeField(auto_now_add=True)
    month = models.PositiveIntegerField(default=datetime.now().month)
    year = models.PositiveIntegerField(default=datetime.now().year)

    class Meta:
        verbose_name = 'Wypłata'
        verbose_name_plural = 'Wypłaty'
        unique_together = ('user', 'month', 'year')  # Ensures one payout per user per month/year combination

    def __str__(self):
        return f"Earnings for {self.user.username} | Monthly: {self.monthly_earnings} | {self.month}/{self.year}"



class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hosted_rooms')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='room-images/', null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_rooms', blank=True)

    class Meta:
        ordering = ['-created', '-updated']
        verbose_name = 'Posty - Strefa Wiedzy'
        verbose_name_plural = 'Posty - Strefa Wiedzy'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Sprawdzamy, czy pokój jest nowy
        super().save(*args, **kwargs)
        if is_new and self.host:
            self.host.points += 10  # Dodanie 10 punktów za nowy pokój
            self.host.save()

    def delete(self, *args, **kwargs):
        host = self.host
        super().delete(*args, **kwargs)
        if host and host.points >= 10:  # Sprawdzenie, czy użytkownik ma co najmniej 10 punktów
            host.points -= 10  # Odjęcie 10 punktów
            host.save()


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='messages')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='message-images/', blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    file = models.FileField(upload_to='message-files/', blank=True, null=True)

    class Meta:
        ordering = ['-updated', '-created']
        verbose_name = 'Komentarze - Strefa Wiedzy'
        verbose_name_plural = 'Komentarze - Strefa Wiedzy'

    def __str__(self):
        return self.body[0:50]

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if the message is new
        super().save(*args, **kwargs)

        if is_new and self.user:
            # Add 5 points for a new message
            self.user.points += 5
            self.user.save()

            # Check if the user has at least 1000 points before performing actions
            if self.user.points >= 1000:
                # Deduct 1000 points from the user
                self.user.points -= 1000
                self.user.save()

                # Check if the user is in the 'Students' group
                if self.user.groups.filter(name='Students').exists():
                    # Get or create the LessonStats object for the student
                    lesson_stats, created = LessonStats.objects.get_or_create(user=self.user)

                    # Check user's level and update the respective field
                    user_level = self.user.level
                    if user_level == 'Podstawa':  # If level is 'Podstawa'
                        lesson_stats.lessons += 1
                    elif user_level == 'Rozszerzenie':  # If level is 'Rozszerzenie'
                        lesson_stats.lessons_intermediate += 1
                    lesson_stats.save()

                # Check if the user is in the 'Teachers' group
                elif self.user.groups.filter(name='Teachers').exists():
                    # Get or create the LessonStats object for the teacher
                    lesson_stats, created = LessonStats.objects.get_or_create(user=self.user)

                    # Add 50 zł bonus to both month_bonus and all_bonus for the teacher
                    lesson_stats.month_bonus += 50  # Add to monthly bonus
                    lesson_stats.all_bonus += 50    # Add to total bonus
                    lesson_stats.save()

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        if user:
            # Subtract 5 points when the message is deleted
            user.points -= 5
            user.save()

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
        return self.lesson_set.filter(feedback__isnull=False).count()

    class Meta:
        ordering = ['-courseCreated']

    def __str__(self):
        return self.student

    class Meta:
        verbose_name = 'Kursy - Strefa Korepetycji'
        verbose_name_plural = 'Kursy - Strefa Korepetycji'


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

    class Meta:
        verbose_name = 'Zgłoszenia - Strefa Wiedzy'
        verbose_name_plural = 'Zgłoszenia - Strefa Wiedzy'

class Lesson(models.Model):
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

    class Meta:
        verbose_name = 'Lekcje - Strefa Korepetycji'
        verbose_name_plural = 'Lekcje - Strefa Korepetycji'



class CourseMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    body = models.TextField()
    messageUpdated = models.DateTimeField(auto_now=True)
    messageCreated = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='message-images/', blank=True, null=True)
    file = models.FileField(upload_to='message-files/', blank=True, null=True)

    class Meta:
        ordering = ['-messageUpdated', '-messageCreated']

    def __str__(self):
        return self.body[0:50]

    class Meta:
        verbose_name = 'Komentarze - Strefa Korepetycji'
        verbose_name_plural = 'Komentarze - Strefa Korepetycji'


class LessonCorrection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, default="")
    feedback = models.TextField(null=True, blank=True, default="")
    attended_students = models.ManyToManyField(User, related_name='attended_students', blank=True)
    attended_teachers = models.ManyToManyField(User, related_name='attended_teachers', blank=True)
    lesson_image = models.ImageField(upload_to='lesson_images/', null=True, blank=True)

    class Meta:
        verbose_name = 'Poprawki lekcji'
        verbose_name_plural = 'Poprawki lekcji'


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


    class Meta:
        verbose_name = 'Rezygnacje'
        verbose_name_plural = 'Rezygnacje'

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

    class Meta:
        verbose_name = 'Dostępności'
        verbose_name_plural = 'Dostępności'

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BLOG~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class BlogCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='blog-category-images/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kategorie - Blog'
        verbose_name_plural = 'Kategorie - Blog'


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


    class Meta:
        verbose_name = 'Posty - Blog'
        verbose_name_plural = 'Posty - Blog'

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
