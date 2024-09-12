from django.contrib import admin
from .models import Room, Topic, Message, Course, Post, CourseMessage, PlatformMessage, NewStudent, \
    RoomMember, NewTeacher, LessonCorrection, Resign, Availability, Report, BlogPost, BlogCategory, ContentBlock
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.forms import DateInput
from django import forms
from website.models import User
from django.contrib.auth.models import Group


class PlatformMessageAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number', 'message', 'created')


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'add_info', 'phone_number', 'display_groups',
                    'lessons', 'lessons_intermediate', 'break_lessons', 'missed_lessons', 'all_break_lessons',
                    'all_missed_lessons', 'all_lessons', 'all_lessons_intermediate')
    list_display_links = ('email',)
    list_editable = ('phone_number', 'add_info', 'lessons', 'lessons_intermediate', 'break_lessons', 'missed_lessons',
                     'all_break_lessons', 'all_missed_lessons', 'all_lessons', 'all_lessons_intermediate')

    def display_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

    display_groups.short_description = 'Groups'


class LessonInfo(admin.ModelAdmin):
    def clicked_users_count(self, obj):
        return obj.clicked_users.count()

    clicked_users_count.short_description = 'Clicked Users Count'

    list_display = ['title', 'host', 'postUpdated', 'postCreated', 'event_datetime', 'clicked_users_count',
                    'feedback', 'points', 'schoolweb_rating', 'get_attended_students', 'get_attended_teachers']
    list_filter = ['host', 'course', 'postCreated', 'postUpdated', 'event_datetime']
    search_fields = ['host', 'title', 'course__name', 'feedback']
    ordering = ['-postCreated', '-postUpdated']

    def get_attended_students(self, obj):
        return ', '.join([str(student) for student in obj.attended_students.all()])

    def get_attended_teachers(self, obj):
        return ', '.join([str(teacher) for teacher in obj.attended_teachers.all()])

    get_attended_students.short_description = 'Attended Students'
    get_attended_teachers.short_description = 'Attended Teachers'


class LessonCorrectionAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'get_attended_students', 'get_attended_teachers', 'display_image')
    search_fields = ['lesson__title', 'attended_students__username', 'attended_teachers__username']

    def get_attended_students(self, obj):
        return ', '.join([str(student) for student in obj.attended_students.all()])

    def get_attended_teachers(self, obj):
        return ', '.join([str(teacher) for teacher in obj.attended_teachers.all()])

    def display_image(self, obj):
        if obj.lesson_image:
            return format_html('<img src="{}" style="max-width: 50px; max-height: 50px;" />'.format(obj.lesson_image.url))
        return "No Image"

    get_attended_students.short_description = 'Attended Students'
    get_attended_teachers.short_description = 'Attended Teachers'
    display_image.short_description = 'Lesson Image'


class ResignationAdminForm(forms.ModelForm):
    class Meta:
        model = Resign
        fields = '__all__'
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
        }


class ResignationAdmin(admin.ModelAdmin):
    form = ResignationAdminForm
    list_display = ('user_email', 'email', 'reason', 'start_date', 'end_date', 'course_info')

    def user_email(self, obj):
        return obj.user.email if obj.user else None

    def start_date(self, obj):
        return obj.start_date.strftime("%Y-%m-%d") if obj.start_date else ""

    def end_date(self, obj):
        return obj.end_date.strftime("%Y-%m-%d") if obj.end_date else ""


class SelectedHoursFilter(admin.SimpleListFilter):
    title = 'Selected Hours'
    parameter_name = 'selected_hours'

    def lookups(self, request, model_admin):
        hours = [(str(hour), str(hour)) for hour in range(6, 22)]
        return hours

    def queryset(self, request, queryset):
        if self.value():
            value = int(self.value())
            return queryset.filter(**{f'hour_{value}_{value+1}': True})
        return queryset


class AddInfoFilter(admin.SimpleListFilter):
    title = 'Add Info'
    parameter_name = 'add_info'

    def lookups(self, request, model_admin):
        users = User.objects.filter(availability__isnull=False).distinct()
        return [(user.add_info, user.add_info) for user in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__add_info=self.value())
        return queryset


class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('user', 'day', 'get_selected_hours', 'user_add_info')
    list_filter = ('day', SelectedHoursFilter, AddInfoFilter)
    search_fields = ('user__name', 'day', 'user__email', 'user__add_info')

    def get_selected_hours(self, obj):
        selected_hours = [hour for hour in range(6, 23) if getattr(obj, f'hour_{hour}_{hour+1}', False)]
        return ', '.join(map(str, selected_hours))

    get_selected_hours.short_description = 'Selected Hours'

    def user_add_info(self, obj):
        return obj.user.add_info if obj.user else None

    user_add_info.short_description = 'User Additional Info'


class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'body_preview', 'room_name', 'created')
    list_filter = ('room__name',)

    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Message'

    def author(self, obj):
        return obj.user.username if obj.user else None
    author.short_description = 'Author'

    def room_name(self, obj):
        return obj.room.name if obj.room else None
    room_name.short_description = 'Room'


class CourseMessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'body_preview', 'room_name', 'messageCreated')
    list_filter = ('room__title',)

    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Message'

    def author(self, obj):
        return obj.user.username if obj.user else None
    author.short_description = 'Author'

    def room_name(self, obj):
        return obj.room.title if obj.room else None
    room_name.short_description = 'Room'


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter teachers (Users in the "Teachers" group)
        teachers_group = Group.objects.get(name="Teachers")
        self.fields['teacher'].queryset = User.objects.filter(groups=teachers_group)

        # Filter students (Users in the "Students" group)
        students_group = Group.objects.get(name="Students")
        self.fields['students'].queryset = User.objects.filter(groups=students_group)


class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = ('name', 'student', 'course_type', 'get_students_list', 'teacher')
    list_filter = ('teacher', 'name', 'student', 'course_type')

    def get_students_list(self, obj):
        return ", ".join([student.username for student in obj.students.all()])
    get_students_list.short_description = 'Students'


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'host_name', 'created', 'total_likes')
    list_filter = ('created', 'host__username')
    search_fields = ('name', 'host__username')

    def host_name(self, obj):
        return obj.host.username if obj.host else "None"
    host_name.short_description = 'Host'

    def total_likes(self, obj):
        return obj.likes.count()
    total_likes.short_description = 'Likes'


class ReportAdmin(admin.ModelAdmin):
    list_display = ['room', 'reporter', 'reason', 'created']
    search_fields = ['room__name', 'reporter__username', 'reason']
    list_filter = ['reason', 'created']


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~BLOG~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    extra = 1


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'category', 'is_new', 'is_trending', 'views', 'likes', 'slug')
    list_filter = ('created_at', 'category', 'is_new', 'is_trending')
    search_fields = ('title', )
    fields = ('title', 'author', 'category', 'image', 'slug', 'is_new', 'is_trending', 'views', 'likes')
    inlines = [ContentBlockInline]
    prepopulated_fields = {"slug": ("title",)}


class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    search_fields = ('name',)


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(BlogCategory, BlogCategoryAdmin)
admin.site.register(PlatformMessage, PlatformMessageAdmin)
admin.site.register(Availability, AvailabilityAdmin)
admin.site.register(LessonCorrection, LessonCorrectionAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(NewStudent)
admin.site.register(NewTeacher)
admin.site.register(Room, RoomAdmin)
admin.site.register(Topic)
admin.site.register(Message, MessageAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Post, LessonInfo)
admin.site.register(Report, ReportAdmin)
admin.site.register(CourseMessage, CourseMessageAdmin)
admin.site.register(RoomMember)
admin.site.register(Resign, ResignationAdmin)
