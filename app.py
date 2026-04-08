import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import time
import segno
from io import BytesIO

# --- CONFIGURATION ---
# เปลี่ยนชื่อที่แสดงบน Tab ของเบราว์เซอร์
st.set_page_config(page_title="ธนาคารบวรพาณิชย์ | Barvorn Commercial Bank", page_icon="🏦", layout="centered")
timezone = pytz.timezone('Asia/Bangkok')

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet):
    return conn.read(worksheet=sheet, ttl=0)

# --- UI DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.2em; font-weight: bold;}
    
    .bank-card {
        background: linear-gradient(135deg, #003366 0%, #00509d 100%);
        color: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0, 51, 102, 0.2); margin-bottom: 25px;
    }
    
    .feature-box {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .qr-box {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 2px dashed #003366;
    }
    </style>
    """, unsafe_allow_html=True)

if 'user_idx' not in st.session_state: st.session_state.user_idx = None
if 'page' not in st.session_state: st.session_state.page = "home"

df_users = get_data("Users")

# --- AUTH SYSTEM ---
if st.session_state.user_idx is None:
    st.markdown("<h1 style='text-align:center; color:#003366; font-size:2.2em;'>ธนาคารบวรพาณิชย์</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#555;'>Barvorn Commercial Bank</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div style="background:white; padding:20px; border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        u = st.text_input("ชื่อผู้ใช้งาน", key="login_u")
        p = st.text_input("รหัสผ่าน", type="password", key="login_p")
        if st.button("เข้าสู่ระบบอย่างปลอดภัย", key="login_btn"):
            user_match = df_users[df_users['username'] == u]
            if not user_match.empty and str(user_match.iloc[0]['password']) == p:
                st.session_state.user_idx = user_match.index[0]
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN APPLICATION ---
else:
    user = df_users.iloc[st.session_state.user_idx]
    
    # --- SIDEBAR MENU ---
    st.sidebar.title("BARVORN BANK")
    if st.sidebar.button("🏠 หน้าหลัก", use_container_width=True): st.session_state.page = "home"; st.rerun()
    if st.sidebar.button("💸 โอนเงิน / สแกน", use_container_width=True): st.session_state.page = "transfer"; st.rerun()
    if st.sidebar.button("📥 รับเงินด้วย QR", use_container_width=True): st.session_state.page = "my_qr"; st.rerun()
    if st.sidebar.button("📊 ประวัติธุรกรรม", use_container_width=True): st.session_state.page = "history"; st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
        st.session_state.user_idx = None
        st.rerun()

    # --- PAGE: HOME ---
    if st.session_state.page == "home":
        st.markdown(f"### ยินดีต้อนรับ, {user['name']}")
        st.markdown(f"""
        <div class="bank-card">
            <div style="font-size:0.8em; opacity:0.8;">ยอดเงินที่ใช้ได้ทั้งหมด (THB)</div>
            <div style="font-size:2.5em; font-weight:bold; margin:10px 0;">฿ {float(user['balance']):,.2f}</div>
            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                <div>เลขบัญชี: {user['acc_id']}</div>
                <div style="font-weight:bold; font-style:italic;">BARVORN COMMERCIAL BANK</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("เมนูแนะนำ")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 โอนเงิน / สแกน"): st.session_state.page = "transfer"; st.rerun()
        with c2:
            if st.button("📥 สร้าง QR รับเงิน"): st.session_state.page = "my_qr"; st.rerun()

    # --- PAGE: MY QR ---
    elif st.session_state.page == "my_qr":
        st.subheader("รับเงินผ่าน QR")
        amount_in = st.number_input("ระบุจำนวนเงิน (บาท) *ใส่ 0 หากไม่ระบุ", min_value=0.0, step=10.0)
        
        qr_data = f"BARVORN:{user['acc_id']}:{amount_in}"
        qr = segno.make(qr_data, error='h')
        out = BytesIO()
        qr.save(out, kind='png', scale=10, border=2, dark='#003366')
        
        st.markdown('<div class="qr-box">', unsafe_allow_html=True)
        st.image(out.getvalue(), width=250)
        st.markdown(f"**{user['name']}**<br>ธนาคารบวรพาณิชย์", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PAGE: TRANSFER ---
    elif st.session_state.page == "transfer":
        st.subheader("โอนเงิน")
        mode = st.radio("วิธีทำรายการ", ["ระบุเลขบัญชี", "จำลองการสแกน QR / สลิป"])
        
        target_id, amount = "", 0.0
        
        if mode == "ระบุเลขบัญชี":
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            target_id = st.text_input("เลขบัญชีผู้รับ")
            amount = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
            memo = st.text_input("บันทึกช่วยจำ")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            qr_scan = st.text_input("วางรหัส QR ที่นี่ (เช่น BARVORN:1001:500)")
            if qr_scan.startswith("BARVORN:"):
                p = qr_scan.split(":")
                target_id, amount = p[1], float(p[2])
                st.success(f"พบข้อมูล: บัญชี {target_id} ยอดเงิน {amount} บาท")
                if amount == 0: amount = st.number_input("ระบุจำนวนเงิน", min_value=1.0)
            memo = st.text_input("บันทึกช่วยจำ")
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("ยืนยันการโอนเงิน", use_container_width=True):
            target_data = df_users[df_users['acc_id'].astype(str) == target_id]
            if not target_data.empty and target_id != str(user['acc_id']):
                if user['balance'] >= amount and amount > 0:
                    with st.status("กำลังตรวจสอบรายการ...", expanded=True):
                        time.sleep(1)
                        df_users.at[st.session_state.user_idx, 'balance'] -= amount
                        df_users.at[target_data.index[0], 'balance'] += amount
                        df_tx = get_data("Transactions")
                        now = datetime.now(timezone).strftime("%d/%m/%Y %H:%M:%S")
                        new_tx = pd.DataFrame([{"from": user['acc_id'], "to": target_id, "amount": amount, "date": now, "memo": memo}])
                        conn.update(worksheet="Users", data=df_users)
                        conn.update(worksheet="Transactions", data=pd.concat([df_tx, new_tx], ignore_index=True))
                    st.balloons()
                    st.success("โอนเงินสำเร็จ!")
                    time.sleep(1.5); st.session_state.page = "home"; st.rerun()
                else: st.error("ยอดเงินไม่เพียงพอ")
            else: st.error("ข้อมูลไม่ถูกต้อง")

    # --- PAGE: HISTORY ---
    elif st.session_state.page == "history":
        st.subheader("ประวัติธุรกรรม")
        df_tx = get_data("Transactions")
        my_tx = df_tx[(df_tx['from'].astype(str) == str(user['acc_id'])) | (df_tx['to'].astype(str) == str(user['acc_id']))]
        for _, row in my_tx.iloc[::-1].iterrows():
            is_out = str(row['from']) == str(user['acc_id'])
            color = "#e74c3c" if is_out else "#2ecc71"
            st.markdown(f"""
            <div class="feature-box" style="border-left:5px solid {color}; padding:15px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <b>{'โอนให้' if is_out else 'รับจาก'} บัญชี {row['to'] if is_out else row['from']}</b><br>
                        <small style="color:gray;">{row['date']} | {row['memo']}</small>
                    </div>
                    <b style="color:{color}; font-size:1.1em;">{' - ' if is_out else ' + '} ฿{row['amount']:,.2f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
