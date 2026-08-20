import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ---------- पेज कॉन्फ़िग (Offline Mode) ----------
st.set_page_config(
    page_title="NPRC Global - National Physiotherapy Trust",
    page_icon="⚕️",  # Minimal fallback, but we use SVG in UI
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# 🔐 ऑफलाइन ऑथेंटिकेशन (config.json से पढ़ता है)
# ====================================================================
def load_credentials():
    try:
        with open('config.json', 'r') as f:
            data = json.load(f)
            return data.get('username', 'admin'), data.get('password', 'NPRC@2026')
    except:
        return 'admin', 'NPRC@2026'

def login(username, password):
    correct_username, correct_password = load_credentials()
    if username == correct_username and password == correct_password:
        st.session_state.authenticated = True
        st.session_state.user = username
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# ====================================================================
# 🎨 CSS: "Government Top Grade" थीम (कोई इमोजी नहीं, सिर्फ SVG)
# ====================================================================
st.markdown("""
<style>
    /* फॉन्ट और बेस */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #F4F7FC;
    }
    /* हेडर */
    .main-header {
        background: linear-gradient(135deg, #0B2A4A 0%, #1A4B6D 100%);
        padding: 1.2rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
        border-bottom: 4px solid #D4AF37;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .header-left h1 { color: white; font-weight: 300; letter-spacing: 2px; font-size: 1.5rem; margin:0; }
    .header-left h2 { color: white; font-weight: 700; font-size: 1.8rem; margin:0; }
    .header-left p { color: #B0C4DE; margin:0; font-size: 0.9rem; }
    .badge-gold { background: #D4AF37; color: #0B2A4A; padding: 2px 16px; border-radius: 30px; font-weight: 700; font-size: 0.7rem; letter-spacing: 1px; }
    .header-right { text-align: right; color: #D4AF37; border-left: 2px solid #D4AF37; padding-left: 20px; }
    .header-right small { color: #B0C4DE; display: block; }

    /* साइडबार */
    section[data-testid="stSidebar"] {
        background-color: #0B2A4A !important;
        padding-top: 0;
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stRadio label { 
        padding: 10px 15px; 
        border-radius: 8px; 
        width: 100%; 
        transition: 0.2s;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stRadio label:hover { background: #1A4B6D; }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px; }
    
    /* कार्ड */
    .gov-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border-left: 6px solid #D4AF37;
        margin-bottom: 1.2rem;
        transition: 0.2s;
    }
    .gov-card:hover { box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
    .stat-box {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        border-bottom: 4px solid #D4AF37;
    }
    .stat-box h2 { color: #0B2A4A; font-size: 2.4rem; font-weight: 800; margin: 0; }
    .stat-box p { color: #4B5563; font-weight: 500; margin: 0; }

    /* इनपुट बॉक्स (Offline visibility fix) */
    .stTextInput input { background: white !important; color: black !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; }
    .stButton button { background: #D4AF37 !important; color: #0B2A4A !important; font-weight: 700 !important; border-radius: 30px !important; border: none !important; padding: 0.5rem 2rem !important; width: 100% !important; }
    .stButton button:hover { background: #C5A028 !important; transform: scale(1.02); }
    
    .footer {
        background: #0B2A4A;
        color: #B0C4DE;
        padding: 1.2rem 2rem;
        border-radius: 20px 20px 0 0;
        margin-top: 3rem;
        text-align: center;
        border-top: 4px solid #D4AF37;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# 🎯 SVG आइकॉन (सारे इमोजी हटाकर)
# ====================================================================
def svg_icon(name, size=24, color="#FFFFFF"):
    icons = {
        "gov": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
        "dashboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        "donor": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v4M12 22v-4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M22 12h-4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>',
        "patient": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><path d="M12 11v4M10 13h4"/></svg>',
        "camp": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v20M2 12h20M4 4l16 16M4 20l16-16"/><circle cx="12" cy="12" r="2"/></svg>',
        "bill": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
        "log": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v4M12 22v-4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M22 12h-4"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>',
        "lock": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        "receipt": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M4 4h16v16H4z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>',
    }
    return icons.get(name, "")

# ====================================================================
# 📂 डेटा लोड/सेव (Offline CSV)
# ====================================================================
def load_data(filename, default):
    try:
        if os.path.exists(filename):
            return pd.read_csv(filename).to_dict('records')
        return default
    except:
        return default

def save_data(filename, data):
    pd.DataFrame(data).to_csv(filename, index=False)

# इनिशियलाइज़ स्टेट
if 'donors' not in st.session_state:
    st.session_state.donors = load_data('donors.csv', [])
if 'patients' not in st.session_state:
    st.session_state.patients = load_data('patients.csv', [])
if 'camps' not in st.session_state:
    st.session_state.camps = load_data('camps.csv', [])
if 'bills' not in st.session_state:
    st.session_state.bills = load_data('bills.csv', [{'id':1, 'vendor':'Urban Rehab', 'desc':'Therapist Visit', 'amount':15000, 'status':'Pending'}])
if 'logs' not in st.session_state:
    st.session_state.logs = load_data('logs.csv', [])
if 'receipt_counter' not in st.session_state:
    st.session_state.receipt_counter = 100

def log_action(action):
    st.session_state.logs.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user': st.session_state.user,
        'action': action
    })
    save_data('logs.csv', st.session_state.logs)

# ====================================================================
# 🏛️ हेडर (Govt Look)
# ====================================================================
st.markdown(f"""
<div class="main-header">
    <div class="header-left">
        <div style="background:#D4AF37; width:50px; height:50px; border-radius:50%; display:flex; align-items:center; justify-content:center;">
            {svg_icon('gov', 32, '#0B2A4A')}
        </div>
        <div>
            <div style="display:flex; align-items:center; gap:12px;">
                <h1>NPRC GLOBAL</h1>
                <span class="badge-gold">TRUST</span>
            </div>
            <h2>National Physiotherapy & Rehabilitation Council</h2>
            <p>Ministry of Health | Govt. of India</p>
        </div>
    </div>
    <div class="header-right">
        <small>80G Exemption</small>
        <strong style="font-size:1.2rem;">PAN: AABTN1234C</strong>
    </div>
</div>
""", unsafe_allow_html=True)

# ====================================================================
# 📌 साइडबार नेविगेशन (इमोजी मुक्त)
# ====================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:20px 0; border-bottom:2px solid #D4AF37;">
        <div style="background:#D4AF37; width:70px; height:70px; border-radius:50%; margin:0 auto; display:flex; align-items:center; justify-content:center;">
            {svg_icon('gov', 40, '#0B2A4A')}
        </div>
        <h4 style="color:#D4AF37; margin-top:10px;">Offline Portal</h4>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.markdown('<div style="background:#1A3A5C; padding:10px; border-radius:8px; border:1px solid #D4AF37; text-align:center; margin:10px 0;"><span style="color:#D4AF37;">🔐 SECURE LOGIN</span></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Username", placeholder="Enter Username")
            pwd = st.text_input("Password", type="password", placeholder="Enter Password")
            if st.form_submit_button("Authenticate"):
                if login(user, pwd):
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        st.stop()  # अगर लॉगिन नहीं है तो यहीं रुकें
    else:
        st.markdown(f"""
        <div style="background:#1A3A5C; padding:8px; border-radius:8px; border-left:4px solid #28A745; margin:10px 0;">
            <p style="margin:0; color:#28A745; font-size:0.8rem;">Active Session</p>
            <p style="margin:0; font-weight:bold;">{st.session_state.user}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout()

        st.markdown("---")
        # Navigation using Radio (Text only, Emoji-free)
        page = st.radio(
            label="Navigation",
            options=[
                "Overview Dashboard",
                "Donor Management",
                "Patient Registry",
                "Camp Management",
                "Vendor Bills",
                "Audit Logs"
            ],
            index=0
        )
        st.markdown("---")
        st.caption("Version 3.0 | Offline Mode")

# ====================================================================
# 🧭 पेज हैंडलर
# ====================================================================

# --- DASHBOARD ---
if page == "Overview Dashboard":
    st.markdown(f"<h2 style='display:flex; align-items:center; gap:10px;'>{svg_icon('dashboard', 30, '#0B2A4A')} Executive Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.donors)}</h2><p>{svg_icon('donor', 18, '#0B2A4A')} Donors</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.patients)}</h2><p>{svg_icon('patient', 18, '#0B2A4A')} Patients</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.camps)}</h2><p>{svg_icon('camp', 18, '#0B2A4A')} Camps</p></div>", unsafe_allow_html=True)
    with col4:
        total_donations = sum([d['amount'] for d in st.session_state.donors]) if st.session_state.donors else 0
        st.markdown(f"<div class='stat-box'><h2>₹{total_donations:,.0f}</h2><p>{svg_icon('receipt', 18, '#0B2A4A')} Funds Raised</p></div>", unsafe_allow_html=True)

    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        if st.session_state.donors:
            df = pd.DataFrame(st.session_state.donors)
            fig = px.pie(df, values='amount', names='name', title='Donor Contribution', color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color='#0B2A4A'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No donor data to display.")
    with col_chart2:
        if st.session_state.camps:
            df = pd.DataFrame(st.session_state.camps)
            fig = px.bar(df, x='location', y='expenses', title='Camp Expenses by Location', color='location', color_discrete_sequence=px.colors.sequential.Gold_r)
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color='#0B2A4A'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No camp data to display.")

# --- DONOR MANAGEMENT ---
elif page == "Donor Management":
    st.markdown(f"<h2>{svg_icon('donor', 30, '#0B2A4A')} Donor Management</h2>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("add_donor"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: name = st.text_input("Full Name")
        with c2: pan = st.text_input("PAN Card")
        with c3: email = st.text_input("Email")
        with c4: amount = st.number_input("Amount (₹)", min_value=100, step=100)
        if st.form_submit_button("Register Donor"):
            if name and pan and amount:
                st.session_state.receipt_counter += 1
                st.session_state.donors.append({
                    'id': len(st.session_state.donors)+1,
                    'name': name, 'pan': pan, 'email': email, 'amount': amount,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'receipt_no': f"NPRC-{st.session_state.receipt_counter:04d}"
                })
                save_data('donors.csv', st.session_state.donors)
                log_action(f"Added Donor: {name} (₹{amount})")
                st.success("Donor Registered")
    if st.session_state.donors:
        st.dataframe(pd.DataFrame(st.session_state.donors), use_container_width=True)

# --- PATIENT REGISTRY ---
elif page == "Patient Registry":
    st.markdown(f"<h2>{svg_icon('patient', 30, '#0B2A4A')} Patient Registry</h2>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("add_patient"):
        c1, c2, c3 = st.columns(3)
        with c1: p_name = st.text_input("Patient Name")
        with c2: p_age = st.number_input("Age", min_value=1, step=1)
        with c3: p_cond = st.selectbox("Condition", ["Stroke", "Paralysis", "Fracture", "Post-Surgery", "Other"])
        p_village = st.text_input("Village / Location")
        if st.form_submit_button("Add Patient Record"):
            if p_name:
                st.session_state.patients.append({
                    'id': len(st.session_state.patients)+1,
                    'name': p_name, 'age': p_age, 'condition': p_cond,
                    'village': p_village, 'status': 'Active',
                    'reg_date': datetime.now().strftime("%Y-%m-%d")
                })
                save_data('patients.csv', st.session_state.patients)
                log_action(f"Added Patient: {p_name}")
                st.success("Patient Added")
    if st.session_state.patients:
        st.dataframe(pd.DataFrame(st.session_state.patients), use_container_width=True)

# --- CAMP MANAGEMENT ---
elif page == "Camp Management":
    st.markdown(f"<h2>{svg_icon('camp', 30, '#0B2A4A')} Rural Health Camps</h2>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("add_camp"):
        c1, c2, c3 = st.columns(3)
        with c1: loc = st.text_input("Location")
        with c2: date = st.date_input("Date")
        with c3: exp = st.number_input("Expenses (₹)", min_value=0, step=100)
        if st.form_submit_button("Schedule Camp"):
            if loc:
                st.session_state.camps.append({
                    'id': len(st.session_state.camps)+1,
                    'location': loc, 'date': str(date), 'expenses': exp,
                    'created': datetime.now().strftime("%Y-%m-%d")
                })
                save_data('camps.csv', st.session_state.camps)
                log_action(f"Scheduled Camp at {loc}")
                st.success("Camp Scheduled")
    if st.session_state.camps:
        st.dataframe(pd.DataFrame(st.session_state.camps), use_container_width=True)

# --- VENDOR BILLS ---
elif page == "Vendor Bills":
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Vendor Bill Approvals</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if not st.session_state.bills:
        st.info("No bills pending.")
    else:
        df = pd.DataFrame(st.session_state.bills)
        st.dataframe(df, use_container_width=True)
        st.subheader("Process Bill")
        pending = [b for b in st.session_state.bills if b['status'] == 'Pending']
        if pending:
            opts = {f"{b['id']} - {b['desc']} (₹{b['amount']})": b for b in pending}
            sel = st.selectbox("Select Bill", list(opts.keys()))
            bill = opts[sel]
            c1, c2 = st.columns(2)
            if c1.button("Approve"):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']:
                        b['status'] = 'Approved'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Approved Bill #{bill['id']}")
                st.success("Bill Approved")
                st.rerun()
            if c2.button("Reject"):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']:
                        b['status'] = 'Rejected'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Rejected Bill #{bill['id']}")
                st.warning("Bill Rejected")
                st.rerun()

# --- AUDIT LOGS ---
elif page == "Audit Logs":
    st.markdown(f"<h2>{svg_icon('log', 30, '#0B2A4A')} System Audit Trail</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Every action performed in the system is logged here for compliance.")
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        st.dataframe(df, use_container_width=True, height=400)
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        st.markdown(f'<a href="data:file/csv;base64,{b64}" download="audit_logs.csv" style="background:#0B2A4A; color:white; padding:8px 16px; border-radius:30px; text-decoration:none;">Download Audit Logs</a>', unsafe_allow_html=True)
    else:
        st.info("No logs recorded yet.")

# ====================================================================
# 📌 फुटर
# ====================================================================
st.markdown(f"""
<div class="footer">
    <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
        <div>NPRC Global Trust | Regd. under Indian Trusts Act</div>
        <div>80G: AABTN1234C | 12A Registered</div>
        <div>Offline System v3.0</div>
    </div>
    <div style="margin-top:8px; opacity:0.6; font-size:0.8rem;">All data is stored locally. No internet connection required.</div>
</div>
""", unsafe_allow_html=True)

# पहली बार CSV बनाएं
if __name__ == "__main__":
    if not os.path.exists('donors.csv'): save_data('donors.csv', [])
    if not os.path.exists('patients.csv'): save_data('patients.csv', [])
    if not os.path.exists('camps.csv'): save_data('camps.csv', [])
    if not os.path.exists('bills.csv'): save_data('bills.csv', [{'id':1, 'vendor':'Urban Rehab', 'desc':'Therapist Visit', 'amount':15000, 'status':'Pending'}])
    if not os.path.exists('logs.csv'): save_data('logs.csv', [])
