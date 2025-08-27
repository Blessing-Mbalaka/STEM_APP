from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .models.course import Course, CourseResource
admin.site.register(Course)
admin.site.register(CourseResource)

from main.models import (
    CustomUser, Profile,
    Game, GameQuestion, GameScore,
    Course, Enrollment,
    ClassSession, Reservation,
    ForumCategory, Thread, Post, PostLike,
)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "display_name", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Extra", {"fields": ("display_name",)}),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    readonly_fields = ("created_at", "updated_at")



@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title","category","difficulty","is_active","duration_minutes","max_points","created_at")
    list_filter = ("category","difficulty","is_active")
    search_fields = ("title","description")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(GameQuestion)
class GameQuestionAdmin(admin.ModelAdmin):
    list_display = ("game","order","qtype","created_at")
    list_filter = ("game","qtype")
    search_fields = ("question",)

@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ("user","game","score_percent","points_awarded","created_at")
    list_filter = ("game",)
    search_fields = ("user__username","game__title")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "progress", "created_at")
    list_filter = ("status", "course")
    search_fields = ("user__username", "course__title")

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "starts_at", "ends_at", "capacity")
    list_filter = ("course",)
    search_fields = ("title", "course__title")

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("user", "session", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "session__title", "session__course__title")

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_locked", "created_at")
    list_filter = ("category", "is_locked")
    search_fields = ("title", "body", "author__username")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at")
    search_fields = ("body", "author__username", "thread__title")

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__thread__title", "user__username")

