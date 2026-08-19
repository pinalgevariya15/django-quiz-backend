from django.contrib import admin
from quiz.models import Quiz, Question, QuizSession, UserAnswer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3
    fields = ('text', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'quiz', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option', 'created_at')
    list_filter = ('quiz',)
    search_fields = ('text',)


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option')
    can_delete = False


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'quiz', 'score', 'is_completed', 'started_at', 'completed_at')
    list_filter = ('is_completed', 'quiz', 'started_at')
    search_fields = ('user__email', 'quiz__title')
    readonly_fields = ('user', 'quiz', 'started_at', 'completed_at', 'score', 'is_completed', 'questions')
    inlines = [UserAnswerInline]
