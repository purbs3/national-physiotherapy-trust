import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import csv

# ---------- पेज कॉन्फ़िग ----------
st.set_page_config(
    page_title="NPRC Global - National Physiotherapy Trust",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# 🔐 AUTHENTICATION (LOGIN) SYSTEM
# ====================================================================

def get_credentials():
    try:
        username = st.secrets["auth"]["username"]
        password = st.secrets["auth"]["password"]
    except:
        # Default credentials (Insecure, change in Streamlit Secrets)
        username = "trustee"
        password = "NPRC@2026"
    return username, password

def login(username, password):
    correct_username, correct_password = get_credentials()
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
# 🎨 UPDATED CSS थीम (VISIBILITY FIX)
# ====================================================================
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .main-header {
        background: linear-gradient(135deg, #0B2A4A 0%, #1A4B6D 100%);
        padding: 1.8rem 2rem;
        border-radius: 0 0 30px 30px;
        margin-bottom: 2rem;
        color: white;
        border-bottom: 6px solid #D4AF37;
        box-shadow: 0 8px 25px rgba(11,42,74,0.3);
    }
    .trust-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-top: 6px solid #D4AF37;
        margin-bottom: 1.5rem;
        transition: transform 0.2s;
    }
    .trust-card:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
    .stat-box {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border-bottom: 4px solid #D4AF37;
    }
    .stat-box h2 { color: #0B2A4A; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .stat-box p { color: #4B5563; margin: 0; font-weight: 500; letter-spacing: 0.5px; }
    .footer {
        background: #0B2A4A;
        color: #B0C4DE;
        padding: 1.5rem 2rem;
        border-radius: 30px 30px 0 0;
        margin-top: 3rem;
        text-align: center;
        border-top: 4px solid #D4AF37;
    }
    
    /* ---------- SIDEBAR VISIBILITY FIX ---------- */
    section[data-testid="stSidebar"] {
        background-color: #0B2A4A !important;
        color: white !important;
    }
    /* Sidebar ke sare labels aur static text white */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4, 
    section[data-testid="stSidebar"] p {
        color: white !important;
    }
    
    /* ✅ INPUT BOX FIX: Text Input ko visible karna */
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #FFFFFF !important;  /* White background */
        color: #000000 !important;             /* Black text */
        border: 2px solid #D4AF37 !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #FFC107 !important;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.4) !important;
    }
    
    /* ✅ LOGIN BUTTON FIX: Gold button clearly visible */
    section[data-testid="stSidebar"] .stFormSubmitButton button {
        background-color: #D4AF37 !important; /* Gold */
        color: #0B2A4A !important;            /* Dark blue text */
        font-weight: bold !important;
        border-radius: 30px !important;
        padding: 10px 24px !important;
        border: none !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transition: 0.3s !important;
    }
    section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
        background-color: #C5A028 !important; /* Darker gold */
        color: #0B2A4A !important;
        transform: scale(1.02) !important;
    }
    
    /* ✅ LOGOUT BUTTON FIX */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #DC3545 !important; /* Red */
        color: white !important;
        font-weight: bold !important;
        border-radius: 30px !important;
        padding: 8px 16px !important;
        border: none !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #B02A37 !important;
    }
    
    /* ✅ SIDEBAR RADIO BUTTONS (Navigation) */
    section[data-testid="stSidebar"] .stRadio label {
        color: white !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        background-color: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        padding: 8px !important;
    }
    
    /* Dataframe headers */
    .dataframe th {
        background-color: #0B2A4A !important;
        color: white !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

def svg_icon(name, size=28, color="#FFFFFF"):
    icons = {
        "trust": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/><path d="M12 7v10"/></svg>',
        "donor": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 2v4M12 22v-4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M22 12h-4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>',
        "bill": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
        "receipt": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M4 4h16v16H4z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>',
        "heart": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    }
    return icons.get(name, "")

# ---------- सत्र अवस्था (डेटा) ----------
if 'donors' not in st.session_state:
    try:
        df = pd.read_csv('donors.csv')
        st.session_state.donors = df.to_dict('records')
    except:
        st.session_state.donors = []

if 'bills' not in st.session_state:
    try:
        df = pd.read_csv('bills.csv')
        st.session_state.bills = df.to_dict('records')
    except:
        st.session_state.bills = []

if 'receipt_counter' not in st.session_state:
    st.session_state.receipt_counter = 100

def save_donors():
    pd.DataFrame(st.session_state.donors).to_csv('donors.csv', index=False)

def save_bills():
    pd.DataFrame(st.session_state.bills).to_csv('bills.csv', index=False)

# ---------- हेडर ----------
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; align-items: center; gap: 25px; flex-wrap: wrap;">
        <div style="background: #D4AF37; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
            {svg_icon("trust", 45, "#0B2A4A")}
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <h1 style="margin:0; font-weight: 300; letter-spacing: 2px; font-size: 1.4rem;">🇮🇳 NPRC GLOBAL</h1>
                <span style="background: #D4AF37; color: #0B2A4A; padding: 2px 14px; border-radius: 30px; font-weight: bold; font-size: 0.7rem;">TRUST</span>
            </div>
            <h2 style="margin:0; font-size: 2rem; font-weight: 700;">National Physiotherapy & Rehabilitation Council</h2>
            <p style="margin:0; opacity:0.8; font-size: 0.95rem;">Affordable Healthcare for All | Regd. under Indian Trusts Act, 1882</p>
        </div>
        <div style="margin-left: auto; text-align: right; border-left: 2px solid #D4AF37; padding-left: 20px;">
            <p style="margin:0; font-size: 0.8rem; opacity:0.7;">80G Tax Exemption</p>
            <p style="margin:0; font-weight: bold; color: #D4AF37;">PAN: AABTN1234C</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- साइडबार (UI अब पूरी तरह Visible है) ----------
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0; border-bottom: 2px solid #D4AF37;">
        <div style="background: #D4AF37; width: 70px; height: 70px; border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
            {svg_icon("trust", 40, "#0B2A4A")}
        </div>
        <h4 style="color: #D4AF37; margin-top: 10px;">NPRC Trust Portal</h4>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ---------- LOGIN FORM (बिना लॉगिन) ----------
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="background:#1A3A5C; padding:12px; border-radius:10px; border:1px solid #D4AF37; margin-bottom:15px; text-align:center;">
            <p style="color:#D4AF37; font-weight:bold; margin:0;">🔐 Trustee Login</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username_input = st.text_input("👤 Username", placeholder="Enter Username")
            password_input = st.text_input("🔑 Password", type="password", placeholder="Enter Password")
            # यह Button अब CSS की वजह से Gold और पूरी तरह Visible होगा
            login_btn = st.form_submit_button("🔓 Login")
            
            if login_btn:
                if login(username_input, password_input):
                    st.success("✅ Login Successful! Welcome Trustee.")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password. Please try again.")
        
        st.markdown("---")
        # बिना लॉगिन सिर्फ Home दिखेगा
        page = "🏠 Home (Public)"
    else:
        # ---------- LOGGED IN USER ----------
        st.markdown(f"""
        <div style="background:#1A3A5C; padding:10px; border-radius:8px; border-left:4px solid #28A745; margin-bottom:15px;">
            <p style="margin:0; color:#28A745; font-size:0.9rem;">✅ Logged in as</p>
            <p style="margin:0; font-weight:bold; color:white; font-size:1.1rem;">{st.session_state.user}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout Button (Red)
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        # पूरा नेविगेशन
        page = st.radio(
            label="📋 Navigation",
            options=["🏠 Home (Public)", "📒 Donor Ledger", "🧾 Generate Receipt", "📑 Vendor Bills"],
            index=0,
            key="nav_nprc_secure"
        )
    
    st.markdown("---")
    st.caption("NPRC Global v2.0 (Secured)")

# ====================================================================
# पेज हैंडलिंग (सुरक्षा)
# ====================================================================
if not st.session_state.authenticated and "Home" not in page:
    st.warning("⚠️ You are not logged in. Please login from the sidebar to access Admin features.")
    st.stop()

# ---------- पेज 1: होम (Public) ----------
if "Home" in page:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-box"><h2 style="color:#D4AF37;">12,847</h2><p>{svg_icon('heart', 18, '#D4AF37')} Patients Treated</p></div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box"><h2>₹4.2Cr</h2><p>{svg_icon('donor', 18, '#0B2A4A')} Funds Raised</p></div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-box"><h2>342</h2><p>{svg_icon('bill', 18, '#0B2A4A')} Rural Health Camps</p></div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-box"><h2 style="color:#D4AF37;">23</h2><p>{svg_icon('trust', 18, '#D4AF37')} Partner Clinics</p></div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(f"""
        <div class="trust-card">
            <h3>{svg_icon('heart', 24, '#D4AF37')} Our Mission</h3>
            <p style="font-size:1.1rem;">"To provide free, high-quality physiotherapy and rehabilitation services to underprivileged communities across rural India."</p>
            <div style="background: #F0F4F8; padding: 15px; border-radius: 10px; margin-top: 10px;">
                <h4>📌 Programs</h4>
                <ul><li><strong>Swavalamban Camps:</strong> Monthly rural outreach camps in Bihar, UP, and Jharkhand.</li>
                <li><strong>Scholarship for Therapists:</strong> Free PG certifications for rural physiotherapists.</li>
                <li><strong>AI Health Monitoring:</strong> In collaboration with Urban Rehab for tech-driven care.</li></ul>
                <p style="color: #6C757D; font-size: 0.9rem; margin-top: 10px;">🔒 <em>Admin features are locked. Please login from the sidebar.</em></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        st.markdown(f"""
        <div style="background: #0B2A4A; color: white; padding: 2rem 1.5rem; border-radius: 16px; text-align: center; border: 2px solid #D4AF37;">
            <h3 style="color: #D4AF37;">Support the Cause</h3>
            <p style="font-size: 2.5rem; margin: 0;">❤️</p>
            <p style="opacity: 0.9;">Your donation is eligible for <strong>80G</strong> tax exemption.</p>
            <br>
            <a href="https://rzp.io/l/nprc-global" target="_blank">
                <div style="background: #D4AF37; color: #0B2A4A; padding: 12px 20px; border-radius: 40px; font-weight: bold; display: inline-block; font-size: 1.2rem;">Donate Now →</div>
            </a>
            <p style="font-size: 0.7rem; margin-top: 15px; opacity: 0.6;">UPI: nprc@upi | Razorpay Secure</p>
        </div>
        """, unsafe_allow_html=True)

# ---------- पेज 2: डोनर लेजर ----------
elif "Donor Ledger" in page:
    st.markdown(f"<h2>{svg_icon('donor', 30, '#0B2A4A')} Donor Management <span style='font-size:1rem; font-weight:normal;'>| Trustee Panel</span></h2>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("add_donor_form", clear_on_submit=True):
        st.subheader("➕ Add New Donor")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            name = st.text_input("Full Name*")
        with col2:
            pan = st.text_input("PAN Card*")
        with col3:
            email = st.text_input("Email ID")
        with col4:
            amount = st.number_input("Donation Amount (₹)*", min_value=100, step=100)
        
        submitted = st.form_submit_button("💾 Save Donor Record")
        if submitted and name and pan and amount:
            new_id = len(st.session_state.donors) + 1
            st.session_state.receipt_counter += 1
            receipt_no = "NPRC-" + str(st.session_state.receipt_counter).zfill(4)
            st.session_state.donors.append({
                "id": new_id,
                "name": name,
                "pan": pan,
                "email": email,
                "amount": amount,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "receipt_no": receipt_no
            })
            save_donors()
            st.success("✅ Donor " + name + " added! Receipt No: " + receipt_no)

    st.markdown("---")
    st.subheader("📋 Donor Ledger")
    df_donors = pd.DataFrame(st.session_state.donors)
    if not df_donors.empty:
        st.dataframe(df_donors, use_container_width=True, height=300)
        csv = df_donors.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = '<a href="data:file/csv;base64,' + b64 + '" download="nprc_donor_ledger.csv" style="background:#0B2A4A; color:white; padding:8px 16px; border-radius:30px; text-decoration:none;">⬇️ Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No donors added yet.")

# ---------- पेज 3: रसीद जनरेटर ----------
elif "Generate Receipt" in page:
    st.markdown(f"<h2>{svg_icon('receipt', 30, '#D4AF37')} Automated Receipt Engine <span style='font-size:1rem; font-weight:normal;'>(80G Compliant)</span></h2>", unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.donors:
        st.warning("No donors found. Please add a donor first in the 'Donor Ledger'.")
    else:
        df = pd.DataFrame(st.session_state.donors)
        donor_names = df['name'].tolist()
        selected_name = st.selectbox("Select Donor for Receipt", donor_names)
        
        if st.button("🧾 Generate PDF Receipt"):
            donor = df[df['name'] == selected_name].iloc[0].to_dict()
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            c.setFillColorRGB(0.043, 0.165, 0.294)
            c.rect(0, height-80, width, 80, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 18)
            c.drawString(40, height-50, "NPRC GLOBAL")
            c.setFont("Helvetica", 10)
            c.drawString(40, height-70, "National Physiotherapy & Rehabilitation Council (Trust)")

            c.setFillColorRGB(0.831, 0.686, 0.216)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(400, height-50, "TAX RECEIPT")
            
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 12)
            y = height - 130
            c.drawString(40, y, "Date: " + datetime.now().strftime('%d-%m-%Y'))
            c.drawString(400, y, "Receipt No: " + donor['receipt_no'])
            
            y -= 40
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Donor Details:")
            y -= 25
            c.setFont("Helvetica", 11)
            c.drawString(60, y, "Name: " + donor['name'])
            y -= 20
            c.drawString(60, y, "PAN: " + donor['pan'])
            y -= 20
            c.drawString(60, y, "Email: " + donor['email'])
            
            y -= 40
            c.line(40, y, width-40, y)
            y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Donation Details:")
            y -= 25
            c.setFont("Helvetica", 11)
            c.drawString(60, y, "Amount: ₹" + str(donor['amount']))
            y -= 20
            c.drawString(60, y, "Mode: Online (UPI / Bank Transfer)")
            
            y -= 40
            c.line(40, y, width-40, y)
            y -= 20
            c.setFont("Helvetica-Bold", 14)
            c.setFillColorRGB(0.043, 0.165, 0.294)
            c.drawString(40, y, "Total: ₹" + str(donor['amount']))
            
            y -= 30
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(40, y, "** This donation is exempted under Section 80G of the Income Tax Act, 1961.")
            y -= 15
            c.drawString(40, y, "** This is a system-generated receipt. No signature required.")
            
            c.setFillColorRGB(0.043, 0.165, 0.294)
            c.rect(0, 20, width, 30, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica", 8)
            c.drawString(40, 30, "NPRC Global Trust | Regd. Office: Patna, Bihar | Contact: nprc@healthcare.in")
            
            c.save()
            buffer.seek(0)

            b64_pdf = base64.b64encode(buffer.getvalue()).decode()
            href = '<a href="data:application/pdf;base64,' + b64_pdf + '" download="Receipt_' + donor["receipt_no"] + '.pdf" style="background:#D4AF37; color:#0B2A4A; padding:12px 25px; border-radius:40px; text-decoration:none; font-weight:bold;">⬇️ Download Receipt (PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("✅ Receipt generated for " + selected_name)

# ---------- पेज 4: वेंडर बिल्स ----------
elif "Vendor Bills" in page:
    st.markdown(f"<h2>{svg_icon('bill', 30, '#0B2A4A')} Vendor Bill Approvals <span style='font-size:1rem; font-weight:normal;'>| Urban Rehab Invoices</span></h2>", unsafe_allow_html=True)
    st.markdown("---")

    df_bills = pd.DataFrame(st.session_state.bills)
    if df_bills.empty:
        st.info("No pending bills from Urban Rehab.")
    else:
        st.dataframe(df_bills, use_container_width=True, height=250)

        st.subheader("⚡ Approve / Reject Bill")
        bill_options = {}
        for b in st.session_state.bills:
            if b['status'] == "Pending":
                bill_options[str(b['id']) + " - " + b['desc'] + " (₹" + str(b['amount']) + ")"] = b
        
        if bill_options:
            selected_bill_key = st.selectbox("Select Pending Bill", list(bill_options.keys()))
            selected_bill = bill_options[selected_bill_key]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Bill"):
                    for b in st.session_state.bills:
                        if b['id'] == selected_bill['id']:
                            b['status'] = "Approved"
                    save_bills()
                    st.success("Bill #" + str(selected_bill['id']) + " Approved! Transfer to Urban Rehab initiated.")
                    st.rerun()
            with col2:
                if st.button("❌ Reject Bill"):
                    for b in st.session_state.bills:
                        if b['id'] == selected_bill['id']:
                            b['status'] = "Rejected"
                    save_bills()
                    st.warning("Bill #" + str(selected_bill['id']) + " Rejected. Reason noted.")
                    st.rerun()
        else:
            st.info("✅ No pending bills. All cleared.")

# ---------- फुटर ----------
st.markdown(f"""
<div class="footer">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>© 2026 NPRC Global Trust | Regd. under Indian Trusts Act</div>
        <div>80G Certificate: AABTN1234C | 12A Regd.</div>
        <div>nprc-global.health</div>
    </div>
    <div style="margin-top: 10px; font-size: 0.8rem; opacity: 0.6;">
        This is a digital record system. All financial data is audited quarterly.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- CSV फाइलें बनाएं ----------
if __name__ == "__main__":
    if not os.path.exists('donors.csv'):
        save_donors()
    if not os.path.exists('bills.csv'):
        save_bills()
        
