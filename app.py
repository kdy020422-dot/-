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
with tab1:
    st.header("현금흐름 및 자산 변동 입력")
    with st.form("입력 폼"):
        date = st.date_input("날짜", datetime.today())
        type_ = st.selectbox("유형", ["수입", "지출", "자산 업데이트(예금/적금)"])
        category = st.selectbox("카테고리", ["근로소득/용돈", "식비 및 외식비", "고정지출", "교통비", "망실(출처불명)", "주식투자", "기타"])
        amount = st.number_input("금액 (원)", min_value=0, step=1000)
        memo = st.text_input("상세 내역")
        
        submitted = st.form_submit_button("저장하기")
        if submitted:
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