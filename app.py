import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN PRESTIGE", page_icon="🏛️", layout="wide")

# --- DATABASE ---
DB_NAME = 'borworn_prestige_v8.db'

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=300)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

@contextmanager
def db_core():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, pin TEXT, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User')''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                      type TEXT, ref_no TEXT PRIMARY KEY, memo TEXT)''')
        
        # บัญชีท่านประธาน (Master Account)
        c.execute("INSERT OR IGNORE INTO Users (acc_id, username, name, password, balance, role) VALUES (?,?,?,?,?,?)",
                  ('2222222222', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 999999999.0, 'Admin'))

init_db()

# --- LUXURY GRID UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: #FFFFFF !important; }
    .stApp { background: radial-gradient(circle at top, #1e293b, #020617); }

    /* Header Design */
    .app-header {
        background: rgba(255, 255, 255, 0.03);
        padding: 30px; border-radius: 0 0 40px 40px; text-align: center;
        border-bottom: 2px solid #f59e0b; margin-bottom: 20px;
    }

    /* Grid Menu System */
    .menu-card {
        background: rgba(255, 255, 255, 0.07);
        padding: 40px 20px; border-radius: 25px; text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: 0.3s; cursor: pointer; height: 200px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .menu-card:hover {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid #f59e0b; transform: translateY(-5px);
    }
    .menu-icon { font-size: 50px; margin-bottom: 15px; }
    .menu-label { font-size: 18px; font-weight: 400; letter-spacing: 1px; }

    /* Input Styling */
    input { background-color: #0f172a !important; color: white !important; border: 1px solid #334155 !important; }
    
    /* Button Styling */
    button[kind="primary"] {
        background: linear-gradient(90deg, #b45309, #f59e0b) !important;
        border: none !important; border-radius: 12px !important; font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "sub_page" not in st.session_state: st.session_state.sub_page = "home"

# --- LOGIN ---
if st.session_state.page == "login":
    st.markdown('<div class="app-header"><h1>BORWORN PRESTIGE</h1><p style="color:#f59e0b;">BANKING MANAGEMENT SYSTEM</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login_form"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("LOGIN", use_container_width=True, type="primary"):
                with db_core() as c:
                    res = c.execute("SELECT acc_id, role, name, password FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    st.session_state.user_id, st.session_state.user_role, st.session_state.user_full_name, st.session_state.user_pw = res
                    st.session_state.page = "main"
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- MAIN SYSTEM ---
elif st.session_state.page == "main":
    with db_core() as c:
        u_bal = c.execute("SELECT balance FROM Users WHERE acc_id=?", (st.session_state.user_id,)).fetchone()[0]

    # --- Header ---
    st.markdown(f'''
    <div class="app-header">
        <p style="margin:0; opacity:0.7;">ยอดเงินในบัญชีของคุณ</p>
        <h1 style="color:#f59e0b !important; font-size:3rem;">฿ {u_bal:,.2f}</h1>
        <p style="margin:0;">{st.session_state.user_full_name}</p>
    </div>
    ''', unsafe_allow_html=True)

    # --- Home Menu (The Grid) ---
    if st.session_state.sub_page == "home":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💸\n\nโอนเงิน", use_container_width=True, key="btn_send"): st.session_state.sub_page = "send"
        with col2:
            if st.button("📥\n\nรับเงิน / QR", use_container_width=True, key="btn_receive"): st.session_state.sub_page = "receive"
        with col3:
            if st.button("📸\n\nสแกนจ่าย", use_container_width=True, key="btn_scan"): st.session_state.sub_page = "scan"
            
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("👤\n\nข้อมูลส่วนตัว", use_container_width=True, key="btn_profile"): st.session_state.sub_page = "profile"
        
        # แสดงเมนูแอดมินเฉพาะท่านประธาน
        if st.session_state.user_role == "Admin":
            with col5:
                if st.button("👑\n\nศูนย์ควบคุมแอดมิน", use_container_width=True, key="btn_admin"): st.session_state.sub_page = "admin"
        else:
            with col5:
                if st.button("📈\n\nการลงทุน", use_container_width=True, key="btn_invest"): st.info("เร็วๆ นี้")
        
        with col6:
            if st.button("🚪\n\nออกจากระบบ", use_container_width=True, key="btn_logout"): 
                st.session_state.page = "login"; st.session_state.sub_page = "home"; st.rerun()

    # --- Sub Pages Logic ---
    if st.session_state.sub_page != "home":
        if st.button("⬅️ กลับหน้าหลัก"): 
            st.session_state.sub_page = "home"; st.rerun()
        st.divider()

    # 1. โอนเงิน
    if st.session_state.sub_page == "send":
        st.subheader("โอนเงินไปยังบัญชีอื่น")
        with st.form("f_send"):
            target = st.text_input("เลขบัญชีปลายทาง")
            amt = st.number_input("จำนวนเงิน", min_value=0.0)
            if st.form_submit_button("ยืนยันการโอน", type="primary"):
                with db_core() as c:
                    if u_bal >= amt:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, st.session_state.user_id))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                        st.success("โอนสำเร็จ!"); time.sleep(1); st.rerun()

    # 2. รับเงิน
    elif st.session_state.sub_page == "receive":
        st.subheader("QR รับเงินของคุณ")
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={st.session_state.user_id}&color=020617&bgcolor=ffffff"
        st.image(qr_url, width=250)
        st.write(f"เลขบัญชี: {st.session_state.user_id}")

    # 3. สแกนจ่าย (จำลอง)
    elif st.session_state.sub_page == "scan":
        st.info("📷 กำลังเปิดกล้องเพื่อสแกน QR Code... (ระบบจำลอง)")
        st.warning("กรุณาอนุญาตการเข้าถึงกล้องในอุปกรณ์ของคุณ")

    # 4. ข้อมูลส่วนตัว (แก้ไขชื่อ/แจ้งปัญหา)
    elif st.session_state.sub_page == "profile":
        st.subheader("👤 จัดการข้อมูลส่วนตัว")
        with st.form("f_profile"):
            new_name = st.text_input("ชื่อ-นามสกุล", value=st.session_state.user_full_name)
            new_pw = st.text_input("เปลี่ยนรหัสผ่าน", value=st.session_state.user_pw, type="password")
            if st.form_submit_button("บันทึกการเปลี่ยนแปลง"):
                with db_core() as c:
                    c.execute("UPDATE Users SET name=?, password=? WHERE acc_id=?", (new_name, new_pw, st.session_state.user_id))
                st.success("อัปเดตข้อมูลแล้ว กรุณาล็อกอินใหม่"); time.sleep(2); st.session_state.page = "login"; st.rerun()
        
        st.divider()
        st.subheader("⚠️ แจ้งปัญหาเกี่ยวกับแอป")
        report = st.text_area("กรุณาระบุปัญหาที่พบ...")
        if st.button("ส่งรายงานปัญหา"):
            st.success("ส่งเรื่องไปยังฝ่ายเทคนิคแล้ว ขอบคุณครับ")

    # 5. แอดมิน (ศูนย์ควบคุม)
    elif st.session_state.sub_page == "admin":
        st.subheader("👑 สิทธิ์ควบคุมระดับแอดมิน")
        with db_core() as c:
            df = pd.read_sql("SELECT acc_id, name, balance, role FROM Users", c.connection)
        st.dataframe(df, use_container_width=True)
        st.divider()
        st.write("💉 เสกเงินด่วน")
        t_id = st.text_input("เลขบัญชีที่ต้องการฉีดเงิน")
        t_amt = st.number_input("ยอดเงินเสก", min_value=0.0)
        if st.button("ดำเนินการเสกเงิน", type="primary"):
            with db_core() as c: c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (t_amt, t_id))
            st.success("สำเร็จ!"); time.sleep(1); st.rerun()
