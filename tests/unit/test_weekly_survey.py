import pytest
from datetime import date, timedelta
from src.models.weekly_survey_model import WeeklySurvey
from src.services.weekly_survey_service import WeeklySurveyService


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