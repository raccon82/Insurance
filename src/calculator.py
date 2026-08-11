"""
Age calculation logic supporting both Age Next Birthday (ANB) and Age Last Birthday (ALB) 
anchored to a fixed policy renewal date (e.g., Oct 1).
"""

from datetime import date


def calculate_age_last_birthday(dob: date, anchor_date: date) -> int:
    """
    Calculate Age Last Birthday (ALB) as of the policy renewal anchor date.
    ALB = Full years elapsed from DOB to anchor_date.
    """
    age = anchor_date.year - dob.year
    if (anchor_date.month, anchor_date.day) < (dob.month, dob.day):
        age -= 1
    return max(0, age)


def calculate_age_next_birthday(dob: date, anchor_date: date) -> int:
    """
    Calculate Age Next Birthday (ANB) as of the policy renewal anchor date.
    Standard insurance ANB convention:
    Age Last Birthday + 1 if the birthday has occurred more than 6 months ago 
    in the policy year, or alternatively age reached on the next birthday 
    anniversary in the policy year.
    Strictly: ALB + (1 if months elapsed since last birthday >= 6 else 0) 
    or simply: age on next birthday.
    Let's implement standard actuarial ANB:
    If the time between DOB and anchor_date has a remainder of >= 6 months, ANB = ALB + 1.
    Alternatively, calendar year minus birth year + 1 if birthday has not passed, or similar.
    We will use the precise actuarial definition:
    Calculate exact fractional age or months since last birthday.
    """
    alb = calculate_age_last_birthday(dob, anchor_date)
    
    # Check exact date difference
    # Find the birthday in the anchor year or previous year
    birthday_this_year = date(anchor_date.year, dob.month, dob.day)
    if birthday_this_year > anchor_date:
        # Birthday hasn't happened yet this calendar year
        last_birthday = date(anchor_date.year - 1, dob.month, dob.day)
    else:
        last_birthday = birthday_this_year
        
    # Months elapsed since last birthday
    months_elapsed = (anchor_date.year - last_birthday.year) * 12 + (anchor_date.month - last_birthday.month)
    if anchor_date.day < last_birthday.day:
        months_elapsed -= 1
        
    # In insurance ANB, if months elapsed >= 6, age rounds up to next birthday (ALB + 1)
    # Or more commonly in group insurance rate tables (like Singlife), ANB = ALB + 1 if past 6 months.
    if months_elapsed >= 6:
        return alb + 1
    else:
        return alb


def calculate_member_age(dob: date, method: str = "ALB", anchor_date: date = date(2026, 10, 1)) -> int:
    """
    Dispatcher for age calculation based on method ('ALB' or 'ANB').
    """
    method = method.upper()
    if method == "ANB":
        return calculate_age_next_birthday(dob, anchor_date)
    else:
        return calculate_age_last_birthday(dob, anchor_date)
