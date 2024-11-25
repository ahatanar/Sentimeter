# tests/test_quiz.py
# from unittest.mock import patch, MagicMock
# from src.services.quiz_service import QuizService


# # Test for creating a new quiz
# @patch.object(QuizService, "create_quiz")
# def test_create_quiz(mock_create_quiz, client):
#     mock_create_quiz.return_value = 1
#     response = client.post(
#         "/api/quizzes", json={"title": "New Quiz", "questions": ["Q1", "Q2"]}
#     )
#     assert response.status_code == 201
#     assert response.json["id"] == 1
#     mock_create_quiz.assert_called_once()


# @patch.object(QuizService, "get_quiz")
# def test_get_quiz(mock_get_quiz, client):
#     mock_quiz = MagicMock()
#     mock_quiz.title = "Sample Quiz"
#     mock_quiz.questions = ["Q1", "Q2"]
#     mock_get_quiz.return_value = mock_quiz
#     response = client.get("/api/quizzes/1")
#     assert response.status_code == 200
#     assert response.json["title"] == "Sample Quiz"
#     mock_get_quiz.assert_called_once()


# @patch.object(QuizService, "evaluate_quiz")
# def test_submit_quiz(mock_evaluate_quiz, client):
#     mock_evaluate_quiz.return_value = (1, "Quiz evaluated successfully")
#     response = client.post(
#         "/api/quizzes/1/submit", json={"answers": ["A1", "A2"]}
#     )
#     assert response.status_code == 200
#     assert response.json["score"] == 1
#     assert response.json["message"] == "Quiz evaluated successfully"
#     mock_evaluate_quiz.assert_called_once()
