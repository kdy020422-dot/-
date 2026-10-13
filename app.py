import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os
from datetime import datetime

# 1. 앱 기본 설정
st.set_page_config(page_title="재무설계 관리자 대시보드", layout="wide")

# 데이터 파일 설정
CLIENTS_FILE = "clients.csv"
DATA_FILE = "finance_data.csv"

# 2. 데이터 관리 함수
def load_clients():
    if os.path.exists(CLIENTS_FILE):
        return pd.read_csv(CLIENTS_FILE)["고객명"].tolist()
    return []

def save_client(name):
    clients = load_clients()
    if name not in clients:
        clients.append(name)
        pd.DataFrame({"고객명": clients}).to_csv(CLIENTS_FILE, index=False)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # 고객명 컬럼이 추가되었습니다.
        return pd.DataFrame(columns=["고객명", "날짜", "유형", "카테고리", "금액", "내역"])

# 3. 화면 전환을 위한 세션 상태(Session State) 초기화
# 'selected_client'에 고객 이름이 담기면 대시보드를 띄우고, 비어있으면 명부를 띄웁니다.
if "selected_client" not in st.session_state:
    st.session_state.selected_client = None


# =========================================================
# 화면 A: 관리자 페이지 (고객 명부 리스트)
# =========================================================
if st.session_state.selected_client is None:
    st.title("👥 재무설계 고객 명부 관리 (Admin)")
    
    # 신규 고객 추가 폼
    with st.form("add_client_form"):
        new_client_name = st.text_input("새로운 고객의 이름을 입력하세요")
        submitted = st.form_submit_button("고객 추가하기")
        if submitted and new_client_name.strip():
            save_client(new_client_name.strip())
            st.success(f"'{new_client_name}' 고객님이 명부에 추가되었습니다!")
            st.rerun()
            
    st.divider()
    
    # 고객 리스트 출력
    st.subheader("📋 등록된 고객 리스트")
    clients = load_clients()
    
    if not clients:
        st.info("아직 등록된 고객이 없습니다. 위에서 고객을 먼저 추가해주세요.")
    else:
        st.write("아래에서 고객명을 클릭하면 해당 고객의 맞춤형 앱(대시보드)으로 이동합니다.")
        # 가로로 버튼을 배치하기 위해 화면을 컬럼으로 나눔 (한 줄에 4명씩)
        cols = st.columns(4)
        for i, client in enumerate(clients):
            with cols[i % 4]:
                # 버튼을 클릭하면 세션 상태에 고객 이름을 저장하고 새로고침
                if st.button(f"👤 {client} 고객님", key=client, use_container_width=True):
                    st.session_state.selected_client = client
                    st.rerun()


# =========================================================
# 화면 B: 개별 고객 앱 (대시보드)
# =========================================================
else:
    current_client = st.session_state.selected_client
    
    # 상단 헤더 및 뒤로가기 버튼 배치
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title(f"📊 {current_client} 고객님 맞춤형 재무 대시보드")
    with col2:
        if st.button("🔙 관리자 명부로 돌아가기", use_container_width=True):
            st.session_state.selected_client = None
            st.rerun()
            
    # 전체 데이터 중 현재 고객의 데이터만 필터링
    df = load_data()
    client_df = df[df["고객명"] == current_client]
    
    # 기존에 만들었던 3개의 탭 구성
    tab1, tab2, tab3 = st.tabs(["📝 가계부 및 자산 입력", "📊 실시간 대시보드", "📈 투자 포트폴리오"])

    # --- TAB 1: 데이터 입력 ---
    with tab1:
        st.header("현금흐름 및 자산 변동 입력")
        
        date = st.date_input("날짜", datetime.today())
        type_ = st.selectbox("유형", ["지출", "수입", "자산 업데이트(예금/적금)"])

        if type_ == "수입":
            categories = ["용돈 및 지원금", "근로 소득(급여/알바)", "현장 실습/인턴비", "금융 소득(이자/배당)", "투자 수익(매도금)", "장학금/학교 지원금", "정부 지원/장려금", "환불 및 모임 정산금", "부수입(중고거래 등)", "기타 수입"]
        elif type_ == "지출":
            categories = ["식비 및 외식비", "고정지출(구독/통신)", "교통비", "쇼핑/생필품", "취미/여가", "여행비용", "망실(출처불명)", "기타 지출"]
        else:
            categories = ["보통예금 잔액", "적금 납입액", "주식 투자금"]

        categories.append("📝 직접 입력 (새로 작성하기)")
        selected_category = st.selectbox("카테고리 선택", categories)

        if selected_category == "📝 직접 입력 (새로 작성하기)":
            category = st.text_input("원하시는 카테고리명을 직접 입력해주세요")
        else:
            category = selected_category

        amount = st.number_input("금액 (원)", min_value=0, step=1000)
        memo = st.text_input("상세 내역")
        
        if st.button("저장하기"):
            if selected_category == "📝 직접 입력 (새로 작성하기)" and category.strip() == "":
                st.warning("직접 입력할 카테고리명을 비워둘 수 없습니다!")
            else:
                # 데이터를 저장할 때 '고객명'을 함께 묶어서 저장합니다.
                new_data = pd.DataFrame([{"고객명": current_client, "날짜": date, "유형": type_, "카테고리": category, "금액": amount, "내역": memo}])
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"{current_client} 고객님의 데이터가 성공적으로 저장되었습니다!")
                st.rerun()
                
        st.subheader("입력된 데이터 히스토리")
        # 화면에는 현재 고객의 내역만 보여줍니다.
        st.dataframe(client_df.drop(columns=["고객명"], errors="ignore"))

    # --- TAB 2: 실시간 대시보드 ---
    with tab2:
        st.header("재무 건전성 모니터링")
        if not client_df.empty:
            total_income = client_df[client_df["유형"] == "수입"]["금액"].sum()
            total_expense = client_df[client_df["유형"] == "지출"]["금액"].sum()
            
            cash_flow_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("총 수입", f"{total_income:,.0f} 원")
            col2.metric("총 지출", f"{total_expense:,.0f} 원")
            
            alert_status = "🔴 위험 (초과)" if cash_flow_ratio > 50 else "🟢 안정"
            col3.metric("가계수지 지표 (목표 50% 이하)", f"{cash_flow_ratio:.1f} %", alert_status, delta_color="off")
            
            expense_df = client_df[client_df["유형"] == "지출"]
            if not expense_df.empty:
                fig = px.pie(expense_df, values="금액", names="카테고리", title="지출 비중 분석 (식비 방어 모니터링)")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("탭 1에서 데이터를 먼저 입력해주세요.")

    # --- TAB 3: 투자 포트폴리오 ---
    with tab3:
        st.header("미국 주식 포트폴리오 (자동 수익률 추적)")
        st.write("`yfinance` API를 통해 시장의 실시간 가격을 불러옵니다.")
        col1, col2 = st.columns(2)
        try:
            ivv_data = yf.Ticker("IVV").history(period="1d")
            if not ivv_data.empty:
                col1.metric(label="IVV (S&P 500) 현재가", value=f"${ivv_data['Close'].iloc[-1]:.2f}")
                
            jepi_data = yf.Ticker("JEPI").history(period="1d")
            if not jepi_data.empty:
                col2.metric(label="JEPI (커버드콜) 현재가", value=f"${jepi_data['Close'].iloc[-1]:.2f}")
        except Exception as e:
            st.error("주식 데이터를 불러오는데 실패했습니다. 인터넷 연결을 확인하세요.")
