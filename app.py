import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- CONFIG ---
st.set_page_config(page_title="ธนาคารบวรพาณิชย์", page_icon="🏦", layout="wide")

# --- DATABASE ---
conn = sqlite3.connect('borworn_bank_v4.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS Users 
             (acc_id TEXT PRIMARY KEY, name TEXT, username TEXT, password TEXT, balance REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
             (sender TEXT, receiver TEXT, amount REAL, date TEXT, type TEXT)''')
conn.commit()

# --- CSS จัดเต็มให้เหมือนแอปธนาคาร ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background-color: #0047ba; color: white; font-weight: bold; }
    .stTab { background-color: white; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=100)
    st.title("Borworn Bank")
    menu = st.radio("เมนูหลัก", ["🏠 หน้าแรก/Login", "🛠️ ระบบจัดการหลังบ้าน"])

# ---------------------------------------------------------
# 🛠️ โหมดช่องลับ (ADMIN PANEL) - รหัสลับ Kub1
# ---------------------------------------------------------
if menu == "🛠️ ระบบจัดการหลังบ้าน":
    st.title("🛠️ แผงควบคุมผู้ดูแล (ช่องลับ)")
    admin_pw = st.text_input("รหัสผ่านลับธนาคาร", type="password")
    
    if admin_pw == "Kub1":
        st.success("เข้าสู่ระบบพระเจ้าสำเร็จ")
        t1, t2 = st.tabs(["🆕 ออกบัญชีใหม่", "📊 จัดการสมาชิก/แก้ไขเงิน"])
        
        with t1:
            with st.form("add_user"):
                c1, c2 = st.columns(2)
                acc = c1.text_input("เลขบัญชี (ID)")
                name = c2.text_input("ชื่อลูกค้า")
                user = c1.text_input("Username")
                pw = c2.text_input("Password")
                bal = st.number_input("เงินฝากเริ่มต้น", value=1000.0)
                if st.form_submit_button("ยืนยันการออกบัญชี"):
                    try:
                        c.execute("INSERT INTO Users VALUES (?,?,?,?,?)", (acc, name, user, pw, bal))
                        conn.commit()
                        st.success(f"ออกบัญชีให้คุณ {name} สำเร็จ!")
                    except: st.error("เลขบัญชีซ้ำ!")

        with t2:
            df_users = pd.read_sql("SELECT * FROM Users", conn)
            st.dataframe(df_users, use_container_width=True)
            st.divider()
            target_acc = st.selectbox("เลือกบัญชีที่ต้องการแก้ไข", df_users['acc_id'])
            new_val = st.number_input("ปรับยอดเงินใหม่เป็น")
            if st.button("บันทึกการแก้ไขเงิน"):
                c.execute("UPDATE Users SET balance = ? WHERE acc_id = ?", (new_val, target_acc))
                conn.commit()
                st.success("แก้ไขยอดเงินสำเร็จ!")
                st.rerun()
    else:
        st.info("กรุณากรอกรหัสผ่านลับเพื่อจัดการฐานข้อมูล")

# ---------------------------------------------------------
# 🏠 โหมดธนาคาร (CUSTOMER MODE)
# ---------------------------------------------------------
else:
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.title("🏦 ธนาคารบวรพาณิชย์")
            st.write("เข้าสู่ระบบเพื่อทำธุรกรรม")
            u_in = st.text_input("ชื่อผู้ใช้")
            p_in = st.text_input("รหัสผ่าน", type="password")
            if st.button("Log In"):
                data = pd.read_sql(f"SELECT * FROM Users WHERE username='{u_in}' AND password='{p_in}'", conn)
                if not data.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = data.iloc[0].to_dict()
                    st.rerun()
                else: st.error("ไม่พบบัญชีนี้")
    else:
        # ดึงข้อมูลล่าสุด
        u = st.session_state.user
        res = c.execute("SELECT * FROM Users WHERE acc_id=?", (u['acc_id'],)).fetchone()
        balance = res[4]

        # หน้า Dashboard
        st.title(f"สวัสดี, คุณ {res[1]} 👋")
        col_bal, col_qr = st.columns([2, 1])
        
        with col_bal:
            st.metric("ยอดเงินในบัญชีปัจจุบัน", f"฿ {balance:,.2f}")
            # กราฟจำลองรายรับรายจ่าย
            df_hist = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{u['acc_id']}' OR receiver='{u['acc_id']}'", conn)
            if not df_hist.empty:
                fig = px.line(df_hist, x='date', y='amount', title="กราฟการเคลื่อนไหวของเงิน")
                st.plotly_chart(fig, use_container_width=True)

        with col_qr:
            st.info("My QR Code")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={u['acc_id']}", caption=f"ID: {u['acc_id']}")

        # แท็บธุรกรรม
        t_pay, t_history = st.tabs(["💸 โอนเงิน/ชำระเงิน", "📜 ประวัติการเดินบัญชี"])
        
        with t_pay:
            target = st.text_input("ระบุเลขบัญชีผู้รับ")
            amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
            if st.button("🚀 ยืนยันการโอนเงิน"):
                recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
                if not recv: st.error("ไม่พบเลขบัญชีผู้รับ")
                elif balance < amt: st.error("ยอดเงินไม่เพียงพอ")
                else:
                    # ทำรายการ
                    c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id = ?", (amt, u['acc_id']))
                    c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id = ?", (amt, target))
                    c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?)", 
                              (u['acc_id'], target, amt, datetime.now().strftime("%d/%m/%Y %H:%M"), "Transfer"))
                    conn.commit()
                    # สลิป
                    st.success("โอนเงินสำเร็จ!")
                    st.balloons()
                    with st.expander("📄 ดูสลิปการโอน"):
                        st.write(f"**ผู้ส่ง:** {res[1]}")
                        st.write(f"**ผู้รับ:** {recv[0]} (บัญชี {target})")
                        st.write(f"**จำนวนเงิน:** ฿{amt:,.2f}")
                        st.write(f"**เวลา:** {datetime.now().strftime('%H:%M:%S')}")
                    st.button("ทำรายการต่อ", on_click=st.rerun)

        with t_history:
            st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True)

        if st.sidebar.button("ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()
