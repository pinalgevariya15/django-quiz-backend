from rest_framework import serializers
from django.utils import timezone
from quiz.models import Quiz, Question, QuizSession, UserAnswer

class QuizListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'text', 'option_1', 'option_2', 'option_3', 'option_4')


class QuizStartSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id')
    quiz_title = serializers.CharField(source='quiz.title')
    quiz_id = serializers.IntegerField(source='quiz.id')
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizSession
        fields = ('session_id', 'quiz_id', 'quiz_title', 'started_at', 'questions')


class UserAnswerSubmissionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option = serializers.IntegerField(min_value=1, max_value=4)


class QuizSubmitSerializer(serializers.Serializer):
    answers = UserAnswerSubmissionSerializer(many=True, required=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer must be submitted.")
        return value

    def validate(self, data):
        session = self.context.get('session')
        if not session:
            raise serializers.ValidationError("No active quiz session found.")
        if session.is_completed:
            raise serializers.ValidationError("This quiz session has already been completed.")
        return data

    def save(self):
        session = self.context['session']
        answers_data = self.validated_data['answers']
        
        # Load the 10 questions that were assigned to this session
        session_questions = {q.id: q for q in session.questions.all()}
        
        score = 0
        total_questions = len(session_questions)
        
        user_answers_to_create = []
        submitted_question_ids = set()
        
        for ans in answers_data:
            q_id = ans['question_id']
            sel_opt = ans['selected_option']
            
            # Check for duplicate submission of same question in request body
            if q_id in submitted_question_ids:
                raise serializers.ValidationError(
                    f"Duplicate answer submitted for question ID {q_id}."
                )
            submitted_question_ids.add(q_id)
            
            # Ensure the question actually belongs to this specific user's session
            if q_id not in session_questions:
                raise serializers.ValidationError(
                    f"Question with ID {q_id} was not assigned to this quiz session."
                )
                
            question = session_questions[q_id]
            
            # Check correctness
            if sel_opt == question.correct_option:
                score += 1
                
            user_answers_to_create.append(
                UserAnswer(
                    session=session,
                    question=question,
                    selected_option=sel_opt
                )
            )

        # Clear any previous saved user answers for safety
        UserAnswer.objects.filter(session=session).delete()
        UserAnswer.objects.bulk_create(user_answers_to_create)
        
        # Update session details
        session.score = score
        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()
        
        # Compile results detail report
        results_breakdown = []
        for ua in user_answers_to_create:
            q = ua.question
            options = {1: q.option_1, 2: q.option_2, 3: q.option_3, 4: q.option_4}
            
            results_breakdown.append({
                "question_id": q.id,
                "question_text": q.text,
                "selected_option": ua.selected_option,
                "selected_text": options.get(ua.selected_option),
                "correct_option": q.correct_option,
                "correct_text": options.get(q.correct_option),
                "is_correct": ua.selected_option == q.correct_option
            })

        return {
            "session_id": session.id,
            "quiz_title": session.quiz.title,
            "score": score,
            "total_questions": total_questions,
            "percentage": round((score / total_questions) * 100, 2) if total_questions > 0 else 0.0,
            "completed_at": session.completed_at,
            "results": results_breakdown
        }
