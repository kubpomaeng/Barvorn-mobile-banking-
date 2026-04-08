import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu

# --- CONFIG ---
st.set_page_config(page_title="Borworn Royal Bank", page_icon="🏛️", layout="wide")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_world_class_v1.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    # ตารางผู้ใช้ (เพิ่มสถานะ และ ข้อมูลเชิงลึก)
    c.execute('''CREATE TABLE IF NOT EXISTS Users 
                 (acc_id TEXT PRIMARY KEY, username TEXT, name TEXT, password TEXT, 
                  balance REAL, pin TEXT, status TEXT DEFAULT 'Active', 
                  created_at TEXT, acc_type TEXT DEFAULT 'Platinum')''')
    # ตารางธุรกรรม (เพิ่มรหัสอ้างอิงและบันทึกช่วยจำ)
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                 (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                  type TEXT, ref_no TEXT, memo TEXT)''')
    conn.commit()

init_db()

# --- CSS: HIGH-END BANKING UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    
    /* Bank Card Luxury */
    .bank-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white; padding: 35px; border-radius: 28px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(234, 179, 8, 0.4);
        margin-bottom: 20px; position: relative; overflow: hidden;
    }
    .bank-card::after {
        content: "VIP"; position: absolute; top: -10px; right: -10px;
        font-size: 80px; color: rgba(255,255,255,0.03); font-weight: bold;
    }
    
    /* Admin Dashboard */
    .admin-stat-card {
        background: white; padding: 20px; border-radius: 15px;
        border-bottom: 4px solid #eab308; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* PIN Pad */
    .pin-btn button {
        border-radius: 50% !important; width: 80px !important; height: 80px !important;
        font-size: 26px !important; background: white !important; color: #1e1b4b !important;
        border: 1px solid #e2e8f0 !important; margin: 10px auto !important; display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_page" not in st.session_state: st.session_state.auth_page = "gateway"
if "user_acc" not in st.session_state: st.session_state.user_acc = None
if "is_staff" not in st.session_state: st.session_state.is_staff = False

# ---------------------------------------------------------
# 🛡️ GATEWAY: CLIENT & STAFF LOGIN
# ---------------------------------------------------------
if st.session_state.auth_page == "gateway":
    st.markdown("<h1 style='text-align:center; color:#0f172a; margin-top:50px;'>🏛️ BORWORN ROYAL BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; letter-spacing:5px; margin-bottom:50px;'>THE ULTIMATE PRIVATE BANKING</p>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.markdown("### 🔑 Client Secure Access")
        with st.form("client_login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Authorized Sign In", use_container_width=True, type="primary"):
                user = c.execute("SELECT acc_id, pin, status FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if user:
                    if user[2] == 'Suspended': st.error("บัญชีถูกระงับ (Suspended) กรุณาติดต่อธนาคาร")
                    else:
                        st.session_state.user_acc = user[0]
                        st.session_state.auth_page = "pin_verify" if user[1] else "setup_pin"
                        st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

    with col_r:
        st.markdown("### 👨‍💼 Staff Terminal")
        with st.form("staff_login"):
            s_key = st.text_input("Staff Access Key", type="password")
            if st.form_submit_button("Enter Management System", use_container_width=True):
                if s_key == "Kub1":
                    st.session_state.is_staff = True
                    st.session_state.auth_page = "admin_dashboard"
                    st.rerun()
                else: st.error("Access Denied")

# ---------------------------------------------------------
# 🔢 PIN VERIFICATION
# ---------------------------------------------------------
elif st.session_state.auth_page == "pin_verify":
    if "pin_in" not in st.session_state: st.session_state.pin_in = ""
    u_info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    st.markdown(f"<h2 style='text-align:center;'>Welcome Back</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:20px; color:#eab308;'>{u_info[0]}</p>", unsafe_allow_html=True)
    
    dots = " ".join(["●" if i < len(st.session_state.pin_in) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#0f172a; letter-spacing:10px;'>{dots}</h1>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    keys = ['1','2','3','4','5','6','7','8','9','Clear','0','Delete']
    for i, k in enumerate(keys):
        with [c1, c2, c3][i % 3]:
            st.markdown('<div class="pin-btn">', unsafe_allow_html=True)
            if st.button(k, key=f"k_{k}"):
                if k == 'Delete': st.session_state.pin_in = st.session_state.pin_in[:-1]
                elif k == 'Clear': st.session_state.pin_in = ""
                elif len(st.session_state.pin_in) < 6: st.session_state.pin_in += k
                
                if len(st.session_state.pin_in) == 6:
                    if st.session_state.pin_in == u_info[1]:
                        st.session_state.auth_page = "client_home"
                        st.rerun()
                    else:
                        st.error("PIN ไม่ถูกต้อง")
                        st.session_state.pin_in = ""
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🏠 CLIENT DASHBOARD
# ---------------------------------------------------------
elif st.session_state.auth_page == "client_home":
    u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    m = option_menu(None, ["หน้าหลัก", "โอนเงิน/สแกน", "ประวัติธุรกรรม", "บริการ"], 
        icons=['house-fill', 'qr-code-scan', 'list-ul', 'grid-fill'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#0f172a"}})

    if m == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:30px;">
                <span style="font-size:18px; color:#eab308;">Platinum Account</span>
                <img src="https://img.icons8.com/color/48/visa.png" width="40">
            </div>
            <small style="opacity:0.7;">ยอดเงินที่สามารถใช้ได้ (Balance)</small>
            <h1 style="color:white; font-size:45px; margin:10px 0;">฿ {u[4]:,.2f}</h1>
            <div style="margin-top:40px; border-top:1px solid rgba(255,255,255,0.1); padding-top:20px; display:flex; justify-content:space-between;">
                <div>
                    <small style="display:block; opacity:0.6;">ชื่อบัญชี</small>
                    <span style="font-size:18px;">{u[2]}</span>
                </div>
                <div style="text-align:right;">
                    <small style="display:block; opacity:0.6;">เลขที่บัญชี</small>
                    <span style="font-family:monospace; font-size:18px;">{u[0][:3]}-{u[0][3:6]}-{u[0][6:]}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📲 My QR Code")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u[0]}&color=0f172a", width=220)
        if st.button("ออกจากระบบ"): 
            st.session_state.auth_page = "gateway"; st.rerun()

    elif m == "โอนเงิน/สแกน":
        st.subheader("📤 ส่งเงินและสแกนจ่าย")
        scan_mode = st.toggle("เปิดกล้องจำลอง (Scan Mode)")
        
        if scan_mode:
            st.info("💡 ระบบกำลังจำลองการสแกนคิวอาร์โค้ด... กรุณากรอกเลขบัญชีปลายทางที่ตรวจพบจากภาพ")
            target = st.text_input("เลขบัญชีที่สแกนพบ")
        else:
            target = st.text_input("ระบุเลขบัญชีปลายทาง (10 หลัก)")
            
        amount = st.number_input("จำนวนเงินที่ต้องการโอน", min_value=1.0)
        note = st.text_input("บันทึกช่วยจำ")
        
        if st.button("ยืนยันการทำรายการ", type="primary", use_container_width=True):
            recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
            if recv and u[4] >= amount and target != u[0]:
                ref = f"TRX{random.randint(10000000,99999999)}"
                c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amount, u[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amount, target))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", (u[0], target, amount, datetime.now().strftime("%d/%m/%y %H:%M"), "Transfer", ref, note))
                conn.commit(); st.success(f"โอนสำเร็จให้ {recv[0]}!"); st.balloons()
            else: st.error("รายการไม่สำเร็จ: ยอดเงินไม่พอหรือเลขบัญชีไม่ถูกต้อง")

    elif m == "ประวัติธุรกรรม":
        df = pd.read_sql(f"SELECT date as 'วันที่', type as 'ประเภท', receiver_id as 'ผู้รับ', amount as 'จำนวน', ref_no as 'รหัสอ้างอิง' FROM Transactions WHERE sender_id='{u[0]}' OR receiver_id='{u[0]}' ORDER BY date DESC", conn)
        st.table(df)

# ---------------------------------------------------------
# 👨‍💼 STAFF MANAGEMENT TERMINAL (แบบ 1,000%)
# ---------------------------------------------------------
elif st.session_state.auth_page == "admin_dashboard":
    st.markdown("<h2 style='color:#0f172a;'>👨‍💼 STAFF MANAGEMENT CONSOLE</h2>", unsafe_allow_html=True)
    
    # --- STATISTICS ---
    st.markdown("### 📊 ธนาคารในภาพรวม (Global Stats)")
    total_users = c.execute("SELECT count(*) FROM Users").fetchone()[0]
    total_money = c.execute("SELECT sum(balance) FROM Users").fetchone()[0] or 0
    total_tx = c.execute("SELECT count(*) FROM Transactions").fetchone()[0]
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='admin-stat-card'><small>ลูกค้าทั้งหมด</small><h3>{total_users} บัญชี</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='admin-stat-card'><small>สินทรัพย์รวมในระบบ</small><h3>฿ {total_money:,.2f}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='admin-stat-card'><small>ธุรกรรมที่เกิดขึ้น</small><h3>{total_tx} รายการ</h3></div>", unsafe_allow_html=True)
    
    adm_menu = option_menu(None, ["เปิดบัญชีใหม่", "จัดการลูกค้า", "ประวัติธุรกรรมรวม", "ตั้งค่าระบบ"], 
        icons=['person-plus', 'people-fill', 'file-text', 'gear'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#eab308", "color": "black"}})

    if adm_menu == "เปิดบัญชีใหม่":
        with st.form("new_acc"):
            st.subheader("📝 ฟอร์มลงทะเบียนลูกค้าใหม่")
            new_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
            st.markdown(f"**ระบบสร้างเลขบัญชีให้อัตโนมัติ:** `{new_id}`")
            
            col1, col2 = st.columns(2)
            n_usr = col1.text_input("ตั้ง Username")
            n_name = col2.text_input("ชื่อ-นามสกุลลูกค้า")
            n_pwd = col1.text_input("รหัสผ่านเริ่มต้น (Password)")
            n_bal = col2.number_input("ยอดฝากเริ่มต้น (THB)", value=1000.0)
            n_type = st.selectbox("ระดับบัญชี", ["Platinum", "Gold", "Infinite Wealth"])
            
            if st.form_submit_button("ยืนยันการเปิดบัญชี", use_container_width=True):
                c.execute("INSERT INTO Users (acc_id, username, name, password, balance, created_at, acc_type) VALUES (?,?,?,?,?,?,?)",
                          (new_id, n_usr, n_name, n_pwd, n_bal, datetime.now().strftime("%d/%m/%Y"), n_type))
                conn.commit(); st.success(f"เปิดบัญชีสำเร็จ! ยินดีต้อนรับคุณ {n_name}")

    elif adm_menu == "จัดการลูกค้า":
        st.subheader("👥 รายชื่อลูกค้าทั้งหมด")
        all_u = pd.read_sql("SELECT acc_id, name, username, balance, status, acc_type FROM Users", conn)
        st.dataframe(all_u, use_container_width=True)
        
        st.divider()
        st.subheader("🛠️ เครื่องมือจัดการรายบุคคล (Advanced Control)")
        target_id = st.text_input("กรอกเลขบัญชีที่ต้องการจัดการ")
        if target_id:
            user_data = c.execute("SELECT name, balance, status FROM Users WHERE acc_id=?", (target_id,)).fetchone()
            if user_data:
                st.write(f"**กำลังจัดการบัญชีคุณ:** {user_data[0]} | **ยอดเงิน:** ฿{user_data[1]:,.2f} | **สถานะ:** {user_data[2]}")
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("⛔ อายัดบัญชี (Suspend)"):
                    c.execute("UPDATE Users SET status='Suspended' WHERE acc_id=?", (target_id,))
                    conn.commit(); st.warning("อายัดบัญชีแล้ว")
                if col_b.button("✅ ปลดล็อกบัญชี"):
                    c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (target_id,))
                    conn.commit(); st.success("ปลดล็อกแล้ว")
                if col_c.button("🗑️ ลบถาวร"):
                    c.execute("DELETE FROM Users WHERE acc_id=?", (target_id,))
                    conn.commit(); st.error("ลบบัญชีแล้ว"); st.rerun()
                
                st.markdown("---")
                st.write("💰 **ปรับเปลี่ยนยอดเงินโดยตรง (Direct Credit/Debit)**")
                adj_amt = st.number_input("จำนวนเงินที่ต้องการปรับ (+ หรือ -)")
                if st.button("ยืนยันการปรับยอด"):
                    c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (adj_amt, target_id))
                    conn.commit(); st.success("ดำเนินการสำเร็จ")
            else: st.warning("ไม่พบเลขบัญชีนี้")

    elif adm_menu == "ประวัติธุรกรรมรวม":
        st.subheader("📑 ธุรกรรมทั้งหมดในระบบ")
        all_tx = pd.read_sql("SELECT * FROM Transactions ORDER BY date DESC", conn)
        st.dataframe(all_tx, use_container_width=True)

    elif adm_menu == "ตั้งค่าระบบ":
        if st.button("🔥 ล้างข้อมูลทั้งธนาคาร (Reset All)"):
            c.execute("DELETE FROM Users"); c.execute("DELETE FROM Transactions")
            conn.commit(); st.success("ข้อมูลทั้งหมดถูกลบแล้ว"); st.rerun()
        if st.button("ออกจากโหมดเจ้าหน้าที่"):
            st.session_state.is_staff = False; st.session_state.auth_page = "gateway"; st.rerun()

# --- SETUP PIN FIRST TIME ---
elif st.session_state.auth_page == "setup_pin":
    st.subheader("🛡️ ยินดีต้อนรับสมาชิกใหม่")
    st.write("กรุณาตั้งรหัส PIN 6 หลักเพื่อความปลอดภัยสูงสุดในการใช้งาน")
    p1 = st.text_input("ตั้งรหัส PIN", type="password", max_chars=6)
    p2 = st.text_input("ยืนยันรหัส PINอีกครั้ง", type="password", max_chars=6)
    if st.button("บันทึกรหัส"):
        if len(p1) == 6 and p1 == p2 and p1.isdigit():
            c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.user_acc))
            conn.commit(); st.session_state.auth_page = "client_home"; st.rerun()
        else: st.error("รหัสต้องเป็นตัวเลข 6 หลักและตรงกัน")
