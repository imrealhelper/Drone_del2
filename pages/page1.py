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
st.set_page_config(page_title="배송 현황", page_icon=":truck:", layout="wide")

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
        qr_data =order['qr_number']
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
        #st.subheader("지도에 표시된 위치")
        #st.table(map_data)

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

def user_page():
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
        background-color: #007bff !important;
        color: white !important;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 20px !important;
        transition: all 0.3s ease !important;
        margin-top: 10px;
        cursor: pointer;
    }
    .tracking-btn:hover {
        background-color: #0056b3 !important;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

    # Welcome message header
    st.markdown("""
    <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="margin-bottom: 10px;">안녕하세요, Induck님!</h1>
        <p style="opacity: 0.8;">현재 진행 중인 드론 배송 현황을 확인하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    # Add 2 days to the current KST date
    current_kst = get_current_kst()
    base_date = (current_kst + timedelta(days=2)).date()

    # Sample order data
    orders_data = [
        {
            "id": "ORD-001",
            "company": "Coupang",
            "logo": load_image_as_data_uri("assets/coupang.svg"),
            "status": "배송중",
            "estimated_delivery": (current_kst + timedelta(days=2)).strftime('%Y-%m-%d'),
            "items": ["나이키 양말"],
            "tracking_number": "1Z999AA10123456784",
            "qr_number":9,
            "tracking_details": update_tracking_dates([
                {"date": "2024-11-18 09:30", "location": "서울 물류센터", "status": "상품 접수"},
                {"date": "2024-03-17 13:45", "location": "인천 드론 배송", "status": "출고 준비"},
                {"date": "2024-03-17 14:01", "location": "인천 송도 제1 스테이션", "status": "배송 중"}
            ], base_date)
        },
        {
            "id": "ORD-002",
            "company": "당근마켓",
            "logo": load_image_as_data_uri("assets/dang.svg"),
            "status": "배달 완료",
            "estimated_delivery": (current_kst - timedelta(days=1)).strftime('%Y-%m-%d'),
            "items": ["F-35 피규어"],
            "tracking_number": "1Z999AA10123456783",
            "qr_number":9,
            "tracking_details": update_tracking_dates([
                {"date": "2024-03-14 11:20", "location": "용현동 판매자", "status": "상품 발송"},
                {"date": "2024-03-15 09:45", "location": "인천 드론 배송", "status": "배송 중"},
                {"date": "2024-03-16 14:30", "location": "인천 송도 제1 스테이션", "status": "배달 완료"}
            ], base_date)
        },
        {
            "id": "ORD-003",
            "company": "Coupang",
            "logo": load_image_as_data_uri("assets/coupang.svg"),
            "status": "취소됨",
            "estimated_delivery": current_kst.strftime('%Y-%m-%d'),
            "items": ["노트북 파우치"],
            "tracking_number": "1Z999AA10123456786",
            "qr_number":9,
            "tracking_details": update_tracking_dates([
                {"date": "2024-03-15 10:00", "location": "주문 취소", "status": "고객 요청 취소"}
            ], base_date)
        }
    ]

    # Display each order
    for order in orders_data:
        st.markdown("---")
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                if order["logo"]:
                    # Embed SVG image as HTML
                    st.markdown(f"<img src='{order['logo']}' width='100' alt='{order['company']} 로고'>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"### {order['company']} - {order['id']}")
                st.write(f"**상품:** {', '.join(order['items'])}")
                st.write(f"**물류 스테이션 번호:** {order['tracking_number']}")
                status_color = get_status_color(order['status'])
                st.markdown(f"<span class='status-badge' style='background-color: {status_color};'>{order['status']}</span>", unsafe_allow_html=True)
                if order['status'] in ["배송중", "배달 완료"]:
                    st.write(f"**예상 배송일:** {order['estimated_delivery']}")
                if order['status'] != "취소됨":
                    if st.button("상세 추적", key=f"tracking_btn_{order['id']}"):
                        show_tracking_details(order)

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; color: #6c757d;">
        © 2024 배송 추적 서비스 | 고객 지원: 1234-5678
    </div>
    """, unsafe_allow_html=True)

# Sidebar and page rendering
make_sidebar()
user_page()
