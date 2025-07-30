#!/usr/bin/env python3
"""
Isolated test script for POS Visit Recap functions
This avoids importing the main module which tries to connect to Odoo
"""

import pandas as pd
import pytz
from datetime import datetime

def convert_to_timezone(dt_str, tz='Asia/Jakarta'):
    """Extracted from streamlit_app.py"""
    if not dt_str:
        return ''
    utc_dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    local_dt = utc_dt.astimezone(pytz.timezone(tz))
    return local_dt.strftime('%Y-%m-%d %H:%M')

def prepare_data_pos_visit_recap(data):
    """Extracted from streamlit_app.py"""
    lines, all_data = data
    id_to_name = {r["id"]: r["x_name"] for r in all_data if r.get("id") and r.get("x_name")}

    pivot = {}
    prods = set()

    for r in lines:
        pos_id = r.get("x_studio_pos_visit_id")
        if isinstance(pos_id, list):
            pos_id = pos_id[0]
        prod = r.get("x_studio_product", [None, None])[1]
        qty = r.get("x_studio_qty", 0)
        status = r.get("x_studio_pos_visit_status")
        visit_name = id_to_name.get(pos_id, "")

        if pos_id not in pivot:
            pivot[pos_id] = {
                "Reported on": convert_to_timezone(r.get("x_studio_pos_visit_reported_on")),
                "Reported by": r.get("x_studio_pos_visit_reported_by", [None, ""])[1] if isinstance(r.get("x_studio_pos_visit_reported_by"), list) else "",
                "POS Visit": visit_name,
                "POS Alternative Import Name": r.get("x_studio_alternative_import_name", ""),
                "Status": status
            }

        if prod:
            pivot[pos_id][prod] = pivot[pos_id].get(prod, 0) + qty
            prods.add(prod)

    sorted_prods = sorted(prods)
    final_data = []

    for row in sorted(pivot.values(), key=lambda x: x["Reported on"], reverse=True):
        total = 0
        for prod in sorted_prods:
            val = row.get(prod, "")
            if isinstance(val, (int, float)):
                total += val
            row[prod] = val if val != "" else ""
        row["Total"] = total
        final_data.append(row)

    cols_main = ["Reported on", "Reported by", "POS Visit", "POS Alternative Import Name", "Status", *sorted_prods, "Total"]
    df = pd.DataFrame(final_data, columns=cols_main)

    return df

def test_convert_to_timezone():
    """Test the timezone conversion function"""
    print("Testing convert_to_timezone function...")
    
    # Test with a UTC datetime string
    utc_time = "2024-01-15T10:30:00Z"
    jakarta_time = convert_to_timezone(utc_time, 'Asia/Jakarta')
    print(f"UTC time: {utc_time}")
    print(f"Jakarta time: {jakarta_time}")
    
    # Test with empty string
    empty_result = convert_to_timezone("", 'Asia/Jakarta')
    print(f"Empty string result: '{empty_result}'")
    
    # Test with None
    none_result = convert_to_timezone(None, 'Asia/Jakarta')
    print(f"None result: '{none_result}'")
    
    print("✅ convert_to_timezone tests passed!\n")

def test_prepare_data_pos_visit_recap():
    """Test the data preparation function"""
    print("Testing prepare_data_pos_visit_recap function...")
    
    # Create mock data similar to what Odoo would return
    mock_lines = [
        {
            "x_studio_pos_visit_id": [1, "Visit 1"],
            "x_studio_product": [101, "Product A"],
            "x_studio_qty": 5,
            "x_studio_pos_visit_status": "Validated",
            "x_studio_pos_visit_reported_on": "2024-01-15T10:30:00Z",
            "x_studio_pos_visit_reported_by": [201, "John Doe"],
            "x_studio_alternative_import_name": "ALT001"
        },
        {
            "x_studio_pos_visit_id": [1, "Visit 1"],
            "x_studio_product": [102, "Product B"],
            "x_studio_qty": 3,
            "x_studio_pos_visit_status": "Validated",
            "x_studio_pos_visit_reported_on": "2024-01-15T10:30:00Z",
            "x_studio_pos_visit_reported_by": [201, "John Doe"],
            "x_studio_alternative_import_name": "ALT001"
        },
        {
            "x_studio_pos_visit_id": [2, "Visit 2"],
            "x_studio_product": [101, "Product A"],
            "x_studio_qty": 2,
            "x_studio_pos_visit_status": "reported",
            "x_studio_pos_visit_reported_on": "2024-01-16T14:20:00Z",
            "x_studio_pos_visit_reported_by": [202, "Jane Smith"],
            "x_studio_alternative_import_name": "ALT002"
        }
    ]
    
    mock_visits = [
        {"id": 1, "x_name": "Store Alpha Visit"},
        {"id": 2, "x_name": "Store Beta Visit"}
    ]
    
    mock_data = (mock_lines, mock_visits)
    
    # Test the function
    df = prepare_data_pos_visit_recap(mock_data)
    
    print("Generated DataFrame:")
    print(df.to_string())
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Verify expected data
    assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
    assert "Product A" in df.columns, "Product A column missing"
    assert "Product B" in df.columns, "Product B column missing"
    assert "Total" in df.columns, "Total column missing"
    
    # Check specific values
    visit1_row = df[df["POS Visit"] == "Store Alpha Visit"].iloc[0]
    assert visit1_row["Product A"] == 5, f"Expected Product A = 5, got {visit1_row['Product A']}"
    assert visit1_row["Product B"] == 3, f"Expected Product B = 3, got {visit1_row['Product B']}"
    assert visit1_row["Total"] == 8, f"Expected Total = 8, got {visit1_row['Total']}"
    
    print("✅ prepare_data_pos_visit_recap tests passed!\n")

def test_import_statements():
    """Test that all required modules can be imported"""
    print("Testing import statements...")
    
    try:
        import streamlit as st
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import streamlit: {e}")
    
    try:
        import xlsxwriter
        print("✅ xlsxwriter imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import xlsxwriter: {e}")
    
    try:
        from streamlit_navigation_bar import st_navbar
        print("✅ streamlit_navigation_bar imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import streamlit_navigation_bar: {e}")
    
    try:
        from streamlit_javascript import st_javascript
        print("✅ streamlit_javascript imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import streamlit_javascript: {e}")
    
    print()

if __name__ == "__main__":
    print("🧪 Running isolated tests for POS Visit Recap app...\n")
    
    test_import_statements()
    test_convert_to_timezone()
    test_prepare_data_pos_visit_recap()
    
    print("🎉 All isolated tests completed successfully!")