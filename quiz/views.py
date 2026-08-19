from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema

from quiz.models import Quiz, Question, QuizSession
from quiz.serializers import (
    QuizStartSerializer,
    QuizSubmitSerializer
)

class QuizStartView(APIView):
    """
    GET /api/quiz/<id>/start/
    Initiates a new quiz attempt (session) with 10 random unique questions,
    or resumes an active session if it exists.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['quiz'],
        responses={200: QuizStartSerializer}
    )
    def get(self, request, id, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=id)
        
        # Check if there is already an incomplete session for this user and quiz
        session = QuizSession.objects.filter(
            user=request.user,
            quiz=quiz,
            is_completed=False
        ).first()
        
        if not session:
            # Create a brand new session
            session = QuizSession.objects.create(
                user=request.user,
                quiz=quiz
            )
            
            # Select 10 random unique questions from this quiz
            random_questions = list(Question.objects.filter(quiz=quiz).order_by('?')[:10])
            session.questions.set(random_questions)
            
        serializer = QuizStartSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizSubmitView(APIView):
    """
    POST /api/quiz/<id>/submit/
    Submits user answers for the active session of the specified quiz,
    evaluates it, and returns the score and results breakdown report.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['quiz'],
        request_body=QuizSubmitSerializer,
        responses={
            200: 'Quiz submitted successfully. Returns score and results breakdown report.',
            400: 'Bad Request. No active session or session already completed.'
        }
    )
    def post(self, request, id, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=id)
        
        # Find the active incomplete session for this user and quiz
        session = QuizSession.objects.filter(
            user=request.user,
            quiz=quiz,
            is_completed=False
        ).first()
        
        if not session:
            return Response(
                {"error": "No active session found for this quiz. Please start the quiz first."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = QuizSubmitSerializer(
            data=request.data,
            context={"session": session}
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        
        return Response(results, status=status.HTTP_200_OK)
