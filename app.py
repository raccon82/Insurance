"""
Streamlit UI entry point managing workflow steps:
1. Sidebar: Sample rate table generator & rate sheet upload.
2. Step 1: Upload Member List (Excel/CSV) with columns Name, DOB, Gender, Occupation Class, Coverage Amount, Product Type/Plan Tier.
3. Step 2: Policy Configuration (Renewal Date 1 Oct 2026 - 30 Sep 2027, Insurer Age Rules: ALB for Singlife & Raffles Health, ANB for HSBC Life, GST %, NEL Limits) & Insurer Selection.
4. Step 3: Run Calculation Engine & Display Comparison Matrix / Individual Product Breakdown / Average Cost per Member / Renewal Recommendation.
5. Step 4: Dedicated "Summary by Product" view matching exact corporate quotation breakdown format.
6. Step 5: Professional Broker Plan & Cost Comparison Matrix matching executive layout (Headcount header, Premium Excl. GST, % Difference from Incumbent, Premium Per Pax, and Benefit Grid).
7. Step 6: Export final comparison report as a formatted Excel spreadsheet.
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
    st.markdown("Compare corporate insurance rate structures across **Singlife** (Incumbent), **Raffles Health**, and **HSBC Life**. Applies insurer-specific age rules (ALB for Singlife & Raffles Health, ANB for HSBC Life) anchored to **1 Oct 2026 – 30 Sep 2027**, occupational multipliers, GST rules, and Non-Evidence Limit (NEL) underwriting checks.")

    # Sidebar: Rate Sheets Configuration
    st.sidebar.header("1. Rate Sheets Configuration")
    
    rate_source = st.sidebar.radio(
        "Rate Sheet Source",
        ["Use Built-in Sample Rates", "Upload Custom Rate Sheet (Excel/CSV)"]
    )
    
    rate_df = pd.DataFrame()
    
    if rate_source == "Use Built-in Sample Rates":
        rate_df = get_sample_rate_tables()
        st.sidebar.success(f"Loaded built-in rate tables for Singlife, HSBC Life, and Raffles Health ({len(rate_df)} rate bands).")
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
    
    st.sidebar.info("ℹ️ **Age Calculation Rules (Automated per Insurer):**\n- **Singlife**: Age Last Birthday (ALB)\n- **Raffles Health**: Age Last Birthday (ALB)\n- **HSBC Life**: Age Next Birthday (ANB)")
    
    gst_pct = st.sidebar.number_input("Prevailing GST Rate (%)", value=9.0, step=0.5)
    nel_limit = st.sidebar.number_input("NEL Limit for GTL/GLC (S$)", value=150000.0, step=10000.0)
    
    policy_config = PolicyConfiguration(
        renewal_year=renewal_year,
        renewal_anchor_date=anchor_date,
        age_calculation_method="ALB",
        gst_percentage=gst_pct,
        nel_limit_gtl_glc=nel_limit
    )

    # Main Workflow Tabs / Steps
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Step 1: Member Census", 
        "⚙️ Step 2: Insurers & Options", 
        "📊 Step 3: Comparison & Recommendation", 
        "📑 Step 4: Summary by Product",
        "📈 Step 5: Total Cost & Executive Table Comparison",
        "📥 Step 6: Export Report"
    ])

    # Initialize session state for members
    if "members" not in st.session_state:
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
        
        available_insurers = rate_df["Insurer"].unique().tolist() if not rate_df.empty else ["Singlife", "Raffles Health", "HSBC Life"]
        selected_insurers = st.multiselect("Choose Insurers to Compare", available_insurers, default=available_insurers)
        
        st.markdown("### Rate Sheet Preview")
        if not rate_df.empty:
            st.dataframe(rate_df.head(10), use_container_width=True)
        else:
            st.warning("No rate table loaded.")

    results = run_batch_comparison(st.session_state.members, selected_insurers if 'selected_insurers' in locals() and selected_insurers else ["Singlife", "Raffles Health", "HSBC Life"], rate_df, policy_config)
    st.session_state.last_results = results

    with tab3:
        st.subheader("📊 Premium Comparison, Product Breakdown & Renewal Recommendation")
        
        if not selected_insurers:
            st.warning("Please select at least one insurer in Step 2.")
        else:
            if results:
                df_res = pd.DataFrame([{
                    "Member": r.member_name,
                    "Product": r.product_type,
                    "Plan Tier": r.plan_tier,
                    "Insurer": r.insurer,
                    "Age": r.age,
                    "Age Calc": r.age_calculation_type,
                    "Coverage (S$)": r.coverage_amount,
                    "Base Premium": r.adjusted_base_premium,
                    "GST": r.gst_amount,
                    "Total Premium (S$)": r.total_premium,
                    "Underwriting": r.underwriting_flag,
                    "Error": r.error_message or ""
                } for r in results])
                
                st.markdown("### 🏆 Insurer Summary & Average Cost per Member")
                total_member_count = len(st.session_state.members)
                
                df_summary = df_res.groupby("Insurer").agg(
                    Total_Members=("Member", "count"),
                    Total_Annual_Premium=("Total Premium (S$)", "sum"),
                    Total_Base_Premium=("Base Premium", "sum"),
                    Total_GST=("GST", "sum"),
                    Underwriting_Flags=("Underwriting", lambda x: (x == "Subject to Underwriting").sum()),
                    Errors=("Error", lambda x: (x != "").sum())
                ).reset_index()
                
                df_summary["Average Cost per Member (S$)"] = (df_summary["Total_Annual_Premium"] / total_member_count).round(2)
                
                df_summary = df_summary[[
                    "Insurer", "Total_Annual_Premium", "Average Cost per Member (S$)", 
                    "Total_Base_Premium", "Total_GST", "Underwriting_Flags", "Errors"
                ]]
                
                st.dataframe(df_summary.sort_values("Total_Annual_Premium"), use_container_width=True)
                
                st.markdown("### 💡 Renewal & Switch Recommendation (1 Oct 2026 – 30 Sep 2027)")
                valid_summary = df_summary[df_summary["Errors"] == 0]
                if not valid_summary.empty:
                    best_row = valid_summary.sort_values("Total_Annual_Premium").iloc[0]
                    best_insurer = best_row["Insurer"]
                    best_cost = best_row["Total_Annual_Premium"]
                    
                    incumbent = "Singlife"
                    incumbent_row = df_summary[df_summary["Insurer"] == incumbent]
                    incumbent_cost = incumbent_row["Total_Annual_Premium"].values[0] if not incumbent_row.empty else best_cost
                    
                    if best_insurer == incumbent:
                        st.success(f"**Recommendation: RENEW with Incumbent ({incumbent})**. Renewing with Singlife yields the lowest total annual premium of **S$ {best_cost:,.2f}** (Average cost per member: **S$ {(best_cost/total_member_count):,.2f}**), matching exact plan coverage without disruption or re-underwriting risks.")
                    else:
                        diff = incumbent_cost - best_cost
                        st.info(f"**Recommendation: SWITCH to {best_insurer}**. Switching from incumbent Singlife (S$ {incumbent_cost:,.2f}) to **{best_insurer}** saves approximately **S$ {diff:,.2f}** per year, with a total annual premium of **S$ {best_cost:,.2f}** (Average cost per member: **S$ {(best_cost/total_member_count):,.2f}**), mirroring similar plan coverage.")
                
                st.markdown("### 🔍 Individual Product Breakdown by Member")
                product_pivot = df_res.pivot_table(
                    index=["Member", "Product", "Plan Tier", "Coverage (S$)"],
                    columns="Insurer",
                    values="Total Premium (S$)",
                    aggfunc="sum"
                ).reset_index()
                st.dataframe(product_pivot, use_container_width=True)

    with tab4:
        st.subheader("📑 Summary by Product (Quotation Breakdown Format)")
        st.markdown("Detailed product-level breakdown displaying **No. of Lives**, **Sum Assured (Total / Accepted / Pending)**, and **Premium Excluding GST (Total / Accepted)** matching the standard corporate quotation format.")
        
        if selected_insurers:
            selected_summary_insurer = st.selectbox("Select Insurer for Summary by Product", selected_insurers)
            
            ins_results = [r for r in results if r.insurer.lower() == selected_summary_insurer.lower()]
            
            product_categories = [
                "Group Term Life",
                "Group Living Care",
                "Group Personal Accident",
                "Group Basic Medical",
                "Group Major Medical",
                "Group Outpatient - GP",
                "Group Outpatient - GP + SP",
                "Group Dental"
            ]
            
            summary_rows = []
            tot_lives = 0
            tot_sum_assured = 0.0
            tot_sum_assured_accepted = 0.0
            tot_sum_assured_pending = 0.0
            tot_premium_excl_gst = 0.0
            tot_premium_accepted = 0.0
            
            from collections import defaultdict
            prod_map = defaultdict(list)
            for r in ins_results:
                prod_map[r.product_type].append(r)
                
            for prod in product_categories:
                p_items = prod_map.get(prod, [])
                if p_items:
                    lives = len(p_items)
                    sum_ass = sum(item.coverage_amount for item in p_items)
                    accepted_items = [item for item in p_items if item.underwriting_flag != "Subject to Underwriting"]
                    pending_items = [item for item in p_items if item.underwriting_flag == "Subject to Underwriting"]
                    
                    sum_ass_accepted = sum(item.coverage_amount for item in accepted_items)
                    sum_ass_pending = sum(item.coverage_amount for item in pending_items)
                    
                    prem_total = sum(item.adjusted_base_premium for item in p_items)
                    prem_accepted = sum(item.adjusted_base_premium for item in accepted_items)
                    
                    tot_lives += lives
                    tot_sum_assured += sum_ass
                    tot_sum_assured_accepted += sum_ass_accepted
                    tot_sum_assured_pending += sum_ass_pending
                    tot_premium_excl_gst += prem_total
                    tot_premium_accepted += prem_accepted
                    
                    summary_rows.append({
                        "MyBenefits Plus": prod,
                        "No. of Lives": lives,
                        "Sum Assured: Total": f"S$ {sum_ass:,.2f}" if sum_ass > 0 else "-",
                        "Sum Assured: Accepted": f"S$ {sum_ass_accepted:,.2f}" if sum_ass_accepted > 0 else "-",
                        "Sum Assured: Pending": f"S$ {sum_ass_pending:,.2f}" if sum_ass_pending > 0 else "-",
                        "Premium (Excl. GST): Total": f"S$ {prem_total:,.2f}" if prem_total > 0 else "-",
                        "Premium (Excl. GST): Accepted": f"S$ {prem_accepted:,.2f}" if prem_accepted > 0 else "-"
                    })
                else:
                    summary_rows.append({
                        "MyBenefits Plus": prod,
                        "No. of Lives": "-",
                        "Sum Assured: Total": "-",
                        "Sum Assured: Accepted": "-",
                        "Sum Assured: Pending": "-",
                        "Premium (Excl. GST): Total": "-",
                        "Premium (Excl. GST): Accepted": "-"
                    })
                    
            df_product_summary = pd.DataFrame(summary_rows)
            
            total_row_data = {
                "MyBenefits Plus": "Total",
                "No. of Lives": tot_lives if tot_lives > 0 else "-",
                "Sum Assured: Total": f"S$ {tot_sum_assured:,.2f}" if tot_sum_assured > 0 else "-",
                "Sum Assured: Accepted": f"S$ {tot_sum_assured_accepted:,.2f}" if tot_sum_assured_accepted > 0 else "-",
                "Sum Assured: Pending": f"S$ {tot_sum_assured_pending:,.2f}" if tot_sum_assured_pending > 0 else "-",
                "Premium (Excl. GST): Total": f"S$ {tot_premium_excl_gst:,.2f}" if tot_premium_excl_gst > 0 else "-",
                "Premium (Excl. GST): Accepted": f"S$ {tot_premium_accepted:,.2f}" if tot_premium_accepted > 0 else "-"
            }
            
            df_product_summary = pd.concat([df_product_summary, pd.DataFrame([total_row_data])], ignore_index=True)
            
            st.markdown(f"#### Insurer: **{selected_summary_insurer}**")
            st.dataframe(df_product_summary, use_container_width=True)
        else:
            st.warning("Please select insurers in Step 2.")

    with tab5:
        st.subheader("📈 Executive Total Cost & Professional Broker Table Comparison")
        st.markdown(f"Based on **{len(st.session_state.members)} eligible headcount (HC)** as of 1 Oct 2026.")
        
        if results:
            df_res_all = pd.DataFrame([{
                "Insurer": r.insurer,
                "Product": r.product_type,
                "Base Premium": r.adjusted_base_premium,
                "GST": r.gst_amount,
                "Total Premium": r.total_premium
            } for r in results])
            
            total_members = len(st.session_state.members)
            
            matrix_summary = df_res_all.groupby("Insurer").agg(
                Total_Base_Premium=("Base Premium", "sum"),
                Total_GST=("GST", "sum"),
                Total_Annual_Premium=("Total Premium", "sum")
            ).reset_index()
            
            # Identify incumbent (Singlife) base cost for % difference calculation
            incumbent_name = "Singlife"
            incumbent_row = matrix_summary[matrix_summary["Insurer"].str.lower() == incumbent_name.lower()]
            incumbent_base = incumbent_row["Total_Base_Premium"].values[0] if not incumbent_row.empty else matrix_summary["Total_Base_Premium"].iloc[0]
            
            exec_rows = []
            for _, row in matrix_summary.iterrows():
                ins = row["Insurer"]
                base = row["Total_Base_Premium"]
                gst = row["Total_GST"]
                total_incl = row["Total_Annual_Premium"]
                per_pax = base / total_members if total_members > 0 else 0.0
                
                # % difference from incumbent base premium
                diff_pct = ((base - incumbent_base) / incumbent_base) * 100.0 if incumbent_base > 0 else 0.0
                diff_str = "-" if abs(diff_pct) < 0.01 else f"+{diff_pct:.1f}%" if diff_pct > 0 else f"{diff_pct:.1f}%"
                
                exec_rows.append({
                    "Metric": ins,
                    "Premium (excl. GST)": f"S$ {base:,.2f}",
                    "Difference from Existing Plan": diff_str,
                    "Premium Per Pax": f"S$ {per_pax:,.2f}",
                    "Total (incl. GST)": f"S$ {total_incl:,.2f}"
                })
                
            df_exec_table = pd.DataFrame(exec_rows)
            st.markdown("### 🏆 Executive Summary Comparison")
            st.dataframe(df_exec_table, use_container_width=True)
            
            # Professional Benefit & Plan Comparison Grid (matching executive style)
            st.markdown("### 🏥 Benefit & Plan Feature Comparison Grid")
            
            benefit_comparison_data = [
                {
                    "Benefit / Plan Type": "Plan Type / Tier",
                    "Singlife (Incumbent)": "Group Plan 2 (Standard)",
                    "Raffles Health": "Raffles Corporate Plan 1",
                    "HSBC Life": "HSBC Corporate Flex Plan"
                },
                {
                    "Benefit / Plan Type": "Age Calculation Rule",
                    "Singlife (Incumbent)": "Age Last Birthday (ALB)",
                    "Raffles Health": "Age Last Birthday (ALB)",
                    "HSBC Life": "Age Next Birthday (ANB)"
                },
                {
                    "Benefit / Plan Type": "Room & Board (GHS)",
                    "Singlife (Incumbent)": "2-Bedded (Private)",
                    "Raffles Health": "1-Bedded (Private)",
                    "HSBC Life": "2-Bedded (Private)"
                },
                {
                    "Benefit / Plan Type": "Outpatient GP & Specialist (GP + SP)",
                    "Singlife (Incumbent)": "Panel preferred, As charged",
                    "Raffles Health": "Panel preferred, As charged",
                    "HSBC Life": "Panel & Non-panel"
                },
                {
                    "Benefit / Plan Type": "Annual Limit (per employee)",
                    "Singlife (Incumbent)": "S$ 500 (Dental/Outpatient)",
                    "Raffles Health": "S$ 600",
                    "HSBC Life": "S$ 500"
                },
                {
                    "Benefit / Plan Type": "Co-payment",
                    "Singlife (Incumbent)": "Nil",
                    "Raffles Health": "20% per claim",
                    "Singlife (Incumbent)": "Nil"
                },
                {
                    "Benefit / Plan Type": "Panel Requirement",
                    "Singlife (Incumbent)": "Panel preferred",
                    "Raffles Health": "Panel & Non-panel (reimbursement)",
                    "HSBC Life": "Panel preferred"
                },
                {
                    "Benefit / Plan Type": "Employee Out-of-Pocket Impact",
                    "Singlife (Incumbent)": "Lowest",
                    "Raffles Health": "Higher (due to co-payment)",
                    "HSBC Life": "Lowest"
                }
            ]
            
            st.dataframe(pd.DataFrame(benefit_comparison_data), use_container_width=True)
            
        else:
            st.warning("No calculation results available.")

    with tab6:
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
            st.info("Run the calculation engine first to generate exportable results.")


if __name__ == "__main__":
    main()
