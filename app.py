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
DB_NAME = 'borworn_final_v13.db'

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
        st.error(f"ระบบขัดข้อง: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User', created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, timestamp TEXT, type TEXT)''')
        
        # บัญชีหลักของท่านประธาน (The Owner)
        c.execute("INSERT OR IGNORE INTO Users (acc_id, username, name, password, balance, role, created_at) VALUES (?,?,?,?,?,?,?)",
                  ('1287892888', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 100000.0, 'Admin', '01/01/2026 00:00'))
◌ุ
init_db()

# --- LUXURY CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: white !important; }
    .stApp { background-color: #020617; margin-bottom: 120px; }
    
    .app-header {
        background: linear-gradient(180deg, #1e293b 0%, #020617 100%);
        padding: 40px 20px; text-align: center; border-bottom: 2px solid #f59e0b; margin-bottom: 20px;
    }

    /* Bottom Navigation */
    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0;
        background: rgba(15, 23, 42, 0.98); backdrop-filter: blur(15px);
        display: flex; justify-content: space-around; padding: 15px 0;
        border-top: 1px solid #f59e0b; z-index: 9999;
    }
    
    .nav-btn { background: transparent !important; border: none !important; font-size: 22px !important; }
    .nav-label { font-size: 11px; color: #94a3b8; display: block; text-align: center; }

    /* Cards */
    .glass-card {
        background: rgba(255,255,255,0.05); padding: 20px; border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px;
    }
    
    input { background-color: #0f172a !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "sub_page" not in st.session_state: st.session_state.sub_page = "หน้าหลัก"

# --- 🔐 LOGIN ---
if st.session_state.page == "login":
    st.markdown('<div class="app-header"><h1>BORWORN PRESTIGE</h1><p>กรุณาใช้รหัสผ่านที่ธนาคารออกให้</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("UNLOCK ACCESS", use_container_width=True):
                with db_core() as c:
                    res = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    if res[5] == 'Banned': st.error("บัญชีนี้ถูกอายัด กรุณาติดต่อธนาคาร")
                    else:
                        st.session_state.user_data = res # (acc_id, user, name, pw, bal, status, role, date)
                        st.session_state.page = "main"; st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- 🏦 MAIN APP ---
elif st.session_state.page == "main":
    # Refresh User Data
    with db_core() as c:
        st.session_state.user_data = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_data[0],)).fetchone()
    
    u = st.session_state.user_data
    
    # 1. หน้าหลัก
    if st.session_state.sub_page == "หน้าหลัก":
        st.markdown(f'<div class="app-header"><small>ยอดเงินที่ใช้ได้</small><h1 style="color:#f59e0b;">฿ {u[4]:,.2f}</h1><p>{u[2]}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="glass-card"><b>เลขบัญชี:</b> {u[0]}<br><b>สถานะ:</b> {u[5]}</div>', unsafe_allow_html=True)
        st.write("🕒 รายการล่าสุด")
        with db_core() as c:
            tx = pd.read_sql("SELECT * FROM Transactions WHERE sender_id=? OR receiver_id=? ORDER BY timestamp DESC LIMIT 5", c.connection, params=(u[0], u[0]))
        st.dataframe(tx, use_container_width=True)

    # 2. รับเงิน
    elif st.session_state.sub_page == "รับเงิน":
        st.markdown("<h2 style='text-align:center;'>รับเงิน</h2>", unsafe_allow_html=True)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}&color=020617&bgcolor=ffffff"
        st.image(qr_url, use_container_width=True)
        st.markdown(f"<div class='glass-card' style='text-align:center;'><h3>{u[0]}</h3><p>{u[2]}</p></div>", unsafe_allow_html=True)

    # 3. โอนเงิน
    elif st.session_state.sub_page == "โอนเงิน":
        st.subheader("โอนเงิน")
        t_mode = st.radio("เลือกวิธีโอน", ["ระบุเลขบัญชี", "สแกน QR Code (จำลอง)"], horizontal=True)
        with st.form("transfer"):
            target = st.text_input("เลขบัญชีปลายทาง")
            amt = st.number_input("จำนวนเงิน (฿)", min_value=0.01)
            if st.form_submit_button("ยืนยันการโอน", use_container_width=True):
                with db_core() as c:
                    recv = c.execute("SELECT balance, status FROM Users WHERE acc_id=?", (target,)).fetchone()
                    if not recv: st.error("ไม่พบเลขบัญชีนี้")
                    elif u[4] < amt: st.error("ยอดเงินไม่เพียงพอ")
                    elif u[5] == 'Banned': st.error("บัญชีท่านถูกอายัด")
                    else:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%d/%m/%Y %H:%M"), "Transfer"))
                        st.success("โอนเงินสำเร็จ!"); time.sleep(1); st.rerun()

    # 4. บัญชี (และเมนู Admin)
    elif st.session_state.sub_page == "บัญชี":
        st.subheader("ข้อมูลบัญชี")
        with st.expander("👤 ข้อมูลส่วนตัว", expanded=True):
            st.write(f"**Username:** {u[1]}")
            st.write(f"**Password:** {u[3]}")
            st.write(f"**ตำแหน่ง:** {u[6]}")
            new_n = st.text_input("แก้ไขชื่อ-นามสกุล", value=u[2])
            if st.button("บันทึกการเปลี่ยนชื่อ"):
                with db_core() as c: c.execute("UPDATE Users SET name=? WHERE acc_id=?", (new_n, u[0]))
                st.success("เปลี่ยนชื่อสำเร็จ"); st.rerun()
        
        # --- 👑 ADMIN SECTION (Visible only to Admin) ---
        if u[6] == 'Admin':
            st.markdown("---")
            st.subheader("👑 ระบบจัดการแอดมิน")
            adm_choice = st.selectbox("เลือกฟังก์ชัน", ["1. สร้างบัญชีใหม่", "2. อายัด/ปลดอายัด", "3. ข้อมูลผู้ใช้ทั้งหมด", "4. ข้อมูลธุรกรรมทั้งหมด", "5. เปลี่ยนเลขบัญชี", "6. เสกเงิน", "7. มอบสิทธิ์ Admin"])
            
            if adm_choice == "1. สร้างบัญชีใหม่":
                with st.form("adm_reg"):
                    new_u = st.text_input("Username")
                    new_p = st.text_input("Password")
                    new_name = st.text_input("ชื่อจริง")
                    if st.form_submit_button("สร้างบัญชี (สุ่มเลข)"):
                        new_acc = str(random.randint(1000000000, 9999999999))
                        with db_core() as c: c.execute("INSERT INTO Users (acc_id, username, name, password, balance, created_at) VALUES (?,?,?,?,?,?)", (new_acc, new_u, new_name, new_p, 0.0, datetime.now().strftime("%d/%m/%Y %H:%M")))
                        st.success(f"สร้างสำเร็จ! เลขบัญชี: {new_acc}")

            elif adm_choice == "2. อายัด/ปลดอายัด":
                target_a = st.text_input("ใส่เลขบัญชี")
                c_a, c_b = st.columns(2)
                if c_a.button("🔴 อายัดบัญชี", use_container_width=True):
                    with db_core() as c: c.execute("UPDATE Users SET status='Banned' WHERE acc_id=?", (target_a,))
                    st.warning("อายัดเรียบร้อย")
                if c_b.button("🟢 ปลดอายัด", use_container_width=True):
                    with db_core() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (target_a,))
                    st.success("ปลดอายัดเรียบร้อย")

            elif adm_choice == "3. ข้อมูลผู้ใช้ทั้งหมด":
                with db_core() as c:
                    all_u = pd.read_sql("SELECT acc_id, name, username, password, created_at, role, status FROM Users", c.connection)
                st.dataframe(all_u, use_container_width=True)

            elif adm_choice == "4. ข้อมูลธุรกรรมทั้งหมด":
                with db_core() as c:
                    all_tx = pd.read_sql("SELECT * FROM Transactions ORDER BY timestamp DESC", c.connection)
                st.dataframe(all_tx, use_container_width=True)

            elif adm_choice == "5. เปลี่ยนเลขบัญชี":
                t_acc = st.text_input("เลขบัญชีเดิม")
                n_acc = st.text_input("เลขบัญชีใหม่")
                if st.button("ยืนยันเปลี่ยนเลขบัญชี"):
                    if t_acc == u[0]: st.error("ไม่สามารถเปลี่ยนเลขบัญชีของเจ้าของ (ตัวท่าน) ได้")
                    else:
                        with db_core() as c: c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (n_acc, t_acc))
                        st.success("เปลี่ยนเลขบัญชีแล้ว")

            elif adm_choice == "6. เสกเงิน":
                s_acc = st.text_input("เลขบัญชีที่จะรับเงิน")
                s_amt = st.number_input("จำนวนเงิน (0.01 - $\infty$)", min_value=0.01, step=1000.0)
                if st.button("✨ EXECUTE (เสกเงิน)"):
                    with db_core() as c: c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (s_amt, s_acc))
                    st.success(f"เสกเงิน ฿{s_amt:,.2f} เข้าบัญชี {s_acc} สำเร็จ")

            elif adm_choice == "7. มอบสิทธิ์ Admin":
                m_acc = st.text_input("ระบุเลขบัญชีที่จะมอบสิทธิ์")
                if st.button("มอบสิทธิ์ Admin"):
                    with db_core() as c: c.execute("UPDATE Users SET role='Admin' WHERE acc_id=?", (m_acc,))
                    st.success("มอบสิทธิ์เรียบร้อย")

        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.page = "login"; st.rerun()

    # --- 📱 BOTTOM NAVIGATION ---
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    nb1, nb2, nb3, nb4 = st.columns(4)
    with nb1:
        if st.button("🏠", key="h"): st.session_state.sub_page = "หน้าหลัก"; st.rerun()
        st.markdown('<span class="nav-label">หน้าหลัก</span>', unsafe_allow_html=True)
    with nb2:
        if st.button("📥", key="r"): st.session_state.sub_page = "รับเงิน"; st.rerun()
        st.markdown('<span class="nav-label">รับเงิน</span>', unsafe_allow_html=True)
    with nb3:
        if st.button("💸", key="t"): st.session_state.sub_page = "โอนเงิน"; st.rerun()
        st.markdown('<span class="nav-label">โอนเงิน</span>', unsafe_allow_html=True)
    with nb4:
        if st.button("👤", key="a"): st.session_state.sub_page = "บัญชี"; st.rerun()
        st.markdown('<span class="nav-label">บัญชี</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
