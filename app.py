import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random
import re

# --- CONFIG ---
st.set_page_config(page_title="Borworn Digital Bank", page_icon="🏦", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_premium_v1.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS Users 
                 (username TEXT PRIMARY KEY, name TEXT, email TEXT, password TEXT, 
                  balance REAL, pin TEXT, acc_type TEXT DEFAULT 'Premium Account')''')
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                 (sender TEXT, receiver TEXT, amount REAL, date TEXT, type TEXT, ref_no TEXT)''')
    conn.commit()

init_db()

# --- CSS: DEEP NAVY & GOLD THEME (หรูหราและสมจริง) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Bank Card Visual */
    .premium-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f1f5f9; padding: 25px; border-radius: 20px;
        box-shadow: 0 12px 24px rgba(0,0,0,0.2); 
        border-left: 6px solid #eab308; margin-bottom: 25px;
    }
    
    /* PIN Keypad Circle Buttons */
    .pin-btn button {
        border-radius: 50% !important;
        width: 75px !important; height: 75px !important;
        font-size: 24px !important;
        background: white !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        margin: 10px auto !important;
        display: block !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    .pin-btn button:hover { border-color: #eab308 !important; color: #eab308 !important; }
    
    /* Admin Section */
    .admin-pnl { background: #ffffff; border: 2px dashed #eab308; padding: 20px; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_status" not in st.session_state: st.session_state.auth_status = "login_page"
if "user_session" not in st.session_state: st.session_state.user_session = None
if "pin_temp" not in st.session_state: st.session_state.pin_temp = ""

# ---------------------------------------------------------
# 🛡️ LOGIN & GATEWAY
# ---------------------------------------------------------
if st.session_state.auth_status == "login_page":
    st.markdown("<h1 style='text-align:center; color:#0f172a; margin-bottom:5px;'>BORWORN BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; margin-bottom:30px;'>Digital Banking Excellence</p>", unsafe_allow_html=True)
    
    choice = option_menu(None, ["Login", "Register", "Staff Only"], 
        icons=['shield-lock', 'person-plus', 'gear'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#0f172a"}})

    if choice == "Login":
        with st.container():
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True, type="primary"):
                user = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if user:
                    st.session_state.user_session = u
                    st.session_state.auth_status = "pin_page" if user[5] else "set_pin_page"
                    st.rerun()
                else: st.error("Invalid credentials")

    elif choice == "Register":
        with st.form("reg_form"):
            r_u = st.text_input("Username (สำหรับเข้าสู่ระบบ)")
            r_n = st.text_input("ชื่อ-นามสกุล")
            r_e = st.text_input("อีเมล (เพื่อยืนยันตัวตนมนุษย์)")
            r_p = st.text_input("Password", type="password")
            if st.form_submit_button("Create Account", use_container_width=True):
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', r_e):
                    st.error("Email format is invalid (@ and .com required)")
                elif r_u and r_n and r_p:
                    try:
                        c.execute("INSERT INTO Users (username, name, email, password, balance) VALUES (?,?,?,?,0)", (r_u, r_n, r_e, r_p))
                        conn.commit(); st.success("Account created! Please Login")
                    except: st.error("Username already exists")

    elif choice == "Staff Only":
        if st.text_input("Staff Password", type="password") == "Kub1":
            st.markdown('<div class="admin-pnl">', unsafe_allow_html=True)
            adm_cmd = st.radio("Management", ["All Users", "Credit/Debit", "Reset System"])
            if adm_cmd == "All Users":
                st.dataframe(pd.read_sql("SELECT username, name, email, balance FROM Users", conn))
            elif adm_cmd == "Credit/Debit":
                t_u = st.text_input("Target Username")
                t_a = st.number_input("Amount")
                if st.button("Update Balance"):
                    c.execute("UPDATE Users SET balance = balance + ? WHERE username=?", (t_a, t_u))
                    conn.commit(); st.success("Success!")
            elif adm_cmd == "Reset System":
                if st.button("🔥 DELETE ALL DATA"):
                    c.execute("DELETE FROM Users"); c.execute("DELETE FROM Transactions")
                    conn.commit(); st.success("Database Cleared")
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🔢 SMART PIN KEYPAD (3-COLUMN LAYOUT)
# ---------------------------------------------------------
elif st.session_state.auth_status == "pin_page":
    user = c.execute("SELECT name, pin FROM Users WHERE username=?", (st.session_state.user_session,)).fetchone()
    st.markdown(f"<h3 style='text-align:center;'>Welcome Back, {user[0]}</h3>", unsafe_allow_html=True)
    
    dots = " ".join(["●" if i < len(st.session_state.pin_temp) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#0f172a; letter-spacing:10px;'>{dots}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    keys = ['1','2','3','4','5','6','7','8','9','Clear','0','Del']
    for i, k in enumerate(keys):
        with [col1, col2, col3][i % 3]:
            st.markdown('<div class="pin-btn">', unsafe_allow_html=True)
            if st.button(k, key=f"k_{k}"):
                if k == 'Del': st.session_state.pin_temp = st.session_state.pin_temp[:-1]
                elif k == 'Clear': st.session_state.pin_temp = ""
                elif len(st.session_state.pin_temp) < 6: st.session_state.pin_temp += k
                
                if len(st.session_state.pin_temp) == 6:
                    if st.session_state.pin_temp == user[1]:
                        st.session_state.auth_status = "dashboard"
                        st.session_state.pin_temp = ""
                        st.rerun()
                    else:
                        st.error("Incorrect PIN")
                        st.session_state.pin_temp = ""
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🏦 MAIN BANKING DASHBOARD
# ---------------------------------------------------------
elif st.session_state.auth_status == "dashboard":
    u = c.execute("SELECT * FROM Users WHERE username=?", (st.session_state.user_session,)).fetchone()
    
    nav = option_menu(None, ["Home", "Transfer", "History", "Account"], 
        icons=['house', 'arrow-left-right', 'clock-history', 'person'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#0f172a"}})

    if nav == "Home":
        st.markdown(f"""
        <div class="premium-card">
            <div style="display:flex; justify-content:space-between;">
                <small>Available Balance</small>
                <span style="color:#eab308; font-weight:bold;">PREMIUM</span>
            </div>
            <h1 style="color:white; margin:10px 0;">฿ {u[4]:,.2f}</h1>
            <div style="display:flex; justify-content:space-between; margin-top:15px; font-size:14px; opacity:0.8;">
                <span>{u[1]}</span>
                <span>ID: {u[0]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("💰 Add Funds", use_container_width=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}", width=220)

    elif nav == "Transfer":
        target = st.text_input("Recipient Username")
        amt = st.number_input("Amount (THB)", min_value=1.0)
        if st.button("Confirm Transfer", type="primary", use_container_width=True):
            recv = c.execute("SELECT name FROM Users WHERE username=?", (target,)).fetchone()
            if recv and u[4] >= amt and target != u[0]:
                ref = f"BNK{random.randint(100000, 999999)}"
                c.execute("UPDATE Users SET balance = balance - ? WHERE username=?", (amt, u[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE username=?", (amt, target))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%H:%M | %d/%m/%y"), "Transfer", ref))
                conn.commit(); st.success(f"Transfer to {recv[0]} Successful!"); st.balloons()
            else: st.error("Transaction Failed: Check balance or recipient")

    elif nav == "History":
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{u[0]}' OR receiver='{u[0]}'", conn)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif nav == "Account":
        st.write(f"Email Verified: {u[2]} ✅")
        if st.button("Log Out", type="primary", use_container_width=True):
            st.session_state.auth_status = "login_page"; st.rerun()

# --- SET PIN FIRST TIME ---
elif st.session_state.auth_status == "set_pin_page":
    st.subheader("🔢 Create Your Security PIN")
    p1 = st.text_input("Enter 6-digit PIN", type="password", max_chars=6)
    p2 = st.text_input("Confirm PIN", type="password", max_chars=6)
    if st.button("Save PIN"):
        if len(p1) == 6 and p1 == p2 and p1.isdigit():
            c.execute("UPDATE Users SET pin=? WHERE username=?", (p1, st.session_state.user_session))
            conn.commit(); st.session_state.auth_status = "dashboard"; st.rerun()
