import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="ธนาคารบวรพาณิชย์", page_icon="🏦", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #6c5ce7; color: white; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. การเชื่อมต่อที่ยืดหยุ่น (Robust Connection) ---
def get_data():
    try:
        # ใช้ TTL=0 เพื่อให้อัปเดตข้อมูลสดใหม่เสมอ
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # ดึงข้อมูล Users
        df_users = conn.read(worksheet="Users", ttl=0)
        # ลบเว้นวรรคที่ชื่อคอลัมน์ และทำให้เป็นตัวเล็กทั้งหมด (ป้องกันการพิมพ์ผิด)
        df_users.columns = df_users.columns.str.strip().str.lower()
        
        # ดึงข้อมูล Transactions
        df_trans = conn.read(worksheet="Transactions", ttl=0)
        df_trans.columns = df_trans.columns.str.strip().str.lower()
        
        return conn, df_users, df_trans
    except Exception as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets ได้: {e}")
        st.info("💡 ตรวจสอบ: 1. ลิงก์ใน Secrets 2. ชื่อแผ่นงานต้องเป็น 'Users' และ 'Transactions'")
        return None, None, None

conn, df_users, df_trans = get_data()

# --- 2. ระบบ LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

if not st.session_state.logged_in:
    st.title("🏦 ธนาคารบวรพาณิชย์")
    st.subheader("กรุณาเข้าสู่ระบบ")
    
    with st.form("login_form"):
        user_input = st.text_input("ชื่อผู้ใช้งาน (Username)")
        pass_input = st.text_input("รหัสผ่าน (Password)", type="password")
        submit = st.form_submit_button("เข้าสู่ระบบ")
        
        if submit:
            if df_users is not None:
                # ตรวจสอบ User (ใช้ .strip() ป้องกันเว้นวรรคในข้อมูล)
                match = df_users[(df_users['username'].astype(str).str.strip() == user_input.strip()) & 
                                 (df_users['password'].astype(str).str.strip() == pass_input.strip())]
                
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# --- 3. หน้าหลักหลัง LOGIN (ระบบโอนเงินจริง) ---
else:
    user = st.session_state.user_info
    st.title(f"สวัสดีคุณ {user['name']} 👋")
    
    # ดึงยอดเงินล่าสุดจาก DB (เผื่อมีการโอนเข้ามา)
    current_user_data = df_users[df_users['acc_id'] == user['acc_id']].iloc[0]
    balance = current_user_data['balance']

    # แสดงยอดเงินแบบสวยงาม
    st.metric(label="ยอดเงินคงเหลือปัจจุบัน", value=f"฿ {balance:,.2f}")
    
    st.divider()

    # เมนูการทำรายการ
    tab1, tab2 = st.tabs(["💸 โอนเงิน", "📜 ประวัติรายการ"])

    with tab1:
        st.write("### ทำรายการโอนเงิน")
        to_acc = st.text_input("เลขบัญชีผู้รับ")
        amount = st.number_input("จำนวนเงินที่ต้องการโอน", min_value=1.0, step=100.0)
        memo = st.text_input("บันทึกช่วยจำ (ไม่ระบุก็ได้)")

        if st.button("ยืนยันการโอนเงิน"):
            # 1. เช็คว่าเลขบัญชีมีจริงไหม
            receiver = df_users[df_users['acc_id'].astype(str).str.strip() == to_acc.strip()]
            
            if to_acc.strip() == str(user['acc_id']):
                st.warning("ไม่สามารถโอนเงินให้ตัวเองได้")
            elif receiver.empty:
                st.error("ไม่พบเลขบัญชีผู้รับในระบบ")
            elif balance < amount:
                st.error("ยอดเงินคงเหลือไม่เพียงพอ")
            else:
                # --- ขั้นตอนการโอนเงิน (Update DataFrame) ---
                # ลดเงินผู้โอน
                df_users.loc[df_users['acc_id'] == user['acc_id'], 'balance'] -= amount
                # เพิ่มเงินผู้รับ
                df_users.loc[df_users['acc_id'] == receiver.iloc[0]['acc_id'], 'balance'] += amount
                
                # เพิ่มประวัติ Transactions
                new_trans = pd.DataFrame([{
                    "from": user['acc_id'],
                    "to": to_acc,
                    "amount": amount,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "memo": memo
                }])
                df_updated_trans = pd.concat([df_trans, new_trans], ignore_index=True)

                # อัปเดตกลับไปยัง Google Sheets
                try:
                    conn.update(worksheet="Users", data=df_users)
                    conn.update(worksheet="Transactions", data=df_updated_trans)
                    st.success(f"โอนเงินสำเร็จ! จำนวน ฿{amount:,.2f} ไปยังบัญชี {to_acc}")
                    st.balloons()
                    st.rerun() # Refresh หน้าจอเพื่ออัปเดตยอดเงิน
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดขณะบันทึกข้อมูล: {e}")

    with tab2:
        st.write("### ประวัติการทำรายการของคุณ")
        my_trans = df_trans[(df_trans['from'].astype(str) == str(user['acc_id'])) | 
                           (df_trans['to'].astype(str) == str(user['acc_id']))]
        if not my_trans.empty:
            st.dataframe(my_trans.sort_index(ascending=False), use_container_width=True)
        else:
            st.write("ยังไม่มีประวัติการทำรายการ")

    if st.button("ออกจากระบบ", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
