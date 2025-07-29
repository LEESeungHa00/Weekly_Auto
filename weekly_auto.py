import streamlit as st
import json
from datetime import datetime, timedelta
import os

# --- 초기 설정 및 페이지 구성 ---
st.set_page_config(layout="wide", page_title="자동 주간 계획서")

# --- CSS 스타일링 ---
# 원본 HTML/CSS와 최대한 유사하게 보이도록 스타일을 적용합니다.
st.markdown("""
<style>
    /* Streamlit 기본 UI 요소 숨기기 */
    #MainMenu, footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 테이블 스타일 */
    .spreadsheet-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
        border: 2px solid #d1d5db;
        border-radius: 8px;
        overflow: hidden;
    }
    .spreadsheet-table th, .spreadsheet-table td {
        border: 1px solid #d1d5db;
        vertical-align: middle;
        text-align: center;
        padding: 0;
    }
    .header-main {
        background-color: #4a0072;
        color: white;
        font-weight: bold;
        padding: 8px;
    }
    .header-day, .header-time, .header-section {
        background-color: #f3e5f5;
        font-weight: bold;
        padding: 8px;
    }
    .header-section {
        width: 15%;
    }
    /* Streamlit의 텍스트 영역에 대한 직접적인 스타일링은 제한적이므로, 전반적인 컨테이너로 스타일을 제어합니다. */
    div[data-testid="stTextArea"] > label {
        display: none; /* 텍스트 영역의 레이블 숨기기 */
    }
    div[data-testid="stTextArea"] > div > textarea {
        background-color: transparent;
        border: none;
        min-height: 80px;
        resize: vertical;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터 관리 ---
DATA_FILE = "plans_data.json"

def load_data():
    """JSON 파일에서 모든 데이터를 불러옵니다."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 기본 데이터 구조
        return {"team_members": ["신부현", "배하얀"], "plans": {}}

def save_data(data):
    """모든 데이터를 JSON 파일에 저장합니다."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 세션 상태 초기화 ---
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()

if 'current_week' not in st.session_state:
    # 'isocalendar()'는 (year, week, weekday)를 반환합니다.
    st.session_state.current_week = datetime.now().isocalendar()[1]
    st.session_state.current_year = datetime.now().year

# --- 유틸리티 함수 ---
def get_week_id(year, week):
    """연도와 주차로 고유 ID를 생성합니다."""
    return f"{year}-W{str(week).zfill(2)}"

def get_week_dates(year, week):
    """해당 주의 월요일부터 금요일까지의 날짜를 계산합니다."""
    # 해당 주의 첫날(월요일)을 계산
    first_day_of_week = datetime.fromisocalendar(year, week, 1)
    return [(first_day_of_week + timedelta(days=i)).strftime("%m/%d") for i in range(5)]

# --- 사이드바 UI ---
with st.sidebar:
    st.title("메뉴")

    # --- 주차 이동 ---
    st.header("주차 이동")
    col1, col2, col3 = st.columns([1, 2, 1])
    if col1.button("< 이전"):
        st.session_state.current_week -= 1
        if st.session_state.current_week < 1:
            st.session_state.current_year -= 1
            # 작년의 마지막 주차를 계산
            st.session_state.current_week = datetime(st.session_state.current_year, 12, 28).isocalendar()[1]

    col2.metric("현재 주차", f"{st.session_state.current_year}년 {st.session_state.current_week}주차")

    if col3.button("다음 >"):
        st.session_state.current_week += 1
        # 올해의 총 주차 수를 계산하여 다음 해로 넘어가는 로직
        year_end_week = datetime(st.session_state.current_year, 12, 28).isocalendar()[1]
        if st.session_state.current_week > year_end_week:
            st.session_state.current_year += 1
            st.session_state.current_week = 1

    if st.button("이번 주로 돌아가기"):
        st.session_state.current_week = datetime.now().isocalendar()[1]
        st.session_state.current_year = datetime.now().year

    # --- 팀원 관리 ---
    st.header("팀원 관리")
    for member in st.session_state.all_data['team_members']:
        col1, col2 = st.columns([3, 1])
        col1.write(member)
        if col2.button("삭제", key=f"del_{member}"):
            st.session_state.all_data['team_members'].remove(member)
            save_data(st.session_state.all_data)
            st.rerun()

    new_member = st.text_input("새 팀원 이름")
    if st.button("팀원 추가"):
        if new_member and new_member not in st.session_state.all_data['team_members']:
            st.session_state.all_data['team_members'].append(new_member)
            save_data(st.session_state.all_data)
            st.success(f"'{new_member}' 님이 추가되었습니다.")
            st.rerun()
        else:
            st.warning("이름을 입력하거나 이미 존재하는 이름입니다.")

    # --- 데이터 추출 기능 추가 ---
    st.header("데이터 추출")
    # 현재 세션의 데이터를 JSON 문자열로 변환
    json_string = json.dumps(st.session_state.all_data, ensure_ascii=False, indent=4)
    st.download_button(
        label="JSON 파일 다운로드",
        data=json_string,
        file_name="weekly_plans_backup.json",
        mime="application/json",
    )


# --- 메인 페이지 UI ---
st.title("🚀 자동 주간 계획서")
st.markdown("---")

# 현재 주차의 ID와 날짜 계산
current_week_id = get_week_id(st.session_state.current_year, st.session_state.current_week)
week_dates = get_week_dates(st.session_state.current_year, st.session_state.current_week)
days = ['mon', 'tue', 'wed', 'thu', 'fri']
day_names = ['월', '화', '수', '목', '금']

# 현재 주차 데이터가 없으면 생성
if current_week_id not in st.session_state.all_data['plans']:
    st.session_state.all_data['plans'][current_week_id] = {}

# --- 각 팀원별 계획표 렌더링 ---
for member in st.session_state.all_data['team_members']:
    st.markdown(f"### {member}")

    # 팀원의 현재 주차 데이터가 없으면 생성
    if member not in st.session_state.all_data['plans'][current_week_id]:
        st.session_state.all_data['plans'][current_week_id][member] = {
            "grid": {f"{day}_{time}": "" for day in days for time in ['am', 'pm']},
            "lastWeekWork": "",
            "lastWeekReview": "",
            "nextWeekPlan": "",
            "selfReview": "",
            "managerReview": ""
        }
        # --- 자동 연동 로직 ---
        # 이전 주 데이터 가져오기
        prev_year, prev_week = (st.session_state.current_year, st.session_state.current_week - 1)
        if prev_week < 1:
            prev_year -= 1
            prev_week = datetime(prev_year, 12, 28).isocalendar()[1]
        
        prev_week_id = get_week_id(prev_year, prev_week)

        if prev_week_id in st.session_state.all_data['plans'] and \
           member in st.session_state.all_data['plans'][prev_week_id]:
            
            prev_data = st.session_state.all_data['plans'][prev_week_id][member]
            
            # 1. 지난주 업무 내역 연동 (지난주 그리드 -> 이번주 업무내역)
            work_summary = []
            for i, day in enumerate(days):
                am_content = prev_data['grid'].get(f"{day}_am", "")
                pm_content = prev_data['grid'].get(f"{day}_pm", "")
                if am_content or pm_content:
                    daily_summary = f"{day_names[i]} - "
                    if am_content: daily_summary += f"오전: {am_content}"
                    if am_content and pm_content: daily_summary += " / "
                    if pm_content: daily_summary += f"오후: {pm_content}"
                    work_summary.append(daily_summary)
            
            st.session_state.all_data['plans'][current_week_id][member]['lastWeekWork'] = "\n".join(work_summary)

            # 2. 지난주 리뷰 연동 (지난주 차주계획 -> 이번주 지난주리뷰)
            st.session_state.all_data['plans'][current_week_id][member]['lastWeekReview'] = prev_data.get('nextWeekPlan', '')

    member_plan = st.session_state.all_data['plans'][current_week_id][member]

    # --- HTML 테이블로 UI 렌더링 ---
    # 주간 계획 그리드
    cols = st.columns([0.1] + [0.18] * 5)
    cols[0].markdown("<div style='height: 40px; display: flex; align-items: center; justify-content: center; background-color: #f3e5f5; border: 1px solid #d1d5db;'><b>구분</b></div>", unsafe_allow_html=True)
    for i, name in enumerate(day_names):
        cols[i+1].markdown(f"<div style='height: 40px; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #f3e5f5; border: 1px solid #d1d5db;'><b>{name}</b><br>({week_dates[i]})</div>", unsafe_allow_html=True)
    
    cols = st.columns([0.1] + [0.18] * 5)
    cols[0].markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; background-color: #f3e5f5; border: 1px solid #d1d5db;'><b>오전</b></div>", unsafe_allow_html=True)
    for i, day in enumerate(days):
        key = f"grid_{member}_{day}_am_{current_week_id}"
        member_plan['grid'][f'{day}_am'] = cols[i+1].text_area(key, value=member_plan['grid'].get(f'{day}_am', ''), height=100)
    
    cols = st.columns([0.1] + [0.18] * 5)
    cols[0].markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; background-color: #f3e5f5; border: 1px solid #d1d5db;'><b>오후</b></div>", unsafe_allow_html=True)
    for i, day in enumerate(days):
        key = f"grid_{member}_{day}_pm_{current_week_id}"
        member_plan['grid'][f'{day}_pm'] = cols[i+1].text_area(key, value=member_plan['grid'].get(f'{day}_pm', ''), height=100)


    # 주간 요약 섹션
    def render_summary_row(label, key_suffix, placeholder, height=100):
        key = f"{key_suffix}_{member}_{current_week_id}"
        cols = st.columns([0.25, 0.75])
        cols[0].markdown(f"<div style='height: {height}px; display: flex; align-items: center; justify-content: center; background-color: #f3e5f5; border: 1px solid #d1d5db;'><b>{label}</b></div>", unsafe_allow_html=True)
        member_plan[key_suffix] = cols[1].text_area(key, value=member_plan.get(key_suffix, ""), placeholder=placeholder, height=height)

    st.markdown("<div style='margin-top: -1px;'></div>", unsafe_allow_html=True) # 테이블 간격 조정
    render_summary_row("지난주 업무 내역", "lastWeekWork", "지난주 계획이 자동으로 채워집니다. 수정 가능합니다.", 120)
    render_summary_row("지난주 리뷰", "lastWeekReview", "지난주의 '차주 계획'이 자동으로 채워집니다. 수정 가능합니다.", 120)
    render_summary_row("차주 계획", "nextWeekPlan", "다음 주 '지난주 리뷰' 칸에 표시될 내용을 입력하세요.")
    render_summary_row("본인 리뷰", "selfReview", "")
    render_summary_row("부서장 리뷰", "managerReview", "")

    st.markdown("---")


# --- 변경사항 저장 ---
# 앱의 마지막에 한 번만 호출하여 모든 변경사항을 저장합니다.
save_data(st.session_state.all_data)
