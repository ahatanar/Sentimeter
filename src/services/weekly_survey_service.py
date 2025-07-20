from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from src.models.weekly_survey_model import WeeklySurvey
from src.models.user_model import User


class WeeklySurveyService:
    """Service for managing weekly surveys"""
    
    REQUIRED_FIELDS = ['stress', 'anxiety', 'depression', 'happiness', 'satisfaction']
    BOOLEAN_FIELDS = ['self_harm_thoughts', 'significant_sleep_issues']
    
    @staticmethod
    def calculate_week_start(target_date: date = None) -> date:
        """Calculate the Monday of the week for the given date (or today)"""
        if target_date is None:
            target_date = date.today()
        # Calculate days since Monday (0 = Monday, 6 = Sunday)
        days_since_monday = target_date.weekday()
        return target_date - timedelta(days=days_since_monday)
    
    @staticmethod
    def validate_survey_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean survey data"""
        # Validate required fields
        for field in WeeklySurveyService.REQUIRED_FIELDS:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            
            value = data[field]
            if not isinstance(value, int) or value < 1 or value > 5:
                raise ValueError(f"{field} must be an integer between 1 and 5")
        
        # Validate boolean fields
        for field in WeeklySurveyService.BOOLEAN_FIELDS:
            if field in data:
                if not isinstance(data[field], bool):
                    raise ValueError(f"{field} must be a boolean")
            else:
                data[field] = False  # Default to False
        
        # Remove week_start from validated data (it's handled separately)
        validated_data = {k: v for k, v in data.items() if k not in ['week_start']}
        
        return validated_data
    
    @classmethod
    def create_weekly_survey(cls, user_id: str, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new weekly survey for the user"""
        # Validate user exists
        user = User.find_by_google_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate and clean survey data
        validated_data = cls.validate_survey_data(survey_data)
        
        # Handle week_start override
        week_start = cls._determine_week_start(survey_data)
        
        # Check for existing survey for the specified week
        existing_survey = WeeklySurvey.find_by_user_and_week(user_id, week_start)
        if existing_survey:
            raise ValueError(f"You already logged this week ({week_start.strftime('%b %d')} - {week_start + timedelta(days=6):strftime('%b %d')}). Edit or view your entry in Insights.")
        
        # Create the survey
        survey = WeeklySurvey.create_survey(user_id, week_start, **validated_data)
        
        return {
            "status": "saved",
            "urgent": survey.urgent_flag,
            "week_start": survey.week_start.isoformat(),
            "week_range": f"{survey.week_start.strftime('%b %d')} - {(survey.week_start + timedelta(days=6)).strftime('%b %d')}",
            "survey_id": f"{survey.user_id}_{survey.week_start.isoformat()}"
        }
    
    @classmethod
    def get_user_surveys(cls, user_id: str, range_type: str = "last12", since_date: str = None) -> List[Dict[str, Any]]:
        """Get surveys for a user based on range parameters"""
        # Validate user exists
        user = User.find_by_google_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if since_date:
            # Get surveys since specific date
            try:
                since = datetime.strptime(since_date, "%Y-%m-%d").date()
                surveys = WeeklySurvey.get_user_surveys_since(user_id, since)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        else:
            # Get last 12 weeks (default)
            if range_type == "last12":
                surveys = WeeklySurvey.get_user_surveys(user_id, limit=12)
            else:
                raise ValueError("Invalid range type. Use 'last12' or provide 'since' parameter")
        
        # Convert to JSON-serializable format
        return [
            {
                "week_start": survey.week_start.isoformat(),
                "stress": survey.stress,
                "anxiety": survey.anxiety,
                "depression": survey.depression,
                "happiness": survey.happiness,
                "satisfaction": survey.satisfaction,
                "self_harm_thoughts": survey.self_harm_thoughts,
                "significant_sleep_issues": survey.significant_sleep_issues,
                "urgent_flag": survey.urgent_flag,
                "created_at": survey.created_at.isoformat() if survey.created_at else None
            }
            for survey in surveys
        ]
    
    @classmethod
    def check_survey_exists_this_week(cls, user_id: str) -> bool:
        """Check if user has already completed a survey this week"""
        week_start = cls.calculate_week_start()
        return WeeklySurvey.find_by_user_and_week(user_id, week_start) is not None

    @classmethod
    def _determine_week_start(cls, survey_data: Dict[str, Any]) -> date:
        """Determine the week_start based on override or current week"""
        # Check for week_start override
        if 'week_start' in survey_data:
            try:
                input_date = datetime.strptime(survey_data['week_start'], "%Y-%m-%d").date()
                
                # Convert any date to the Monday of that week
                week_start = cls.calculate_week_start(input_date)
                
                # Validate it's not in the future
                if week_start > date.today():
                    raise ValueError("Cannot create surveys for future weeks")
                
                return week_start
            except ValueError as e:
                # Handle date parsing errors
                raise ValueError("Invalid week_start format. Use YYYY-MM-DD")
        
        # Default to current week
        return cls.calculate_week_start()

    @classmethod
    def get_missing_weeks(cls, user_id: str, weeks_back: int = 8) -> List[str]:
        """Get list of missing weeks for the user (for week picker)"""
        today = date.today()
        missing_weeks = []
        
        # Generate last N weeks (excluding current week if it's not Sunday yet)
        for i in range(weeks_back):
            target_date = today - timedelta(weeks=i)
            week_start = cls.calculate_week_start(target_date)
            
            # Skip current week if it's not Sunday yet
            if i == 0 and today.weekday() < 6:  # Not Sunday
                continue
            
            # Check if survey exists for this week
            existing_survey = WeeklySurvey.find_by_user_and_week(user_id, week_start)
            if not existing_survey:
                missing_weeks.append(week_start.isoformat())
        
        return missing_weeks 