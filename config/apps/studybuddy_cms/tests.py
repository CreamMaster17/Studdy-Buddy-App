# Run:
# python manage.py test apps.studybuddy_cms

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

from apps.studybuddy_cms.services.gemini_service import (
    summarize_notes,
    generate_flashcards,
    generate_quiz,
)


User = get_user_model()


# ============================================================
# API ENDPOINT TESTS
# ============================================================

class StudyToolsAPITest(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="teststudent",
            password="password123"
        )

        self.client.force_authenticate(
            user=self.user
        )


    @patch(
        "apps.studybuddy_cms.views.summarize_notes"
    )
    def test_summary_endpoint(self, mock_summary):

        mock_summary.return_value = {
            "title": "Photosynthesis",

            "topics": [
                {
                    "heading": "Process",

                    "points": [
                        "Plants convert sunlight into energy."
                    ]
                }
            ],

            "key_takeaways": [
                "Sunlight is required."
            ]
        }


        response = self.client.post(
            "/api/study-tools/summarize/",
            {
                "text": "Plants use sunlight."
            },
            format="json"
        )

        print(response.data)


        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )


        self.assertEqual(
            response.data["title"],
            "Photosynthesis"
        )


        self.assertTrue(
            len(response.data["topics"]) > 0
        )



    @patch(
        "apps.studybuddy_cms.views.generate_flashcards"
    )
    def test_flashcards_endpoint(self, mock_flashcards):

        mock_flashcards.return_value = {
            "flashcards": [
                {
                    "question": "What is ATP?",
                    "answer": "Energy molecule."
                }
            ]
        }


        response = self.client.post(
            "/api/study-tools/flashcards/",
            {
                "text": "ATP stores energy."
            },
            format="json"
        )


        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )


        self.assertTrue(
            len(response.data["flashcards"]) > 0
        )


        self.assertEqual(
            response.data["flashcards"][0]["question"],
            "What is ATP?"
        )



    @patch(
        "apps.studybuddy_cms.views.generate_quiz"
    )
    def test_quiz_endpoint(self, mock_quiz):

        mock_quiz.return_value = {
            "quiz": [
                {
                    "question": "Where does photosynthesis occur?",

                    "choices": [
                        "Nucleus",
                        "Chloroplast",
                        "Mitochondria",
                        "Ribosome"
                    ],

                    "answer": "Chloroplast"
                }
            ]
        }


        response = self.client.post(
            "/api/study-tools/quiz/",
            {
                "text": "Photosynthesis notes."
            },
            format="json"
        )


        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )


        self.assertTrue(
            len(response.data["quiz"]) > 0
        )


        quiz_question = response.data["quiz"][0]


        self.assertIn(
            "question",
            quiz_question
        )


        self.assertIn(
            quiz_question["answer"],
            quiz_question["choices"]
        )



    def test_empty_text_returns_error(self):

        response = self.client.post(
            "/api/study-tools/summarize/",
            {
                "text": ""
            },
            format="json"
        )


        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


        self.assertIn(
            "error",
            response.data
        )



# ============================================================
# GEMINI SERVICE TESTS
# ============================================================

class GeminiServiceTests(TestCase):

    """
    Tests Gemini JSON parsing and service output.
    """


    @patch(
        "apps.studybuddy_cms.services.gemini_service.get_client"
    )
    def test_summary_returns_expected_json(self, mock_client):

        mock_response = type(
            "Response",
            (),
            {
                "text": """
                {
                    "title": "Photosynthesis",

                    "topics": [
                        {
                            "heading": "Process",

                            "points": [
                                "Plants convert sunlight into energy."
                            ]
                        }
                    ],

                    "key_takeaways": [
                        "Photosynthesis requires sunlight."
                    ]
                }
                """
            }
        )


        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )


        result = summarize_notes(
            "Plants use sunlight to create energy."
        )


        self.assertEqual(
            result["title"],
            "Photosynthesis"
        )


        self.assertEqual(
            result["topics"][0]["heading"],
            "Process"
        )


        self.assertEqual(
            result["topics"][0]["points"][0],
            "Plants convert sunlight into energy."
        )


        self.assertEqual(
            result["key_takeaways"][0],
            "Photosynthesis requires sunlight."
        )



    @patch(
        "apps.studybuddy_cms.services.gemini_service.get_client"
    )
    def test_flashcards_returns_expected_json(self, mock_client):

        mock_response = type(
            "Response",
            (),
            {
                "text": """
                {
                    "flashcards": [
                        {
                            "question": "What is ATP?",
                            "answer": "Energy molecule used by cells."
                        }
                    ]
                }
                """
            }
        )


        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )


        result = generate_flashcards(
            "ATP provides energy for cells."
        )


        self.assertEqual(
            result["flashcards"][0]["question"],
            "What is ATP?"
        )


        self.assertEqual(
            result["flashcards"][0]["answer"],
            "Energy molecule used by cells."
        )



    @patch(
        "apps.studybuddy_cms.services.gemini_service.get_client"
    )
    def test_quiz_returns_expected_json(self, mock_client):

        mock_response = type(
            "Response",
            (),
            {
                "text": """
                {
                    "quiz": [
                        {
                            "question": "Where does photosynthesis occur?",

                            "choices": [
                                "Nucleus",
                                "Chloroplast",
                                "Mitochondria",
                                "Ribosome"
                            ],

                            "answer": "Chloroplast"
                        }
                    ]
                }
                """
            }
        )


        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )


        result = generate_quiz(
            "Photosynthesis occurs in chloroplasts."
        )


        quiz = result["quiz"][0]


        self.assertEqual(
            quiz["question"],
            "Where does photosynthesis occur?"
        )


        self.assertIn(
            "Chloroplast",
            quiz["choices"]
        )


        self.assertEqual(
            quiz["answer"],
            "Chloroplast"
        )



    @patch(
        "apps.studybuddy_cms.services.gemini_service.get_client"
    )
    def test_invalid_json_raises_error(self, mock_client):

        mock_response = type(
            "Response",
            (),
            {
                "text": "This is not JSON"
            }
        )


        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )


        with self.assertRaises(ValueError):

            summarize_notes(
                "Some notes"
            )