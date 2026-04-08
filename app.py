import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random

# --- CONFIG ---
st.set_page_config(page_title="Borworn Bank", page_icon="🏦", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_bank_v4.db', check_same_thread=False)
c = conn.cursor()

def upgrade_db():
    try: c.execute("ALTER TABLE Users ADD COLUMN pin TEXT"); conn.commit()
    except: pass
    try: c.execute("ALTER TABLE Users ADD COLUMN branch TEXT DEFAULT 'สำนักงานใหญ่'"); conn.commit()
    except: pass
    c.execute("CREATE TABLE IF NOT EXISTS Transactions (sender TEXT, receiver TEXT, amount REAL, date TEXT, type TEXT)")
    conn.commit()

upgrade_db()

# --- CSS: THE "REAL APP" LOOK ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    
    /* Login & PIN Box */
    .auth-container { background: white; padding: 40px; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; }
    
    /* Digital Card */
    .bank-card {
        background: linear-gradient(135deg, #0047ba 0%, #002d72 100%);
        color: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 20px rgba(0,71,186,0.3); margin-bottom: 20px;
    }
    
    /* PIN Keypad Buttons */
    .stButton>button { border-radius: 50% !important; width: 70px !important; height: 70px !important; font-size: 24px !important; background: white !important; color: #333 !important; border: 1px solid #ddd !important; margin: 5px; }
    .stButton>button:hover { background: #f1f5f9 !important; border-color: #0047ba !important; }
    
    /* Bottom Bar Fix */
    div[data-testid="stVerticalBlock"] > div:has(div.nav-fix) { position: fixed; bottom: 0; left: 0; width: 100%; z-index: 100; background: white; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_state" not in st.session_state:
    st.session_state.auth_state = "logged_out" # logged_out, pin_lock, authenticated
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "input_pin" not in st.session_state:
    st.session_state.input_pin = ""

# ---------------------------------------------------------
# 🛡️ SECURITY FLOW (หน้า Login & PIN)
# ---------------------------------------------------------

# 1. หน้า Login (Username/Password) - ทำแค่ครั้งแรก
if st.session_state.auth_state == "logged_out":
    st.markdown("<h1 style='text-align:center; color:#0047ba;'>🏦 BORWORN BANK</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("เข้าสู่ระบบ")
        u = st.text_input("ชื่อผู้ใช้งาน", placeholder="Username")
        p = st.text_input("รหัสผ่าน", type="password", placeholder="Password")
        if st.button("ตกลง", use_container_width=True):
            data = pd.read_sql(f"SELECT * FROM Users WHERE username='{u}' AND password='{p}'", conn)
            if not data.empty:
                st.session_state.user_id = data.iloc[0]['acc_id']
                # ถ้ายังไม่ได้ตั้ง PIN ให้ไปตั้งก่อน ถ้าตั้งแล้วให้ไปหน้า PIN
                if not data.iloc[0]['pin']:
                    st.session_state.auth_state = "set_pin"
                else:
                    st.session_state.auth_state = "pin_lock"
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. หน้าใส่ PIN (Numeric Keypad แบบแอปจริง)
elif st.session_state.auth_state == "pin_lock":
    user = pd.read_sql(f"SELECT * FROM Users WHERE acc_id='{st.session_state.user_id}'", conn).iloc[0]
    st.markdown(f"<h3 style='text-align:center;'>สวัสดี, คุณ {user['name']}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>กรุณาใส่รหัส PIN เพื่อเข้าใช้งาน</p>", unsafe_allow_html=True)
    
    # แสดงจุดไข่ปลาตามจำนวนที่กด
    dots = " ".join(["●" if i < len(st.session_state.input_pin) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#0047ba;'>{dots}</h1>", unsafe_allow_html=True)
    
    # สร้างปุ่มตัวเลข 3x4
    cols = st.columns(3)
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "ล้าง", "0", "ลบ"]
    for i, key in enumerate(keys):
        if cols[i % 3].button(key, key=f"btn_{key}"):
            if key == "ล้าง": st.session_state.input_pin = ""
            elif key == "ลบ": st.session_state.input_pin = st.session_state.input_pin[:-1]
            elif len(st.session_state.input_pin) < 6: st.session_state.input_pin += key
            
            # ตรวจสอบ PIN เมื่อครบ 6 หลัก
            if len(st.session_state.input_pin) == 6:
                if st.session_state.input_pin == user['pin']:
                    st.session_state.auth_state = "authenticated"
                    st.session_state.input_pin = ""
                    st.rerun()
                else:
                    st.error("PIN ไม่ถูกต้อง")
                    st.session_state.input_pin = ""

# 3. หน้าตั้ง PIN (สำหรับลูกค้าใหม่)
elif st.session_state.auth_state == "set_pin":
    st.title("🔢 ตั้งรหัส PIN 6 หลัก")
    st.write("เพื่อความปลอดภัยในการใช้งานครั้งต่อไป")
    p1 = st.text_input("ระบุ PIN 6 หลัก", type="password", max_chars=6)
    p2 = st.text_input("ยืนยัน PIN อีกครั้ง", type="password", max_chars=6)
    if st.button("ยืนยันการตั้งค่า"):
        if len(p1) == 6 and p1 == p2 and p1.isdigit():
            c.execute("UPDATE Users SET pin = ? WHERE acc_id = ?", (p1, st.session_state.user_id))
            conn.commit()
            st.session_state.auth_state = "authenticated"
            st.rerun()
        else: st.error("กรุณาตรวจสอบความถูกต้อง (ตัวเลข 6 หลัก)")

# ---------------------------------------------------------
# 🏠 MAIN APP (หลังผ่านด่าน PIN)
# ---------------------------------------------------------
elif st.session_state.auth_state == "authenticated":
    user = pd.read_sql(f"SELECT * FROM Users WHERE acc_id='{st.session_state.user_id}'", conn).iloc[0]
    
    selected = option_menu(
        menu_title=None, options=["หน้าหลัก", "โอนเงิน", "ประวัติ", "โปรไฟล์"],
        icons=["house-fill", "arrow-repeat", "list-check", "person-fill"],
        orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#0047ba"}}
    )

    if selected == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <small>ยอดเงินในบัญชี (ออมทรัพย์)</small>
            <h1 style="color:white; margin:10px 0;">฿ {user['balance']:,.2f}</h1>
            <div style="display:flex; justify-content:space-between;">
                <span>{user['name']}</span>
                <span>{user['acc_id']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("📲 สแกน QR รับเงิน")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['acc_id']}")

    elif selected == "โอนเงิน":
        st.subheader("💸 โอนเงินไปยังบัญชีอื่น")
        target = st.text_input("เลขบัญชีผู้รับ")
        amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
        if st.button("ยืนยันการโอน", use_container_width=True, type="primary"):
            recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
            if not recv: st.error("ไม่พบบัญชีปลายทาง")
            elif user['balance'] < amt: st.error("เงินไม่พอ")
            else:
                c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id = ?", (amt, user['acc_id']))
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id = ?", (amt, target))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?)", (user['acc_id'], target, amt, datetime.now().strftime("%d/%m/%y %H:%M"), "โอนเงิน"))
                conn.commit()
                st.success(f"โอนให้คุณ {recv[0]} สำเร็จ!")
                st.balloons()

    elif selected == "ประวัติ":
        st.subheader("📜 รายการล่าสุด")
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{user['acc_id']}' OR receiver='{user['acc_id']}'", conn)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif selected == "โปรไฟล์":
        st.subheader("⚙️ ตั้งค่า")
        if st.button("ล็อกเอาต์ (ออกจากระบบ)"):
            st.session_state.auth_state = "logged_out"
            st.rerun()
        
        # --- ADMIN HIDDEN GATE ---
        st.divider()
        adm = st.text_input("Staff Code", type="password")
        if adm == "Kub1":
            st.info("Admin Mode Active")
            with st.form("add_user"):
                n_acc = st.text_input("เลขบัญชี")
                n_name = st.text_input("ชื่อ")
                n_usr = st.text_input("User")
                n_pwd = st.text_input("Pass")
                if st.form_submit_button("บันทึก"):
                    c.execute("INSERT INTO Users (acc_id, name, username, password, balance) VALUES (?,?,?,?,500)")
                    conn.commit(); st.success("เพิ่มสำเร็จ")
