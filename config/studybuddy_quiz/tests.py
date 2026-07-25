"""
Unit tests for quiz generation, history, stats, and recommendations
Author: Samuel Gamon

Run: python manage.py test studybuddy_quiz
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import QuizQuestionResult, QuizResult
from .quiz_generator import (
    QUIZ_GENERATION_PROMPT,
    _parse_ai_response,
    grade_quiz_submission,
)
from .quiz_history import get_user_quiz_history, get_user_quiz_stats, save_quiz_result
from .study_recommendations import (
    _build_recommendation_prompt,
    _parse_recommendations,
    _variance_to_consistency,
    check_rate_limit,
    reset_rate_limit,
)
from .study_stats import _calculate_progress, _empty_stats, get_user_dashboard_stats


class TestQuizGenerator(TestCase):
    def test_parse_ai_response_with_markdown(self):
        md_response = '```json\n{"quiz_title": "Test", "questions": []}\n```'
        result = _parse_ai_response(md_response)
        self.assertIsNotNone(result)
        self.assertEqual(result["quiz_title"], "Test")

    def test_parse_ai_response_raw_json(self):
        raw = '{"quiz_title": "Raw Test", "total_questions": 2, "questions": []}'
        result = _parse_ai_response(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result["quiz_title"], "Raw Test")

    def test_parse_ai_response_invalid(self):
        self.assertIsNone(_parse_ai_response("This is not JSON at all"))

    def test_parse_ai_response_empty(self):
        self.assertIsNone(_parse_ai_response(None))
        self.assertIsNone(_parse_ai_response(""))

    def test_grade_quiz_all_correct(self):
        quiz_data = {
            "questions": [
                {
                    "question_id": 1,
                    "question_text": "Q1?",
                    "correct_answer": "A",
                    "explanation": "E1",
                },
                {
                    "question_id": 2,
                    "question_text": "Q2?",
                    "correct_answer": "B",
                    "explanation": "E2",
                },
                {
                    "question_id": 3,
                    "question_text": "Q3?",
                    "correct_answer": "C",
                    "explanation": "E3",
                },
            ]
        }
        result = grade_quiz_submission(quiz_data, {"1": "A", "2": "B", "3": "C"})
        self.assertEqual(result["correct_count"], 3)
        self.assertEqual(result["incorrect_count"], 0)
        self.assertEqual(result["score_percentage"], 100.0)

    def test_grade_quiz_mixed(self):
        quiz_data = {
            "questions": [
                {
                    "question_id": 1,
                    "question_text": "Q1?",
                    "correct_answer": "A",
                    "explanation": "E1",
                },
                {
                    "question_id": 2,
                    "question_text": "Q2?",
                    "correct_answer": "B",
                    "explanation": "E2",
                },
                {
                    "question_id": 3,
                    "question_text": "Q3?",
                    "correct_answer": "C",
                    "explanation": "E3",
                },
                {
                    "question_id": 4,
                    "question_text": "Q4?",
                    "correct_answer": "D",
                    "explanation": "E4",
                },
            ]
        }
        result = grade_quiz_submission(
            quiz_data, {"1": "A", "2": "B", "3": "A", "4": "D"}
        )
        self.assertEqual(result["correct_count"], 3)
        self.assertEqual(result["incorrect_count"], 1)
        self.assertEqual(result["score_percentage"], 75.0)

    def test_grade_quiz_unanswered(self):
        quiz_data = {
            "questions": [
                {
                    "question_id": 1,
                    "question_text": "Q1?",
                    "correct_answer": "A",
                    "explanation": "E1",
                },
                {
                    "question_id": 2,
                    "question_text": "Q2?",
                    "correct_answer": "B",
                    "explanation": "E2",
                },
            ]
        }
        result = grade_quiz_submission(quiz_data, {"1": "A"})
        self.assertEqual(result["correct_count"], 1)
        self.assertEqual(result["unanswered_count"], 1)
        self.assertEqual(result["score_percentage"], 50.0)

    def test_grade_quiz_case_insensitive(self):
        quiz_data = {
            "questions": [
                {
                    "question_id": 1,
                    "question_text": "Q1?",
                    "correct_answer": "a",
                    "explanation": "E1",
                }
            ]
        }
        result = grade_quiz_submission(quiz_data, {"1": "A"})
        self.assertEqual(result["correct_count"], 1)
        self.assertTrue(result["question_results"][0]["is_correct"])

    def test_grade_quiz_invalid_data(self):
        result = grade_quiz_submission(None, {})
        self.assertIn("error", result)

    def test_quiz_prompt_format(self):
        prompt = QUIZ_GENERATION_PROMPT.format(
            num_questions=5, notes="Test notes about biology"
        )
        self.assertIn("5", prompt)
        self.assertIn("Test notes about biology", prompt)
        self.assertIn("JSON", prompt)


class TestQuizHistory(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sam", password="testpass")

    def test_save_and_list_history(self):
        save = save_quiz_result(
            user=self.user,
            quiz_title="Biology - Cell Structure",
            score_percentage=80.0,
            correct_count=4,
            total_questions=5,
            question_results=[
                {
                    "question_id": 1,
                    "question_text": "What is the powerhouse of the cell?",
                    "user_answer": "B",
                    "correct_answer": "B",
                    "is_correct": True,
                    "explanation": "Mitochondria.",
                }
            ],
        )
        self.assertTrue(save["success"])
        self.assertEqual(QuizResult.objects.filter(user=self.user).count(), 1)
        self.assertEqual(QuizQuestionResult.objects.count(), 1)

        history = get_user_quiz_history(self.user)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["quiz_title"], "Biology - Cell Structure")
        self.assertEqual(history[0]["score_percentage"], 80.0)

    def test_new_user_empty_stats(self):
        stats = get_user_quiz_stats(self.user)
        self.assertEqual(stats["total_quizzes"], 0)
        self.assertEqual(stats["average_score"], 0.0)


class TestStudyStats(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sam2", password="testpass")

    def test_empty_stats_structure(self):
        stats = _empty_stats()
        self.assertEqual(stats["overview"]["total_quizzes_taken"], 0)
        self.assertEqual(stats["progress_indicator"]["status"], "new")

    def test_dashboard_empty_user_safe(self):
        stats = get_user_dashboard_stats(self.user)
        self.assertEqual(stats["overview"]["total_quizzes_taken"], 0)
        self.assertEqual(stats["weekly_activity"]["quizzes_this_week"], 0)

    def test_dashboard_with_history(self):
        QuizResult.objects.create(
            user=self.user,
            quiz_title="Chemistry",
            score_percentage=60,
            correct_count=3,
            total_questions=5,
        )
        QuizResult.objects.create(
            user=self.user,
            quiz_title="Chemistry",
            score_percentage=80,
            correct_count=4,
            total_questions=5,
        )
        stats = get_user_dashboard_stats(self.user)
        self.assertEqual(stats["overview"]["total_quizzes_taken"], 2)
        self.assertEqual(len(stats["subject_breakdown"]), 1)
        self.assertTrue(len(stats["score_trend"]) >= 1)

    def test_calculate_progress_improving(self):
        scores = [
            {"score": 60},
            {"score": 65},
            {"score": 70},
            {"score": 80},
            {"score": 85},
            {"score": 90},
        ]
        progress = _calculate_progress(scores)
        self.assertEqual(progress["trend_direction"], "up")


class TestStudyRecommendations(TestCase):
    def test_parse_recommendations_standard_format(self):
        ai_text = """RECOMMENDATION 1: Review Cell Biology
Focus on studying the structure and function of cellular organelles.

RECOMMENDATION 2: Practice More Quizzes
Take additional quizzes to reinforce your understanding.

FOCUS AREA: Cell Biology
WHY: This is your lowest scoring subject at 45%."""
        result = _parse_recommendations(ai_text)
        self.assertIsNotNone(result)
        self.assertTrue(len(result["recommendations"]) >= 1)
        self.assertEqual(result["focus_area"]["topic"], "Cell Biology")

    def test_parse_recommendations_empty(self):
        self.assertIsNone(_parse_recommendations(""))
        self.assertIsNone(_parse_recommendations(None))

    def test_variance_to_consistency(self):
        self.assertEqual(_variance_to_consistency(5), "very_consistent")
        self.assertEqual(_variance_to_consistency(15), "consistent")
        self.assertEqual(_variance_to_consistency(25), "variable")
        self.assertEqual(_variance_to_consistency(35), "inconsistent")
        self.assertEqual(_variance_to_consistency(None), "unknown")

    def test_rate_limiter(self):
        reset_rate_limit(999)
        self.assertTrue(check_rate_limit(999))
        self.assertFalse(check_rate_limit(999))
        reset_rate_limit(999)

    def test_build_recommendation_prompt_structure(self):
        history = {
            "overall_stats": {
                "total_quizzes": 5,
                "average_score": 75.0,
                "last_quiz_date": "2025-07-01",
            },
            "subject_performance": [
                {"subject": "Biology", "times_taken": 3, "average_score": 80.0}
            ],
            "recent_quizzes": [
                {
                    "subject": "Biology",
                    "score": 85.0,
                    "correct": 4,
                    "total": 5,
                    "date": "2025-07-01",
                }
            ],
            "weak_areas": [{"subject": "Chemistry", "average_score": 60.0}],
            "strong_areas": [{"subject": "Biology", "average_score": 90.0}],
        }
        prompt = _build_recommendation_prompt(history)
        self.assertIn("Biology", prompt)
        self.assertIn("Chemistry", prompt)
        self.assertIn("RECOMMENDATION", prompt)
        self.assertIn("FOCUS AREA", prompt)


class TestQuizAPIIntegration(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="testpass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_history_list_empty_for_new_user(self):
        response = self.client.get("/api/history/list")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["history"], [])

    def test_stats_dashboard_empty_for_new_user(self):
        response = self.client.get("/api/stats/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overview"]["total_quizzes_taken"], 0)

    def test_save_history_endpoint(self):
        response = self.client.post(
            "/api/history/save",
            {
                "quiz_title": "World History",
                "score_percentage": 100.0,
                "correct_count": 5,
                "total_questions": 5,
                "question_results": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

    def test_grade_without_quiz_returns_400(self):
        response = self.client.post(
            "/api/quiz/grade",
            {"answers": {"1": "A"}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_full_quiz_flow_grade_logic(self):
        quiz_data = {
            "quiz_title": "Test Quiz",
            "questions": [
                {
                    "question_id": 1,
                    "question_text": "What is 2+2?",
                    "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
                    "correct_answer": "B",
                    "explanation": "2+2 equals 4.",
                },
                {
                    "question_id": 2,
                    "question_text": "Capital of France?",
                    "options": {
                        "A": "London",
                        "B": "Berlin",
                        "C": "Paris",
                        "D": "Madrid",
                    },
                    "correct_answer": "C",
                    "explanation": "Paris.",
                },
            ],
        }
        session = self.client.session
        session["last_generated_quiz"] = quiz_data
        session.save()

        response = self.client.post(
            "/api/quiz/submit-and-save",
            {"answers": {"1": "B", "2": "C"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score_percentage"], 100.0)
        self.assertTrue(response.data["saved_to_history"]["success"])
        self.assertEqual(QuizResult.objects.filter(user=self.user).count(), 1)
