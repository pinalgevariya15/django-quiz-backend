from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from quiz.models import Quiz, Question, QuizSession, UserAnswer

User = get_user_model()

class QuizAPITests(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(email="quizuser@example.com", password="Password123!")
        
        # Create a quiz
        self.quiz = Quiz.objects.create(title="Python Basics", description="Test your Python knowledge")
        
        # Create 15 questions for the quiz to test the randomized selection of exactly 10
        self.questions = []
        for i in range(1, 16):
            q = Question.objects.create(
                quiz=self.quiz,
                text=f"Question number {i}",
                option_1=f"Answer A to Q{i}",
                option_2=f"Answer B to Q{i}",
                option_3=f"Answer C to Q{i}",
                option_4=f"Answer D to Q{i}",
                correct_option=(i % 4) + 1  # correct choice will cycle between 1, 2, 3, 4
            )
            self.questions.append(q)
            
        # Another quiz (empty)
        self.empty_quiz = Quiz.objects.create(title="Empty Quiz", description="No questions")

        # Endpoint paths
        self.start_url = lambda q_id: reverse('quiz_start', args=[q_id])
        self.submit_url = lambda q_id: reverse('quiz_submit', args=[q_id])

    def test_start_quiz_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.start_url(self.quiz.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        
        self.assertIn('session_id', response.data['data'])
        self.assertEqual(response.data['data']['quiz_title'], "Python Basics")
        
        questions = response.data['data']['questions']
        # Verification: Checks that exactly 10 random unique questions were picked
        self.assertEqual(len(questions), 10)
        
        # Verify no correct answer info leaks
        for q in questions:
            self.assertNotIn('correct_option', q)
            self.assertIn('text', q)
            self.assertIn('option_1', q)
            self.assertIn('option_2', q)
            self.assertIn('option_3', q)
            self.assertIn('option_4', q)

        # Verify QuizSession is created with 10 questions linked ManyToMany
        session_id = response.data['data']['session_id']
        session = QuizSession.objects.get(id=session_id)
        self.assertEqual(session.questions.count(), 10)
        self.assertFalse(session.is_completed)

    def test_start_quiz_resumes_existing_session(self):
        self.client.force_authenticate(user=self.user)
        
        # Call start first time
        r1 = self.client.get(self.start_url(self.quiz.id))
        session_id_1 = r1.data['data']['session_id']
        questions_1 = [q['id'] for q in r1.data['data']['questions']]
        
        # Call start second time
        r2 = self.client.get(self.start_url(self.quiz.id))
        session_id_2 = r2.data['data']['session_id']
        questions_2 = [q['id'] for q in r2.data['data']['questions']]
        
        # Verify it returns the same session and questions list
        self.assertEqual(session_id_1, session_id_2)
        self.assertEqual(questions_1, questions_2)
        self.assertEqual(QuizSession.objects.filter(user=self.user, quiz=self.quiz).count(), 1)

    def test_submit_quiz_success(self):
        self.client.force_authenticate(user=self.user)
        
        # Start the quiz session to get 10 random questions
        start_res = self.client.get(self.start_url(self.quiz.id))
        session_id = start_res.data['data']['session_id']
        session = QuizSession.objects.get(id=session_id)
        assigned_questions = list(session.questions.all())
        
        # Formulate answers payload: make 5 correct and 5 incorrect
        answers_payload = []
        expected_score = 0
        
        for idx, question in enumerate(assigned_questions):
            if idx < 5:
                # Correct choice
                selected_option = question.correct_option
                expected_score += 1
            else:
                # Incorrect choice (make sure it differs from correct_option)
                selected_option = (question.correct_option % 4) + 1
            
            answers_payload.append({
                "question_id": question.id,
                "selected_option": selected_option
            })
            
        submit_payload = {"answers": answers_payload}
        response = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        
        # Verify calculations
        self.assertEqual(response.data['data']['score'], expected_score)
        self.assertEqual(response.data['data']['total_questions'], 10)
        self.assertEqual(response.data['data']['percentage'], round((expected_score / 10) * 100, 2))
        self.assertIn('results', response.data['data'])
        
        # Verify session is marked completed
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        self.assertEqual(session.score, expected_score)

    def test_submit_quiz_without_active_session(self):
        self.client.force_authenticate(user=self.user)
        
        # Post submission without doing a GET /start/ first
        submit_payload = {
            "answers": [
                {"question_id": self.q1.id if hasattr(self, 'q1') else 1, "selected_option": 1}
            ]
        }
        response = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertIn('message', response.data)

    def test_submit_quiz_invalid_question_id(self):
        self.client.force_authenticate(user=self.user)
        self.client.get(self.start_url(self.quiz.id))
        
        # Submit answer containing a question ID that doesn't exist
        submit_payload = {
            "answers": [
                {"question_id": 99999, "selected_option": 1}
            ]
        }
        response = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertIn('message', response.data)

    def test_submit_quiz_invalid_option_fails(self):
        self.client.force_authenticate(user=self.user)
        start_res = self.client.get(self.start_url(self.quiz.id))
        assigned_questions = start_res.data['data']['questions']
        
        # Submit an option outside of 1-4 bounds (e.g. 5)
        submit_payload = {
            "answers": [
                {"question_id": assigned_questions[0]['id'], "selected_option": 5}
            ]
        }
        response = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertIn('message', response.data)

    def test_submit_quiz_duplicate_question_id_fails(self):
        self.client.force_authenticate(user=self.user)
        start_res = self.client.get(self.start_url(self.quiz.id))
        assigned_questions = start_res.data['data']['questions']
        q_id = assigned_questions[0]['id']
        
        submit_payload = {
            "answers": [
                {"question_id": q_id, "selected_option": 1},
                {"question_id": q_id, "selected_option": 2}
            ]
        }
        response = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertIn('message', response.data)

    def test_submit_twice_fails(self):
        self.client.force_authenticate(user=self.user)
        start_res = self.client.get(self.start_url(self.quiz.id))
        assigned_questions = start_res.data['data']['questions']
        
        answers = [{"question_id": q['id'], "selected_option": 1} for q in assigned_questions]
        submit_payload = {"answers": answers}
        
        # First submission is success
        r1 = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.data['status'], True)
        
        # Second submission should fail because session is closed
        r2 = self.client.post(self.submit_url(self.quiz.id), submit_payload, format='json')
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r2.data['status'], False)
        self.assertIn('message', r2.data)
