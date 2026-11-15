from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError

def calculate_age(born, today=None):
    """Accurately calculate age handling leap years and birthday anniversaries."""
    if not born:
        return 0
    if today is None:
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def validate_age_18_plus(dob, today=None):
    """Validates that a date of birth is not in the future and represents someone at least 18 years old."""
    if not dob:
        raise ValidationError("Date of birth is required.")
    if today is None:
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    if dob > today:
        raise ValidationError("Date of birth cannot be in the future.")
    age = calculate_age(dob, today)
    if age < 18:
        raise ValidationError("You must be 18 years or older to register.")
    return True

