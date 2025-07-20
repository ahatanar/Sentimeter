import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.controllers.weekly_survey_controller import weekly_survey_bp


class TestWeeklySurveyRoutes(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.app.register_blueprint(weekly_survey_bp)
        self.jwt = JWTManager(self.app)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def get_jwt_headers(self, user_id):
        access_token = create_access_token(identity=user_id)
        return {'Authorization': f'Bearer {access_token}'}

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_success(self, mock_create_survey):
        """Test successful survey creation"""
        mock_create_survey.return_value = {
            "status": "saved",
            "urgent": False,
            "week_start": "2024-01-01",
            "survey_id": "test_user_2024-01-01"
        }

        survey_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "self_harm_thoughts": False,
            "significant_sleep_issues": False
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'saved')
        self.assertEqual(response.json['urgent'], False)
        mock_create_survey.assert_called_once_with('test_user', survey_data)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_urgent_flag(self, mock_create_survey):
        """Test survey creation with urgent flag"""
        mock_create_survey.return_value = {
            "status": "saved",
            "urgent": True,
            "week_start": "2024-01-01",
            "survey_id": "test_user_2024-01-01"
        }

        survey_data = {
            "stress": 3,
            "anxiety": 4,  # High anxiety triggers urgent flag
            "depression": 1,
            "happiness": 2,
            "satisfaction": 2,
            "self_harm_thoughts": False,
            "significant_sleep_issues": False
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['urgent'], True)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_duplicate_week(self, mock_create_survey):
        """Test survey creation with duplicate week error"""
        mock_create_survey.side_effect = ValueError("Survey already exists for this week")

        survey_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Survey already exists for this week')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_missing_data(self, mock_create_survey):
        """Test survey creation with missing required fields"""
        mock_create_survey.side_effect = ValueError("Missing required field: stress")

        survey_data = {
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
            # Missing stress field
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Missing required field: stress')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_invalid_range(self, mock_create_survey):
        """Test survey creation with invalid rating values"""
        mock_create_survey.side_effect = ValueError("stress must be an integer between 1 and 5")

        survey_data = {
            "stress": 6,  # Invalid: should be 1-5
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'stress must be an integer between 1 and 5')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_no_data(self, mock_create_survey):
        """Test survey creation with no data"""
        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json={}, headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Survey data is required')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_user_surveys')
    def test_get_weekly_surveys_success(self, mock_get_surveys):
        """Test successful retrieval of surveys"""
        mock_surveys = [
            {
                "week_start": "2024-01-01",
                "stress": 3,
                "anxiety": 2,
                "depression": 1,
                "happiness": 4,
                "satisfaction": 4,
                "self_harm_thoughts": False,
                "significant_sleep_issues": False,
                "urgent_flag": False,
                "created_at": "2024-01-01T10:00:00"
            },
            {
                "week_start": "2023-12-25",
                "stress": 2,
                "anxiety": 1,
                "depression": 1,
                "happiness": 5,
                "satisfaction": 5,
                "self_harm_thoughts": False,
                "significant_sleep_issues": False,
                "urgent_flag": False,
                "created_at": "2023-12-25T10:00:00"
            }
        ]
        mock_get_surveys.return_value = mock_surveys

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['surveys'], mock_surveys)
        mock_get_surveys.assert_called_once_with('test_user', 'last12', None)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_user_surveys')
    def test_get_weekly_surveys_with_since_param(self, mock_get_surveys):
        """Test retrieval of surveys with since parameter"""
        mock_surveys = [
            {
                "week_start": "2024-01-01",
                "stress": 3,
                "anxiety": 2,
                "depression": 1,
                "happiness": 4,
                "satisfaction": 4,
                "urgent_flag": False
            }
        ]
        mock_get_surveys.return_value = mock_surveys

        headers = self.get_jwt_headers('test_user')
        response = self.client.get(
            '/api/weekly-surveys?since=2024-01-01', headers=headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['surveys'], mock_surveys)
        mock_get_surveys.assert_called_once_with('test_user', 'last12', '2024-01-01')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_user_surveys')
    def test_get_weekly_surveys_invalid_date(self, mock_get_surveys):
        """Test retrieval with invalid date format"""
        mock_get_surveys.side_effect = ValueError("Invalid date format. Use YYYY-MM-DD")

        headers = self.get_jwt_headers('test_user')
        response = self.client.get(
            '/api/weekly-surveys?since=invalid-date', headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid date format. Use YYYY-MM-DD')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.check_survey_exists_this_week')
    def test_check_survey_exists_true(self, mock_check_exists):
        """Test checking if survey exists this week (exists)"""
        mock_check_exists.return_value = True

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/check', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['survey_exists_this_week'], True)
        mock_check_exists.assert_called_once_with('test_user')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.check_survey_exists_this_week')
    def test_check_survey_exists_false(self, mock_check_exists):
        """Test checking if survey exists this week (doesn't exist)"""
        mock_check_exists.return_value = False

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/check', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['survey_exists_this_week'], False)
        mock_check_exists.assert_called_once_with('test_user')

    def test_create_weekly_survey_no_auth(self):
        """Test survey creation without authentication"""
        survey_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }

        response = self.client.post('/api/weekly-surveys', json=survey_data)
        self.assertEqual(response.status_code, 401)

    def test_get_weekly_surveys_no_auth(self):
        """Test survey retrieval without authentication"""
        response = self.client.get('/api/weekly-surveys')
        self.assertEqual(response.status_code, 401)

    def test_check_survey_exists_no_auth(self):
        """Test survey existence check without authentication"""
        response = self.client.get('/api/weekly-surveys/check')
        self.assertEqual(response.status_code, 401)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_missing_weeks')
    def test_get_missing_weeks_success(self, mock_get_missing_weeks):
        """Test successful missing weeks retrieval"""
        mock_get_missing_weeks.return_value = ["2024-01-01", "2024-01-08"]

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/missing-weeks', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['missing_weeks'], ["2024-01-01", "2024-01-08"])
        mock_get_missing_weeks.assert_called_once_with('test_user')

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_missing_weeks')
    def test_get_missing_weeks_error(self, mock_get_missing_weeks):
        """Test missing weeks retrieval error"""
        mock_get_missing_weeks.side_effect = Exception("Database error")

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/missing-weeks', headers=headers)

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_survey_summary')
    def test_get_survey_summary_success(self, mock_get_summary):
        """Test successful survey summary retrieval"""
        mock_summary = {
            "weeks": [
                {
                    "week_start": "2024-01-01",
                    "label": "Jan 1",
                    "stress": 3,
                    "anxiety": 2,
                    "depression": 1,
                    "happiness": 4,
                    "satisfaction": 4,
                    "urgent": False,
                    "sleep_issue": False
                }
            ],
            "computed": {
                "avg_happiness": 4.0,
                "avg_satisfaction": 4.0,
                "avg_stress": 3.0,
                "avg_anxiety": 2.0,
                "streak_weeks": 1,
                "high_alerts": 0,
                "completion_rate": 100
            }
        }
        mock_get_summary.return_value = mock_summary

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/summary?weeks=12', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_summary)
        mock_get_summary.assert_called_once_with('test_user', 12)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_survey_summary')
    def test_get_survey_summary_default_weeks(self, mock_get_summary):
        """Test survey summary with default weeks parameter"""
        mock_get_summary.return_value = {"weeks": [], "computed": {}}

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/summary', headers=headers)

        self.assertEqual(response.status_code, 200)
        mock_get_summary.assert_called_once_with('test_user', 12)

    def test_get_survey_summary_invalid_weeks(self):
        """Test survey summary with invalid weeks parameter"""
        headers = self.get_jwt_headers('test_user')
        
        # Test weeks < 1
        response = self.client.get('/api/weekly-surveys/summary?weeks=0', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        
        # Test weeks > 52
        response = self.client.get('/api/weekly-surveys/summary?weeks=53', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_survey_summary')
    def test_get_survey_summary_error(self, mock_get_summary):
        """Test survey summary retrieval error"""
        mock_get_summary.side_effect = ValueError("User not found")

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/summary', headers=headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_get_survey_summary_unauthorized(self):
        """Test survey summary without authentication"""
        response = self.client.get('/api/weekly-surveys/summary')
        self.assertEqual(response.status_code, 401)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.get_survey_summary')
    def test_get_survey_summary_custom_weeks(self, mock_get_summary):
        """Test survey summary with custom weeks parameter"""
        mock_get_summary.return_value = {"weeks": [], "computed": {}}

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/weekly-surveys/summary?weeks=8', headers=headers)

        self.assertEqual(response.status_code, 200)
        mock_get_summary.assert_called_once_with('test_user', 8)

    @patch('src.services.weekly_survey_service.WeeklySurveyService.create_weekly_survey')
    def test_create_weekly_survey_with_week_override(self, mock_create_survey):
        """Test survey creation with week_start override"""
        mock_create_survey.return_value = {
            "status": "saved",
            "urgent": False,
            "week_start": "2024-01-01",
            "week_range": "Jan 01 - Jan 07",
            "survey_id": "test_user_2024-01-01"
        }

        survey_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "week_start": "2024-01-01"
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/weekly-surveys', json=survey_data, headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['week_range'], "Jan 01 - Jan 07")
        mock_create_survey.assert_called_once_with('test_user', survey_data) 