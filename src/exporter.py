"""
Excel export functionality using pandas and openpyxl, capturing member info, 
age brackets, per-insurer matched premiums, GST calculations, underwriting flags, and summary totals.
"""

import io
import pandas as pd
from typing import List
from src.models import ComparisonResult


def export_comparison_to_excel(results: List[ComparisonResult]) -> bytes:
    """
    Export comparison results to a professionally formatted Excel workbook in bytes.
    Includes:
    - Detailed Member Comparison Sheet
    - Summary by Insurer Sheet
    """
    output = io.BytesIO()
    
    # Convert results to DataFrame
    data = []
    for r in results:
        data.append({
            "Member Name": r.member_name,
            "Product Type": r.product_type,
            "Plan Tier": r.plan_tier,
            "Insurer": r.insurer,
            "Age": r.age,
            "Age Calc Type": r.age_calculation_type,
            "Coverage Amount": r.coverage_amount,
            "Base Premium (S$)": r.base_premium,
            "Occ Multiplier": r.occ_multiplier,
            "Adjusted Base Premium (S$)": r.adjusted_base_premium,
            "GST Rate (%)": r.gst_rate,
            "GST Amount (S$)": r.gst_amount,
            "Total Premium (S$)": r.total_premium,
            "Underwriting Flag": r.underwriting_flag,
            "Error Message": r.error_message or ""
        })
        
    df_results = pd.DataFrame(data)
    
    # Summary DataFrame grouped by Insurer
    if not df_results.empty:
        df_summary = df_results.groupby("Insurer").agg(
            Total_Members=("Member Name", "count"),
            Total_Base_Premium=("Adjusted Base Premium (S$)", "sum"),
            Total_GST=("GST Amount (S$)", "sum"),
            Total_Premium=("Total Premium (S$)", "sum"),
            Underwriting_Count=("Underwriting Flag", lambda x: (x == "Subject to Underwriting").sum()),
            Error_Count=("Underwriting Flag", lambda x: (x == "Rate Not Found").sum())
        ).reset_index()
    else:
        df_summary = pd.DataFrame(columns=["Insurer", "Total_Members", "Total_Base_Premium", "Total_GST", "Total_Premium", "Underwriting_Count", "Error_Count"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_results.to_excel(writer, sheet_name="Member Breakdown", index=False)
        df_summary.to_excel(writer, sheet_name="Insurer Summary", index=False)
        
    return output.getvalue()
