"""
Streamlit Application
Main entry point for the data management system.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO

st.set_page_config(
    page_title="Data Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database import init_db, check_connection, SessionLocal
from models import Record
from crud import (
    create_record, get_record, get_records, update_record, 
    delete_record, get_categories, get_statuses, bulk_create_records
)
from schemas import RecordCreate, RecordUpdate
from utils.importer import (
    validate_file, clean_dataframe, dataframe_to_records, generate_template
)
from utils.exporter import records_to_dataframe, export_to_csv, export_to_excel

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center; }
    .stat-number { font-size: 2rem; font-weight: 700; }
    .stat-label { font-size: 0.9rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize():
    init_db()
    return True

initialize()

def get_db_session():
    return SessionLocal()

with st.sidebar:
    st.markdown("### 📊 Data Manager")
    success, msg = check_connection()
    if success:
        st.success("🟢 MySQL Connected")
    else:
        st.error(msg)
        st.info("Update credentials in database.py")
    st.divider()
    page = st.radio("Navigation", [
        "🏠 Dashboard", "➕ Add Record", "📥 Bulk Import", 
        "📋 View Records", "📤 Export Data"
    ], label_visibility="collapsed")
    st.divider()
    st.caption("v1.0 • Streamlit + MySQL")

if page == "🏠 Dashboard":
    st.markdown('<div class="main-header">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of your data</div>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        total_records = db.query(Record).count()
        active_records = db.query(Record).filter(Record.status == "active").count()
        pending_records = db.query(Record).filter(Record.status == "pending").count()
        cat_data = db.query(Record.category, db.func.count(Record.id)).group_by(Record.category).all()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{total_records}</div><div class="stat-label">Total Records</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);"><div class="stat-number">{active_records}</div><div class="stat-label">Active</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><div class="stat-number">{pending_records}</div><div class="stat-label">Pending</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><div class="stat-number">{len(cat_data)}</div><div class="stat-label">Categories</div></div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("📋 Recent Records")
        recent, _ = get_records(db, limit=10)
        if recent:
            st.dataframe(records_to_dataframe(recent), use_container_width=True, hide_index=True)
        else:
            st.info("No records found. Add some data to get started!")

        if cat_data:
            st.subheader("📊 Records by Category")
            cat_df = pd.DataFrame(cat_data, columns=["Category", "Count"])
            st.bar_chart(cat_df.set_index("Category"))
    finally:
        db.close()

elif page == "➕ Add Record":
    st.markdown('<div class="main-header">Add New Record</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Enter details for a single record</div>', unsafe_allow_html=True)

    with st.form("add_record_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", placeholder="Enter full name")
            email = st.text_input("Email", placeholder="email@example.com")
            phone = st.text_input("Phone", placeholder="+92-300-1234567")
            category = st.text_input("Category *", placeholder="e.g., Customer, Vendor")
        with c2:
            amount = st.number_input("Amount", min_value=0.0, value=0.0, step=100.0)
            record_date = st.date_input("Date", value=date.today())
            status = st.selectbox("Status", ["active", "inactive", "pending"])
            notes = st.text_area("Notes", placeholder="Additional information...", height=100)

        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)

        if submitted:
            if not name or not category:
                st.error("❌ Name and Category are required fields!")
            else:
                try:
                    record_data = RecordCreate(
                        name=name.strip(),
                        email=email.strip() if email else None,
                        phone=phone.strip() if phone else None,
                        category=category.strip(),
                        amount=amount,
                        date=datetime.combine(record_date, datetime.min.time()) if record_date else None,
                        status=status,
                        notes=notes.strip() if notes else None
                    )
                    db = get_db_session()
                    try:
                        new_record = create_record(db, record_data)
                        st.success(f"✅ Record created successfully! ID: {new_record.id}")
                    finally:
                        db.close()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

elif page == "📥 Bulk Import":
    st.markdown('<div class="main-header">Bulk Import</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload Excel or CSV files to import multiple records</div>', unsafe_allow_html=True)

    st.subheader("📄 Download Template")
    template_df = generate_template()

    c1, c2 = st.columns(2)
    with c1:
        csv_template = template_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Template", csv_template, "template.csv", "text/csv", use_container_width=True)
    with c2:
        excel_buffer = BytesIO()
        template_df.to_excel(excel_buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel Template", excel_buffer.getvalue(), "template.xlsx", 
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.divider()
    st.subheader("📤 Upload File")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx', 'xls'],
                                    help="File must contain at least 'name' and 'category' columns")

    if uploaded_file:
        is_valid, message, df = validate_file(uploaded_file)
        if not is_valid:
            st.error(message)
        else:
            st.success(message)
            with st.expander("👁️ Preview Data"):
                st.dataframe(df.head(20), use_container_width=True)

            cleaned_df, warnings = clean_dataframe(df)
            if warnings:
                for warning in warnings:
                    st.warning(warning)

            st.info(f"📊 Ready to import: **{len(cleaned_df)}** valid records")
            with st.expander("👁️ Preview Cleaned Data"):
                st.dataframe(cleaned_df.head(20), use_container_width=True)

            st.subheader("⚙️ Import Options")
            skip_duplicates = st.checkbox("Skip records with duplicate emails", value=True)

            if st.button("🚀 Import to Database", type="primary", use_container_width=True):
                if len(cleaned_df) == 0:
                    st.error("❌ No valid records to import!")
                else:
                    with st.spinner("Importing records..."):
                        try:
                            records_list = dataframe_to_records(cleaned_df)
                            db = get_db_session()
                            try:
                                inserted = bulk_create_records(db, records_list)
                                st.success(f"✅ Successfully imported **{inserted}** records!")
                                st.balloons()
                            finally:
                                db.close()
                        except Exception as e:
                            st.error(f"❌ Import failed: {str(e)}")

elif page == "📋 View Records":
    st.markdown('<div class="main-header">View Records</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Search, filter, edit, and delete records</div>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        with st.expander("🔍 Filters", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                search_term = st.text_input("Search", placeholder="Name, email, notes...")
            with c2:
                categories = ["All"] + get_categories(db)
                category_filter = st.selectbox("Category", categories)
            with c3:
                statuses = ["All"] + get_statuses(db)
                status_filter = st.selectbox("Status", statuses)
            with c4:
                date_filter = st.date_input("From Date", value=None)

        c1, c2, c3 = st.columns([2, 1, 1])
        with c2:
            page_size = st.selectbox("Per page", [10, 25, 50, 100], index=1)

        cat = None if category_filter == "All" else category_filter
        stat = None if status_filter == "All" else status_filter
        date_from = date_filter.strftime("%Y-%m-%d") if date_filter else None

        records, total = get_records(db, limit=page_size, search=search_term if search_term else None,
                                     category=cat, status=stat, date_from=date_from)

        st.caption(f"Showing {len(records)} of {total} records")

        if records:
            df = records_to_dataframe(records)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("✏️ Edit / 🗑️ Delete Record")

            c1, c2 = st.columns(2)
            with c1:
                record_id = st.number_input("Enter Record ID", min_value=1, step=1)

            action = st.radio("Action", ["Edit", "Delete"], horizontal=True)

            if action == "Edit" and record_id:
                record = get_record(db, record_id)
                if record:
                    with st.form("edit_form"):
                        st.write(f"Editing: **{record.name}** (ID: {record.id})")
                        e1, e2 = st.columns(2)
                        with e1:
                            new_name = st.text_input("Name", value=record.name)
                            new_email = st.text_input("Email", value=record.email or "")
                            new_phone = st.text_input("Phone", value=record.phone or "")
                            new_category = st.text_input("Category", value=record.category)
                        with e2:
                            new_amount = st.number_input("Amount", value=float(record.amount or 0), step=100.0)
                            new_date = st.date_input("Date", value=record.date.date() if record.date else date.today())
                            new_status = st.selectbox("Status", ["active", "inactive", "pending"], 
                                                      index=["active", "inactive", "pending"].index(record.status))
                            new_notes = st.text_area("Notes", value=record.notes or "", height=80)

                        if st.form_submit_button("💾 Update Record"):
                            try:
                                update_data = RecordUpdate(
                                    name=new_name.strip(),
                                    email=new_email.strip() if new_email else None,
                                    phone=new_phone.strip() if new_phone else None,
                                    category=new_category.strip(),
                                    amount=new_amount,
                                    date=datetime.combine(new_date, datetime.min.time()),
                                    status=new_status,
                                    notes=new_notes.strip() if new_notes else None
                                )
                                updated = update_record(db, record_id, update_data)
                                if updated:
                                    st.success("✅ Record updated successfully!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Record not found")

            elif action == "Delete" and record_id:
                record = get_record(db, record_id)
                if record:
                    st.warning(f"Are you sure you want to delete: **{record.name}**?")
                    if st.button("🗑️ Confirm Delete", type="primary"):
                        if delete_record(db, record_id):
                            st.success("✅ Record deleted successfully!")
                            st.rerun()
                else:
                    st.warning("Record not found")
        else:
            st.info("No records match your filters")
    finally:
        db.close()

elif page == "📤 Export Data":
    st.markdown('<div class="main-header">Export Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Download your data in CSV or Excel format</div>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        with st.expander("🔍 Export Filters", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                exp_category = st.selectbox("Category", ["All"] + get_categories(db))
            with c2:
                exp_status = st.selectbox("Status", ["All"] + get_statuses(db))
            with c3:
                exp_date_from = st.date_input("From Date", value=None, key="exp_from")

        cat = None if exp_category == "All" else exp_category
        stat = None if exp_status == "All" else exp_status
        date_from = exp_date_from.strftime("%Y-%m-%d") if exp_date_from else None

        records, total = get_records(db, limit=10000, category=cat, status=stat, date_from=date_from)

        st.info(f"📊 **{total}** records ready for export")

        if records:
            df = records_to_dataframe(records)

            c1, c2 = st.columns(2)
            with c1:
                csv_data = export_to_csv(df)
                st.download_button("📥 Download as CSV", csv_data,
                    f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)

            with c2:
                excel_data = export_to_excel(df)
                st.download_button("📥 Download as Excel", excel_data,
                    f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

            with st.expander("👁️ Preview Export Data"):
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No records to export with current filters")
    finally:
        db.close()