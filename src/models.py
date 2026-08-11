"""
Data models, dataclasses, and validation schemas for members, rate tables, 
policy configurations, and comparison results.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
import pandas as pd


@dataclass
class Member:
    """Represents an employee/member insured under the corporate policy."""
    name: str
    dob: date
    gender: str  # 'M', 'F'
    occupation_class: int  # 1, 2, 3
    coverage_amount: float
    product_type: str  # e.g., 'Group Term Life', 'Group Living Care', 'Group Basic Medical', 'Group Major Medical', 'Group Personal Accident'
    plan_tier: str  # e.g., 'Plan 1', 'Plan 2', etc.
    id: Optional[str] = None


@dataclass
class RateTableEntry:
    """Represents a single row in an insurer rate sheet."""
    insurer: str
    product_type: str
    plan_tier: str
    age_min: int
    age_max: int
    gender: Optional[str] = None  # None or 'M'/'F' if gender-specific
    occupation_class: Optional[int] = None  # For GPA
    coverage_amount: float = 0.0
    annual_premium: float = 0.0


@dataclass
class ComparisonResult:
    """Represents the pricing and underwriting result for a member against an insurer."""
    member_name: str
    product_type: str
    plan_tier: str
    insurer: str
    age: int
    age_calculation_type: str  # 'ANB' or 'ALB'
    coverage_amount: float
    base_premium: float
    occ_multiplier: float
    adjusted_base_premium: float
    gst_rate: float
    gst_amount: float
    total_premium: float
    underwriting_flag: str  # 'Standard', 'Subject to Underwriting', 'Rate Not Found'
    error_message: Optional[str] = None


@dataclass
class PolicyConfiguration:
    """Global policy configuration parameters."""
    renewal_year: int = 2026
    renewal_anchor_date: date = date(2026, 10, 1)  # e.g. Oct 1
    age_calculation_method: str = "ALB"  # 'ALB' or 'ANB'
    gst_percentage: float = 9.0  # Prevailing Singapore GST e.g. 9%
    nel_limit_gtl_glc: float = 150000.0  # Non-Evidence Limit for GTL/GLC
