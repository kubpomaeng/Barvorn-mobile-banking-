import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN PRIVATE BANK", page_icon="🏛️", layout="wide")

# --- DATABASE ENGINE: HIGH-TRAFFIC ARCHITECTURE ---
# ใช้ชื่อไฟล์ใหม่เพื่อเริ่มต้นระบบที่รองรับคนจำนวนมากอย่างสมบูรณ์
DB_NAME = 'borworn_enterprise_final.db'

@st.cache_resource
def get_connection():
    """สร้าง Connection ครั้งเดียวและแชร์ใช้ร่วมกันเพื่อความเร็วสูงสุด"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=300) # รอคิวได้นาน 5 นาที
    # เปิดโหมด WAL (Write-Ahead Logging) เพื่อให้อ่านและเขียนพร้อมกันได้โดยไม่ล็อกไฟล์
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=-128000') # จองแรม 128MB เพื่อความลื่นไหล
    return conn

@contextmanager
def db_core():
    """ระบบจัดการธุรกรรมที่ปลอดภัยที่สุด ป้องกันข้อมูลพังเมื่อคนรุมใช้งาน"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Database Busy: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, pin TEXT, status TEXT DEFAULT 'Active', created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                      type TEXT, ref_no TEXT PRIMARY KEY, memo TEXT)''')

init_db()

# --- CSS: LUXURY SPACE GREY & GOLD (QR OPTIMIZED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #020617; }
    
    .luxury-header {
        background: linear-gradient(135deg, #1e293b 0%, #020617 100%);
        padding: 40px; border-radius: 0 0 40px 40px; color: #f8fafc;
        text-align: center; border-bottom: 2px solid #d4af37;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .qr-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px; border-radius: 20px;
        border: 1px solid #334155; text-align: center;
    }

    button[kind="primary"] {
        background: linear-gradient(90deg, #b45309 0%, #f59e0b 100%) !important;
        border: none !important; border-radius: 12px !important;
        font-weight: 600 !important; height: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- APP STATES ---
if "page" not in st.session_state: st.session_state.page = "login"
if "user" not in st.session_state: st.session_state.user = None
if "pin" not in st.session_state: st.session_state.pin = ""

# ---------------------------------------------------------
# 🛡️ GATEWAY
# ---------------------------------------------------------
if st.session_state.page == "login":
    st.markdown('<div class="luxury-header"><h1>BORWORN PRIVATE BANK</h1><p style="color:#d4af37; letter-spacing:5px;">ENTERPRISE ACCESS</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("SIGN IN", use_container_width=True, type="primary"):
                with db_core() as c:
                    res = c.execute("SELECT acc_id, pin, status FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    if res[2] == 'Active':
                        st.session_state.user = res[0]
                        st.session_state.page = "pin" if res[1] else "set_pin"
                        st.rerun()
                    else: st.error("Account Suspended")
                elif u == "admin" and p == "Kub1":
                    st.session_state.page = "admin"
                    st.rerun()
                else: st.error("Access Denied")

# ---------------------------------------------------------
# 🏠 CLIENT DASHBOARD (QR สีขาว)
# ---------------------------------------------------------
elif st.session_state.page == "main":
    with db_core() as c:
        u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user,)).fetchone()
    
    st.markdown(f'<div class="luxury-header"><small>ยอดเงินปัจจุบัน</small><h1 style="color:#f59e0b;">฿ {u[4]:,.2f}</h1></div>', unsafe_allow_html=True)
    
    nav = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "ออกจากระบบ"], icons=['house', 'send', 'clock', 'door-closed'], orientation="horizontal")

    if nav == "หน้าหลัก":
        st.markdown(f"""<div style="background:#1e293b; padding:20px; border-radius:20px; color:white; border-left:5px solid #d4af37;">
            <p style="margin:0; opacity:0.7;">เลขที่บัญชี</p>
            <h2 style="margin:0;">{u[0]}</h2>
            <p style="margin:10px 0 0 0;">คุณ {u[2]}</p>
        </div>""", unsafe_allow_html=True)
        
        st.write("")
        st.markdown('<p style="color:white; text-align:center;">QR รับเงิน (สีขาวสว่าง)</p>', unsafe_allow_html=True)
        
        # QR Code: ปรับสีเป็นสีขาว (Foreground: ffffff) และพื้นหลังโปร่งใส (Background: 020617)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}&color=ffffff&bgcolor=020617"
        
        col_q1, col_q2, col_q3 = st.columns([1,2,1])
        with col_q2:
            st.markdown(f'<div class="qr-container"><img src="{qr_url}" width="100%"></div>', unsafe_allow_html=True)

    elif nav == "โอนเงิน":
        with st.form("tx"):
            t = st.text_input("เลขบัญชีผู้รับ")
            a = st.number_input("จำนวนเงิน", min_value=1.0)
            if st.form_submit_button("ยืนยันการโอน", use_container_width=True, type="primary"):
                with db_core() as c:
                    recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (t,)).fetchone()
                    if recv and u[4] >= a and t != u[0]:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (a, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (a, t))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", (u[0], t, a, datetime.now().strftime("%d/%m/%Y %H:%M"), "Transfer", f"TX{int(time.time())}", ""))
                        st.success(f"โอนสำเร็จไปยังคุณ {recv[0]}"); st.balloons()
                    else: st.error("ยอดเงินไม่พอหรือเลขบัญชีไม่ถูกต้อง")

    elif nav == "ออกจากระบบ":
        st.session_state.page = "login"; st.rerun()

# ---------------------------------------------------------
# 👑 ADMIN: GOD MODE (รองรับคนเป็นร้อย)
# ---------------------------------------------------------
elif st.session_state.page == "admin":
    st.markdown('<div class="luxury-header"><h1>ADMIN CONTROL</h1></div>', unsafe_allow_html=True)
    a_nav = option_menu(None, ["รายชื่อสมาชิก", "เปิดบัญชีด่วน", "เปลี่ยนเลขบัญชี"], orientation="horizontal")

    if a_nav == "รายชื่อสมาชิก":
        with db_core() as c:
            df = pd.read_sql("SELECT acc_id, name, balance, status FROM Users", c.connection)
        st.dataframe(df, use_container_width=True)
        
        target = st.text_input("เลขบัญชีเป้าหมาย")
        if st.button("💰 เสกเงิน 1,000,000 บาท"):
            with db_core() as c: c.execute("UPDATE Users SET balance = balance + 1000000 WHERE acc_id=?", (target,))
            st.success("เสกเงินเข้าบัญชีเรียบร้อย")

    elif a_nav == "เปลี่ยนเลขบัญชี":
        old = st.text_input("เลขบัญชีเดิม")
        new = st.text_input("เลขบัญชีใหม่ (VIP)")
        if st.button("ตกลงอัปเดตเลขบัญชี"):
            with db_core() as c:
                c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (new, old))
                c.execute("UPDATE Transactions SET sender_id=? WHERE sender_id=?", (new, old))
                c.execute("UPDATE Transactions SET receiver_id=? WHERE receiver_id=?", (new, old))
            st.success("เปลี่ยนเลขบัญชีสำเร็จทั่วโลก!")

    if st.button("Exit Admin"): st.session_state.page = "login"; st.rerun()

# 🔢 PIN & SET PIN (ตัดย่อเพื่อประหยัดพื้นที่แต่ทำงานเหมือนเดิม)
elif st.session_state.page == "pin":
    st.markdown('<h2 style="text-align:center; color:white;">ENTER PIN</h2>', unsafe_allow_html=True)
    dots = " ".join(["●" if i < len(st.session_state.pin) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#f59e0b;'>{dots}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for i, k in enumerate(['1','2','3','4','5','6','7','8','9','C','0','<']):
        with [c1, c2, c3][i % 3]:
            if st.button(k, key=f"p_{k}", use_container_width=True):
                if k == '<': st.session_state.pin = st.session_state.pin[:-1]
                elif k == 'C': st.session_state.pin = ""
                elif len(st.session_state.pin) < 6: st.session_state.pin += k
                if len(st.session_state.pin) == 6:
                    with db_core() as c:
                        saved = c.execute("SELECT pin FROM Users WHERE acc_id=?", (st.session_state.user,)).fetchone()[0]
                    if st.session_state.pin == saved: st.session_state.page = "main"; st.session_state.pin = ""; st.rerun()
                    else: st.error("PIN ผิด"); st.session_state.pin = ""

elif st.session_state.page == "set_pin":
    p = st.text_input("ตั้งรหัส PIN 6 หลัก", type="password", max_chars=6)
    if st.button("ยืนยัน"):
        with db_core() as c: c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p, st.session_state.user))
        st.session_state.page = "main"; st.rerun()
