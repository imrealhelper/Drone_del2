import streamlit as st
from datetime import datetime, timedelta
import base64
import os
import pandas as pd
import qrcode
from io import BytesIO
from navigation import make_sidebar
import pytz  # For timezone handling

# 페이지 설정
st.set_page_config(page_title="배송하고 싶어요", page_icon=":package:", layout="wide")

# Define the KST timezone globally
KST = pytz.timezone("Asia/Seoul")

def load_image_as_data_uri(image_path):
    """Converts an SVG image to a Data URI."""
    try:
        if not os.path.exists(image_path):
            st.error(f"이미지를 찾을 수 없습니다: {image_path}")
            return ""
        
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/svg+xml;base64,{encoded}"
    except Exception as e:
        st.error(f"이미지 로딩 중 오류 발생: {image_path}, 오류: {e}")
        return ""

def get_status_color(status):
    """Returns color based on order status."""
    status_colors = {
        "배달 완료": "#28a745",  # Green
        "배송중": "#ffc107",     # Yellow
        "취소됨": "#dc3545"      # Red
    }
    return status_colors.get(status, "#6c757d")  # Default Gray

def generate_qr_code(data):
    """Generates a QR code image from the given data and returns it as a Data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@st.dialog("배송 상세 정보", width="large")
def show_tracking_details(order):
    """Displays the detailed delivery information in a modal dialog."""
    st.markdown(f"### {order['company']} - {order['id']}")
    st.write(f"**운송장 번호:** {order['tracking_number']}")
    st.markdown("---")
    st.markdown("#### 배송 추적")
    tracking_df = pd.DataFrame(order['tracking_details'])
    st.table(tracking_df)
    
    # If delivery is completed, add QR code and map
    if order['status'] == "배달 완료":
        st.markdown("---")
        st.markdown("#### 배송 확인 QR 코드")
        qr_data = f"물류 스테이션 번호: {order['tracking_number']}"
        qr_data_uri = generate_qr_code(qr_data)
        st.markdown(f"<img src='{qr_data_uri}' width='200' alt='QR Code'>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 스테이션 위치 지도")
        
        # Station location coordinates (Latitude: 37.3840662, Longitude: 126.6574478)
        station_lat = 37.3840662
        station_lon = 126.6574478
        
        # Prepare data for the map
        map_data = pd.DataFrame({
            'lat': [station_lat],
            'lon': [station_lon],
            'label': ['스테이션 위치']
        })
        
        st.map(map_data)
        
        # Optionally, display the data in a table
        st.subheader("지도에 표시된 위치")
        st.table(map_data)

def get_current_kst():
    """Returns the current Korean Standard Time (KST)."""
    return datetime.now(KST)

def update_tracking_dates(tracking_details, base_date):
    """
    Updates the 'date' field in tracking_details to be base_date + original_time, localized to KST.

    :param tracking_details: List of dicts, each dict is a tracking detail
    :param base_date: datetime.date object, the base date to add
    :return: Updated tracking_details list
    """
    updated_details = []
    for detail in tracking_details:
        # Parse the original time
        try:
            original_datetime = datetime.strptime(detail['date'], "%Y-%m-%d %H:%M")
            original_time = original_datetime.time()
        except ValueError:
            st.error(f"잘못된 날짜 형식: {detail['date']}")
            original_time = datetime.now(KST).time()
        
        # Combine base_date + original_time
        new_datetime = datetime.combine(base_date, original_time)
        # Localize to KST
        new_datetime = KST.localize(new_datetime)
        # Format back to string
        detail['date'] = new_datetime.strftime("%Y-%m-%d %H:%M")
        updated_details.append(detail)
    return updated_details

def delivery_request_page():
    """Creates the '배송하고 싶어요' delivery request page."""
    # Custom CSS styling
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #f4f6f9;
    }
    .order-card {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .order-card:hover {
        transform: scale(1.02);
    }
    .status-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        color: white;
    }
    .tracking-btn {
        display: inline-block;
        background-color: #28a745 !important;
        color: white !important;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 20px !important;
        transition: all 0.3s ease !important;
        margin-top: 10px;
        cursor: pointer;
    }
    .tracking-btn:hover {
        background-color: #218838 !important;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="background-color: #28a745; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="margin-bottom: 10px;">배송하고 싶어요</h1>
        <p style="opacity: 0.8;">드론 배송을 요청하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    # Delivery Request Form
    with st.form(key='delivery_request_form'):
        st.markdown("### 배송 요청 정보")
        
        # Sender Information
        st.markdown("#### 송신인 정보")
        sender_name = st.text_input("이름", max_chars=50, help="송신인의 이름을 입력하세요.")
        sender_address = st.text_area("주소", height=100, help="송신인의 주소를 입력하세요.")
        sender_contact = st.text_input("연락처", max_chars=15, help="송신인의 연락처를 입력하세요.")
        
        st.markdown("---")
        
        # Recipient Information
        st.markdown("#### 수신인 정보")
        recipient_name = st.text_input("이름", max_chars=50, help="수신인의 이름을 입력하세요.")
        recipient_address = st.text_area("주소", height=100, help="수신인의 주소를 입력하세요.")
        recipient_contact = st.text_input("연락처", max_chars=15, help="수신인의 연락처를 입력하세요.")
        
        st.markdown("---")
        
        # Package Details
        st.markdown("#### 패키지 정보")
        package_description = st.text_input("내용물", max_chars=100, help="배송할 패키지의 내용물을 입력하세요.")
        package_weight = st.number_input("무게 (kg)", min_value=0.1, step=0.1, help="패키지의 무게를 kg 단위로 입력하세요.")
        
        st.markdown("---")
        
        # Pickup Details
        st.markdown("#### 픽업 정보")
        pickup_date = st.date_input("픽업 날짜", min_value=datetime.now().date(), help="픽업 날짜를 선택하세요.")
        pickup_time = st.time_input("픽업 시간", help="픽업 시간을 선택하세요.")
        
        # Submit Button
        submit_button = st.form_submit_button(label='배송 요청 제출', type='primary')
    
    if submit_button:
        # Validate inputs (basic validation)
        if not all([sender_name, sender_address, sender_contact, recipient_name, recipient_address, recipient_contact, package_description, package_weight]):
            st.error("모든 필드를 올바르게 입력해주세요.")
        else:
            # Here, you can implement logic to save the delivery request to a database or send an email.
            # For demonstration, we'll just display a success message.
            st.success("배송 요청이 성공적으로 제출되었습니다!")
            
            # Optionally, display the submitted information
            st.markdown("---")
            st.markdown("#### 제출된 배송 요청 정보")
            submitted_data = {
                "송신인 이름": sender_name,
                "송신인 주소": sender_address,
                "송신인 연락처": sender_contact,
                "수신인 이름": recipient_name,
                "수신인 주소": recipient_address,
                "수신인 연락처": recipient_contact,
                "내용물": package_description,
                "무게 (kg)": package_weight,
                "픽업 날짜": pickup_date.strftime("%Y-%m-%d"),
                "픽업 시간": pickup_time.strftime("%H:%M")
            }
            st.table(pd.DataFrame.from_dict(submitted_data, orient='index', columns=['정보']))
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; color: #6c757d;">
        © 2024 드론 배송 서비스 | 고객 지원: 1234-5678
    </div>
    """, unsafe_allow_html=True)


make_sidebar()

delivery_request_page()

