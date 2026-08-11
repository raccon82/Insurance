"""
Streamlit UI entry point managing workflow steps:
1. Sidebar: Sample rate table generator & rate sheet upload.
2. Step 1: Upload Member List (Excel/CSV) with columns Name, DOB, Gender, Occupation Class, Coverage Amount, Product Type/Plan Tier.
3. Step 2: Policy Configuration (Renewal Date, Age Calculation ALB/ANB, GST %, NEL Limits) & Insurer Selection.
4. Step 3: Run Calculation Engine & Display Comparison Matrix / Summary Totals / Underwriting Flags.
5. Step 4: Export final comparison report as a formatted Excel spreadsheet.
"""

import streamlit as st
import pandas as pd
from datetime import date
from typing import List

from src.models import Member, PolicyConfiguration
from src.pricing import get_sample_rate_tables, run_batch_comparison
from src.exporter import export_comparison_to_excel

st.set_page_config(
    page_title="Corporate Insurance Premium Comparison App",
    page_icon="🛡️",
    layout="wide"
)

def main():
    st.title("🛡️ Corporate Insurance Premium Comparison Engine")
    st.markdown("Compare corporate insurance rate structures across insurers (Singlife, HSBC Life, AIA), apply occupation multipliers, Singapore GST rules, ANB/ALB age calculations, and Non-Evidence Limit (NEL) underwriting checks.")

    # Sidebar: Rate Sheets Configuration
    st.sidebar.header("1. Rate Sheets Configuration")
    
    rate_source = st.sidebar.radio(
        "Rate Sheet Source",
        ["Use Built-in Sample Rates", "Upload Custom Rate Sheet (Excel/CSV)"]
    )
    
    rate_df = pd.DataFrame()
    
    if rate_source == "Use Built-in Sample Rates":
        rate_df = get_sample_rate_tables()
        st.sidebar.success(f"Loaded built-in rate table ({len(rate_df)} rate bands).")
    else:
        rate_file = st.sidebar.file_uploader("Upload Rate Sheet", type=["xlsx", "csv"])
        if rate_file is not None:
            try:
                if rate_file.name.endswith(".csv"):
                    rate_df = pd.read_csv(rate_file)
                else:
                    rate_df = pd.read_excel(rate_file)
                st.sidebar.success(f"Successfully loaded {len(rate_df)} rate rows.")
            except Exception as e:
                st.sidebar.error(f"Error loading rate file: {e}")
        else:
            st.sidebar.info("Please upload a rate sheet or switch to built-in sample rates.")
            rate_df = get_sample_rate_tables()  # fallback

    # Sidebar: Policy Configuration
    st.sidebar.header("2. Policy & Calculation Settings")
    renewal_year = st.sidebar.number_input("Policy Renewal Year", value=2026, step=1)
    renewal_month = st.sidebar.selectbox("Renewal Month", list(range(1, 13)), index=9) # Default October (9th index in 1-12)
    renewal_day = st.sidebar.number_input("Renewal Day", value=1, min_value=1, max_value=31)
    
    anchor_date = date(renewal_year, renewal_month, renewal_day)
    
    age_calc_method = st.sidebar.selectbox("Age Calculation Method", ["ALB", "ANB"], index=0, help="ALB = Age Last Birthday; ANB = Age Next Birthday")
    gst_pct = st.sidebar.number_input("Prevailing GST Rate (%)", value=9.0, step=0.5)
    nel_limit = st.sidebar.number_input("NEL Limit for GTL/GLC (S$)", value=150000.0, step=10000.0)
    
    policy_config = PolicyConfiguration(
        renewal_year=renewal_year,
        renewal_anchor_date=anchor_date,
        age_calculation_method=age_calc_method,
        gst_percentage=gst_pct,
        nel_limit_gtl_glc=nel_limit
    )

    # Main Workflow Tabs / Steps
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Step 1: Member Census", 
        "⚙️ Step 2: Insurers & Options", 
        "📊 Step 3: Comparison Matrix", 
        "📥 Step 4: Export Report"
    ])

    # Initialize session state for members
    if "members" not in st.session_state:
        # Default sample census
        st.session_state.members = [
            Member(name="John Tan", dob=date(1985, 4, 12), gender="M", occupation_class=1, coverage_amount=100000.0, product_type="Group Term Life", plan_tier="Standard"),
            Member(name="Alice Wong", dob=date(1992, 8, 25), gender="F", occupation_class=1, coverage_amount=50000.0, product_type="Group Living Care", plan_tier="Standard"),
            Member(name="David Lim", dob=date(1978, 11, 5), gender="M", occupation_class=2, coverage_amount=100000.0, product_type="Group Personal Accident", plan_tier="Standard"),
            Member(name="Siti Rahayu", dob=date(1990, 2, 15), gender="F", occupation_class=1, coverage_amount=5000.0, product_type="Group Basic Medical", plan_tier="Standard"),
            Member(name="Michael Chen", dob=date(1968, 6, 30), gender="M", occupation_class=3, coverage_amount=200000.0, product_type="Group Term Life", plan_tier="Plan 1")
        ]

    with tab1:
        st.subheader("Employee Member Census")
        st.markdown("Upload employee census list via Excel/CSV or edit/view sample members below.")
        
        uploaded_member_file = st.file_uploader("Upload Member Census (Excel/CSV)", type=["xlsx", "csv"], key="member_upload")
        if uploaded_member_file is not None:
            try:
                if uploaded_member_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_member_file)
                else:
                    df_upload = pd.read_excel(uploaded_member_file)
                
                # Parse members from uploaded dataframe
                parsed_members = []
                for _, row in df_upload.iterrows():
                    dob_val = pd.to_datetime(row["DOB"]).date() if "DOB" in row else date(1990, 1, 1)
                    parsed_members.append(Member(
                        name=str(row.get("Name", "Unknown")),
                        dob=dob_val,
                        gender=str(row.get("Gender", "M")),
                        occupation_class=int(row.get("Occupation Class", 1)),
                        coverage_amount=float(row.get("Coverage Amount", 100000.0)),
                        product_type=str(row.get("Product Type", "Group Term Life")),
                        plan_tier=str(row.get("Plan Tier", "Standard"))
                    ))
                st.session_state.members = parsed_members
                st.success(f"Successfully loaded {len(parsed_members)} members from upload.")
            except Exception as e:
                st.error(f"Error parsing member file: {e}")

        # Display current members in table
        member_data = []
        for m in st.session_state.members:
            member_data.append({
                "Name": m.name,
                "DOB": m.dob.strftime("%Y-%m-%d"),
                "Gender": m.gender,
                "Occupation Class": m.occupation_class,
                "Coverage Amount (S$)": m.coverage_amount,
                "Product Type": m.product_type,
                "Plan Tier": m.plan_tier
            })
        st.dataframe(pd.DataFrame(member_data), use_container_width=True)

        if st.button("Reset to Default Sample Census"):
            st.session_state.members = [
                Member(name="John Tan", dob=date(1985, 4, 12), gender="M", occupation_class=1, coverage_amount=100000.0, product_type="Group Term Life", plan_tier="Standard"),
                Member(name="Alice Wong", dob=date(1992, 8, 25), gender="F", occupation_class=1, coverage_amount=50000.0, product_type="Group Living Care", plan_tier="Standard"),
                Member(name="David Lim", dob=date(1978, 11, 5), gender="M", occupation_class=2, coverage_amount=100000.0, product_type="Group Personal Accident", plan_tier="Standard"),
                Member(name="Siti Rahayu", dob=date(1990, 2, 15), gender="F", occupation_class=1, coverage_amount=5000.0, product_type="Group Basic Medical", plan_tier="Standard"),
                Member(name="Michael Chen", dob=date(1968, 6, 30), gender="M", occupation_class=3, coverage_amount=200000.0, product_type="Group Term Life", plan_tier="Plan 1")
            ]
            st.rerun()

    with tab2:
        st.subheader("Select Insurers & Comparison Parameters")
        
        available_insurers = rate_df["Insurer"].unique().tolist() if not rate_df.empty else ["Singlife", "HSBC Life", "AIA Corporate"]
        selected_insurers = st.multiselect("Choose Insurers to Compare", available_insurers, default=available_insurers)
        
        st.markdown("### Rate Sheet Preview")
        if not rate_df.empty:
            st.dataframe(rate_df.head(10), use_container_width=True)
        else:
            st.warning("No rate table loaded.")

    with tab3:
        st.subheader("Comparison Matrix & Calculation Results")
        
        if not selected_insurers:
            st.warning("Please select at least one insurer in Step 2.")
        else:
            results = run_batch_comparison(st.session_state.members, selected_insurers, rate_df, policy_config)
            
            # Display summary metrics
            if results:
                df_res = pd.DataFrame([{
                    "Member": r.member_name,
                    "Product": r.product_type,
                    "Insurer": r.insurer,
                    "Age": r.age,
                    "Coverage": r.coverage_amount,
                    "Base Premium": r.adjusted_base_premium,
                    "GST": r.gst_amount,
                    "Total Premium": r.total_premium,
                    "Underwriting": r.underwriting_flag,
                    "Error": r.error_message or ""
                } for r in results])
                
                st.markdown("### Detailed Comparison Results")
                st.dataframe(df_res, use_container_width=True)
                
                st.markdown("### Insurer Summary Totals")
                df_summary = df_res.groupby("Insurer").agg(
                    Total_Members=("Member", "count"),
                    Total_Base_Premium=("Base Premium", "sum"),
                    Total_GST=("GST", "sum"),
                    Total_Annual_Premium=("Total Premium", "sum"),
                    Underwriting_Count=("Underwriting", lambda x: (x == "Subject to Underwriting").sum()),
                    Error_Count=("Error", lambda x: (x != "").sum())
                ).reset_index()
                
                st.dataframe(df_summary, use_container_width=True)
                
                # Store results in session state for export
                st.session_state.last_results = results

    with tab4:
        st.subheader("Export Comparison Report")
        st.markdown("Download the complete insurance premium comparison report formatted as an Excel spreadsheet.")
        
        if "last_results" in st.session_state and st.session_state.last_results:
            excel_bytes = export_comparison_to_excel(st.session_state.last_results)
            st.download_button(
                label="📥 Download Excel Comparison Report",
                data=excel_bytes,
                file_name=f"Insurance_Premium_Comparison_{renewal_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Run the calculation engine in Step 3 first to generate exportable results.")


if __name__ == "__main__":
    main()
