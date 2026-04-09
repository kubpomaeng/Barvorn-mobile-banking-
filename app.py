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
DB_NAME = 'borworn_prestige_v16.db'

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
        st.error(f"เกิดข้อผิดพลาดทางเทคนิค: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User', created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, timestamp TEXT, tx_id TEXT)''')
        
        # บัญชีพระเจ้า (ท่านประธาน)
        c.execute("INSERT OR IGNORE INTO Users VALUES (?,?,?,?,?,?,?,?)",
                  ('2222222222', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 999999999.0, 'Active', 'Admin', '01/01/2026 00:00'))

init_db()

# --- PRESTIGE STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: white !important; }
    .stApp { background: radial-gradient(circle at top, #1e293b 0%, #020617 100%); margin-bottom: 100px; }
    
    .header-box { background: rgba(255,255,255,0.03); padding: 30px; border-radius: 0 0 40px 40px; border-bottom: 1px solid #f59e0b; text-align: center; margin-bottom: 25px; }
    .glass { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px; }
    
    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0;
        background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(15px);
        display: flex; justify-content: space-around; padding: 12px 0;
        border-top: 1px solid #f59e0b; z-index: 9999;
    }
    .nav-label { font-size: 10px; color: #94a3b8; margin-top: 4px; display: block; text-align: center; }
    
    .stButton > button { background: transparent !important; border: none !important; transition: 0.3s; }
    .stButton > button:hover { transform: scale(1.1); color: #f59e0b !important; }
    
    input { background-color: #0f172a !important; border: 1px solid #334155 !important; color: white !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "sub_page" not in st.session_state: st.session_state.sub_page = "หน้าหลัก"

# --- LOGIN PAGE ---
if st.session_state.page == "login":
    st.markdown('<div class="header-box"><h1>🏛️ BORWORN PRESTIGE</h1><p style="color:#f59e0b">PRIVATE BANKING SYSTEM</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("UNLOCK ACCESS", use_container_width=True):
                with db_core() as c:
                    res = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    if res[5] == 'Banned': st.error("บัญชีถูกอายัดชั่วคราว")
                    else:
                        st.session_state.user = res
                        st.session_state.page = "main"; st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- MAIN APPLICATION ---
elif st.session_state.page == "main":
    with db_core() as c:
        st.session_state.user = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user[0],)).fetchone()
    
    u = st.session_state.user
    
    st.markdown(f'''<div class="header-box">
        <small style="color:#94a3b8">ยอดเงินคงเหลือ</small>
        <h1 style="color:#f59e0b; margin:0">฿ {u[4]:,.2f}</h1>
        <p style="margin:5px 0 0 0">{u[2]}</p>
        <code style="background:transparent; color:#94a3b8">ACC: {u[0]}</code>
    </div>''', unsafe_allow_html=True)

    # 1. หน้าหลัก
    if st.session_state.sub_page == "หน้าหลัก":
        st.write("🕒 **ธุรกรรมล่าสุด**")
        with db_core() as c:
            tx = pd.read_sql("SELECT receiver_id as 'ผู้รับ', amount as 'ยอดเงิน', timestamp as 'เวลา' FROM Transactions WHERE sender_id=? OR receiver_id=? ORDER BY timestamp DESC LIMIT 5", c.connection, params=(u[0], u[0]))
        if tx.empty: st.caption("ยังไม่มีรายการเดินบัญชี")
        else: st.table(tx)

    # 2. รับเงิน
    elif st.session_state.sub_page == "รับเงิน":
        st.subheader("QR Code รับโอน")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}&color=020617&bgcolor=ffffff"
        st.image(qr, use_container_width=True)
        st.markdown(f"<div class='glass' style='text-align:center;'><h4>{u[0]}</h4><p>{u[2]}</p></div>", unsafe_allow_html=True)

    # 3. โอนเงิน
    elif st.session_state.sub_page == "โอนเงิน":
        st.subheader("โอนเงินด่วน")
        with st.form("t_acc"):
            target = st.text_input("ระบุเลขบัญชีปลายทาง")
            amt = st.number_input("จำนวนเงิน (฿)", min_value=0.01)
            if st.form_submit_button("ยืนยันการโอน", use_container_width=True):
                with db_core() as c:
                    recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
                    if not recv: st.error("เลขบัญชีไม่ถูกต้อง")
                    elif u[4] < amt: st.error("ยอดเงินคงเหลือไม่พอ")
                    else:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%H:%M"), f"TX{random.randint(100,999)}"))
                        st.balloons(); st.success("โอนสำเร็จ!"); time.sleep(1); st.rerun()

    # 4. บัญชี & Admin Control
    elif st.session_state.sub_page == "บัญชี":
        st.subheader("โปรไฟล์ผู้ใช้งาน")
        st.markdown(f'''<div class="glass">
            <b>ชื่อ-นามสกุล:</b> {u[2]} <br>
            <b>ตำแหน่ง:</b> <span style="color:#f59e0b">{u[6]}</span> <br>
            <b>สถานะ:</b> {u[5]}
        </div>''', unsafe_allow_html=True)
        
        with st.expander("👤 แก้ไขโปรไฟล์"):
            new_name = st.text_input("เปลี่ยนชื่อ-นามสกุล", value=u[2])
            if st.button("บันทึกการเปลี่ยนแปลง"):
                with db_core() as c: c.execute("UPDATE Users SET name=? WHERE acc_id=?", (new_name, u[0]))
                st.success("เปลี่ยนชื่อเรียบร้อย"); time.sleep(0.5); st.rerun()

        # --- 👑 ADMIN POWER (No LINE Notify) ---
        if u[6] == 'Admin':
            st.divider()
            st.subheader("👑 ศูนย์ควบคุมแอดมิน")
            adm_opt = st.selectbox("เลือกฟังก์ชันจัดการ", [
                "1. สร้างบัญชีใหม่ (สุ่มเลข)", 
                "2. อายัด/ปลดอายัดบัญชี", 
                "3. ข้อมูลผู้ใช้ทั้งหมด", 
                "4. ข้อมูลธุรกรรมทั้งหมด", 
                "5. เปลี่ยนเลขบัญชี (Override)", 
                "6. เสกเงิน (Injections)", 
                "7. มอบอำนาจ Admin"
            ])

            if adm_opt == "1. สร้างบัญชีใหม่ (สุ่มเลข)":
                with st.form("admin_reg"):
                    new_u = st.text_input("Username")
                    new_p = st.text_input("Password")
                    new_n = st.text_input("ชื่อจริง")
                    if st.form_submit_button("สร้างบัญชี"):
                        new_acc = str(random.randint(1000000000, 9999999999))
                        with db_core() as c: c.execute("INSERT INTO Users VALUES (?,?,?,?,?,?,?,?)", (new_acc, new_u, new_n, new_p, 0.0, 'Active', 'User', datetime.now().strftime("%d/%m/%Y %H:%M")))
                        st.success(f"สร้างบัญชีใหม่เลขที่ {new_acc} สำเร็จ")

            elif adm_opt == "2. อายัด/ปลดอายัดบัญชี":
                target_f = st.text_input("ใส่เลขบัญชี")
                c_f1, c_f2 = st.columns(2)
                if c_f1.button("🔴 อายัด (Freeze)"):
                    with db_core() as c: c.execute("UPDATE Users SET status='Banned' WHERE acc_id=?", (target_f,))
                    st.warning("บัญชีถูกอายัดแล้ว")
                if c_f2.button("🟢 ปลด (Active)"):
                    with db_core() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (target_f,))
                    st.success("บัญชีกลับมาใช้งานปกติ")

            elif adm_opt == "3. ข้อมูลผู้ใช้ทั้งหมด":
                with db_core() as c:
                    all_u = pd.read_sql("SELECT acc_id, name, username, password, role, status FROM Users", c.connection)
                st.dataframe(all_u, use_container_width=True)

            elif adm_opt == "4. ตรวจสอบธุรกรรมทั้งหมด":
                with db_core() as c:
                    all_tx = pd.read_sql("SELECT * FROM Transactions", c.connection)
                st.dataframe(all_tx, use_container_width=True)

            elif adm_opt == "5. เปลี่ยนเลขบัญชี (Override)":
                old_acc = st.text_input("เลขเดิม")
                new_acc_id = st.text_input("เลขใหม่")
                if st.button("ยืนยันเปลี่ยนเลขบัญชี"):
                    if old_acc == "2222222222": st.error("ไม่สามารถเปลี่ยนเลขบัญชีของเจ้าของได้")
                    else:
                        with db_core() as c: c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (new_acc_id, old_acc))
                        st.success("แก้ไขเลขบัญชีสำเร็จ")

            elif adm_opt == "6. เสกเงิน (Injections)":
                target_s = st.text_input("เลขบัญชีที่ต้องการรับเงิน")
                amt_s = st.number_input("ยอดเงินเสก", min_value=0.01)
                if st.button("✨ EXECUTE"):
                    with db_core() as c: c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt_s, target_s))
                    st.success(f"เสกเงินสำเร็จ ฿{amt_s:,.2f}")

            elif adm_opt == "7. มอบอำนาจ Admin":
                target_a = st.text_input("เลขบัญชีที่ต้องการมอบสิทธิ์")
                if st.button("Grant Admin Rights"):
                    with db_core() as c: c.execute("UPDATE Users SET role='Admin' WHERE acc_id=?", (target_a,))
                    st.success("มอบสิทธิ์แอดมินเรียบร้อย")

        st.divider()
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.page = "login"; st.rerun()

    # --- 📱 BOTTOM NAVIGATION BAR ---
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("🏠", key="n1"): st.session_state.sub_page = "หน้าหลัก"; st.rerun()
        st.markdown('<span class="nav-label">หน้าหลัก</span>', unsafe_allow_html=True)
    with b2:
        if st.button("📥", key="n2"): st.session_state.sub_page = "รับเงิน"; st.rerun()
        st.markdown('<span class="nav-label">รับเงิน</span>', unsafe_allow_html=True)
    with b3:
        if st.button("💸", key="n3"): st.session_state.sub_page = "โอนเงิน"; st.rerun()
        st.markdown('<span class="nav-label">โอนเงิน</span>', unsafe_allow_html=True)
    with b4:
        if st.button("👤", key="n4"): st.session_state.sub_page = "บัญชี"; st.rerun()
        st.markdown('<span class="nav-label">บัญชี</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
