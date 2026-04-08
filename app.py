import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random
import re

# --- CONFIG ---
st.set_page_config(page_title="Borworn Private Banking", page_icon="🏦", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_private_v1.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS Users 
                 (username TEXT PRIMARY KEY, name TEXT, email TEXT, password TEXT, 
                  balance REAL, pin TEXT, acc_type TEXT DEFAULT 'Private Wealth')''')
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                 (sender TEXT, receiver TEXT, amount REAL, date TEXT, type TEXT, ref_no TEXT)''')
    conn.commit()

init_db()

# --- CSS: LUXURY DEEP NAVY ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .premium-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15); 
        border-top: 5px solid #eab308; margin-bottom: 25px;
    }
    
    .pin-btn button {
        border-radius: 50% !important; width: 75px !important; height: 75px !important;
        font-size: 24px !important; background: white !important; color: #0f172a !important;
        border: 1px solid #e2e8f0 !important; margin: 8px auto !important; display: block !important;
    }
    .pin-btn button:hover { border-color: #eab308 !important; color: #eab308 !important; }
    
    .admin-area { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_status" not in st.session_state: st.session_state.auth_status = "login_page"
if "user_session" not in st.session_state: st.session_state.user_session = None
if "pin_temp" not in st.session_state: st.session_state.pin_temp = ""

# ---------------------------------------------------------
# 🛡️ LOGIN & STAFF CONTROL
# ---------------------------------------------------------
if st.session_state.auth_status == "login_page":
    st.markdown("<h1 style='text-align:center; color:#0f172a;'>BORWORN BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; margin-bottom:30px;'>Private Banking Service</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 เข้าสู่ระบบลูกค้า", "👨‍💼 สำหรับเจ้าหน้าที่"])
    
    with tab1:
        with st.form("login_form"):
            u = st.text_input("Username (ชื่อผู้ใช้งาน)")
            p = st.text_input("Password (รหัสผ่าน)", type="password")
            if st.form_submit_button("ยืนยันเข้าใช้งาน", use_container_width=True, type="primary"):
                user = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if user:
                    st.session_state.user_session = u
                    st.session_state.auth_status = "pin_page" if user[5] else "set_pin_page"
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง กรุณาติดต่อธนาคารเพื่อขอรับบัญชี")

    with tab2:
        if st.text_input("กรอกรหัสพนักงาน (Staff Key)", type="password") == "Kub1":
            st.markdown('<div class="admin-area">', unsafe_allow_html=True)
            st.subheader("📋 ระบบลงทะเบียนลูกค้าใหม่")
            with st.form("admin_reg"):
                col1, col2 = st.columns(2)
                new_u = col1.text_input("เลขบัญชี/Username")
                new_n = col2.text_input("ชื่อ-นามสกุลลูกค้า")
                new_e = col1.text_input("อีเมลลูกค้า (เพื่อยืนยัน)")
                new_p = col2.text_input("กำหนดรหัสผ่านเบื้องต้น")
                new_b = st.number_input("เงินฝากเริ่มต้น (บาท)", value=1000.0)
                
                if st.form_submit_button("ออกใบเปิดบัญชี"):
                    if new_u and new_n and new_p:
                        try:
                            c.execute("INSERT INTO Users (username, name, email, password, balance) VALUES (?,?,?,?,?)", 
                                      (new_u, new_n, new_e, new_p, new_b))
                            conn.commit()
                            st.success(f"✅ บัญชี {new_u} ถูกสร้างเรียบร้อยแล้ว!")
                        except: st.error("❌ เลขบัญชี/Username นี้มีอยู่ในระบบแล้ว")
            
            st.divider()
            st.subheader("⚙️ จัดการฐานข้อมูล")
            manage_op = st.radio("เลือกการทำงาน", ["ดูรายชื่อทั้งหมด", "ลบข้อมูลลูกค้า", "ล้างระบบทั้งหมด"])
            if manage_op == "ดูรายชื่อทั้งหมด":
                st.write(pd.read_sql("SELECT username, name, balance FROM Users", conn))
            elif manage_op == "ล้างระบบทั้งหมด":
                if st.button("🔥 ยืนยันล้างข้อมูล"):
                    c.execute("DELETE FROM Users"); c.execute("DELETE FROM Transactions")
                    conn.commit(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🔢 PIN KEYPAD
# ---------------------------------------------------------
elif st.session_state.auth_status == "pin_page":
    user = c.execute("SELECT name, pin FROM Users WHERE username=?", (st.session_state.user_session,)).fetchone()
    st.markdown(f"<h3 style='text-align:center;'>ยินดีต้อนรับคุณ {user[0]}</h3>", unsafe_allow_html=True)
    
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
                        st.error("PIN ไม่ถูกต้อง")
                        st.session_state.pin_temp = ""
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🏠 DASHBOARD
# ---------------------------------------------------------
elif st.session_state.auth_status == "dashboard":
    u = c.execute("SELECT * FROM Users WHERE username=?", (st.session_state.user_session,)).fetchone()
    
    nav = option_menu(None, ["หน้าแรก", "โอนเงิน", "ประวัติ", "บัญชี"], 
        icons=['house', 'arrow-left-right', 'clock-history', 'person'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#0f172a"}})

    if nav == "หน้าแรก":
        st.markdown(f"""
        <div class="premium-card">
            <small>ยอดเงินที่ใช้ได้</small>
            <h1 style="color:white; margin:10px 0;">฿ {u[4]:,.2f}</h1>
            <div style="display:flex; justify-content:space-between; margin-top:15px; font-size:14px; opacity:0.8;">
                <span>{u[1]}</span>
                <span>เลขที่บัญชี: {u[0]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}", width=220)

    elif nav == "โอนเงิน":
        target = st.text_input("เลขบัญชีผู้รับ")
        amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
        if st.button("ยืนยันโอนเงิน", type="primary", use_container_width=True):
            recv = c.execute("SELECT name FROM Users WHERE username=?", (target,)).fetchone()
            if recv and u[4] >= amt and target != u[0]:
                ref = f"REF{random.randint(100000, 999999)}"
                c.execute("UPDATE Users SET balance = balance - ? WHERE username=?", (amt, u[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE username=?", (amt, target))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%H:%M | %d/%m/%y"), "โอนเงิน", ref))
                conn.commit(); st.success(f"โอนสำเร็จ!"); st.balloons()
            else: st.error("ไม่สามารถโอนได้ กรุณาเช็คเลขบัญชีหรือยอดเงิน")

    elif nav == "ประวัติ":
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{u[0]}' OR receiver='{u[0]}'", conn)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif nav == "บัญชี":
        if st.button("ออกจากระบบ", type="primary", use_container_width=True):
            st.session_state.auth_status = "login_page"; st.rerun()

# --- SET PIN ---
elif st.session_state.auth_status == "set_pin_page":
    st.subheader("🔢 ตั้งค่ารหัสความปลอดภัย (PIN 6 หลัก)")
    p1 = st.text_input("ตั้งรหัส PIN", type="password", max_chars=6)
    p2 = st.text_input("ยืนยันรหัส", type="password", max_chars=6)
    if st.button("บันทึกรหัส PIN"):
        if len(p1) == 6 and p1 == p2 and p1.isdigit():
            c.execute("UPDATE Users SET pin=? WHERE username=?", (p1, st.session_state.user_session))
            conn.commit(); st.session_state.auth_status = "dashboard"; st.rerun()
