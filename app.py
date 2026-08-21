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
import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ---------- पेज कॉन्फ़िग ----------
st.set_page_config(
    page_title="NPRC Global - National Physiotherapy Trust",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ---------- PWA (Mobile App) Meta Tags ----------
st.markdown("""
    <style>
        /* मोबाइल ऐप जैसा फील देने के लिए टेक्स्ट सेलेक्शन और हाईलाइट बंद करें */
        .stApp {
            -webkit-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
    </style>
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#0B2A4A">
""", unsafe_allow_html=True)

# ====================================================================
# 🖼️ कस्टम लोगो लोडर (NPRC GLOBAL LOGO)
# ====================================================================
LOGO_PATH = "nprc_logo.png"  # अपने लोगो का नाम यही रखें और फोल्डर में डाल दें

def get_logo_base64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_b64 = get_logo_base64()

if logo_b64:
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">'
else:
    logo_html = f'<div style="color:#0B2A4A; font-weight:bold; font-size:12px;">LOGO<br>HERE</div>'

# ====================================================================
# 1. 🔐 SECURE CREDENTIAL MANAGEMENT (SHA-256 HASHED)
# ====================================================================
DEFAULT_USER = "admin"
DEFAULT_PW_HASH = hashlib.sha256("NPRC@2026".encode()).hexdigest()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_credentials():
    try:
        with open('config.json', 'r') as f:
            data = json.load(f)
            return data.get('username', DEFAULT_USER), data.get('password_hash', DEFAULT_PW_HASH)
    except:
        return DEFAULT_USER, DEFAULT_PW_HASH

def save_credentials(username, password_hash):
    with open('config.json', 'w') as f:
        json.dump({'username': username, 'password_hash': password_hash}, f, indent=4)

def login(username, password):
    correct_username, correct_pw_hash = load_credentials()
    if username == correct_username and hash_pw(password) == correct_pw_hash:
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
# 2. 🎨 डार्क/लाइट थीम + CSS (Footer Removed)
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
    
    /* Responsive Header Base */
    .main-header {{
        background: linear-gradient(135deg, #0B2A4A 0%, #1A4B6D 100%);
        padding: 1.2rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
        border-bottom: 4px solid #D4AF37;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap; /* जगह कम होने पर नीचे खिसकाएं */
        gap: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    /* Logo Container Fix - इसे सिकुड़ने से रोकेगा */
    .logo-container {{
        background: white; 
        width: 65px; 
        height: 65px; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); 
        overflow: hidden;
        flex-shrink: 0; /* बहुत जरूरी: लोगो को दबने नहीं देगा */
    }}
    
    .header-left-wrap {{ display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }}
    .header-text-wrap h1 {{ color: white; font-weight: 800; font-size: 1.6rem; margin:0; line-height:1.2; }}
    .header-text-wrap h2 {{ color: white; font-weight: 500; font-size: 1.1rem; margin:5px 0 0 0; line-height:1.3; }}
    .header-text-wrap p {{ color: #B0C4DE; margin:0; font-size: 0.85rem; }}
    .badge-gold {{ background: #D4AF37; color: #0B2A4A; padding: 3px 12px; border-radius: 20px; font-weight: 800; font-size: 0.75rem; white-space: nowrap; }}
    .right-info {{ text-align: right; color: #D4AF37; }}
    
    /* ========================================= */
    /* 📱 MOBILE RESPONSIVENESS (Media Query)    */
    /* ========================================= */
    @media screen and (max-width: 768px) {{
        .main-header {{
            padding: 1rem;
            flex-direction: column; /* मोबाइल पर ऊपर-नीचे सेट करें */
            align-items: flex-start;
        }}
        .header-left-wrap {{
            gap: 12px;
            align-items: flex-start;
        }}
        .logo-container {{
            width: 50px; /* मोबाइल पर लोगो थोड़ा छोटा */
            height: 50px;
        }}
        .header-text-wrap h1 {{ font-size: 1.3rem; }}
        .header-text-wrap h2 {{ font-size: 0.95rem; }}
        .right-info {{
            text-align: left; /* मोबाइल पर टेक्स्ट लेफ्ट कर दें */
            width: 100%;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.1); /* बीच में एक हल्की लाइन */
        }}
    }}
    
    /* बाकी पुरानी CSS वैसी ही रहेगी */
    .stat-box {{ background: {bg_card}; padding: 1.2rem; border-radius: 12px; text-align: center; box-shadow: {shadow}; border-bottom: 4px solid {border_color}; color: {text_color}; }}
    .stat-box h2 {{ color: {text_color}; font-size: 2.2rem; font-weight: 800; margin: 0; }}
    .stat-box p {{ color: #4B5563; font-weight: 500; margin: 0; }}
    .footer {{ background: #0B2A4A; color: #B0C4DE; padding: 1.2rem 2rem; border-radius: 20px 20px 0 0; margin-top: 3rem; text-align: center; border-top: 4px solid #D4AF37; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div {{ background: {bg_card} !important; color: {text_color} !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; }}
    .stButton button {{ background: #D4AF37 !important; color: #0B2A4A !important; font-weight: 700 !important; border-radius: 30px !important; border: none !important; }}
</style>
""", unsafe_allow_html=True)

# ====================================================================
# 🎯 SVG आइकॉन लाइब्रेरी (फंक्शनल टैब्स के लिए)
# ====================================================================
def svg_icon(name, size=24, color="#FFFFFF"):
    icons = {
        "dashboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        "donor": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v4M12 22v-4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M22 12h-4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>',
        "patient": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><path d="M12 11v4M10 13h4"/></svg>',
        "camp": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v20M2 12h20M4 4l16 16M4 20l16-16"/><circle cx="12" cy="12" r="2"/></svg>',
        "bill": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
        "settings": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
        "report": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    }
    return icons.get(name, "")

# ====================================================================
# 📂 डेटा मैनेजमेंट फंक्शन्स
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
if 'rehab_logs' not in st.session_state:
    st.session_state.rehab_logs = load_data('rehab_logs.csv', [])
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

# 80G रसीद जनरेटर (PDF में लोगो सपोर्ट के साथ)
def generate_80g_receipt(donor):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFillColorRGB(0.043, 0.165, 0.294)
    c.rect(0, height-100, width, 100, fill=1)
    
    # अगर लोगो है तो PDF में भी लगाएं
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, 30, height-90, width=70, height=70, preserveAspectRatio=True, mask='auto')
        except:
            pass
            
    c.setFillColorRGB(0.831, 0.686, 0.215)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(120, height-40, "NPRC GLOBAL TRUST")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 9)
    c.drawString(120, height-58, "National Physiotherapy & Rehabilitation Council | Regd. Indian Trusts Act")
    c.drawString(120, height-72, "80G Order No: ITBA/EXM/80G/2024-25/101 | PAN: AABTN1234C")
    
    c.setFillColorRGB(0.043, 0.165, 0.294)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height-130, "DONATION RECEIPT (UNDER SECTION 80G OF I.T. ACT)")
    
    c.setStrokeColorRGB(0.831, 0.686, 0.215)
    c.setLineWidth(1)
    c.line(40, height-140, width-40, height-140)
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    y = height - 170
    c.drawString(40, y, f"Receipt No: {donor.get('receipt_no', 'NPRC-REC')}")
    c.drawString(width-200, y, f"Date: {donor.get('date', datetime.now().strftime('%Y-%m-%d'))}")
    
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Received with thanks from:")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(200, y, f"{donor.get('name', 'Anonymous')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Donor PAN:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(200, y, f"{donor.get('pan', 'N/A')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Email Address:")
    c.drawString(200, y, f"{donor.get('email', 'N/A')}")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Donation Amount:")
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
# 🏛️ हेडर (WITH LOGO)
# ====================================================================
st.markdown(f"""
<div class="main-header">
    <div style="display:flex; align-items:center; gap:20px;">
        <div style="background:white; width:200px; height:65px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 10px rgba(0,0,0,0.2); overflow:hidden;">
            {logo_html}
        </div>
        <div>
            <div style=" display:flex; align-items:center; gap:12px;">
                <h1 style ="font-size: 55px; color: #F8F6F0;">NPRC GLOBAL</h1>
                <span class="badge-gold">TRUST</span>
            </div>
            <h2>National Physiotherapy & Rehabilitation Council</h2>
            <p style="color:#B0C4DE; margin:0;">Ministry of Health | Govt. of India</p>
        </div>
    </div>
    <div style="text-align:right; color:#D4AF37;">
        <small>80G Exemption</small>
        <div><strong>PAN: AABTN1234C</strong></div>
        <small style="color:#B0C4DE; font-size:0.7rem;">Production v4.5</small>
    </div>
</div>
""", unsafe_allow_html=True)

# ====================================================================
# 📌 साइडबार + सुरक्षित लॉगिन (WITH LOGO)
# ====================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:15px 0; border-bottom:2px solid #D4AF37;">
        <div style="background:white; width:70px; height:70px; border-radius:50%; margin:0 auto; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 10px rgba(0,0,0,0.2); overflow:hidden;">
            {logo_html}
        </div>
        <h4 style="color:#D4AF37; margin-top:10px;">NPRC Portal</h4>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.authenticated:
        with st.form("login_form"):
            st.subheader("Secure Access")
            st.text_input("Username", key="u")
            st.text_input("Password", type="password", key="p")
            if st.form_submit_button("Authenticate (SHA-256)"):
                if login(st.session_state.u, st.session_state.p):
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
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
            ["Dashboard", "Donors", "Patients & Rehab", "Camps", "Expenses", "Bills", "Reports (FY Filter)", "Settings"]
        )
        st.markdown("---")
        st.caption("NPRC v4.5 | Secure Enterprise")

# ====================================================================
# 🧭 पेज हैंडलिंग
# ====================================================================

# ========== 1. DASHBOARD ==========
if page == "Dashboard":
    st.markdown(f"<h2>{svg_icon('dashboard', 30, '#0B2A4A')} Executive Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    pending_bills = len([b for b in st.session_state.bills if b.get('status')=='Pending'])
    today = datetime.now().date()
    followups = len([p for p in st.session_state.patients if 'next_followup' in p and str(p.get('next_followup')) not in ['None', ''] and datetime.strptime(str(p['next_followup']), '%Y-%m-%d').date() <= today + timedelta(days=3)])
    
    if pending_bills > 0 or followups > 0:
        st.markdown('<div style="background:#FEF9E7; padding:15px; border-radius:10px; border-left:6px solid #F1C40F; margin-bottom:20px;"><strong>System Notifications</strong>', unsafe_allow_html=True)
        if pending_bills > 0: st.markdown(f'- {pending_bills} bill(s) pending approval.')
        if followups > 0: st.markdown(f'- {followups} patient(s) due for clinical follow-up within 3 days.')
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    total_donations = sum(d.get('amount', 0) for d in st.session_state.donors)
    total_expenses = sum(e.get('amount', 0) for e in st.session_state.expenses)
    with col1: st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.donors)}</h2><p>{svg_icon('donor',18,'#0B2A4A')} Donors</p></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='stat-box'><h2>{len(st.session_state.patients)}</h2><p>{svg_icon('patient',18,'#0B2A4A')} Patients</p></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='stat-box'><h2>₹{total_donations:,.0f}</h2><p>Funds Raised</p></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='stat-box'><h2>₹{total_expenses:,.0f}</h2><p>Total Expenses</p></div>", unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if len(st.session_state.donors) > 0:
            df = pd.DataFrame(st.session_state.donors)
            fig = px.pie(df, values='amount', names='name', title='Donor Contribution Share')
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    with col_c2:
        if len(st.session_state.expenses) > 0:
            df = pd.DataFrame(st.session_state.expenses)
            fig = px.bar(df, x='category', y='amount', title='Expense Allocation by Category', color='category')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ========== 2. DONORS ==========
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

# ========== 3. PATIENTS (WITH REHAB ASSESSMENT) ==========
elif page == "Patients & Rehab":
    st.markdown(f"<h2>{svg_icon('patient', 30, '#0B2A4A')} Patient Registry & Clinical Rehab Hub</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📝 Register Patient", "📊 Patient Rehab Trajectory", "📋 Roster & Reminders"])
    
    with tab1:
        with st.form("add_patient"):
            c1,c2,c3 = st.columns(3)
            with c1: name = st.text_input("Full Name")
            with c2: age = st.number_input("Age", min_value=1)
            with c3: cond = st.selectbox("Condition", ["Stroke Rehab", "Paralysis", "Post-Fracture Stiffness", "ACL/Post-Surgery", "Cerebral Palsy", "Spinal Cord Injury", "Other"])
            
            c4,c5,c6 = st.columns(3)
            with c4: village = st.text_input("Village / Address")
            with c5: status = st.selectbox("Status", ["Active Treatment", "Recovered / Discharged", "Referred to DH", "Dropout"])
            with c6: contact = st.text_input("Phone Number")
            
            c7,c8 = st.columns(2)
            with c7: pain_vas = st.slider("Baseline Pain Score (VAS: 0 = No Pain, 10 = Severe)", 0, 10, 6)
            with c8: rom_pct = st.slider("Baseline Range of Motion / Mobility (% of Normal ROM)", 0, 100, 40)
            
            c9,c10 = st.columns(2)
            with c9: last_visit = st.date_input("Registration Date")
            with c10: next_followup = st.date_input("Next Follow-up Scheduled")
            
            if st.form_submit_button("Register Patient Profile"):
                if name:
                    p_id = len(st.session_state.patients) + 1
                    st.session_state.patients.append({
                        'id': p_id, 'name': name, 'age': age,
                        'condition': cond, 'village': village, 'status': status,
                        'contact': contact, 'pain_vas': pain_vas, 'mobility': "Recorded",
                        'last_visit': str(last_visit), 'next_followup': str(next_followup),
                        'reg_date': datetime.now().strftime("%Y-%m-%d")
                    })
                    st.session_state.rehab_logs.append({
                        'patient_id': p_id, 'name': name,
                        'session_date': str(last_visit),
                        'pain_vas': pain_vas, 'rom_pct': rom_pct
                    })
                    save_data('patients.csv', st.session_state.patients)
                    save_data('rehab_logs.csv', st.session_state.rehab_logs)
                    log_action(f"Registered Patient: {name}")
                    st.success("Patient Profile & Baseline Rehab Metrics Recorded")
                    st.rerun()

    with tab2:
        if st.session_state.patients:
            st.markdown("#### Patient Outcome Progress Tracker (VAS Pain & ROM Range)")
            patient_map = {f"{p['id']} - {p['name']} ({p.get('condition')})": p for p in st.session_state.patients}
            chosen_label = st.selectbox("Select Patient for Clinical Evaluation", list(patient_map.keys()))
            chosen_patient = patient_map[chosen_label]
            
            col_add_s1, col_add_s2 = st.columns(2)
            with col_add_s1:
                with st.expander("➕ Log New Follow-up Rehab Session"):
                    with st.form("log_session"):
                        new_vas = st.slider("Current VAS Pain Score (0-10)", 0, 10, 4)
                        new_rom = st.slider("Current Functional ROM (%)", 0, 100, 65)
                        sess_date = st.date_input("Session Date", datetime.now().date())
                        if st.form_submit_button("Record Session Progress"):
                            st.session_state.rehab_logs.append({
                                'patient_id': chosen_patient['id'],
                                'name': chosen_patient['name'],
                                'session_date': str(sess_date),
                                'pain_vas': new_vas, 'rom_pct': new_rom
                            })
                            save_data('rehab_logs.csv', st.session_state.rehab_logs)
                            log_action(f"Logged Rehab Progress for {chosen_patient['name']}")
                            st.success("Rehab Progress Logged")
                            st.rerun()
            
            with col_add_s2:
                logs_df = pd.DataFrame(st.session_state.rehab_logs)
                if not logs_df.empty:
                    p_logs = logs_df[logs_df['patient_id'] == chosen_patient['id']].sort_values(by='session_date')
                    if len(p_logs) > 0:
                        fig_vas = px.line(
                            p_logs, x='session_date', y=['pain_vas', 'rom_pct'],
                            markers=True,
                            title=f"Rehab Trajectory: {chosen_patient['name']}",
                            labels={'value': 'Score / Percentage', 'session_date': 'Date', 'variable': 'Metric'}
                        )
                        st.plotly_chart(fig_vas, use_container_width=True)
                    else:
                        st.info("No rehab sessions recorded yet.")
        else:
            st.info("No patients available.")

    with tab3:
        if st.session_state.patients:
            st.markdown("#### Patient Registry & Follow-up Actions")
            for p in st.session_state.patients:
                cp1, cp2, cp3, cp4 = st.columns([3, 2, 2, 3])
                with cp1: st.write(f"**{p['name']}** ({p.get('condition')}) | Pain: `{p.get('pain_vas', 'N/A')}/10`")
                with cp2: st.write(f"Status: `{p.get('status')}`")
                with cp3: st.write(f"Follow-up: `{p.get('next_followup', 'N/A')}`")
                with cp4:
                    msg = f"Namaste {p['name']}, reminder from NPRC Global Physiotherapy Trust. Your clinical rehab follow-up is due on {p.get('next_followup')}. Please attend your session."
                    encoded_msg = urllib.parse.quote(msg)
                    phone_num = str(p.get('contact', '')).replace('+', '').replace(' ', '')
                    wa_url = f"https://wa.me/{phone_num}?text={encoded_msg}" if phone_num else f"https://wa.me/?text={encoded_msg}"
                    st.link_button(" WhatsApp Reminder", wa_url, key=f"wa_{p['id']}")

# ========== 4. CAMPS ==========
elif page == "Camps":
    st.markdown(f"<h2>{svg_icon('camp', 30, '#0B2A4A')} Outreach Camp Management</h2>", unsafe_allow_html=True)
    with st.form("add_camp"):
        c1,c2,c3 = st.columns(3)
        with c1: loc = st.text_input("Camp Location / Village")
        with c2: date = st.date_input("Scheduled Date")
        with c3: exp = st.number_input("Budget / Expenses (₹)", min_value=0)
        if st.form_submit_button("Schedule Camp"):
            if loc:
                st.session_state.camps.append({
                    'id': len(st.session_state.camps)+1, 'location': loc,
                    'date': str(date), 'expenses': exp
                })
                save_data('camps.csv', st.session_state.camps)
                log_action(f"Scheduled Camp at {loc}")
                st.success("Camp Logged")
    if st.session_state.camps:
        st.dataframe(pd.DataFrame(st.session_state.camps), use_container_width=True)

# ========== 5. EXPENSES ==========
elif page == "Expenses":
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Expense Ledger</h2>", unsafe_allow_html=True)
    with st.form("add_expense"):
        c1,c2,c3 = st.columns(3)
        with c1: cat = st.selectbox("Category", ["Office Logistics", "Therapist Honorarium", "Rehab Equipment", "Travel / Camps", "Medicines & Consumables", "Other"])
        with c2: desc = st.text_input("Expense Description")
        with c3: amt = st.number_input("Amount (₹)", min_value=0)
        if st.form_submit_button("Commit Expense"):
            if desc and amt:
                st.session_state.expenses.append({
                    'id': len(st.session_state.expenses)+1, 'category': cat,
                    'description': desc, 'amount': amt,
                    'date': datetime.now().strftime("%Y-%m-%d")
                })
                save_data('expenses.csv', st.session_state.expenses)
                log_action(f"Added Expense: {desc}")
                st.success("Expense Recorded")
    if st.session_state.expenses:
        st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)

# ========== 6. BILLS ==========
elif page == "Bills":
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Vendor Bills & Invoices</h2>", unsafe_allow_html=True)
    if not st.session_state.bills:
        st.info("No vendor bills in queue.")
    else:
        df = pd.DataFrame(st.session_state.bills)
        st.dataframe(df, use_container_width=True)
        pending = [b for b in st.session_state.bills if b.get('status')=='Pending']
        if pending:
            opts = {f"#{b['id']} - {b['vendor']} (₹{b['amount']})": b for b in pending}
            sel = st.selectbox("Select Pending Bill to Audit", list(opts.keys()))
            bill = opts[sel]
            c1,c2 = st.columns(2)
            if c1.button("Approve Invoice", use_container_width=True):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']: b['status']='Approved'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Approved Bill #{bill['id']}")
                st.rerun()
            if c2.button("Reject Invoice", use_container_width=True):
                for b in st.session_state.bills:
                    if b['id'] == bill['id']: b['status']='Rejected'
                save_data('bills.csv', st.session_state.bills)
                log_action(f"Rejected Bill #{bill['id']}")
                st.rerun()

# ========== 7. REPORTS (AUTO-FINANCIAL YEAR FILTERING) ==========
elif page == "Reports (FY Filter)":
    st.markdown(f"<h2>{svg_icon('report', 30, '#0B2A4A')} Statutory Financial Year (FY) Audits</h2>", unsafe_allow_html=True)
    
    fy_selected = st.selectbox("Select Statutory Financial Year", ["2024-25", "2025-26", "2026-27", "2027-28"], index=2)
    start_year = int(fy_selected.split("-")[0])
    fy_start = datetime(start_year, 4, 1).date()
    fy_end = datetime(start_year + 1, 3, 31).date()
    
    st.caption(f"Active Accounting Period: **{fy_start.strftime('%d %b %Y')}** to **{fy_end.strftime('%d %b %Y')}**")
    
    def in_fy(date_str):
        try:
            d = datetime.strptime(str(date_str), "%Y-%m-%d").date()
            return fy_start <= d <= fy_end
        except:
            return False
            
    fy_donors = [d for d in st.session_state.donors if in_fy(d.get('date'))]
    fy_expenses = [e for e in st.session_state.expenses if in_fy(e.get('date'))]
    fy_patients = [p for p in st.session_state.patients if in_fy(p.get('reg_date', p.get('last_visit')))]
    
    total_fy_funds = sum(d.get('amount', 0) for d in fy_donors)
    total_fy_exp = sum(e.get('amount', 0) for e in fy_expenses)
    net_fy_balance = total_fy_funds - total_fy_exp
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("FY Donations Raised (80G)", f"₹{total_fy_funds:,.2f}")
    col_r2.metric("FY Operational Expenses", f"₹{total_fy_exp:,.2f}")
    col_r3.metric("FY Net Balance (Carried Fwd)", f"₹{net_fy_balance:,.2f}")
    
    col_tab1, col_tab2 = st.tabs(["📊 FY Inflow / Outflow Breakdown", "📄 Statutory PDF Export"])
    
    with col_tab1:
        if fy_donors or fy_expenses:
            summary_data = {
                'Category': ['Total Inflow (Donations)', 'Total Outflow (Expenses)'],
                'Amount': [total_fy_funds, total_fy_exp]
            }
            fig_fy = px.bar(summary_data, x='Category', y='Amount', color='Category', color_discrete_map={'Total Inflow (Donations)': '#28A745', 'Total Outflow (Expenses)': '#DC3545'}, title=f"Financial Overview for FY {fy_selected}")
            st.plotly_chart(fig_fy, use_container_width=True)
        else:
            st.info(f"No financial transactions found within the date range {fy_start} - {fy_end}.")

    with col_tab2:
        if st.button("Generate Official FY Audit Report (PDF)", use_container_width=True):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            c.setFillColorRGB(0.043, 0.165, 0.294)
            c.rect(0, height-100, width, 100, fill=1)
            
            # Logo in Audit Report
            if os.path.exists(LOGO_PATH):
                try:
                    c.drawImage(LOGO_PATH, 30, height-90, width=70, height=70, preserveAspectRatio=True, mask='auto')
                except: pass
                
            c.setFillColorRGB(0.831, 0.686, 0.215)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(120, height-45, "NPRC GLOBAL TRUST")
            c.setFillColorRGB(1,1,1)
            c.setFont("Helvetica", 10)
            c.drawString(120, height-65, f"Annual Statutory Audit & Clinical Impact - FY {fy_selected}")
            
            c.setFillColorRGB(0,0,0)
            y = height - 140
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "1. Philanthropic Inflow (80G Eligible)")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"Total Registered Donors in FY: {len(fy_donors)}")
            y -= 15
            c.drawString(60, y, f"Total Funds Collected: INR {total_fy_funds:,.2f}")
            
            y -= 30
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "2. Clinical & Patient Rehabilitation Summary")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"Total Patients Enrolled in FY: {len(fy_patients)}")
            y -= 15
            recovered_count = len([p for p in fy_patients if "Recovered" in str(p.get('status', ''))])
            c.drawString(60, y, f"Fully Recovered / Discharged: {recovered_count}")
            
            y -= 30
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "3. Expenditure & Net Financial Summary")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"Total Program & Operational Expenses: INR {total_fy_exp:,.2f}")
            y -= 15
            c.drawString(60, y, f"Net Balance Carried Forward: INR {net_fy_balance:,.2f}")

            c.setFillColorRGB(0.043, 0.165, 0.294)
            c.rect(0, 20, width, 30, fill=1)
            c.setFillColorRGB(1,1,1)
            c.setFont("Helvetica", 8)
            c.drawString(40, 30, "System Generated Statutory Audit Document | NPRC Global Compliance Portal")
            
            c.save()
            buffer.seek(0)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Annual_Audit_Report_{fy_selected}.pdf" style="background:#D4AF37; color:#0B2A4A; padding:12px 25px; border-radius:30px; text-decoration:none; font-weight:bold; display:block; text-align:center; margin-top:15px;">⬇️ Download Official Audit PDF</a>', unsafe_allow_html=True)

# ========== 8. SETTINGS & SECURE CREDENTIAL UPDATE ==========
elif page == "Settings":
    st.markdown(f"<h2>{svg_icon('settings', 30, '#0B2A4A')} System Settings & Security Vault</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.subheader(" Update Admin Credentials (SHA-256)")
        with st.form("update_creds"):
            new_u = st.text_input("New Admin Username", value=st.session_state.user)
            new_p = st.text_input("New Password", type="password")
            confirm_p = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Credentials"):
                if new_p and new_p == confirm_p:
                    hashed_val = hash_pw(new_p)
                    save_credentials(new_u, hashed_val)
                    st.session_state.user = new_u
                    log_action(f"Updated security credentials for {new_u}")
                    st.success("Credentials updated with SHA-256 encryption.")
                else:
                    st.error("Passwords do not match or cannot be empty.")
                    
        st.markdown("---")
        if st.button("Toggle Dark / Light Theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    with col_s2:
        st.subheader("Data Vault Backup & Disaster Recovery")
        if st.button("Create Full Encrypted Archive (ZIP)", use_container_width=True):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for f in ['donors.csv', 'patients.csv', 'rehab_logs.csv', 'camps.csv', 'bills.csv', 'expenses.csv', 'logs.csv', 'config.json']:
                    if os.path.exists(f):
                        zf.write(f)
            zip_buffer.seek(0)
            b64_zip = base64.b64encode(zip_buffer.getvalue()).decode()
            st.markdown(f'<a href="data:application/zip;base64,{b64_zip}" download="NPRC_DataVault_{datetime.now().strftime("%Y%m%d")}.zip" style="background:#0B2A4A; color:white; padding:10px 20px; border-radius:30px; text-decoration:none; display:block; text-align:center; margin-top:10px;">Download Archive ZIP</a>', unsafe_allow_html=True)
            log_action("Created Data Vault Archive")
        
        st.markdown("---")
        uploaded = st.file_uploader("Restore Database from ZIP Archive", type=['zip'])
        if uploaded:
            with zipfile.ZipFile(uploaded, 'r') as zf:
                zf.extractall('.')
            st.success("Database Restored Successfully! Reloading system...")
            log_action("Restored from Archive")
            st.rerun()

# पहली बार CSV / JSON इनिशियलाइज़ेशन
if __name__ == "__main__":
    for f in ['donors.csv', 'patients.csv', 'rehab_logs.csv', 'camps.csv', 'bills.csv', 'expenses.csv', 'logs.csv']:
        if not os.path.exists(f):
            save_data(f, [])
    if not os.path.exists('bills.csv'):
        save_data('bills.csv', [{'id':1, 'vendor':'Urban Rehab', 'desc':'Therapist Visit', 'amount':15000, 'status':'Pending'}])
    if not os.path.exists('config.json'):
        save_credentials(DEFAULT_USER, DEFAULT_PW_HASH)
