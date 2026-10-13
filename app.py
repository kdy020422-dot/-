import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os
from datetime import datetime

# 1. 앱 기본 설정
st.set_page_config(page_title="재무 모니터링 앱", layout="wide")
st.title("💸 개인 재무 모니터링 및 자산 관리 대시보드")

DATA_FILE = "finance_data.csv"

# 2. 데이터 로드 함수 (CSV 파일 연동)
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["날짜", "유형", "카테고리", "금액", "내역"])

df = load_data()

# 3. 메인 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 가계부 및 자산 입력", "📊 실시간 대시보드", "📈 투자 포트폴리오"])

# --- TAB 1: 데이터 입력 ---
# --- TAB 1: 데이터 입력 ---
with tab1:
    st.header("현금흐름 및 자산 변동 입력")
    
    # 동적 UI(직접 입력 시 새 창 띄우기)를 위해 st.form 대신 일반 위젯으로 배치합니다.
    date = st.date_input("날짜", datetime.today())
    type_ = st.selectbox("유형", ["지출", "수입", "자산 업데이트(예금/적금)"])

    # 1. 유형에 따라 기본 카테고리 목록 설정
    if type_ == "수입":
        categories = [
            "용돈 및 지원금", "근로 소득(급여/알바)", "현장 실습/인턴비", 
            "금융 소득(이자/배당)", "투자 수익(매도금)", "장학금/학교 지원금", 
            "정부 지원/장려금", "환불 및 모임 정산금", "부수입(중고거래 등)", "기타 수입"
        ]
    elif type_ == "지출":
        categories = [
            "식비 및 외식비", "고정지출(구독/통신)", "교통비", "쇼핑/생필품", 
            "취미/여가", "여행비용", "망실(출처불명)", "기타 지출"
        ]
    else:
        categories = ["보통예금 잔액", "적금 납입액", "주식 투자금"]

    # 2. 리스트 맨 끝에 '직접 입력' 옵션을 추가
    categories.append("📝 직접 입력 (새로 작성하기)")

    # 3. 카테고리 선택 위젯
    selected_category = st.selectbox("카테고리 선택", categories)

    # 4. '직접 입력' 선택 시 텍스트 입력창 표시
    if selected_category == "📝 직접 입력 (새로 작성하기)":
        category = st.text_input("원하시는 카테고리명을 직접 입력해주세요")
    else:
        category = selected_category

    amount = st.number_input("금액 (원)", min_value=0, step=1000)
    memo = st.text_input("상세 내역")
    
    # st.form_submit_button 대신 일반 st.button 사용
    if st.button("저장하기"):
        # 직접 입력을 골랐는데 아무것도 안 적었을 경우 경고
        if selected_category == "📝 직접 입력 (새로 작성하기)" and category.strip() == "":
            st.warning("직접 입력할 카테고리명을 비워둘 수 없습니다!")
        else:
            new_data = pd.DataFrame([{"날짜": date, "유형": type_, "카테고리": category, "금액": amount, "내역": memo}])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success("성공적으로 저장되었습니다!")
            st.rerun() # 화면 새로고침
            
    st.subheader("입력된 데이터 히스토리")
    st.dataframe(df)

# --- TAB 2: 실시간 대시보드 ---
with tab2:
    st.header("재무 건전성 모니터링")
    if not df.empty:
        total_income = df[df["유형"] == "수입"]["금액"].sum()
        total_expense = df[df["유형"] == "지출"]["금액"].sum()
        
        # 가계수지 지표 계산 (지출/수입 비율)
        cash_flow_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 수입", f"{total_income:,.0f} 원")
        col2.metric("총 지출", f"{total_expense:,.0f} 원")
        
        # 50% 초과 시 경고 표시
        alert_status = "🔴 위험 (초과)" if cash_flow_ratio > 50 else "🟢 안정"
        col3.metric("가계수지 지표 (목표 50% 이하)", f"{cash_flow_ratio:.1f} %", alert_status, delta_color="off")
        
        # 지출 카테고리 시각화 (식비, 망실 등 추적)
        expense_df = df[df["유형"] == "지출"]
        if not expense_df.empty:
            fig = px.pie(expense_df, values="금액", names="카테고리", title="지출 비중 분석 (식비 방어 모니터링)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("탭 1에서 데이터를 먼저 입력해주세요.")

# --- TAB 3: 투자 포트폴리오 (yfinance 연동) ---
with tab3:
    st.header("미국 주식 포트폴리오 및 자동 수익률 추적")
    st.write("`yfinance` API를 통해 시장의 실시간 가격을 불러옵니다.")
    
    # 추적할 주식 티커 리스트
    tickers = ["IVV", "JEPI"]
    
    col1, col2 = st.columns(2)
    try:
        # IVV 데이터
        ivv_data = yf.Ticker("IVV").history(period="1d")
        if not ivv_data.empty:
            ivv_price = ivv_data['Close'].iloc[-1]
            col1.metric(label="IVV (S&P 500) 현재가", value=f"${ivv_price:.2f}")
            
        # JEPI 데이터
        jepi_data = yf.Ticker("JEPI").history(period="1d")
        if not jepi_data.empty:
            jepi_price = jepi_data['Close'].iloc[-1]
            col2.metric(label="JEPI (커버드콜) 현재가", value=f"${jepi_price:.2f}")
            
    except Exception as e:
        st.error("주식 데이터를 불러오는데 실패했습니다. 인터넷 연결을 확인하세요.")
