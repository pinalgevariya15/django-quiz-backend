from django.urls import path
from quiz.views import QuizStartView, QuizSubmitView

urlpatterns = [
    path('quiz/<int:id>/start/', QuizStartView.as_view(), name='quiz_start'),
    path('quiz/<int:id>/submit/', QuizSubmitView.as_view(), name='quiz_submit'),
]
