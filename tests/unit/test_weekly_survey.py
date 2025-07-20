import pytest
from datetime import date, timedelta
from src.models.weekly_survey_model import WeeklySurvey
from src.services.weekly_survey_service import WeeklySurveyService
from unittest.mock import patch, MagicMock


class TestWeeklySurveyModel:
    """Test WeeklySurvey model functionality"""
    
    def test_compute_urgent_flag_self_harm(self):
        """Test urgent flag when self_harm_thoughts is True"""
        survey = WeeklySurvey(
            user_id="test_user",
            week_start=date.today(),
            stress=1,
            anxiety=1,
            depression=1,
            happiness=5,
            satisfaction=5,
            self_harm_thoughts=True,
            significant_sleep_issues=False
        )
        assert survey.compute_urgent_flag() is True
    
    def test_compute_urgent_flag_high_depression(self):
        """Test urgent flag when depression >= 4"""
        survey = WeeklySurvey(
            user_id="test_user",
            week_start=date.today(),
            stress=1,
            anxiety=1,
            depression=4,
            happiness=1,
            satisfaction=1,
            self_harm_thoughts=False,
            significant_sleep_issues=False
        )
        assert survey.compute_urgent_flag() is True
    
    def test_compute_urgent_flag_high_anxiety(self):
        """Test urgent flag when anxiety >= 4"""
        survey = WeeklySurvey(
            user_id="test_user",
            week_start=date.today(),
            stress=1,
            anxiety=4,
            depression=1,
            happiness=1,
            satisfaction=1,
            self_harm_thoughts=False,
            significant_sleep_issues=False
        )
        assert survey.compute_urgent_flag() is True
    
    def test_compute_urgent_flag_normal(self):
        """Test urgent flag when all values are normal"""
        survey = WeeklySurvey(
            user_id="test_user",
            week_start=date.today(),
            stress=2,
            anxiety=2,
            depression=2,
            happiness=4,
            satisfaction=4,
            self_harm_thoughts=False,
            significant_sleep_issues=False
        )
        assert survey.compute_urgent_flag() is False


class TestWeeklySurveyService:
    """Test WeeklySurveyService functionality"""
    
    def test_calculate_week_start_monday(self):
        """Test week start calculation for Monday"""
        monday = date(2024, 1, 1)  # This is a Monday
        week_start = WeeklySurveyService.calculate_week_start(monday)
        assert week_start == monday
    
    def test_calculate_week_start_wednesday(self):
        """Test week start calculation for Wednesday"""
        wednesday = date(2024, 1, 3)  # This is a Wednesday
        expected_monday = date(2024, 1, 1)
        week_start = WeeklySurveyService.calculate_week_start(wednesday)
        assert week_start == expected_monday
    
    def test_calculate_week_start_sunday(self):
        """Test week start calculation for Sunday"""
        sunday = date(2024, 1, 7)  # This is a Sunday
        expected_monday = date(2024, 1, 1)
        week_start = WeeklySurveyService.calculate_week_start(sunday)
        assert week_start == expected_monday

    def test_determine_week_start_current_week(self):
        """Test week start determination defaults to current week"""
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }
        week_start = WeeklySurveyService._determine_week_start(data)
        expected = WeeklySurveyService.calculate_week_start()
        assert week_start == expected

    def test_determine_week_start_override_valid(self):
        """Test week start determination with valid override"""
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "week_start": "2024-01-01"  # Monday
        }
        week_start = WeeklySurveyService._determine_week_start(data)
        assert week_start == date(2024, 1, 1)

    def test_determine_week_start_override_not_monday(self):
        """Test week start determination with non-Monday override (should convert to Monday)"""
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "week_start": "2024-01-02"  # Tuesday
        }
        week_start = WeeklySurveyService._determine_week_start(data)
        # Should convert Tuesday to Monday of that week
        expected_monday = date(2024, 1, 1)  # Monday of that week
        assert week_start == expected_monday

    def test_determine_week_start_override_future(self):
        """Test week start determination with future date"""
        # Use a future Monday to test the future date validation
        future_monday = (date.today() + timedelta(days=7))
        # Adjust to next Monday if today is not Monday
        while future_monday.weekday() != 0:
            future_monday += timedelta(days=1)
        
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "week_start": future_monday.strftime("%Y-%m-%d")
        }
        with pytest.raises(ValueError, match="Cannot create surveys for future weeks"):
            WeeklySurveyService._determine_week_start(data)
    
    def test_validate_survey_data_valid(self):
        """Test validation of valid survey data"""
        valid_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "self_harm_thoughts": False,
            "significant_sleep_issues": True
        }
        validated = WeeklySurveyService.validate_survey_data(valid_data)
        assert validated == valid_data
    
    def test_validate_survey_data_missing_field(self):
        """Test validation fails with missing required field"""
        invalid_data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4
            # Missing satisfaction
        }
        with pytest.raises(ValueError, match="Missing required field: satisfaction"):
            WeeklySurveyService.validate_survey_data(invalid_data)
    
    def test_validate_survey_data_invalid_range(self):
        """Test validation fails with invalid range"""
        invalid_data = {
            "stress": 6,  # Should be 1-5
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }
        with pytest.raises(ValueError, match="stress must be an integer between 1 and 5"):
            WeeklySurveyService.validate_survey_data(invalid_data)
    
    def test_validate_survey_data_defaults_booleans(self):
        """Test that boolean fields default to False when not provided"""
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4
        }
        validated = WeeklySurveyService.validate_survey_data(data)
        assert validated["self_harm_thoughts"] is False
        assert validated["significant_sleep_issues"] is False

    def test_validate_survey_data_removes_week_start(self):
        """Test that week_start is removed from validated data"""
        data = {
            "stress": 3,
            "anxiety": 2,
            "depression": 1,
            "happiness": 4,
            "satisfaction": 4,
            "week_start": "2024-01-01"
        }
        validated = WeeklySurveyService.validate_survey_data(data)
        assert "week_start" not in validated
        assert validated["stress"] == 3


class TestWeeklySurveySummary:
    """Test WeeklySurvey summary functionality"""
    
    @patch('src.services.weekly_survey_service.User.find_by_google_id')
    @patch('src.services.weekly_survey_service.db.session.query')
    def test_get_survey_summary_success(self, mock_query, mock_find_user):
        """Test successful survey summary generation"""
        # Mock user
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        
        # Mock survey data - using dates that match the week calculation
        # For 2 weeks starting from Jan 8, 2024 (when today is Jan 15)
        mock_survey1 = MagicMock()
        mock_survey1.week_start = date(2024, 1, 8)  # First week in range
        mock_survey1.stress = 3
        mock_survey1.anxiety = 2
        mock_survey1.depression = 1
        mock_survey1.happiness = 4
        mock_survey1.satisfaction = 4
        mock_survey1.urgent_flag = False
        mock_survey1.significant_sleep_issues = False
        
        mock_survey2 = MagicMock()
        mock_survey2.week_start = date(2024, 1, 15)  # Second week in range
        mock_survey2.stress = 2
        mock_survey2.anxiety = 1
        mock_survey2.depression = 1
        mock_survey2.happiness = 5
        mock_survey2.satisfaction = 5
        mock_survey2.urgent_flag = False
        mock_survey2.significant_sleep_issues = False
        
        # Mock query chain
        mock_query_instance = MagicMock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_survey1, mock_survey2]
        mock_query.return_value = mock_query_instance
        
        with patch('src.services.weekly_survey_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            
            result = WeeklySurveyService.get_survey_summary("test_user", 2)
            
            assert "weeks" in result
            assert "computed" in result
            assert len(result["weeks"]) == 2
            # With 2 surveys, we expect the average to be calculated correctly
            # First survey: happiness=4, satisfaction=4, stress=3, anxiety=2
            # Second survey: happiness=5, satisfaction=5, stress=2, anxiety=1
            # Averages: happiness=4.5, satisfaction=4.5, stress=2.5, anxiety=1.5
            assert result["computed"]["avg_happiness"] == 4.5
            assert result["computed"]["avg_satisfaction"] == 4.5
            assert result["computed"]["avg_stress"] == 2.5
            assert result["computed"]["avg_anxiety"] == 1.5
            assert result["computed"]["streak_weeks"] == 2
            assert result["computed"]["high_alerts"] == 0
            assert result["computed"]["completion_rate"] == 100
    
    @patch('src.services.weekly_survey_service.User.find_by_google_id')
    def test_get_survey_summary_user_not_found(self, mock_find_user):
        """Test survey summary with non-existent user"""
        mock_find_user.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            WeeklySurveyService.get_survey_summary("nonexistent_user", 12)
    
    @patch('src.services.weekly_survey_service.User.find_by_google_id')
    @patch('src.services.weekly_survey_service.db.session.query')
    def test_get_survey_summary_with_missing_weeks(self, mock_query, mock_find_user):
        """Test survey summary with missing weeks (nulls)"""
        # Mock user
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        
        # Mock only one survey (missing week) - using correct date
        mock_survey = MagicMock()
        mock_survey.week_start = date(2024, 1, 8)  # First week in range
        mock_survey.stress = 3
        mock_survey.anxiety = 2
        mock_survey.depression = 1
        mock_survey.happiness = 4
        mock_survey.satisfaction = 4
        mock_survey.urgent_flag = False
        mock_survey.significant_sleep_issues = False
        
        # Mock query chain
        mock_query_instance = MagicMock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_survey]
        mock_query.return_value = mock_query_instance
        
        with patch('src.services.weekly_survey_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            
            result = WeeklySurveyService.get_survey_summary("test_user", 2)
            
            assert len(result["weeks"]) == 2
            # Check that we have one week with data and one with nulls
            filled_weeks = [w for w in result["weeks"] if w["stress"] is not None]
            null_weeks = [w for w in result["weeks"] if w["stress"] is None]
            assert len(filled_weeks) == 1
            assert len(null_weeks) == 1
            # Streak should be 0 since the most recent week (Jan 15) has no data
            assert result["computed"]["streak_weeks"] == 0
            assert result["computed"]["completion_rate"] == 50
    
    @patch('src.services.weekly_survey_service.User.find_by_google_id')
    @patch('src.services.weekly_survey_service.db.session.query')
    def test_get_survey_summary_with_urgent_flags(self, mock_query, mock_find_user):
        """Test survey summary with urgent flags"""
        # Mock user
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        
        # Mock survey with urgent flag - using correct date for 1 week
        mock_survey = MagicMock()
        mock_survey.week_start = date(2024, 1, 15)  # Current week in range
        mock_survey.stress = 5
        mock_survey.anxiety = 5
        mock_survey.depression = 5
        mock_survey.happiness = 1
        mock_survey.satisfaction = 1
        mock_survey.urgent_flag = True
        mock_survey.significant_sleep_issues = True
        
        # Mock query chain
        mock_query_instance = MagicMock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_survey]
        mock_query.return_value = mock_query_instance
        
        with patch('src.services.weekly_survey_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            
            result = WeeklySurveyService.get_survey_summary("test_user", 1)
            
            # For 1 week, we should have exactly one week with data
            assert len(result["weeks"]) == 1
            data_week = result["weeks"][0]
            assert data_week["stress"] is not None
            assert data_week["urgent"] is True
            assert data_week["sleep_issue"] is True
            assert result["computed"]["high_alerts"] == 1
    
    @patch('src.services.weekly_survey_service.User.find_by_google_id')
    @patch('src.services.weekly_survey_service.db.session.query')
    def test_get_survey_summary_no_surveys(self, mock_query, mock_find_user):
        """Test survey summary with no surveys"""
        # Mock user
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        
        # Mock empty survey list
        mock_query_instance = MagicMock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = []
        mock_query.return_value = mock_query_instance
        
        with patch('src.services.weekly_survey_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            
            result = WeeklySurveyService.get_survey_summary("test_user", 2)
            
            assert len(result["weeks"]) == 2
            assert result["weeks"][0]["stress"] is None
            assert result["weeks"][1]["stress"] is None
            assert result["computed"]["avg_happiness"] == 0
            assert result["computed"]["avg_satisfaction"] == 0
            assert result["computed"]["avg_stress"] == 0
            assert result["computed"]["avg_anxiety"] == 0
            assert result["computed"]["streak_weeks"] == 0
            assert result["computed"]["high_alerts"] == 0
            assert result["computed"]["completion_rate"] == 0 