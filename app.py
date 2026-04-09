import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN PRESTIGE", page_icon="🏛️", layout="centered")

# --- DATABASE ENGINE ---
DB_NAME = 'borworn_prestige_v17.db'

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
        st.error(f"เกิดข้อผิดพลาด: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User', created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, timestamp TEXT)''')
        
        # บัญชีท่านประธาน (The Owner)
        c.execute("INSERT OR IGNORE INTO Users VALUES (?,?,?,?,?,?,?,?)",
                  ('1456428988', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 100000.0, 'Active', 'Admin', '01/01/2026 00:00'))

init_db()

# --- LUXURY CSS (FIX OVERLAP) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: white !important; }
    .stApp { background: #020617; }
    
    /* Header Style */
    .main-header {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        padding: 20px; border-radius: 15px; border-left: 5px solid #f59e0b;
        margin-bottom: 20px;
    }
    .balance-text { color: #f59e0b; font-size: 32px; font-weight: 600; margin: 0; }
    
    /* Sidebar Fixes */
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #f59e0b; }
    
    /* Input & Button */
    .stTextInput>div>div>input { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #f59e0b !important; background: transparent; color: white; transition: 0.3s; }
    .stButton>button:hover { background: #f59e0b !important; color: #020617 !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"

# --- 🔐 LOGIN ---
if st.session_state.page == "login":
    st.markdown('<div style="text-align:center; padding:50px 0;"><h1>🏛️ BORWORN PRESTIGE</h1><p>PRIVATE BANKING</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            u_in = st.text_input("Username")
            p_in = st.text_input("Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ"):
                with db_core() as c:
                    res = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u_in, p_in)).fetchone()
                if res:
                    if res[5] == 'Banned': st.error("บัญชีถูกอายัด")
                    else:
                        st.session_state.user = res
                        st.session_state.page = "main"; st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- 🏦 MAIN APP (SIDEBAR MENU) ---
elif st.session_state.page == "main":
    # Refresh User Data
    with db_core() as c:
        st.session_state.user = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user[0],)).fetchone()
    
    u = st.session_state.user

    # --- 🍔 SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown(f"### 👤 {u[2]}")
        st.caption(f"ตำแหน่ง: {u[6]}")
        st.divider()
        menu = st.radio("เมนูการใช้งาน", ["หน้าหลัก", "รับเงิน", "โอนเงิน", "บัญชี"])
        st.divider()
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.page = "login"; st.rerun()

    # --- CONTENT AREA ---
    if menu == "หน้าหลัก":
        st.markdown(f'''<div class="main-header">
            <small>ยอดเงินที่ใช้ได้</small>
            <p class="balance-text">฿ {u[4]:,.2f}</p>
            <p>เลขบัญชี: {u[0]}</p>
        </div>''', unsafe_allow_html=True)
        
        st.write("🕒 **ธุรกรรมล่าสุดของคุณ**")
        with db_core() as c:
            tx = pd.read_sql("SELECT receiver_id as 'ผู้รับ', amount as 'ยอดเงิน', timestamp as 'เวลา' FROM Transactions WHERE sender_id=? OR receiver_id=? ORDER BY timestamp DESC LIMIT 5", c.connection, params=(u[0], u[0]))
        if tx.empty: st.caption("ยังไม่มีรายการเดินบัญชี")
        else: st.dataframe(tx, use_container_width=True)

    elif menu == "รับเงิน":
        st.subheader("QR Code สำหรับรับเงิน")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}&color=020617&bgcolor=ffffff"
        st.image(qr, use_container_width=True)
        st.info(f"เลขบัญชี: {u[0]}")

    elif menu == "โอนเงิน":
        st.subheader("โอนเงินผ่านระบบ")
        mode = st.tabs(["เลขบัญชี", "QR Code"])
        with mode[0]:
            with st.form("t_form"):
                target = st.text_input("ระบุเลขบัญชีปลายทาง")
                amt = st.number_input("จำนวนเงิน (฿)", min_value=0.01)
                if st.form_submit_button("ตกลงโอนเงิน"):
                    with db_core() as c:
                        recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
                        if not recv: st.error("ไม่พบเลขบัญชี")
                        elif u[4] < amt: st.error("เงินในบัญชีไม่พอ")
                        else:
                            c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                            c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                            c.execute("INSERT INTO Transactions VALUES (?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%H:%M")))
                            st.success(f"โอนสำเร็จไปยัง {recv[0]}"); time.sleep(1); st.rerun()

    elif menu == "บัญชี":
        st.subheader("ข้อมูลบัญชีผู้ใช้งาน")
        st.markdown(f'''<div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:15px;">
            <b>ชื่อ:</b> {u[2]} <br>
            <b>Username:</b> {u[1]} <br>
            <b>รหัสผ่าน:</b> {u[3]} <br>
            <b>สถานะ:</b> {u[5]}
        </div>''', unsafe_allow_html=True)
        
        new_n = st.text_input("เปลี่ยนชื่อ-นามสกุล", value=u[2])
        if st.button("บันทึกชื่อใหม่"):
            with db_core() as c: c.execute("UPDATE Users SET name=? WHERE acc_id=?", (new_n, u[0]))
            st.success("เปลี่ยนชื่อสำเร็จ"); st.rerun()

        # --- 👑 ADMIN SECTION ---
        if u[6] == 'Admin':
            st.divider()
            st.subheader("👑 ระบบควบคุมแอดมิน")
            opt = st.selectbox("เลือกฟังก์ชัน", ["1. สร้างบัญชีใหม่", "2. อายัด/ปลดอายัด", "3. ข้อมูลผู้ใช้ทั้งหมด", "4. ข้อมูลธุรกรรมทั้งหมด", "5. เปลี่ยนเลขบัญชี", "6. เสกเงิน", "7. มอบสิทธิ์ Admin"])
            
            if opt == "1. สร้างบัญชีใหม่":
                with st.form("a1"):
                    un = st.text_input("Username")
                    pw = st.text_input("Password")
                    nm = st.text_input("ชื่อจริง")
                    if st.form_submit_button("สร้างบัญชี (สุ่มเลข)"):
                        new_id = str(random.randint(1000000000, 9999999999))
                        with db_core() as c: c.execute("INSERT INTO Users VALUES (?,?,?,?,?,?,?,?)", (new_id, un, nm, pw, 0.0, 'Active', 'User', datetime.now().strftime("%H:%M")))
                        st.success(f"สร้างสำเร็จ! เลขบัญชี: {new_id}")

            elif opt == "2. อายัด/ปลดอายัด":
                tid = st.text_input("เลขบัญชีที่ต้องการจัดการ")
                ca, cb = st.columns(2)
                if ca.button("🔴 อายัด"):
                    with db_core() as c: c.execute("UPDATE Users SET status='Banned' WHERE acc_id=?", (tid,))
                    st.warning("อายัดแล้ว")
                if cb.button("🟢 ปลด"):
                    with db_core() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (tid,))
                    st.success("ปลดแล้ว")

            elif opt == "3. ข้อมูลผู้ใช้ทั้งหมด":
                with db_core() as c:
                    df = pd.read_sql("SELECT acc_id, name, username, password, created_at, role, status FROM Users", c.connection)
                st.dataframe(df, use_container_width=True)

            elif opt == "4. ข้อมูลธุรกรรมทั้งหมด":
                with db_core() as c:
                    df_t = pd.read_sql("SELECT * FROM Transactions", c.connection)
                st.dataframe(df_t, use_container_width=True)

            elif opt == "5. เปลี่ยนเลขบัญชี":
                oid = st.text_input("เลขเดิม")
                nid = st.text_input("เลขใหม่")
                if st.button("เปลี่ยนเลข"):
                    if oid == "2222222222": st.error("ห้ามเปลี่ยนเลขบัญชีเจ้าของระบบ")
                    else:
                        with db_core() as c: c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (nid, oid))
                        st.success("เปลี่ยนเลขสำเร็จ")

            elif opt == "6. เสกเงิน":
                sid = st.text_input("เลขบัญชีรับเงิน")
                samt = st.number_input("จำนวนเงินเสก", min_value=0.01)
                if st.button("✨ EXECUTE"):
                    with db_core() as c: c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (samt, sid))
                    st.success("เสกเงินสำเร็จ")

            elif opt == "7. มอบสิทธิ์ Admin":
                mid = st.text_input("เลขบัญชีที่จะให้สิทธิ์")
                if st.button("Grant Admin Role"):
                    with db_core() as c: c.execute("UPDATE Users SET role='Admin' WHERE acc_id=?", (mid,))
                    st.success("มอบสิทธิ์สำเร็จ")
