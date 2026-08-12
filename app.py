"""
Streamlit UI entry point for Corporate Insurance Premium & Benefit Comparison App.
Compares AIA, Singlife, Great Eastern, Raffles Health, and Tokio Marine across 
Group Hospital & Surgical benefit schedules and premium rate tables matching 
the Avallis Financial executive quotation style.
"""

import streamlit as st
import pandas as pd
from datetime import date
from typing import List

from src.models import Member, PolicyConfiguration
from src.pricing import get_sample_rate_tables, run_batch_comparison
from src.exporter import export_comparison_to_excel

st.set_page_config(
    page_title="Corporate Insurance Benefit & Premium Comparison",
    page_icon="🛡️",
    layout="wide"
)

def main():
    st.title("🛡️ Corporate Insurance Benefit & Premium Comparison Engine")
    st.markdown("Comparing benefit schedules and premium rates across **AIA**, **Singlife**, **Great Eastern**, **Raffles Health**, and **Tokio Marine** for **Life Bible Presbyterian Church** (Period: 01/10/2025 - 30/09/2026).")

    # Sidebar: Policy Configuration
    st.sidebar.header("1. Policy & Calculation Settings")
    renewal_year = st.sidebar.number_input("Policy Renewal Year", value=2025, step=1)
    renewal_month = st.sidebar.selectbox("Renewal Month", list(range(1, 13)), index=9) # October
    renewal_day = st.sidebar.number_input("Renewal Day", value=1, min_value=1, max_value=31)
    
    anchor_date = date(renewal_year, renewal_month, renewal_day)
    
    gst_pct = st.sidebar.number_input("Prevailing GST Rate (%)", value=9.0, step=0.5)
    nel_limit = st.sidebar.number_input("NEL Limit (S$)", value=150000.0, step=10000.0)
    
    policy_config = PolicyConfiguration(
        renewal_year=renewal_year,
        renewal_anchor_date=anchor_date,
        age_calculation_method="ALB",
        gst_percentage=gst_pct,
        nel_limit_gtl_glc=nel_limit
    )

    # Main Workflow Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Step 1: Member Census",
        "🏥 Step 2: Benefit Schedule Comparison (Avallis Style)",
        "📊 Step 3: Raffles Health Plans & Rates",
        "📈 Step 4: Tokio Marine Plans & Rates",
        "📥 Step 5: Export Report"
    ])

    if "members" not in st.session_state:
        st.session_state.members = [
            Member(name="John Tan", dob=date(1985, 4, 12), gender="M", occupation_class=1, coverage_amount=100000.0, product_type="Group Basic Medical", plan_tier="Plan 1"),
            Member(name="Alice Wong", dob=date(1992, 8, 25), gender="F", occupation_class=1, coverage_amount=50000.0, product_type="Group Major Medical", plan_tier="Plan 2A"),
            Member(name="David Lim", dob=date(1978, 11, 5), gender="M", occupation_class=2, coverage_amount=100000.0, product_type="Group Basic Medical", plan_tier="Plan 3"),
            Member(name="Siti Rahayu", dob=date(1990, 2, 15), gender="F", occupation_class=1, coverage_amount=5000.0, product_type="Group Basic Medical", plan_tier="Plan 4"),
            Member(name="Michael Chen", dob=date(1968, 6, 30), gender="M", occupation_class=3, coverage_amount=200000.0, product_type="Group Basic Medical", plan_tier="Plan 6")
        ]

    with tab1:
        st.subheader("Employee Member Census")
        st.markdown("View and manage employee headcount for premium calculations.")
        
        member_data = []
        for m in st.session_state.members:
            member_data.append({
                "Name": m.name,
                "DOB": m.dob.strftime("%Y-%m-%d"),
                "Gender": m.gender,
                "Occupation Class": m.occupation_class,
                "Product Type": m.product_type,
                "Plan Tier": m.plan_tier
            })
        st.dataframe(pd.DataFrame(member_data), use_container_width=True)

    with tab2:
        st.subheader("🏥 Schedule of Benefits Comparison (Avallis Financial Format)")
        st.markdown("Comparing **AIA**, **Singlife**, **Great Eastern**, **Raffles Health**, and **Tokio Marine** side-by-side.")
        
        benefits_comparison_table = [
            {
                "Schedule of Benefits": "1. Daily Room & Board (Max. 120 days)",
                "AIA": "1(a). $250",
                "Singlife": "4 bedded Govt/Restr",
                "Great Eastern": "4 bedded Govt/Restr",
                "Raffles Health": "1-bedded / 2-bedded / 4-bedded",
                "Tokio Marine": "Standard Room & Board (100 to 600)"
            },
            {
                "Schedule of Benefits": "Intensive Care Unit (Max. 30 days)",
                "AIA": "1(b). $750",
                "Singlife": "$10,000 per disability",
                "Great Eastern": "$10,000 per disability",
                "Raffles Health": "$10,000",
                "Tokio Marine": "$10,000 (ICU & HDW)"
            },
            {
                "Schedule of Benefits": "2. Other Hospital Services (including implants)",
                "AIA": "$3,500",
                "Singlife": "As charged / Max limit per disability",
                "Great Eastern": "As charged / Max limit per disability",
                "Raffles Health": "As charged to $200,000 or up to $30,000",
                "Tokio Marine": "As Charged / up to $25,000"
            },
            {
                "Schedule of Benefits": "3. Surgical Benefit",
                "AIA": "$5,500",
                "Singlife": "$15,000 max limit",
                "Great Eastern": "$15,000 max limit",
                "Raffles Health": "As charged to $200,000 / up to $30,000",
                "Tokio Marine": "As Charged / up to $25,000"
            },
            {
                "Schedule of Benefits": "4. Pre- & Post-Hospitalization Treatment",
                "AIA": "$800",
                "Singlife": "Combined limit",
                "Great Eastern": "$15,000 max limit",
                "Raffles Health": "As charged to $200,000 / up to $2,500",
                "Tokio Marine": "Pre & Post Hospitalization included"
            },
            {
                "Schedule of Benefits": "5. Emergency Out-Patient Treatment (Accident)",
                "AIA": "$2,300",
                "Singlife": "$1,000",
                "Great Eastern": "$1,000",
                "Raffles Health": "$2,000 to $3,500 (incl TCM)",
                "Tokio Marine": "$1,000 to $3,000"
            },
            {
                "Schedule of Benefits": "6. Outpatient Kidney Dialysis / Cancer Treatment",
                "AIA": "$15,000",
                "Singlife": "$12,000",
                "Great Eastern": "$15,000",
                "Raffles Health": "$15,000 to $60,000",
                "Tokio Marine": "$10,000 to $30,000"
            },
            {
                "Schedule of Benefits": "7. Death Benefit",
                "AIA": "$10,000",
                "Singlife": "$5,000",
                "Great Eastern": "$10,000",
                "Raffles Health": "$5,000 - $20,000",
                "Tokio Marine": "$10,000"
            }
        ]
        st.dataframe(pd.DataFrame(benefits_comparison_table), use_container_width=True)

    with tab3:
        st.subheader("📊 Raffles Health Group Hospital & Surgical (GHS) - Plans & Rates")
        st.markdown("Annual Premium Rates (Exclude prevailing GST) - Age Next Birthday (ANB).")
        
        raffles_rates = [
            {"Age Next Birthday": "Up to 25", "PLAN 1": "$740.06", "PLAN 2A": "$491.24", "PLAN 2B": "$369.22", "PLAN 3": "$362.10", "PLAN 4 (NEW)": "$253.47", "PLAN 5": "$372.31", "PLAN 6": "$169.33"},
            {"Age Next Birthday": "26-30", "PLAN 1": "$1,014.65", "PLAN 2A": "$521.08", "PLAN 2B": "$460.42", "PLAN 3": "$365.63", "PLAN 4 (NEW)": "$255.95", "PLAN 5": "$375.87", "PLAN 6": "$200.42"},
            {"Age Next Birthday": "31-35", "PLAN 1": "$1,114.75", "PLAN 2A": "$564.75", "PLAN 2B": "$503.75", "PLAN 3": "$421.20", "PLAN 4 (NEW)": "$294.84", "PLAN 5": "$431.44", "PLAN 6": "$205.84"},
            {"Age Next Birthday": "36-40", "PLAN 1": "$1,246.70", "PLAN 2A": "$622.48", "PLAN 2B": "$526.78", "PLAN 3": "$457.72", "PLAN 4 (NEW)": "$320.41", "PLAN 5": "$473.85", "PLAN 6": "$241.04"},
            {"Age Next Birthday": "41-45", "PLAN 1": "$1,336.19", "PLAN 2A": "$691.50", "PLAN 2B": "$629.69", "PLAN 3": "$544.38", "PLAN 4 (NEW)": "$381.07", "PLAN 5": "$563.06", "PLAN 6": "$287.09"},
            {"Age Next Birthday": "46-50", "PLAN 1": "$1,791.19", "PLAN 2A": "$877.40", "PLAN 2B": "$800.32", "PLAN 3": "$691.98", "PLAN 4 (NEW)": "$484.39", "PLAN 5": "$715.17", "PLAN 6": "$365.63"},
            {"Age Next Birthday": "51-55", "PLAN 1": "$2,302.14", "PLAN 2A": "$1,301.35", "PLAN 2B": "$1,114.76", "PLAN 3": "$995.76", "PLAN 4 (NEW)": "$697.04", "PLAN 5": "$1,089.78", "PLAN 6": "$492.93"},
            {"Age Next Birthday": "56-60", "PLAN 1": "$3,025.87", "PLAN 2A": "$1,622.08", "PLAN 2B": "$1,389.38", "PLAN 3": "$1,240.90", "PLAN 4 (NEW)": "$868.63", "PLAN 5": "$1,358.46", "PLAN 6": "$646.43"},
            {"Age Next Birthday": "61-65", "PLAN 1": "$3,804.99", "PLAN 2A": "$2,334.04", "PLAN 2B": "$1,958.13", "PLAN 3": "$1,487.74", "PLAN 4 (NEW)": "$1,041.42", "PLAN 5": "$1,628.79", "PLAN 6": "$814.03"},
            {"Age Next Birthday": "66-70", "PLAN 1": "$5,050.94", "PLAN 2A": "$3,121.58", "PLAN 2B": "$2,483.00", "PLAN 3": "$1,885.70", "PLAN 4 (NEW)": "$1,319.99", "PLAN 5": "$2,063.71", "PLAN 6": "$1,030.90"},
            {"Age Next Birthday": "71-75*", "PLAN 1": "$7,045.79", "PLAN 2A": "$4,787.30", "PLAN 2B": "$3,807.38", "PLAN 3": "$2,893.20", "PLAN 4 (NEW)": "$2,025.24", "PLAN 5": "$3,165.23", "PLAN 6": "$1,580.15"}
        ]
        st.dataframe(pd.DataFrame(raffles_rates), use_container_width=True)

    with tab4:
        st.subheader("📈 Tokio Marine Group Deluxe Medical Insurance - Plans & Rates")
        st.markdown("Annual Premium Rate (S$) per Insured Member - Age Next Birthday (ANB).")
        
        tm_rates = [
            {"Age Next Birthday": "25 & Below", "Plan 1": "$652.00", "Plan 2": "$506.00", "Plan 3": "$328.00", "Plan 4": "$234.00", "Plan 5": "$182.00"},
            {"Age Next Birthday": "26 to 30", "Plan 1": "$652.00", "Plan 2": "$524.00", "Plan 3": "$340.00", "Plan 4": "$242.00", "Plan 5": "$188.00"},
            {"Age Next Birthday": "31 to 35", "Plan 1": "$704.00", "Plan 2": "$550.00", "Plan 3": "$357.00", "Plan 4": "$254.00", "Plan 5": "$198.00"},
            {"Age Next Birthday": "36 to 40", "Plan 1": "$704.00", "Plan 2": "$583.00", "Plan 3": "$378.00", "Plan 4": "$269.00", "Plan 5": "$209.00"},
            {"Age Next Birthday": "41 to 45", "Plan 1": "$757.00", "Plan 2": "$612.00", "Plan 3": "$397.00", "Plan 4": "$282.00", "Plan 5": "$220.00"},
            {"Age Next Birthday": "46 to 50", "Plan 1": "$1,091.00", "Plan 2": "$800.00", "Plan 3": "$519.00", "Plan 4": "$369.00", "Plan 5": "$287.00"},
            {"Age Next Birthday": "51 to 55", "Plan 1": "$1,320.00", "Plan 2": "$994.00", "Plan 3": "$644.00", "Plan 4": "$458.00", "Plan 5": "$355.00"},
            {"Age Next Birthday": "56 to 60", "Plan 1": "$1,618.00", "Plan 2": "$1,272.00", "Plan 3": "$824.00", "Plan 4": "$586.00", "Plan 5": "$455.00"},
            {"Age Next Birthday": "61 to 65", "Plan 1": "$2,286.00", "Plan 2": "$1,843.00", "Plan 3": "$1,194.00", "Plan 4": "$849.00", "Plan 5": "$658.00"},
            {"Age Next Birthday": "66 to 70", "Plan 1": "$3,353.00", "Plan 2": "$2,727.00", "Plan 3": "$1,766.00", "Plan 4": "$1,255.00", "Plan 5": "$973.00"},
            {"Age Next Birthday": "71 to 75*", "Plan 1": "$4,801.00", "Plan 2": "$3,905.00", "Plan 3": "$2,529.00", "Plan 4": "$1,797.00", "Plan 5": "$1,393.00"}
        ]
        st.dataframe(pd.DataFrame(tm_rates), use_container_width=True)

    with tab5:
        st.subheader("📥 Export Report")
        rate_df_export = get_sample_rate_tables()
        results = run_batch_comparison(st.session_state.members, ["Singlife", "AIA", "Great Eastern"], rate_df_export, policy_config)
        excel_bytes = export_comparison_to_excel(results)
        
        st.download_button(
            label="📥 Download Executive Comparison Report (Excel)",
            data=excel_bytes,
            file_name="Insurance_Comparison_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
