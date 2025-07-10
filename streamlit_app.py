import streamlit as st
import pandas as pd
import requests
import io
import pytz
import xlsxwriter
from datetime import datetime, timedelta
from streamlit_navigation_bar import st_navbar
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime

# Odoo settings
url = st.secrets["URL"]
db = st.secrets["DB"]
username = st.secrets["USERNAME"]
password = st.secrets["API_KEY"]

def get_uid():
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "login",
            "args": [db, username, password],
        },
        "id": 1,
    }
    r = requests.post(url, json=payload)
    return r.json()["result"]

def fetch_odoo_data(uid, model, fields, domain=[]):
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [db, uid, password, model, "search_read", [domain], {'fields': fields, 'limit': 50000}],
        },
        "id": 2,
    }
    r = requests.post(url, json=payload)
    return r.json()["result"]

def convert_to_timezone(dt_str, tz='Asia/Jakarta'):
    if not dt_str:
        return ''
    utc_dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    local_dt = utc_dt.astimezone(pytz.timezone(tz))
    return local_dt.strftime('%Y-%m-%d %H:%M')

def prepare_data_pos_visit_recap(data):
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

def fetchDataPosVisitRecap():
    with st.spinner("Connecting to Odoo..."):
        uid = get_uid()

        # Fetch visit line data
        visit_lines = fetch_odoo_data(
            uid, 
            "x_pos_visit_line_1233b", 
            [
                'x_studio_pos_visit_reported_on',
                'x_studio_pos_visit_reported_by',
                'x_studio_pos_visit_id',
                'x_studio_alternative_import_name',
                'x_studio_pos_visit_status',
                'x_studio_product',
                'x_studio_qty',
            ],
            [
                ['x_studio_pos_visit_reported_on', '>=', (datetime.today() - timedelta(days=60)).strftime('%Y-%m-%d')],
                ['x_studio_pos_visit_status', 'in', ['Validated', 'reported']]
            ]
        )

        # Fetch visit headers (id + name)
        visits = fetch_odoo_data(uid, "x_pos_visit", ['id', 'x_name'])
        return visit_lines, visits

def showDataPosVisitRecap(data):
    # Prepare pivoted DataFrame
    df = prepare_data_pos_visit_recap(data)

    st.success(f"Total {len(df)} rows")
    st.dataframe(df)

def showDownloadButtonPosVisitRecap(data):
    # Prepare pivoted DataFrame
    df = prepare_data_pos_visit_recap(data)
    
    # Export to Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="pos_visit_recap.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- UI ---
st.set_page_config(layout="wide")
st.title("📊 POS Visit Recap")

# Get user timezone from browser
# Pass as dict: {label: js_expression}
# Correct structure: list of dicts with label + expression
result = streamlit_js_eval(
    [
        {
            "label": "timezone",
            "expression": "Intl.DateTimeFormat().resolvedOptions().timeZone"
        }
    ],
    key="tz"
)
tz = result.get("timezone")

# --- Session Data ---
if "dataPosVisitRecap" not in st.session_state:
    st.session_state.dataPosVisitRecap = fetchDataPosVisitRecap()
if "lastUpdatePosVisitRecap" not in st.session_state:
    if tz:
        now_local = datetime.now(pytz.timezone(tz))
        st.session_state.lastUpdatePosVisitRecap = now_local.strftime("%Y-%m-%d %H:%M:%S")
if "needs_update" not in st.session_state:
    st.session_state.needs_update = False



# --- Handle Button ---
col1, col2, col3 = st.columns([1,1,1])
with col1:
    update_trigger = st.button("🔄 Update Data")

if update_trigger:
    with st.spinner("Updating data..."):
        st.session_state.dataPosVisitRecap = fetchDataPosVisitRecap()
        st.session_state.lastUpdatePosVisitRecap = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success("Data updated!")

with col2:
    st.caption(f"🕒 Last updated: {st.session_state.lastUpdatePosVisitRecap} ({tz})")

# --- Show Download + Data ---
with col3:
    showDownloadButtonPosVisitRecap(st.session_state.dataPosVisitRecap)

showDataPosVisitRecap(st.session_state.dataPosVisitRecap)