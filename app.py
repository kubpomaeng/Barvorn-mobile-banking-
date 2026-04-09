import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN PRESTIGE", page_icon="🏛️", layout="centered")

# --- DATABASE ---
DB_NAME = 'borworn_ultimate_v9.db'

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
                      balance REAL, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User')''')
        c.execute("INSERT OR IGNORE INTO Users (acc_id, username, name, password, balance, role) VALUES (?,?,?,?,?,?)",
                  ('2222222222', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 999999999.0, 'Admin'))

init_db()

# --- NEW CIRCULAR UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: white !important; }
    .stApp { background: #020617; }

    /* Header */
    .app-header {
        background: linear-gradient(180deg, #1e293b 0%, #020617 100%);
        padding: 40px 20px; border-radius: 0 0 40px 40px; text-align: center;
        border-bottom: 2px solid #f59e0b; margin-bottom: 30px;
    }

    /* Circle Menu Container */
    .menu-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
        text-align: center; margin-top: 20px;
    }

    /* Circle Button Style */
    .stButton > button {
        background: #1e293b !important;
        color: white !important;
        border: 2px solid #334155 !important;
        border-radius: 50% !important; /* ทำเป็นวงกลม */
        width: 100px !important;
        height: 100px !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 30px !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        border-color: #f59e0b !important;
        transform: scale(1.1);
        background: #0f172a !important;
    }
    
    /* Label under circle */
    .menu-label {
        font-size: 14px; margin-top: 8px; font-weight: 300;
        display: block; text-align: center; color: #f59e0b;
    }

    /* Admin Card */
    .admin-card {
        background: #0f172a; border: 1px solid #f59e0b;
        padding: 20px; border-radius: 20px; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "sub_page" not in st.session_state: st.session_state.sub_page = "home"

# --- LOGIN ---
if st.session_state.page == "login":
    st.markdown('<div class="app-header"><h1>BORWORN PRESTIGE</h1><p style="color:#f59e0b;">PRESTIGE ACCESS</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login_gate"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("UNLOCK", use_container_width=True):
                with db_core() as c:
                    res = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    st.session_state.user_id, st.session_state.username, st.session_state.user_full_name, st.session_state.user_pw, st.session_state.balance, st.session_state.status, st.session_state.user_role = res
                    st.session_state.page = "main"
                    st.rerun()
                else: st.error("ข้อมูลผิดพลาด")

# --- MAIN SYSTEM ---
elif st.session_state.page == "main":
    with db_core() as c:
        u_data = c.execute("SELECT balance, name FROM Users WHERE acc_id=?", (st.session_state.user_id,)).fetchone()
    
    st.markdown(f'''
    <div class="app-header">
        <p style="margin:0; opacity:0.7;">สวัสดีท่านประธาน</p>
        <h2 style="margin:0;">{u_data[1]}</h2>
        <h1 style="color:#f59e0b !important; font-size:3rem;">฿ {u_data[0]:,.2f}</h1>
    </div>
    ''', unsafe_allow_html=True)

    # --- เมนูวงกลม (Dashboard) ---
    if st.session_state.sub_page == "home":
        # แถวที่ 1
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💸", key="m1"): st.session_state.sub_page = "send"
            st.markdown('<span class="menu-label">โอนเงิน</span>', unsafe_allow_html=True)
        with col2:
            if st.button("📥", key="m2"): st.session_state.sub_page = "receive"
            st.markdown('<span class="menu-label">รับเงิน</span>', unsafe_allow_html=True)
        with col3:
            if st.button("📸", key="m3"): st.session_state.sub_page = "scan"
            st.markdown('<span class="menu-label">สแกน</span>', unsafe_allow_html=True)
            
        # แถวที่ 2
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("👤", key="m4"): st.session_state.sub_page = "profile"
            st.markdown('<span class="menu-label">โปรไฟล์</span>', unsafe_allow_html=True)
        with col5:
            # ตรวจสอบสิทธิ์ Admin
            if st.session_state.user_role == "Admin":
                if st.button("👑", key="m5"): st.session_state.sub_page = "admin"
                st.markdown('<span class="menu-label">แอดมิน</span>', unsafe_allow_html=True)
            else:
                if st.button("🎁", key="m5_u"): st.info("สิทธิพิเศษ")
                st.markdown('<span class="menu-label">ของขวัญ</span>', unsafe_allow_html=True)
        with col6:
            if st.button("🚪", key="m6"): 
                st.session_state.page = "login"; st.session_state.sub_page = "home"; st.rerun()
            st.markdown('<span class="menu-label">ออก</span>', unsafe_allow_html=True)

    # --- เนื้อหาหน้าย่อย ---
    if st.session_state.sub_page != "home":
        if st.button("⬅️ ย้อนกลับ"): 
            st.session_state.sub_page = "home"; st.rerun()
        st.divider()

    if st.session_state.sub_page == "send":
        st.subheader("โอนเงิน")
        t_id = st.text_input("เลขบัญชีผู้รับ")
        t_amt = st.number_input("จำนวนเงิน (฿)", min_value=0.0)
        if st.button("ตกลงโอนเงิน", type="primary"):
            st.success("โอนสำเร็จ!"); time.sleep(1); st.rerun()

    elif st.session_state.sub_page == "receive":
        st.subheader("รับเงินผ่าน QR")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={st.session_state.user_id}&color=020617&bgcolor=ffffff"
        st.image(qr, width=200)
        st.code(f"เลขบัญชี: {st.session_state.user_id}")

    elif st.session_state.sub_page == "profile":
        st.subheader("ข้อมูลส่วนตัว")
        new_name = st.text_input("ชื่อ-นามสกุล", value=u_data[1])
        if st.button("บันทึก"):
            with db_core() as c: c.execute("UPDATE Users SET name=? WHERE acc_id=?", (new_name, st.session_state.user_id))
            st.success("แก้ไขแล้ว"); st.rerun()

    # --- 👑 หน้า ADMIN แบบจัดเต็ม (MASTER CONTROL) ---
    elif st.session_state.sub_page == "admin":
        st.subheader("👑 ศูนย์ควบคุมอำนาจเบ็ดเสร็จ")
        
        tab1, tab2, tab3 = st.tabs(["👥 จัดการสมาชิก", "💰 เสก/คุมเงิน", "📊 ภาพรวมธนาคาร"])
        
        with tab1:
            st.write("รายชื่อลูกค้าทั้งหมด")
            with db_core() as c:
                users = pd.read_sql("SELECT acc_id, name, username, status, role FROM Users", c.connection)
            st.dataframe(users, use_container_width=True)
            
            target_acc = st.text_input("ระบุเลขบัญชีที่ต้องการจัดการ")
            c1, c2, c3 = st.columns(3)
            if c1.button("🔴 ระงับบัญชี (Ban)"):
                with db_core() as c: c.execute("UPDATE Users SET status='Banned' WHERE acc_id=?", (target_acc,))
                st.warning("ระงับสำเร็จ"); st.rerun()
            if c2.button("🟢 ปลดระงับ"):
                with db_core() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (target_acc,))
                st.success("ปลดระงับแล้ว"); st.rerun()
            if c3.button("🗑️ ลบบัญชีทิ้ง"):
                if target_acc != "2222222222":
                    with db_core() as c: c.execute("DELETE FROM Users WHERE acc_id=?", (target_acc,))
                    st.error("ลบเรียบร้อย"); st.rerun()

        with tab2:
            st.write("สั่งการด้านการเงิน")
            t_acc = st.text_input("เลขบัญชีที่ต้องการฉีดเงิน")
            t_amt = st.number_input("จำนวนเงิน (เสกเข้า)", min_value=0.0)
            if st.button("✨ ยืนยันการเสกเงิน", type="primary"):
                with db_core() as c: c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (t_amt, t_acc))
                st.success("เสกเงินเข้าเรียบร้อย!"); st.rerun()
            
            st.divider()
            if st.button("💸 ล้างเงินทั้งหมดในระบบ (Set 0)"):
                with db_core() as c: c.execute("UPDATE Users SET balance = 0 WHERE acc_id != '2222222222'")
                st.warning("ล้างเงินเรียบร้อย (ยกเว้นท่านประธาน)"); st.rerun()

        with tab3:
            with db_core() as c:
                total_m = c.execute("SELECT SUM(balance) FROM Users").fetchone()[0]
                count_u = c.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
            st.metric("จำนวนเงินหมุนเวียนทั้งหมด", f"฿ {total_m:,.2f}")
            st.metric("จำนวนสมาชิกทั้งหมด", f"{count_u} ราย")
