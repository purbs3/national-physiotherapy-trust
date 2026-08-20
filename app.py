import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import io
import base64
import zipfile
import urllib.parse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors

# ---------- पेज कॉन्फ़िग ----------
st.set_page_config(
    page_title="NPRC Global - National Physiotherapy Trust",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# 🔐 ऑफलाइन ऑथेंटिकेशन (config.json से)
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
# 🎨 डार्क/लाइट थीम + CSS (Govt Look)
# ====================================================================
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if st.session_state.dark_mode:
    bg_main = "#0E1117"
    bg_sidebar = "#1A1A2E"
    bg_card = "#16213E"
    text_color = "#E0E0E0"
    border_color = "#D4AF37"
    shadow = "0 2px 12px rgba(0,0,0,0.5)"
else:
    bg_main = "#F4F7FC"
    bg_sidebar = "#0B2A4A"
    bg_card = "#FFFFFF"
    text_color = "#0B2A4A"
    border_color = "#D4AF37"
    shadow = "0 2px 12px rgba(0,0,0,0.04)"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_main}; }}
    section[data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    .main-header {{
        background: linear-gradient(135deg, #0B2A4A 0%, #1A4B6D 100%);
        padding: 1.2rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
        border-bottom: 4px solid #D4AF37;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    .header-left h1 {{ color: white; font-weight: 300; font-size: 1.4rem; margin:0; }}
    .header-left h2 {{ color: white; font-weight: 700; font-size: 1.8rem; margin:0; }}
    .badge-gold {{ background: #D4AF37; color: #0B2A4A; padding: 2px 16px; border-radius: 30px; font-weight: 700; font-size: 0.7rem; }}
    .gov-card {{
        background: {bg_card};
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: {shadow};
        border-left: 6px solid {border_color};
        margin-bottom: 1.2rem;
        color: {text_color};
    }}
    .stat-box {{
        background: {bg_card};
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: {shadow};
        border-bottom: 4px solid {border_color};
        color: {text_color};
    }}
    .stat-box h2 {{ color: {text_color}; font-size: 2.2rem; font-weight: 800; margin: 0; }}
    .stat-box p {{ color: #4B5563; font-weight: 500; margin: 0; }}
    .alert-card {{
        background: #FEF9E7;
        border-left: 6px solid #F1C40F;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #0B2A4A;
    }}
    .footer {{
        background: #0B2A4A;
        color: #B0C4DE;
        padding: 1.2rem 2rem;
        border-radius: 20px 20px 0 0;
        margin-top: 3rem;
        text-align: center;
        border-top: 4px solid #D4AF37;
    }}
    .stTextInput input, .stNumberInput input, .stSelectbox div {{
        background: {bg_card} !important;
        color: {text_color} !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }}
    .stButton button {{
        background: #D4AF37 !important;
        color: #0B2A4A !important;
        font-weight: 700 !important;
        border-radius: 30px !important;
        border: none !important;
    }}
</style>
""", unsafe_allow_html=True)

# ====================================================================
# 🎯 SVG आइकॉन
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
        "settings": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
        "report": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    }
    return icons.get(name, "")

# ====================================================================
# 📂 डेटा फंक्शन्स
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

if 'donors' not in st.session_state:
    st.session_state.donors = load_data('donors.csv', [])
if 'patients' not in st.session_state:
    st.session_state.patients = load_data('patients.csv', [])
if 'camps' not in st.session_state:
    st.session_state.camps = load_data('camps.csv', [])
if 'bills' not in st.session_state:
    st.session_state.bills = load_data('bills.csv', [{'id':1, 'vendor':'Urban Rehab', 'desc':'Therapist Visit', 'amount':15000, 'status':'Pending'}])
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_data('expenses.csv', [])
if 'logs' not in st.session_state:
    st.session_state.logs = load_data('logs.csv', [])
if 'receipt_counter' not in st.session_state:
    st.session_state.receipt_counter = 100

def log_action(action):
    st.session_state.logs.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user': st.session_state.user if 'user' in st.session_state else 'admin',
        'action': action
    })
    save_data('logs.csv', st.session_state.logs)

# 80G रसीद जनरेटर फंक्शन
def generate_80g_receipt(donor):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # हेडर
    c.setFillColorRGB(0.043, 0.165, 0.294)
    c.rect(0, height-90, width, 90, fill=1)
    c.setFillColorRGB(0.831, 0.686, 0.215)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height-40, "NPRC GLOBAL TRUST")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 9)
    c.drawString(40, height-58, "National Physiotherapy & Rehabilitation Council | Regd. Indian Trusts Act")
    c.drawString(40, height-72, "80G Order No: ITBA/EXM/80G/2024-25/101 | PAN: AABTN1234C")
    
    # रसीद टाइटल
    c.setFillColorRGB(0.043, 0.165, 0.294)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height-120, "DONATION RECEIPT (UNDER SECTION 80G OF I.T. ACT)")
    
    c.setStrokeColorRGB(0.831, 0.686, 0.215)
    c.setLineWidth(1)
    c.line(40, height-130, width-40, height-130)
    
    # डिटेल्स
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    y = height - 160
    c.drawString(40, y, f"Receipt No: {donor.get('receipt_no', 'NPRC-REC')}")
    c.drawString(width-200, y, f"Date: {donor.get('date', datetime.now().strftime('%Y-%m-%d'))}")
    
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Received with thanks from:")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(200, y, f"{donor.get('name', 'Anonymous')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Donor PAN:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(200, y, f"{donor.get('pan', 'N/A')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Email Address:")
    c.drawString(200, y, f"{donor.get('email', 'N/A')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Donation Amount:")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(200, y, f"INR {donor.get('amount', 0):,.2f}")
    
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, y, "This donation is eligible for deduction under Section 80G of the Income Tax Act, 1961.")
    
    y -= 60
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width-50, y, "For NPRC GLOBAL TRUST")
    y -= 30
    c.setFont("Helvetica", 8)
    c.drawRightString(width-50, y, "Authorized Signatory")
    
    c.setFillColorRGB(0.043, 0.165, 0.294)
    c.rect(0, 0, width, 25, fill=1)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica", 8)
    c.drawString(40, 9, "Official Computer Generated Document | NPRC Global Compliance Portal")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ====================================================================
# 🏛️ हेडर
# ====================================================================
st.markdown(f"""
<div class="main-header">
    <div style="display:flex; align-items:center; gap:20px;">
        <div style="background:#D4AF37; width:50px; height:50px; border-radius:50%; display:flex; align-items:center; justify-content:center;">
            {svg_icon('gov', 32, '#0B2A4A')}
        </div>
        <div>
            <div style="display:flex; align-items:center; gap:12px;">
                <h1>NPRC GLOBAL</h1>
                <span class="badge-gold">TRUST</span>
            </div>
            <h2>National Physiotherapy & Rehabilitation Council</h2>
            <p style="color:#B0C4DE; margin:0;">Ministry of Health | Govt. of India</p>
        </div>
    </div>
    <div style="text-align:right; color:#D4AF37;">
        <small>80G Exemption</small>
        <div><strong>PAN: AABTN1234C</strong></div>
        <small style="color:#B0C4DE; font-size:0.7rem;">Offline v4.2</small>
    </div>
</div>
""", unsafe_allow_html=True)

# ====================================================================
# 📌 साइडबार + Login
# ====================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:15px 0; border-bottom:2px solid #D4AF37;">
        <div style="background:#D4AF37; width:60px; height:60px; border-radius:50%; margin:0 auto; display:flex; align-items:center; justify-content:center;">
            {svg_icon('gov', 35, '#0B2A4A')}
        </div>
        <h4 style="color:#D4AF37; margin-top:10px;">NPRC Portal</h4>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.authenticated:
        with st.form("login_form"):
            st.text_input("Username", key="u")
            st.text_input("Password", type="password", key="p")
            if st.form_submit_button("Authenticate"):
                if login(st.session_state.u, st.session_state.p):
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid")
        st.stop()
    else:
        st.markdown(f"""
        <div style="background:#1A3A5C; padding:8px; border-radius:8px; border-left:4px solid #28A745; margin:10px 0;">
            <p style="margin:0; color:#28A745;">Active Session</p>
            <p style="margin:0; font-weight:bold;">{st.session_state.user}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True):
            logout()

        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["Dashboard", "Donors", "Patients", "Camps", "Expenses", "Bills", "Reports", "Settings"]
        )
        st.markdown("---")
        st.caption("NPRC v4.2 | Offline Production")

# ====================================================================
# 🧭 पेज हैंडलिंग
# ====================================================================

# ========== 1. DASHBOARD ==========
if page == "Dashboard":
    st.markdown(f"<h2>{svg_icon('dashboard', 30, '#0B2A4A')} Executive Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    pending_bills = len([b for b in st.session_state.bills if b['status']=='Pending'])
    today = datetime.now().date()
    followups = len([p for p in st.session_state.patients if 'next_followup' in p and datetime.strptime(str(p['next_followup']), '%Y-%m-%d').date() <= today + timedelta(days=3)])
    
    if pending_bills > 0 or followups > 0:
        st.markdown('<div style="background:#FEF9E7; padding:15px; border-radius:10px; border-left:6px solid #F1C40F; margin-bottom:20px;"><strong>System Notifications</strong>', unsafe_allow_html=True)
        if pending_bills > 0: st.markdown(f'- {pending_bills} bill(s) pending approval.')
        if followups > 0: st.markdown(f'- {followups} patient(s) due for clinical follow-up within 3 days.')
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    total_donations = sum(d['amount'] for d in st.session_state.donors)
    total_expenses = sum(e['amount'] for e in st.session_state.expenses)
    with col1: st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.donors)}</h2><p>{svg_icon('donor',18,'#0B2A4A')} Donors</p></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.patients)}</h2><p>{svg_icon('patient',18,'#0B2A4A')} Patients</p></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='stat-box'><h2>₹{total_donations:,.0f}</h2><p>Funds Raised</p></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='stat-box'><h2>₹{total_expenses:,.0f}</h2><p>Total Expenses</p></div>", unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.session_state.donors:
            df = pd.DataFrame(st.session_state.donors)
            fig = px.pie(df, values='amount', names='name', title='Donor Contribution')
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    with col_c2:
        if st.session_state.expenses:
            df = pd.DataFrame(st.session_state.expenses)
            fig = px.bar(df, x='category', y='amount', title='Expense by Category', color='category')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ========== 2. DONORS (80G RECEIPT GENERATION) ==========
elif page == "Donors":
    st.markdown(f"<h2>{svg_icon('donor', 30, '#0B2A4A')} Donor Management & 80G Receipts</h2>", unsafe_allow_html=True)
    with st.form("add_donor"):
        c1,c2,c3,c4 = st.columns(4)
        with c1: name = st.text_input("Full Name")
        with c2: pan = st.text_input("PAN (for 80G Tax Exemption)")
        with c3: email = st.text_input("Email")
        with c4: amt = st.number_input("Amount (₹)", min_value=100)
        if st.form_submit_button("Register Donor"):
            if name and amt:
                st.session_state.receipt_counter += 1
                st.session_state.donors.append({
                    'id': len(st.session_state.donors)+1, 'name': name, 'pan': pan,
                    'email': email, 'amount': amt, 'date': datetime.now().strftime("%Y-%m-%d"),
                    'receipt_no': f"NPRC-{st.session_state.receipt_counter:04d}"
                })
                save_data('donors.csv', st.session_state.donors)
                log_action(f"Added Donor: {name}")
                st.success("Donor Registered & 80G Receipt Created")

    if st.session_state.donors:
        st.markdown("#### Registered Donors Registry")
        for donor in st.session_state.donors:
            cd1, cd2, cd3, cd4 = st.columns([3, 2, 2, 2])
            with cd1: st.write(f"**{donor['name']}** ({donor.get('receipt_no', 'REC')})")
            with cd2: st.write(f"PAN: `{donor.get('pan', 'N/A')}`")
            with cd3: st.write(f"₹{donor.get('amount', 0):,.2f}")
            with cd4:
                pdf_bytes = generate_80g_receipt(donor)
                st.download_button(
                    label="📄 80G Receipt",
                    data=pdf_bytes,
                    file_name=f"80G_Receipt_{donor.get('receipt_no', 'NPRC')}.pdf",
                    mime="application/pdf",
                    key=f"dl_rec_{donor['id']}"
                )

# ========== 3. PATIENTS (WHATSAPP REMINDERS) ==========
elif page == "Patients":
    st.markdown(f"<h2>{svg_icon('patient', 30, '#0B2A4A')} Patient Registry & Follow-up Hub</h2>", unsafe_allow_html=True)
    with st.form("add_patient"):
        c1,c2,c3 = st.columns(3)
        with c1: name = st.text_input("Name")
        with c2: age = st.number_input("Age", min_value=1)
        with c3: cond = st.selectbox("Condition", ["Stroke", "Paralysis", "Fracture", "Post-Surgery", "CP Child", "Other"])
        
        c4,c5,c6 = st.columns(3)
        with c4: village = st.text_input("Village / Location")
        with c5: status = st.selectbox("Status", ["Active", "Recovered", "Referred", "Dropout"])
        with c6: contact = st.text_input("Contact Phone Number")
        
        c7,c8 = st.columns(2)
        with c7: last_visit = st.date_input("Last Visit")
        with c8: next_followup = st.date_input("Next Follow-up")
        
        if st.form_submit_button("Add Patient"):
            if name:
                st.session_state.patients.append({
                    'id': len(st.session_state.patients)+1, 'name': name, 'age': age,
                    'condition': cond, 'village': village, 'status': status,
                    'contact': contact,
                    'last_visit': str(last_visit), 'next_followup': str(next_followup),
                    'reg_date': datetime.now().strftime("%Y-%m-%d")
                })
                save_data('patients.csv', st.session_state.patients)
                log_action(f"Added Patient: {name}")
                st.success("Patient Added")

    if st.session_state.patients:
        st.markdown("#### Patient Roster & Follow-up Actions")
        for p in st.session_state.patients:
            cp1, cp2, cp3, cp4 = st.columns([3, 2, 2, 3])
            with cp1: st.write(f"**{p['name']}** ({p.get('condition')})")
            with cp2: st.write(f"Village: {p.get('village', 'N/A')}")
            with cp3: st.write(f"Follow-up: `{p.get('next_followup', 'N/A')}`")
            with cp4:
                # WhatsApp Reminder Link
                msg = f"Namaste {p['name']}, this is a reminder from NPRC Global Physiotherapy Trust. Your clinical rehab follow-up is scheduled for {p.get('next_followup')}. Please visit the center."
                encoded_msg = urllib.parse.quote(msg)
                phone_num = p.get('contact', '').replace('+', '').replace(' ', '')
                wa_url = f"https://wa.me/{phone_num}?text={encoded_msg}" if phone_num else f"https://wa.me/?text={encoded_msg}"
                st.link_button("📲 WhatsApp Reminder", wa_url, key=f"wa_{p['id']}")

# ========== 4. CAMPS ==========
elif page == "Camps":
    st.markdown(f"<h2>{svg_icon('camp', 30, '#0B2A4A')} Camp Management</h2>", unsafe_allow_html=True)
    with st.form("add_camp"):
        c1,c2,c3 = st.columns(3)
        with c1: loc = st.text_input("Location")
        with c2: date = st.date_input("Date")
        with c3: exp = st.number_input("Expenses (₹)", min_value=0)
        if st.form_submit_button("Schedule Camp"):
            if loc:
                st.session_state.camps.append({
                    'id': len(st.session_state.camps)+1, 'location': loc,
                    'date': str(date), 'expenses': exp
                })
                save_data('camps.csv', st.session_state.camps)
                log_action(f"Scheduled Camp at {loc}")
                st.success("Camp Scheduled")
    if st.session_state.camps:
        st.dataframe(pd.DataFrame(st.session_state.camps), use_container_width=True)

# ========== 5. EXPENSES ==========
elif page == "Expenses":
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Expense Ledger</h2>", unsafe_allow_html=True)
    with st.form("add_expense"):
        c1,c2,c3 = st.columns(3)
        with c1: cat = st.selectbox("Category", ["Office", "Staff Salary", "Equipment", "Travel", "Medicine", "Camp Logistics", "Other"])
        with c2: desc = st.text_input("Description")
        with c3: amt = st.number_input("Amount (₹)", min_value=0)
        if st.form_submit_button("Add Expense"):
            if desc and amt:
                st.session_state.expenses.append({
                    'id': len(st.session_state.expenses)+1, 'category': cat,
                    'description': desc, 'amount': amt,
                    'date': datetime.now().strftime("%Y-%m-%d")
                })
                save_data('expenses.csv', st.session_state.expenses)
                log_action(f"Added Expense: {desc}")
                st.success("Expense Added")
    if st.session_state.expenses:
        st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)

# ========== 6. BILLS ==========
elif page == "Bills":
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Vendor Bills</h2>", unsafe_allow_html=True)
    if not st.session_state.bills:
        st.info("No bills")
    else:
        df = pd.DataFrame(st.session_state.bills)
        st.dataframe(df, use_container_width=True)
        pending = [b for b in st.session_state.bills if b['status']=='Pending']
        if pending:
            opts = {f"{b['id']} - {b['desc']}": b for b in pending}
            sel = st.selectbox("Select Bill", list(opts.keys()))
            bill = opts[sel]
            c1,c2 = st.columns(2)
            if c1.button("Approve"):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']: b['status']='Approved'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Approved Bill #{bill['id']}")
                st.rerun()
            if c2.button("Reject"):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']: b['status']='Rejected'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Rejected Bill #{bill['id']}")
                st.rerun()

# ========== 7. REPORTS ==========
elif page == "Reports":
    st.markdown(f"<h2>{svg_icon('report', 30, '#0B2A4A')} Compliance Reports</h2>", unsafe_allow_html=True)
    year = st.selectbox("Financial Year", ["2024-25", "2025-26", "2026-27"])
    
    if st.button("Generate Annual Report (PDF)"):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        c.setFillColorRGB(0.043, 0.165, 0.294)
        c.rect(0, height-80, width, 80, fill=1)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height-50, "NPRC GLOBAL TRUST")
        c.setFont("Helvetica", 10)
        c.drawString(40, height-70, f"Annual Compliance Report - FY {year}")
        
        c.setFillColorRGB(0,0,0)
        y = height - 120
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "1. Donor Summary")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Total Donors: {len(st.session_state.donors)}")
        y -= 15
        c.drawString(60, y, f"Total Funds: ₹{sum(d['amount'] for d in st.session_state.donors):,.2f}")
        
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "2. Patient Impact")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Total Patients Treated: {len(st.session_state.patients)}")
        y -= 15
        recovered = len([p for p in st.session_state.patients if p.get('status')=='Recovered'])
        c.drawString(60, y, f"Recovered: {recovered}")
        
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "3. Financial Summary")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Total Expenses: ₹{sum(e['amount'] for e in st.session_state.expenses):,.2f}")
        y -= 15
        c.drawString(60, y, f"Net Balance: ₹{(sum(d['amount'] for d in st.session_state.donors) - sum(e['amount'] for e in st.session_state.expenses)):,.2f}")

        c.setFillColorRGB(0.043, 0.165, 0.294)
        c.rect(0, 20, width, 30, fill=1)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica", 8)
        c.drawString(40, 30, "This is a system-generated report for internal compliance.")
        c.save()
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Annual_Report_{year}.pdf" style="background:#D4AF37; color:#0B2A4A; padding:12px 25px; border-radius:30px; text-decoration:none; font-weight:bold;">⬇️ Download PDF Report</a>', unsafe_allow_html=True)

# ========== 8. SETTINGS ==========
elif page == "Settings":
    st.markdown(f"<h2>{svg_icon('settings', 30, '#0B2A4A')} System Settings</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("Toggle Dark Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    
    st.markdown("---")
    st.subheader("Data Backup & Restore")
    
    if st.button("Create Full Backup (ZIP)"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for f in ['donors.csv', 'patients.csv', 'camps.csv', 'bills.csv', 'expenses.csv', 'logs.csv']:
                if os.path.exists(f):
                    zf.write(f)
        zip_buffer.seek(0)
        b64_zip = base64.b64encode(zip_buffer.getvalue()).decode()
        st.markdown(f'<a href="data:application/zip;base64,{b64_zip}" download="NPRC_Backup_{datetime.now().strftime("%Y%m%d")}.zip" style="background:#0B2A4A; color:white; padding:10px 20px; border-radius:30px; text-decoration:none;">Download Backup ZIP</a>', unsafe_allow_html=True)
        log_action("Created Backup")
    
    uploaded = st.file_uploader("Restore from Backup", type=['zip'])
    if uploaded:
        with zipfile.ZipFile(uploaded, 'r') as zf:
            zf.extractall('.')
        st.success("Restore Successful! Reloading...")
        log_action("Restored from Backup")
        st.rerun()

# ====================================================================
# 📌 फुटर
# ====================================================================
st.markdown(f"""
<div class="footer">
    <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
        <div>NPRC Global Trust | Regd. under Indian Trusts Act</div>
        <div>80G: AABTN1234C | 12A Registered</div>
        <div>Offline System v4.2</div>
    </div>
    <div style="margin-top:8px; opacity:0.6; font-size:0.8rem;">All data is stored locally. No internet connection required.</div>
</div>
""", unsafe_allow_html=True)

# पहली बार CSV बनाएं
if __name__ == "__main__":
    for f in ['donors.csv', 'patients.csv', 'camps.csv', 'bills.csv', 'expenses.csv', 'logs.csv']:
        if not os.path.exists(f):
            save_data(f, [])
    if not os.path.exists('bills.csv'):
        save_data('bills.csv', [{'id':1, 'vendor':'Urban Rehab', 'desc':'Therapist Visit', 'amount':15000, 'status':'Pending'}])
