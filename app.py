import streamlit as st
import pandas as pd
import random
import math
import time
import altair as alt
import unicodedata

# =================================================================
# 🔬 HUFS SMART CAMPUS MULTI-BUILDING TOILET CONSTANTS
# =================================================================
AVG_USAGE_TIME_MIN = 2.0      # 1인당 평균 이용 시간 T (분)

# 1. 인문과학관
TOTAL_CHAMBERS_HUMANITIES_1F = 7
TOTAL_CHAMBERS_HUMANITIES_35F = 8

# 2. 사회과학관
TOTAL_CHAMBERS_SOCIAL_SCIENCE = 9

# 3. 교수학습개발원
TOTAL_CHAMBERS_CTL = 10
# =================================================================

# 페이지 설정
st.set_page_config(
    page_title="HUFS 스마트 캠퍼스: 실시간 화장실 현황",
    page_icon="🚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 세션 상태 초기화 (멀티 빌딩 독립 관리) -----------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_building = "인문과학관"
    st.session_state.current_floor = "1층"
    
    # 1. 인문과학관 (1층: 7칸, 3층: 8칸, 5층: 8칸)
    st.session_state.chambers_인문과학관_1층 = ["사용중", "사용중", "사용가능", "사용중", "사용가능", "사용가능", "사용중"]
    st.session_state.queue_인문과학관_1층 = 2
    st.session_state.chambers_인문과학관_3층 = ["사용중", "사용중", "사용불가", "사용중", "사용중", "사용중", "사용불가", "사용중"]
    st.session_state.queue_인문과학관_3층 = 3
    st.session_state.chambers_인문과학관_5층 = ["사용중", "사용중", "사용중", "사용중", "사용중", "사용중", "사용불가", "사용중"]
    st.session_state.queue_인문과학관_5층 = 2
    
    # 2. 사회과학관 (1층, 3층, 5층 모두 9칸)
    st.session_state.chambers_사회과학관_1층 = ["사용중", "사용중", "사용불가", "사용중", "사용중", "사용중", "사용불가", "사용중", "사용중"]
    st.session_state.queue_사회과학관_1층 = 2
    st.session_state.chambers_사회과학관_3층 = ["사용가능", "사용중", "사용중", "사용가능", "사용중", "사용가능", "사용중", "사용불가", "사용가능"]
    st.session_state.queue_사회과학관_3층 = 0
    st.session_state.chambers_사회과학관_5층 = ["사용중", "사용중", "사용중", "사용중", "사용중", "사용중", "사용불가", "사용중", "사용중"]
    st.session_state.queue_사회과학관_5층 = 3
    
    # 3. 교수학습개발원 (2층, 4층, 6층 모두 10칸)
    st.session_state.chambers_교수학습개발원_2층 = ["사용중", "사용중", "사용불가", "사용중", "사용중", "사용중", "사용불가", "사용중", "사용중", "사용중"]
    st.session_state.queue_교수학습개발원_2층 = 3
    st.session_state.chambers_교수학습개발원_4층 = ["사용가능", "사용중", "사용중", "사용가능", "사용중", "사용가능", "사용중", "사용불가", "사용가능", "사용가능"]
    st.session_state.queue_교수학습개발원_4층 = 0
    st.session_state.chambers_교수학습개발원_6층 = ["사용중", "사용중", "사용중", "사용중", "사용중", "사용중", "사용불가", "사용중", "사용중", "사용중"]
    st.session_state.queue_교수학습개발원_6층 = 2

    # 사용자 고장 신고 기록 리스트
    st.session_state.reports = []

def nfc(text):
    return unicodedata.normalize('NFC', text) if isinstance(text, str) else text

# 건물 선택에 따른 층 목록 결정
b_current = nfc(st.session_state.current_building)
if b_current == "교수학습개발원":
    floors_list = ["2층", "4층", "6층"]
else:
    floors_list = ["1층", "3층", "5층"]

# 안전 장치: 현재 선택된 층이 활성 건물 층 목록에 없으면 기본값 설정
current_floor_nfc = nfc(st.session_state.current_floor)
if current_floor_nfc not in floors_list:
    st.session_state.current_floor = floors_list[0]
else:
    st.session_state.current_floor = current_floor_nfc

# 각 건물의 층별 칸수 및 상태/대기 정보 해석
# 층별 대기시간 및 가용도 계산
f1_name, f2_name, f3_name = floors_list[0], floors_list[1], floors_list[2]

# 1. 첫 번째 층 (f1_name)
c_key_1 = f"chambers_{b_current}_{f1_name}"
q_key_1 = f"queue_{b_current}_{f1_name}"
chambers_f1 = st.session_state[c_key_1]
total_f1 = TOTAL_CHAMBERS_CTL if b_current == "교수학습개발원" else (TOTAL_CHAMBERS_SOCIAL_SCIENCE if b_current == "사회과학관" else TOTAL_CHAMBERS_HUMANITIES_1F)

occ_f1 = chambers_f1.count("사용중")
out_f1 = chambers_f1.count("사용불가")
avail_f1 = total_f1 - occ_f1 - out_f1
is_f1_disabled = avail_f1 > 0
if is_f1_disabled:
    st.session_state[q_key_1] = 0
    display_queue_f1 = 0
    wait_f1 = 0.0
else:
    display_queue_f1 = st.session_state[q_key_1]
    wait_f1 = round((display_queue_f1 * AVG_USAGE_TIME_MIN) / max(1, (total_f1 - out_f1)), 1) if display_queue_f1 > 0 else 0.0
status_f1 = "🔴 혼잡" if avail_f1 == 0 else ("🟡 보통" if avail_f1 <= 2 else "🟢 여유")
color_f1 = "#ef4444" if status_f1 == "🔴 혼잡" else ("#eab308" if status_f1 == "🟡 보통" else "#22c55e")

# 2. 두 번째 층 (f2_name)
c_key_2 = f"chambers_{b_current}_{f2_name}"
q_key_2 = f"queue_{b_current}_{f2_name}"
chambers_f2 = st.session_state[c_key_2]
total_f2 = TOTAL_CHAMBERS_CTL if b_current == "교수학습개발원" else (TOTAL_CHAMBERS_SOCIAL_SCIENCE if b_current == "사회과학관" else TOTAL_CHAMBERS_HUMANITIES_35F)

occ_f2 = chambers_f2.count("사용중")
out_f2 = chambers_f2.count("사용불가")
avail_f2 = total_f2 - occ_f2 - out_f2
is_f2_disabled = avail_f2 > 0
if is_f2_disabled:
    st.session_state[q_key_2] = 0
    display_queue_f2 = 0
    wait_f2 = 0.0
else:
    display_queue_f2 = st.session_state[q_key_2]
    wait_f2 = round((display_queue_f2 * AVG_USAGE_TIME_MIN) / max(1, (total_f2 - out_f2)), 1) if display_queue_f2 > 0 else 0.0
status_f2 = "🔴 혼잡" if avail_f2 == 0 else ("🟡 보통" if avail_f2 <= 2 else "🟢 여유")
color_f2 = "#ef4444" if status_f2 == "🔴 혼잡" else ("#eab308" if status_f2 == "🟡 보통" else "#22c55e")

# 3. 세 번째 층 (f3_name)
c_key_3 = f"chambers_{b_current}_{f3_name}"
q_key_3 = f"queue_{b_current}_{f3_name}"
chambers_f3 = st.session_state[c_key_3]
total_f3 = TOTAL_CHAMBERS_CTL if b_current == "교수학습개발원" else (TOTAL_CHAMBERS_SOCIAL_SCIENCE if b_current == "사회과학관" else TOTAL_CHAMBERS_HUMANITIES_35F)

occ_f3 = chambers_f3.count("사용중")
out_f3 = chambers_f3.count("사용불가")
avail_f3 = total_f3 - occ_f3 - out_f3
is_f3_disabled = avail_f3 > 0
if is_f3_disabled:
    st.session_state[q_key_3] = 0
    display_queue_f3 = 0
    wait_f3 = 0.0
else:
    display_queue_f3 = st.session_state[q_key_3]
    wait_f3 = round((display_queue_f3 * AVG_USAGE_TIME_MIN) / max(1, (total_f3 - out_f3)), 1) if display_queue_f3 > 0 else 0.0
status_f3 = "🔴 혼잡" if avail_f3 == 0 else ("🟡 보통" if avail_f3 <= 2 else "🟢 여유")
color_f3 = "#ef4444" if status_f3 == "🔴 혼잡" else ("#eab308" if status_f3 == "🟡 보통" else "#22c55e")

# HUFS 테마 컬러 및 고대비 글자 색상 CSS 주입
# 사용자가 글자가 안 보인다고 지적한 피드백을 완벽히 해결하기 위해 모든 Streamlit 기본 구성 요소의 글씨 색상을 백색(#FFFFFF)으로 강제 적용하고
# 흰색 입력창(selectbox, input) 내부의 텍스트만 차콜 블랙(#0f172a)으로 강제 전환하여 완벽한 대비 형성
st.markdown("""
    <style>
    /* 전체 다크 모드 스타일 및 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;500;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0b0f19;
        color: #ffffff !important;
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    /* 사이드바 스타일링 및 글씨색 흰색 강제화 */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* 메인 화면 기본 텍스트 백색 강제화 */
    h1, h2, h3, h4, h5, h6, label, p, li, span {
        color: #ffffff !important;
    }
    
    /* 흰색 배경을 가지는 입력 폼(Selectbox, Input) 텍스트를 차콜 블랙(#0f172a)으로 강제 설정하여 가독성 가시성 완전 해결 */
    div[data-baseweb="select"] * {
        color: #0f172a !important; 
        font-weight: 700 !important;
    }
    input {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    
    /* 셀렉트박스 드롭다운 메뉴 및 팝업 내부의 모든 텍스트가 흰색 배경에서 안 보이는 현상 해결 (대비색 차콜 지정) */
    div[data-baseweb="popover"] *, 
    ul[role="listbox"] *, 
    li[role="option"] *, 
    [data-baseweb="menu"] * {
        color: #0f172a !important;
        font-weight: bold !important;
    }
    
    /* 모든 버튼(대시보드 조회 버튼 및 불편 신고 버튼 포함) 가독성을 위해 흰색 글자 고대비 스타일링 */
    /* 메인 앱 영역의 버튼만 스타일링하여 상단 헤더/설정 메뉴 등의 시스템 버튼이 오염되는 것을 차단 */
    [data-testid="stAppViewContainer"] button {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stAppViewContainer"] button:hover {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.5) !important;
    }
    
    /* 슬라이더 라벨 텍스트 가시화 */
    [data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* 카드 내 텍스트 가독성 강제 주입 */
    .glass-card, .chamber-card {
        color: #ffffff !important;
    }
    .glass-card p, .glass-card div, .glass-card span, .glass-card h1, .glass-card h2, .glass-card h3, .glass-card h4 {
        color: #ffffff !important;
    }
    
    /* 카드 공통 스타일 (Glassmorphism) */
    .glass-card {
        background: rgba(15, 23, 42, 0.85);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* 활성화된 층 카드 강조 스타일 (파란색 테두리 + 글로우 효과) */
    .active-floor-card {
        border: 3px solid #38bdf8 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.6) !important;
        background: rgba(15, 23, 42, 0.95);
    }
    
    /* 고대비 커스텀 안내/성공 메세지 박스 (st.info, st.success 충돌 방지용) */
    .custom-info-box {
        background: rgba(56, 189, 248, 0.15);
        border: 2px solid #38bdf8;
        border-radius: 10px;
        padding: 15px;
        color: #ffffff !important;
        font-weight: bold;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    .custom-success-box {
        background: rgba(34, 197, 94, 0.15);
        border: 2px solid #22c55e;
        border-radius: 10px;
        padding: 15px;
        color: #ffffff !important;
        font-weight: bold;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 사이드바 설정 및 테스트 구성 -----------------
st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color:#38bdf8; margin:0; font-size: 18px;'>⚙️ 데이터 및 시뮬레이션</h2>
    </div>
    <hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);' />
""", unsafe_allow_html=True)

# 층별 대기 현황 제어 조절
st.sidebar.write("### 🎛️ 층별 실시간 대기열 조절")

selected_control_floor = st.sidebar.selectbox(
    "시뮬레이션할 층 선택", 
    floors_list, 
    index=floors_list.index(st.session_state.current_floor)
)
selected_control_floor = nfc(selected_control_floor)

if selected_control_floor != nfc(st.session_state.current_floor):
    st.session_state.current_floor = selected_control_floor
    st.rerun()

if selected_control_floor == floors_list[0]:
    active_disabled = is_f1_disabled
    q_key = q_key_1
    c_key = c_key_1
    active_total = total_f1
elif selected_control_floor == floors_list[1]:
    active_disabled = is_f2_disabled
    q_key = q_key_2
    c_key = c_key_2
    active_total = total_f2
else:
    active_disabled = is_f3_disabled
    q_key = q_key_3
    c_key = c_key_3
    active_total = total_f3

st.sidebar.slider(
    f"{selected_control_floor} 대기 인원 (명)", 
    min_value=0, max_value=15, disabled=active_disabled, key=q_key
)
if active_disabled:
    st.sidebar.caption("⚠️ 빈 칸이 존재하므로 대기열이 0명으로 고정됩니다 (자동 락).")

st.sidebar.write("---")
st.sidebar.write("### 🧻 칸별 상태 조절")
st.sidebar.write(f"현재 선택된 층의 총 칸 수: **{active_total}개**")

# Dynamic cubicle options based on active_total
cubicle_options = [f"{i}번 칸" for i in range(1, active_total + 1)]
selected_cubicle_str = st.sidebar.selectbox(
    "시뮬레이션할 칸 선택", 
    cubicle_options,
    key=f"sb_cubicle_{b_current}_{selected_control_floor}"
)
selected_cubicle_idx = int(selected_cubicle_str.replace("번 칸", "")) - 1

# Current state of the selected cubicle
current_cubicle_state = st.session_state[c_key][selected_cubicle_idx]
state_options = ["사용가능", "사용중", "사용불가"]
selected_state = st.sidebar.selectbox(
    "칸 상태 설정",
    state_options,
    index=state_options.index(current_cubicle_state),
    key=f"sb_state_{b_current}_{selected_control_floor}_{selected_cubicle_idx}"
)

if selected_state != current_cubicle_state:
    st.session_state[c_key][selected_cubicle_idx] = selected_state
    st.rerun()

st.sidebar.write("---")
if st.sidebar.button("🔄 시뮬레이션 상태 초기화", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# ----------------- 2. 층별 선택 및 실시간 summary 카드 (3개 뜨게 하고 클릭 연동) -----------------
st.markdown("<h1 style='text-align: center; color: #38bdf8; margin-bottom: 20px;'>🏫 HUFS 스마트 캠퍼스: 실시간 화장실 현황</h1>", unsafe_allow_html=True)
st.write("")

col_b1, col_b2 = st.columns([2, 1])
with col_b1:
    st.write(f"### 🏢 현재 조회 중인 건물: **{b_current}**")
with col_b2:
    selected_building = st.selectbox(
        "건물 선택",
        ["인문과학관", "사회과학관", "교수학습개발원"],
        index=["인문과학관", "사회과학관", "교수학습개발원"].index(st.session_state.current_building)
    )
    if selected_building != st.session_state.current_building:
        st.session_state.current_building = selected_building
        # 층 기본값 세팅
        if selected_building == "교수학습개발원":
            st.session_state.current_floor = "2층"
        else:
            st.session_state.current_floor = "1층"
        st.rerun()

st.markdown(f"### 🏢 {b_current} 여자화장실 층별 혼잡도 및 조회")
st.write("조회하고 싶으신 층의 카드를 클릭(선택)해 주세요. 아래에 해당 층의 **세부 실시간 칸별 상태 및 시간 흐름별 대기 예측 그래프**가 나타납니다.")

col_floor1, col_floor2, col_floor3 = st.columns(3)

# 1번째 층 요약 카드
with col_floor1:
    is_active = st.session_state.current_floor == f1_name
    active_class = "active-floor-card" if is_active else ""
    st.markdown(f"""
        <div class='glass-card {active_class}' style='border-left: 6px solid {color_f1}; margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                <span style='font-size: 16px; font-weight: 800; color: #ffffff; white-space: nowrap;'>🏢 {f1_name} 여자화장실</span>
                <span style='background-color: {color_f1}; color: #ffffff; padding: 2px 10px; border-radius: 12px; font-weight: 800; font-size: 11px; white-space: nowrap;'>{status_f1}</span>
            </div>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 사용 가능 잔여칸: <b>{avail_f1} / {total_f1} 칸</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 실시간 복도 대기: <b>{display_queue_f1} 명</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 평균 예상 대기시간: <b style='color:#ff4b4b;'>약 {wait_f1}분</b></p>
        </div>
    """, unsafe_allow_html=True)
    if st.button(f"👇 {f1_name} 실시간 칸별 현황 조회", key="btn_f1", use_container_width=True, type="primary" if is_active else "secondary"):
        st.session_state.current_floor = f1_name
        st.rerun()

# 2번째 층 요약 카드
with col_floor2:
    is_active = st.session_state.current_floor == f2_name
    active_class = "active-floor-card" if is_active else ""
    st.markdown(f"""
        <div class='glass-card {active_class}' style='border-left: 6px solid {color_f2}; margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                <span style='font-size: 16px; font-weight: 800; color: #ffffff; white-space: nowrap;'>🏢 {f2_name} 여자화장실</span>
                <span style='background-color: {color_f2}; color: #ffffff; padding: 2px 10px; border-radius: 12px; font-weight: 800; font-size: 11px; white-space: nowrap;'>{status_f2}</span>
            </div>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 사용 가능 잔여칸: <b>{avail_f2} / {total_f2} 칸</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 실시간 복도 대기: <b>{display_queue_f2} 명</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 평균 예상 대기시간: <b style='color:#ff4b4b;'>약 {wait_f2}분</b></p>
        </div>
    """, unsafe_allow_html=True)
    if st.button(f"👇 {f2_name} 실시간 칸별 현황 조회", key="btn_f2", use_container_width=True, type="primary" if is_active else "secondary"):
        st.session_state.current_floor = f2_name
        st.rerun()

# 3번째 층 요약 카드
with col_floor3:
    is_active = st.session_state.current_floor == f3_name
    active_class = "active-floor-card" if is_active else ""
    st.markdown(f"""
        <div class='glass-card {active_class}' style='border-left: 6px solid {color_f3}; margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                <span style='font-size: 16px; font-weight: 800; color: #ffffff; white-space: nowrap;'>🏢 {f3_name} 여자화장실</span>
                <span style='background-color: {color_f3}; color: #ffffff; padding: 2px 10px; border-radius: 12px; font-weight: 800; font-size: 11px; white-space: nowrap;'>{status_f3}</span>
            </div>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 사용 가능 잔여칸: <b>{avail_f3} / {total_f3} 칸</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 실시간 복도 대기: <b>{display_queue_f3} 명</b></p>
            <p style='font-size: 13px; color: #ffffff; margin: 5px 0;'>• 평균 예상 대기시간: <b style='color:#ff4b4b;'>약 {wait_f3}분</b></p>
        </div>
    """, unsafe_allow_html=True)
    if st.button(f"👇 {f3_name} 실시간 칸별 현황 조회", key="btn_f3", use_container_width=True, type="primary" if is_active else "secondary"):
        st.session_state.current_floor = f3_name
        st.rerun()

# ----------------- 3. 선택된 층 상세 조회 영역 (그래프와 칸 현황 렌더링) -----------------
active_floor = st.session_state.current_floor

if active_floor == f1_name:
    chamber_states = chambers_f1
    hallway_queue = display_queue_f1
    floor_status = status_f1
    floor_color = color_f1
    floor_avail = avail_f1
    floor_wait = wait_f1
    floor_out = out_f1
    total_active_chambers = total_f1
elif active_floor == f2_name:
    chamber_states = chambers_f2
    hallway_queue = display_queue_f2
    floor_status = status_f2
    floor_color = color_f2
    floor_avail = avail_f2
    floor_wait = wait_f2
    floor_out = out_f2
    total_active_chambers = total_f2
else:
    chamber_states = chambers_f3
    hallway_queue = display_queue_f3
    floor_status = status_f3
    floor_color = color_f3
    floor_avail = avail_f3
    floor_wait = wait_f3
    floor_out = out_f3
    total_active_chambers = total_f3

st.write("---")
st.markdown(f"### 🧻 {active_floor} 여자화장실 실시간 세부 현황")

col_detail_1, col_detail_2 = st.columns([1, 1])

with col_detail_1:
    # 시간대별 정체 예측 그래프 (1교시부터 9교시까지 시간 흐름 순 정렬 완료)
    st.markdown(f"<div style='font-size:14px; font-weight:800; color:#38bdf8; margin-bottom:8px;'>📈 {active_floor} 시간 흐름별 정체 예측 (1교시~9교시)</div>", unsafe_allow_html=True)
    
    # 1교시부터 9교시 및 쉬는 시간 대기열 추이 데이터셋
    chart_data = pd.DataFrame({
        "시간대": [
            "09:00 (1교시)", "10:15 (쉬는시간)", 
            "10:30 (2교시)", "11:45 (쉬는시간)", 
            "12:00 (3교시)", "13:15 (쉬는시간)", 
            "13:30 (4교시)", "14:45 (쉬는시간)", 
            "15:00 (5교시)", "16:15 (쉬는시간)", 
            "16:30 (6교시)", "17:45 (쉬는시간)",
            "18:00 (7교시)", "19:15 (쉬는시간)",
            "19:30 (8교시)", "20:45 (쉬는시간)",
            "21:00 (9교시)"
        ],
        "대기시간": [0.5, 4.5, 0.8, 5.5, 1.0, 4.0, 0.6, 5.0, 0.3, 3.5, 0.2, 3.0, 0.2, 2.5, 0.1, 2.0, 0.1]
    })
    
    # 가독성이 높은 막대 차트 (가로축 텍스트 각도를 -60도로 눕혀 모든 텍스트가 겹치지 않게 조절)
    timeline_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("시간대:N", sort=None, title=None, axis=alt.Axis(labelAngle=-60, labelColor="#ffffff", titleColor="#ffffff", labelFontSize=10)),
        y=alt.Y("대기시간:Q", title="평균 대기 시간 (분)", axis=alt.Axis(labelColor="#ffffff", titleColor="#ffffff", labelFontSize=10)),
        color=alt.value("#38bdf8")
    ).properties(
        height=350,
        background="transparent"
    ).configure_view(
        strokeOpacity=0
    )
    
    st.altair_chart(timeline_chart, use_container_width=True)

with col_detail_2:
    # ----------------- 도면 기준 평면도 레이아웃 그리기 -----------------
    
    # SVG 미니 아이콘
    svg_occ_mini = """<svg viewBox="0 0 100 100" width="16" height="16" style="fill:white; vertical-align:middle; margin-right:3px;"><circle cx="50" cy="20" r="10"/><line x1="50" y1="30" x2="50" y2="60" stroke="white" stroke-width="8"/><line x1="50" y1="60" x2="35" y2="85" stroke="white" stroke-width="8"/><line x1="50" y1="60" x2="65" y2="85" stroke="white" stroke-width="8"/></svg>"""
    svg_avail_mini = """<svg viewBox="0 0 100 100" width="16" height="16" style="fill:white; vertical-align:middle; margin-right:3px;"><rect x="30" y="20" width="40" height="60" rx="5"/></svg>"""
    svg_tool_mini = """<svg viewBox="0 0 100 100" width="16" height="16" style="fill:white; vertical-align:middle; margin-right:3px;"><path d="M20 80 L80 20 M80 20 L60 20 M80 20 L80 40" stroke="white" stroke-width="8" stroke-linecap="round"/></svg>"""

    # 개별 칸 렌더러 함수
    def get_cell_html(num, is_disabled=False):
        state = chamber_states[num-1]
        label = f"장애인 {num} 화장실" if is_disabled else f"화장실 {num}"
        if state == "사용중":
            bg = "linear-gradient(180deg, #d32f2f 0%, #ef5350 100%)"
            border = "2px solid #ef4444"
            status_text = "❌ 사용중"
            icon = svg_occ_mini
        elif state == "사용가능":
            bg = "linear-gradient(180deg, #1b5e20 0%, #4caf50 100%)"
            border = "2px solid #22c55e"
            status_text = "🟢 가능"
            icon = svg_avail_mini
        else: # 사용불가
            bg = "linear-gradient(180deg, #475569 0%, #64748b 100%)"
            border = "2px dashed #94a3b8"
            status_text = "⚠️ 점검"
            icon = svg_tool_mini
            
        return f"<div style='background: {bg}; border: {border}; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; box-shadow: 0 4px 8px rgba(0,0,0,0.3); color: #ffffff !important; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.8);'><div style='font-size: 13px; color:#ffffff !important;'>{label}</div><div style='font-size: 11px; margin-top: 3px; color:#ffffff !important;'>{icon} {status_text}</div></div>"

    sinks_html_double = """
    <div style='height: 18%; border: 2px dashed #38bdf8; background: rgba(56, 189, 248, 0.08); border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #38bdf8 !important; font-weight: bold;'>
        <div style='display: flex; flex-direction: column; gap: 4px; margin-bottom: 3px; align-items: center;'>
            <div style='width: 12px; height: 12px; border: 2px solid #38bdf8; border-radius: 50%;'></div>
            <div style='width: 12px; height: 12px; border: 2px solid #38bdf8; border-radius: 50%;'></div>
        </div>
        <div style='font-size: 11px; color:#38bdf8 !important;'>세면대</div>
    </div>
    """

    aisle_content = """
    <div style='width: 14%; display: flex; flex-direction: column; align-items: center; justify-content: center; border-left: 1px dashed rgba(255,255,255,0.1); border-right: 1px dashed rgba(255,255,255,0.1); height: 100%; color: rgba(255,255,255,0.3); font-weight: bold; font-size: 12px; letter-spacing: 2px;'>
        복<br/>도
    </div>
    """

    if b_current == "인문과학관":
        left_cells = "".join([f"<div style='height: 18%;'>{get_cell_html(i)}</div>" for i in range(1, 5)])
        left_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{left_cells}{sinks_html_double}</div>"
        
        if active_floor == "1층":
            storage_html = "<div style='height: 18%; background: #1e293b; border: 2px dashed rgba(255,255,255,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 12px; font-weight: bold;'>창고</div>"
            cell_5 = f"<div style='height: 18%;'>{get_cell_html(5)}</div>"
            cell_6 = f"<div style='height: 18%;'>{get_cell_html(6)}</div>"
            cell_7 = f"<div style='height: 38%;'>{get_cell_html(7, is_disabled=True)}</div>"
            right_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{storage_html}{cell_5}{cell_6}{cell_7}</div>"
        else:
            cell_5 = f"<div style='height: 18%;'>{get_cell_html(5)}</div>"
            cell_6 = f"<div style='height: 18%;'>{get_cell_html(6)}</div>"
            cell_7 = f"<div style='height: 18%;'>{get_cell_html(7)}</div>"
            cell_8 = f"<div style='height: 38%;'>{get_cell_html(8, is_disabled=True)}</div>"
            right_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{cell_5}{cell_6}{cell_7}{cell_8}</div>"

    elif b_current == "사회과학관":
        left_cells = "".join([f"<div style='height: 18%;'>{get_cell_html(i)}</div>" for i in range(1, 5)])
        left_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{left_cells}{sinks_html_double}</div>"
        
        right_cells = "".join([f"<div style='height: 16%;'>{get_cell_html(i)}</div>" for i in range(5, 10)])
        mirror_html = "<div style='height: 16%; border: 2px dashed rgba(255,255,255,0.2); background: rgba(255, 255, 255, 0.05); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 11px; font-weight: bold;'>🪞 거울</div>"
        right_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{right_cells}{mirror_html}</div>"

    else:  # 교수학습개발원
        left_cells = "".join([f"<div style='height: 15%;'>{get_cell_html(i)}</div>" for i in range(1, 6)])
        left_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{left_cells}{sinks_html_double}</div>"
        
        right_cells = "".join([f"<div style='height: 15%;'>{get_cell_html(i)}</div>" for i in range(6, 11)])
        right_column_content = f"<div style='width: 42%; display: flex; flex-direction: column; justify-content: space-between; height: 100%;'>{right_cells}{sinks_html_double}</div>"

    # 프레임 조합
    layout_html = f"""
    <div style='border: 3px solid rgba(255,255,255,0.2); background: #0f172a; border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 10px; width: 100%; max-width: 480px; margin: 0 auto; box-shadow: 0 8px 32px rgba(0,0,0,0.5);'>
        <div style='text-align: center; color: #ffffff !important; font-weight: 800; font-size: 15px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 5px;'>
            🚶‍♀️ {b_current} {active_floor} 여자화장실 실측 평면도
        </div>
        <div style='display: flex; justify-content: space-between; height: 440px;'>
            {left_column_content}
            {aisle_content}
            {right_column_content}
        </div>
        <div style='text-align: center; margin-top: 10px; border-top: 2px solid rgba(255,255,255,0.1); padding-top: 10px;'>
            <span style='background: #002F6C; color: #ffffff !important; padding: 4px 15px; border-radius: 20px; font-size: 11px; font-weight: bold;'>⬇️ 입구 (Entrance)</span>
        </div>
    </div>
    """
    
    st.markdown(layout_html.replace("\n", ""), unsafe_allow_html=True)

st.write("---")

# ----------------- 4. 고장 및 불편 신고 창 (실제 사용할 수 있는 창처럼 연동 구현) -----------------
st.markdown("### 🚨 실시간 시설 관리 및 고장/민원 신고")
st.write("화장실 칸의 고장(변기막힘, 용품부족 등)을 발견하면 아래 폼을 통해 실시간으로 접수해 주세요. 접수 즉시 해당 칸이 '점검중'으로 임시 자동 잠금 처리됩니다.")

# 신고 폼 컴포넌트
with st.form("report_form", clear_on_submit=True):
    col_form1, col_form2, col_form3 = st.columns(3)
    with col_form1:
        report_floor = st.selectbox("신고 대상 층", floors_list, index=floors_list.index(active_floor))
    with col_form2:
        # 선택된 신고 대상 층의 실제 칸 수에 맞춰 동적으로 번호 매칭
        if b_current == "교수학습개발원":
            active_chambers_count = TOTAL_CHAMBERS_CTL
        elif b_current == "사회과학관":
            active_chambers_count = TOTAL_CHAMBERS_SOCIAL_SCIENCE
        else:
            active_chambers_count = TOTAL_CHAMBERS_HUMANITIES_1F if report_floor == "1층" else TOTAL_CHAMBERS_HUMANITIES_35F
        report_chamber = st.selectbox("신고 대상 칸 번호", [f"{i+1}번 칸" for i in range(active_chambers_count)])
    with col_form3:
        report_issue = st.selectbox("민원 내용", ["변기 막힘 / 물이 내려가지 않음", "화장지 부족 / 빈 통", "문고리 / 문 잠금 장치 고장", "위생 불량 및 청소 요청", "기타"])
        
    report_details = st.text_input("상세 고장 정보 (선택 사항)", placeholder="예: 3번 칸 변기가 막혀 물이 넘칠 것 같습니다.")
    submit_btn = st.form_submit_button("🚨 불편 신고 접수하기")
    
    if submit_btn:
        chamber_idx = int(report_chamber.split("번")[0]) - 1
        
        # 민원 기록 세션 상태에 저장
        report_entry = {
            "time": time.strftime('%H:%M:%S'),
            "building": b_current,
            "floor": report_floor,
            "chamber": report_chamber,
            "issue": report_issue,
            "details": report_details
        }
        st.session_state.reports.append(report_entry)
        
        # 실제로 대시보드 상태에 동적 피드백 연계
        st.session_state[f"chambers_{b_current}_{report_floor}"][chamber_idx] = "사용불가"
            
        # 커스텀 고대비 메세지 박스로 렌더링
        st.markdown(f"""
            <div class='custom-success-box'>
                ✅ <b>신고 접수 완료 ({time.strftime('%H:%M:%S')})</b><br/>
                {b_current} {report_floor} {report_chamber}이(가) '사용 불가(점검중)' 상태로 즉시 임시 차단 조치되었습니다. 
                시설물 관리팀(시설팀)에 실시간 접수 통보되었습니다.
            </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
        st.rerun()

# 등록된 신고 리스트 관리자 확인 보드 (프리미엄 디테일)
if len(st.session_state.reports) > 0:
    with st.expander("🛠&nbsp; 현재 접수된 시설물 고장/민원 내역 보기 (실시간 현황)"):
        for i, r in enumerate(reversed(st.session_state.reports)):
            st.write(f"[{r['time']}] **{r.get('building', '인문과학관')} {r['floor']} {r['chamber']}** - **{r['issue']}** ({r['details']})")
            st.write("---")

# 🔬 공간 및 대기 분석 설계 (요청하신 대로 상수 튜닝 설명 가이드 글귀 삭제)
st.write("")
st.markdown("### 🔬 공간 및 대기 분석 설계")
st.markdown(f"""
    <div class='custom-info-box'>
        💡 <b>실측 공식 세팅</b>: 평균 예상 대기시간은 2.0분을 기준 변수로 하여 
        <code>(대기열 인원 * {AVG_USAGE_TIME_MIN}분) / 가용 작동 칸수</code> 로 자동 계산됩니다.
    </div>
""", unsafe_allow_html=True)

# ----------------- 하단 푸터 -----------------
st.markdown("""
    <div style='text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid rgba(255,255,255,0.05); color: #64748b; font-size: 11px;'>
        © 2026 HUFS Smart Campus Project - 캠퍼스 화장실 실시간 혼잡도 분석 서비스. Designed by Antigravity.
    </div>
""", unsafe_allow_html=True)
# 🚽 HUFS 스마트 캠퍼스: 인문과학관 화장실 실시간 현황 프로토타입

한국외국어대학교 인문과학관 화장실의 칸수 증설이 불가능한 상황에서, **무선 개폐 센서 정보 시각화**와 **오프라인 바닥 테이프(Nudge)**를 연계하여 지각 불안감을 해소하고 동선 분산을 유도하는 스마트 캠퍼스 인프라 대시보드 프로토타입입니다.

## 🚀 깃허브(GitHub) 업로드 및 배포 방법 (Streamlit Cloud)

이 레포지토리는 **Streamlit Community Cloud**에 무료로 배포하여 스마트폰(한국외대 캠퍼스 앱 링크 등) 및 발표용 모니터 화면으로 즉시 시연할 수 있도록 최적화되어 있습니다.

### 1단계: 내 깃허브(GitHub)에 소스 올리기
1. 깃허브(https://github.com)에 로그인하고 새로운 레포지토리(New Repository)를 생성합니다. (예: `hufs-smart-toilet`)
2. 생성된 레포지토리에 이 폴더의 다음 파일들을 업로드합니다:
   - `app.py`: 메인 대시보드 및 시뮬레이터 프로그램
   - `requirements.txt`: 배포에 필요한 패키지 명세서
   - `README.md`: 설명 문서

> 💡 **깃 배시(Git Bash) 또는 터미널을 이용할 경우:**
> ```bash
> git init
> git add .
> git commit -m "Initial commit of HUFS Smart Toilet app"
> git branch -M main
> git remote add origin https://github.com/사용자아이디/hufs-smart-toilet.git
> git push -u origin main
> ```

---

### 2단계: Streamlit Community Cloud에 무료 배포하기
1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다. (GitHub 계정으로 로그인 가능)
2. **"Create app"** 또는 **"New app"** 버튼을 클릭합니다.
3. 배포 설정 입력창에 다음과 같이 설정합니다:
   - **Repository**: `사용자아이디/hufs-smart-toilet` (선택 가능 목록에 나타남)
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **"Deploy!"** 버튼을 클릭합니다.
5. 약 1~2분 정도 패키지 설치 및 빌드가 완료되면 전 세계 어디서나 모바일/PC로 접속 가능한 공개 공유 링크(`https://hufs-smart-toilet.streamlit.app/` 등)가 생성됩니다!

---

## 🔬 실측 데이터 반영 방법 (내일 실측 후 설정)

내일 실제 인문과학관 2층 여자 화장실의 구조를 실측하신 뒤, `app.py` 코드 최상단에 있는 아래 상수 영역의 값만 에디터로 변경하여 깃허브에 다시 커밋(Commit)해 주시면 배포된 웹사이트에 자동으로 실시간 반영됩니다:

```python
# =================================================================
# 🔬 HUFS HUMANITIES BUILDING FIELD MEASUREMENT CONSTANTS (FOR TOMORROW)
# =================================================================
TOTAL_CHAMBERS = 8            # 인문과학관 2층 여자화장실 실측 칸 개수 (기본 8칸 고정)
AVG_USAGE_TIME_MIN = 1.5      # 1인당 실제 측정된 평균 이용 시간 T (분)
PEOPLE_PER_TILE_ZONE = 3      # 복도 바닥 타일 1개 Zone당 대기 가능 인원 (명)
WAIT_TIME_ALPHA_MIN = 0.5     # 대기 지연 보정상수 alpha (분)
# =================================================================
```

---

## 🎨 주요 시연 기능 (발표 활용용)
- **발표용 시나리오 단축 버튼**: 왼쪽 사이드바에서 시나리오(여유/혼잡/만석 및 바닥테이프 연계/점검 중)를 선택하면 실시간 센서 및 대기 상태가 단번에 전환되어 조작 실수를 막아줍니다.
- **GPS 지오펜싱 시뮬레이터**: 캠퍼스(인문관 반경 50m) 내부에서만 조회할 수 있는 넛지 보안을 시각화합니다. (사이드바의 거리 슬라이더를 50m 초과로 조절 시 화면이 불투명하게 잠기며 안내문 노출)
- **복도 대기선(Zone A/B/C) 연동**: 대기자가 늘어남에 따라 "3층으로 우회해 주세요" 등 오프라인 바닥 테이프 가이드와 동기화된 메시지를 동적으로 뿌려줍니다.
