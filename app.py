import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random

# --- CONFIG & THEME ---
st.set_page_config(page_title="Borworn Bank", page_icon="🏦", layout="centered")

# --- DATABASE ---
conn = sqlite3.connect('borworn_bank_v4.db', check_same_thread=False)
c = conn.cursor()

# --- CUSTOM CSS (THE "REAL BANK" LOOK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; }
    
    .stApp { background: linear-gradient(180deg, #003399 0%, #001a4d 30%, #f0f2f5 30.1%); }
    
    /* Bank Card Style */
    .bank-card {
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    /* Transaction List */
    .trans-item {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* Bottom Nav Bar Fix */
    .nav-fix { position: fixed; bottom: 0; left: 0; width: 100%; z-index: 99; }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.hide_money = True

# ---------------------------------------------------------
# 📱 NAVIGATION (BOTTOM BAR)
# ---------------------------------------------------------
if st.session_state.logged_in:
    selected = option_menu(
        menu_title=None,
        options=["หน้าหลัก", "โอนเงิน", "ประวัติ", "โปรไฟล์"],
        icons=["house-fill", "arrow-repeat", "list-check", "person-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#ffffff", "border-top": "1px solid #eee"},
            "nav-link": {"font-size": "12px", "text-align": "center", "margin":"0px", "--hover-color": "#f1f5f9"},
            "nav-link-selected": {"background-color": "transparent", "color": "#003399", "font-weight": "bold"},
        }
    )
else:
    selected = "Login"

# ---------------------------------------------------------
# 🏠 APP LOGIC
# ---------------------------------------------------------

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white; padding-top:50px;'>BORWORN BANK</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:white; padding:30px; border-radius:25px; box-shadow:0 10px 25px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        mode = st.tabs(["👤 รหัสผ่าน", "🔢 PIN"])
        with mode[0]:
            u = st.text_input("ชื่อผู้ใช้งาน", placeholder="Username")
            p = st.text_input("รหัสผ่าน", type="password", placeholder="Password")
            if st.button("เข้าสู่ระบบ", use_container_width=True):
                data = pd.read_sql(f"SELECT * FROM Users WHERE username='{u}' AND password='{p}'", conn)
                if not data.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_id = data.iloc[0]['acc_id']
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")
        with mode[1]:
            pin = st.text_input("ใส่ PIN 6 หลัก", type="password", max_chars=6)
            if len(pin) == 6:
                data = pd.read_sql(f"SELECT * FROM Users WHERE pin='{pin}'", conn)
                if not data.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_id = data.iloc[0]['acc_id']
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Get Current User Data
    user = pd.read_sql(f"SELECT * FROM Users WHERE acc_id='{st.session_state.user_id}'", conn).iloc[0]

    if selected == "หน้าหลัก":
        st.markdown("<br>", unsafe_allow_html=True)
        # Digital Card
        money_display = f"{user['balance']:,.2f}" if not st.session_state.hide_money else "• • • • • •"
        eye_icon = "👁️" if st.session_state.hide_money else "🕶️"
        
        st.markdown(f"""
        <div class="bank-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <small>ยอดเงินในบัญชี (ออมทรัพย์)</small>
                <span>{user['acc_id']}</span>
            </div>
            <div style="display:flex; align-items:center; gap:15px; margin: 15px 0;">
                <h1 style="margin:0; color:white;">฿ {money_display}</h1>
            </div>
            <small>ชื่อบัญชี: {user['name']}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"{eye_icon} แสดง/ซ่อนยอดเงิน"):
            st.session_state.hide_money = not st.session_state.hide_money
            st.rerun()

        st.info("📲 สแกน QR เพื่อรับเงิน")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['acc_id']}", width=180)

    elif selected == "โอนเงิน":
        st.markdown("<h3 style='color:white;'>โอนเงินไปยังบัญชีอื่น</h3><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div style="background:white; padding:20px; border-radius:20px;">', unsafe_allow_html=True)
            target = st.text_input("เลขที่บัญชีผู้รับ")
            amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
            note = st.text_input("บันทึกช่วยจำ")
            if st.button("ตรวจสอบข้อมูล", type="primary", use_container_width=True):
                recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
                if not recv: st.error("ไม่พบบัญชีปลายทาง")
                elif target == user['acc_id']: st.warning("โอนให้ตัวเองไม่ได้")
                elif user['balance'] < amt: st.error("ยอดเงินไม่พอ")
                else:
                    # Execute Transfer
                    ref = f"BORN{random.randint(100000, 999999)}"
                    c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id = ?", (amt, user['acc_id']))
                    c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id = ?", (amt, target))
                    c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?)", (user['acc_id'], target, amt, datetime.now().strftime("%d/%m/%y %H:%M"), note if note else "โอนเงิน"))
                    conn.commit()
                    st.success("โอนเงินสำเร็จ!")
                    st.balloons()
                    # Digital Slip
                    st.markdown(f"""
                    <div style="background:white; border:1px solid #ddd; padding:20px; border-radius:15px; text-align:center; color:#333;">
                        <h2 style="color:#003399;">โอนเงินสำเร็จ</h2>
                        <p>{datetime.now().strftime('%d %b %Y - %H:%M')}</p>
                        <hr>
                        <div style="text-align:left;">
                            <p><b>จาก:</b> {user['name']}</p>
                            <p><b>ถึง:</b> {recv[0]}</p>
                            <p><b>จำนวน:</b> ฿{amt:,.2f}</p>
                        </div>
                        <p style="font-size:10px; color:gray;">Ref: {ref}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif selected == "ประวัติ":
        st.subheader("ประวัติรายการ")
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{user['acc_id']}' OR receiver='{user['acc_id']}'", conn)
        for _, row in df.sort_index(ascending=False).iterrows():
            is_out = row['sender'] == user['acc_id']
            color = "#ff4d4d" if is_out else "#2eb82e"
            sign = "-" if is_out else "+"
            st.markdown(f"""
            <div class="trans-item">
                <div>
                    <b>{row['type']}</b><br>
                    <small style="color:gray;">{row['date']}</small>
                </div>
                <div style="text-align:right; color:{color}; font-weight:bold;">
                    {sign} ฿{row['amount']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif selected == "โปรไฟล์":
        st.subheader("ตั้งค่าบัญชี")
        with st.expander("👤 ข้อมูลส่วนตัว"):
            new_n = st.text_input("ชื่อ-นามสกุล", value=user['name'])
            if st.button("บันทึกชื่อ"):
                c.execute("UPDATE Users SET name = ? WHERE acc_id = ?", (new_n, user['acc_id']))
                conn.commit(); st.rerun()
        
        with st.expander("🔢 ตั้งค่า PIN / รหัสผ่าน"):
            st.text_input("รหัสผ่านเดิม", type="password")
            st.text_input("รหัสผ่านใหม่", type="password")
            st.text_input("PIN 6 หลักใหม่", type="password", max_chars=6)
            st.button("ยืนยันการเปลี่ยน")

        # --- เมนู ADMIN ล่องหน (รหัส Kub1) ---
        st.divider()
        adm = st.text_input("Staff Code", type="password")
        if adm == "Kub1":
            st.warning("โหมดผู้ดูแลระบบ")
            with st.form("add"):
                acc = st.text_input("เลขบัญชีใหม่")
                name = st.text_input("ชื่อ")
                u_n = st.text_input("Username")
                p_w = st.text_input("Password")
                if st.form_submit_button("สร้างบัญชี"):
                    c.execute("INSERT INTO Users (acc_id, name, username, password, balance) VALUES (?,?,?,?,500)")
                    conn.commit(); st.success("เพิ่มแล้ว!")

        if st.button("ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False; st.rerun()
