import streamlit as st
import json
from datetime import datetime, timedelta
import os
from fpdf import FPDF

# --- 초기 설정 및 페이지 구성 ---
st.set_page_config(layout="wide", page_title="자동 주간 계획서")

# --- CSS 스타일링 ---
st.markdown("""
<style>
    /* Streamlit 기본 UI 요소 숨기기 */
    #MainMenu, footer, header {visibility: hidden;}

    /* 중앙 정렬 및 색상 테마 적용 */
    .header-base {
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        vertical-align: middle;
        font-weight: bold;
        border: 1px solid #d1d5db;
        color: white;
    }
    .header-default {
        background-color: #4682B4; /* SteelBlue (Dark Cornflower Blue 3 대용) */
    }
    .header-automated {
        background-color: #9932CC; /* DarkOrchid (Dark Magenta 2 대용) */
    }
    .header-day { height: 60px; }
    .header-time { height: 120px; }
    .header-summary { height: 140px; }

    /* 입력창 레이블 숨기기 */
    div[data-testid="stTextArea"] > label, div[data-testid="stTextInput"] > label, div[data-testid="stSelectbox"] > label {
        display: none;
    }
    /* 입력창 기본 스타일 */
    div[data-testid="stTextArea"] > div > textarea {
        background-color: transparent;
        border: none;
        min-height: 100px; /* 최소 높이 지정, 사용자가 수동으로 조절 가능 */
        resize: vertical;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터 및 상수 정의 ---
DATA_FILE = "plans_data.json"
TEAM_ORDER = ["Team종철", "AE/AM", "BDR", "GD", "BSA"]
FONT_FILE = "NanumGothic.ttf"

def load_data():
    """JSON 파일에서 모든 데이터를 불러옵니다."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                # 파일이 비어있는 경우를 대비
                content = f.read()
                if not content:
                    return create_default_data()
                return json.loads(content)
            except json.JSONDecodeError:
                return create_default_data() # 파일이 손상된 경우 기본 데이터 반환
    else:
        return create_default_data()

def create_default_data():
    """기본 데이터 구조를 생성합니다."""
    return {
        "team_members": [
            {"name": "이종철", "rank": "책임", "team": "Team종철"},
            {"name": "배하얀", "rank": "사원", "team": "AE/AM"},
            {"name": "신부현", "rank": "선임", "team": "BSA"}
        ],
        "plans": {}
    }

def save_data(data):
    """모든 데이터를 JSON 파일에 저장합니다."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- PDF 생성 함수 ---
def generate_pdf(plans_data, members_data, year, week, week_dates, day_names, team_order):
    """현재 주의 계획 데이터를 팀별로 정렬하여 PDF 파일로 생성합니다."""
    pdf = FPDF()
    
    # PDF에서 한글을 사용하기 위해 폰트 추가
    pdf.add_font('NanumGothic', '', FONT_FILE, uni=True)
    
    pdf.add_page()
    pdf.set_font('NanumGothic', '', 20)
    pdf.cell(0, 12, f'주간 계획서 - {year}년 {week}주차', ln=True, align='C')
    pdf.ln(10)

    for team_name in team_order:
        team_members_in_group = [m for m in members_data if m.get('team') == team_name]
        if not team_members_in_group:
            continue

        # PDF에 팀 이름 섹션 추가
        pdf.set_font('NanumGothic', 'B', 16)
        pdf.set_fill_color(230, 230, 250) # Lavender
        pdf.cell(0, 10, f'<<< {team_name} 팀 >>>', ln=True, align='C', fill=True)
        pdf.ln(5)

        for member_data in team_members_in_group:
            member_name = member_data.get('name')
            if not member_name or member_name not in plans_data:
                continue

            member_plan = plans_data[member_name]
            member_info = f"[{member_data.get('team', '')}] {member_data.get('rank', '')} {member_name}"

            pdf.set_font('NanumGothic', '', 14)
            pdf.cell(0, 10, member_info, ln=True, align='L')
            pdf.ln(2)

            # 주간 계획 그리드
            pdf.set_font('NanumGothic', 'B', 11)
            pdf.set_fill_color(70, 130, 180) # SteelBlue
            pdf.cell(0, 8, '주간 계획', ln=True, fill=True, border=1, align='C')
            pdf.set_font('NanumGothic', '', 10)
            for i, day_key in enumerate(['mon', 'tue', 'wed', 'thu', 'fri']):
                am_content = member_plan.get('grid', {}).get(f'{day_key}_am', '')
                pm_content = member_plan.get('grid', {}).get(f'{day_key}_pm', '')
                if am_content or pm_content:
                    pdf.set_font('NanumGothic', 'B', 10)
                    pdf.multi_cell(0, 6, f'{day_names[i]} ({week_dates[i]})')
                    pdf.set_font('NanumGothic', '', 10)
                    if am_content: pdf.multi_cell(0, 5, f'  오전: {am_content}')
                    if pm_content: pdf.multi_cell(0, 5, f'  오후: {pm_content}')
            pdf.ln(5)

            # 요약 섹션
            def draw_summary_section(label, content, is_automated):
                pdf.set_font('NanumGothic', 'B', 11)
                fill_color = (153, 50, 204) if is_automated else (70, 130, 180)
                pdf.set_fill_color(*fill_color)
                pdf.cell(0, 8, label, ln=True, fill=True, border=1, align='C')
                pdf.set_font('NanumGothic', '', 10)
                pdf.multi_cell(0, 6, content if content else ' ')
                pdf.ln(3)

            draw_summary_section("지난주 업무 내역", member_plan.get("lastWeekWork", ""), True)
            draw_summary_section("지난주 리뷰", member_plan.get("lastWeekReview", ""), True)
            draw_summary_section("차주 계획", member_plan.get("nextWeekPlan", ""), False)
            draw_summary_section("본인 리뷰", member_plan.get("selfReview", ""), False)
            draw_summary_section("부서장 리뷰", member_plan.get("managerReview", ""), False)
            pdf.ln(10) # 팀원 간 간격

    return pdf.output(dest='S').encode('latin-1')


# --- 세션 상태 초기화 ---
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()
if 'current_week' not in st.session_state:
    st.session_state.current_week = datetime.now().isocalendar()[1]
    st.session_state.current_year = datetime.now().year

# --- 유틸리티 함수 ---
def get_week_id(year, week): return f"{year}-W{str(week).zfill(2)}"
def get_week_dates(year, week):
    first_day = datetime.fromisocalendar(year, week, 1)
    return [(first_day + timedelta(days=i)).strftime("%m/%d") for i in range(5)]

# --- 메인 페이지 UI ---
st.title("🚀 자동 주간 계획서")
st.markdown("---")

# --- 상단 컨트롤 패널 ---
top_cols = st.columns([3, 2])
with top_cols[0]:
    st.subheader("주차 선택")
    nav_cols = st.columns([1, 2, 1, 2, 1])
    if nav_cols[0].button("◀️", use_container_width=True):
        st.session_state.current_week -= 1
        if st.session_state.current_week < 1:
            st.session_state.current_year -= 1
            st.session_state.current_week = datetime(st.session_state.current_year, 12, 28).isocalendar()[1]
    year = st.session_state.current_year
    st.session_state.current_year = nav_cols[1].selectbox("년도", range(year - 5, year + 5), index=5)
    week_range = range(1, datetime(st.session_state.current_year, 12, 28).isocalendar()[1] + 1)
    st.session_state.current_week = nav_cols[3].selectbox("주차", week_range, index=st.session_state.current_week - 1)
    if nav_cols[4].button("▶️", use_container_width=True):
        st.session_state.current_week += 1
        year_end_week = datetime(st.session_state.current_year, 12, 28).isocalendar()[1]
        if st.session_state.current_week > year_end_week:
            st.session_state.current_year += 1
            st.session_state.current_week = 1

with top_cols[1]:
    with st.expander("팀원 추가 및 관리 / PDF 저장", expanded=True):
        add_cols = st.columns([2, 2, 2, 1])
        new_name = add_cols[0].text_input("이름")
        new_rank = add_cols[1].selectbox("직급", ["인턴", "사원", "대리", "선임", "책임", "기타"])
        new_team = add_cols[2].selectbox("팀", TEAM_ORDER)
        if add_cols[3].button("생성"):
            # 'team_members' 키가 없는 경우를 대비하여 안전하게 초기화
            if 'team_members' not in st.session_state.all_data or not isinstance(st.session_state.all_data.get('team_members'), list):
                st.session_state.all_data['team_members'] = []
            
            team_members_list = st.session_state.all_data['team_members']
            
            if new_name and not any(m.get('name') == new_name for m in team_members_list):
                team_members_list.append({"name": new_name, "rank": new_rank, "team": new_team})
                save_data(st.session_state.all_data)
                st.rerun()
            elif not new_name:
                st.warning("이름을 입력해주세요.")
            else:
                st.warning(f"'{new_name}' 이름의 팀원이 이미 존재합니다.")

        st.markdown("---")
        
        # Get the list of team members safely
        team_members_list = st.session_state.all_data.get('team_members', [])
        member_names = []
        # Ensure it's a list of dicts before creating the name list
        if isinstance(team_members_list, list):
            member_names = [m.get('name') for m in team_members_list if isinstance(m, dict) and m.get('name')]

        if member_names:
            member_to_delete = st.selectbox("삭제할 팀원 선택", member_names)
            if st.button("선택한 팀원 삭제", type="secondary"):
                # The list comprehension for deletion needs the original list of dicts
                st.session_state.all_data['team_members'] = [m for m in team_members_list if m.get('name') != member_to_delete]
                save_data(st.session_state.all_data)
                st.rerun()
        else:
            st.info("삭제할 팀원이 없습니다.")

        st.markdown("---")
        # PDF 다운로드 버튼 로직 수정
        if st.button("현재 뷰 PDF로 저장", type="primary"):
            if not os.path.exists(FONT_FILE):
                st.error(f"PDF 생성 오류: '{FONT_FILE}' 폰트 파일을 찾을 수 없습니다. app.py와 같은 폴더에 폰트 파일을 추가해주세요.")
            else:
                current_week_id_for_pdf = get_week_id(st.session_state.current_year, st.session_state.current_week)
                pdf_data = generate_pdf(
                    st.session_state.all_data['plans'].get(current_week_id_for_pdf, {}),
                    st.session_state.all_data['team_members'],
                    st.session_state.current_year, st.session_state.current_week,
                    get_week_dates(st.session_state.current_year, st.session_state.current_week),
                    ['월', '화', '수', '목', '금'], TEAM_ORDER
                )
                st.download_button("PDF 다운로드 준비 완료", pdf_data, f"weekly_plan_{current_week_id_for_pdf}.pdf", "application/pdf")

st.markdown("---")

# --- 메인 계획표 렌더링 (팀별 그룹화 적용) ---
current_week_id = get_week_id(st.session_state.current_year, st.session_state.current_week)
week_dates = get_week_dates(st.session_state.current_year, st.session_state.current_week)
days, day_names = ['mon', 'tue', 'wed', 'thu', 'fri'], ['월', '화', '수', '목', '금']

if current_week_id not in st.session_state.all_data['plans']:
    st.session_state.all_data['plans'][current_week_id] = {}

for team_name in TEAM_ORDER:
    team_members_in_group = [m for m in st.session_state.all_data.get('team_members', []) if isinstance(m, dict) and m.get('team') == team_name]
    if not team_members_in_group: continue

    st.title(f"<{team_name} 팀>")
    for member_data in team_members_in_group:
        member_name = member_data.get('name')
        if not member_name: continue
        
        member_info = f"[{member_data.get('team', '')}] {member_data.get('rank', '')} {member_name}"
        st.subheader(member_info)

        if member_name not in st.session_state.all_data['plans'][current_week_id]:
            st.session_state.all_data['plans'][current_week_id][member_name] = {"grid": {}}
            prev_year, prev_week = (st.session_state.current_year, st.session_state.current_week - 1)
            if prev_week < 1: prev_year -= 1; prev_week = datetime(prev_year, 12, 28).isocalendar()[1]
            prev_week_id = get_week_id(prev_year, prev_week)
            if prev_week_id in st.session_state.all_data['plans'] and member_name in st.session_state.all_data['plans'][prev_week_id]:
                prev_data = st.session_state.all_data['plans'][prev_week_id][member_name]
                if isinstance(prev_data, dict):
                    work_summary = [f"{day_names[i]} - " + (f"오전: {prev_data.get('grid', {}).get(f'{d}_am', '')}" if prev_data.get('grid', {}).get(f'{d}_am', '') else "") + (" / " if prev_data.get('grid', {}).get(f'{d}_am', '') and prev_data.get('grid', {}).get(f'{d}_pm', '') else "") + (f"오후: {prev_data.get('grid', {}).get(f'{d}_pm', '')}" if prev_data.get('grid', {}).get(f'{d}_pm', '') else "") for i, d in enumerate(days) if prev_data.get('grid', {}).get(f'{d}_am', '') or prev_data.get('grid', {}).get(f'{d}_pm', '')]
                    st.session_state.all_data['plans'][current_week_id][member_name]['lastWeekWork'] = "\n".join(work_summary)
                    st.session_state.all_data['plans'][current_week_id][member_name]['lastWeekReview'] = prev_data.get('nextWeekPlan', '')

        member_plan = st.session_state.all_data['plans'][current_week_id].get(member_name, {})

        grid_cols = st.columns([0.1] + [0.18] * 5)
        grid_cols[0].markdown("<div class='header-base header-default header-day'><b>구분</b></div>", unsafe_allow_html=True)
        for i, name in enumerate(day_names):
            grid_cols[i+1].markdown(f"<div class='header-base header-default header-day'><b>{name}</b><br>({week_dates[i]})</div>", unsafe_allow_html=True)
        
        am_cols, pm_cols = st.columns([0.1] + [0.18] * 5), st.columns([0.1] + [0.18] * 5)
        am_cols[0].markdown("<div class='header-base header-default header-time'><b>오전</b></div>", unsafe_allow_html=True)
        pm_cols[0].markdown("<div class='header-base header-default header-time'><b>오후</b></div>", unsafe_allow_html=True)
        for i, day in enumerate(days):
            if 'grid' not in member_plan: member_plan['grid'] = {}
            member_plan['grid'][f'{day}_am'] = am_cols[i+1].text_area(f"grid_{member_name}_{day}_am_{current_week_id}", value=member_plan.get('grid', {}).get(f'{day}_am', ''), height=120)
            member_plan['grid'][f'{day}_pm'] = pm_cols[i+1].text_area(f"grid_{member_name}_{day}_pm_{current_week_id}", value=member_plan.get('grid', {}).get(f'{day}_pm', ''), height=120)

        def render_summary_row(label, key, placeholder, is_auto, height=140):
            header_class = "header-automated" if is_auto else "header-default"
            cols = st.columns([0.2, 0.8])
            cols[0].markdown(f"<div class='header-base {header_class} header-summary'><b>{label}</b></div>", unsafe_allow_html=True)
            member_plan[key] = cols[1].text_area(f"{key}_{member_name}_{current_week_id}", value=member_plan.get(key, ""), placeholder=placeholder, height=height)

        st.markdown("<div style='margin-top: -8px;'></div>", unsafe_allow_html=True)
        render_summary_row("지난주 업무 내역", "lastWeekWork", "지난주 계획이 자동으로 채워집니다. 수정 가능합니다.", True)
        render_summary_row("지난주 리뷰", "lastWeekReview", "지난주의 '차주 계획'이 자동으로 채워집니다. 수정 가능합니다.", True)
        render_summary_row("차주 계획", "nextWeekPlan", "다음 주 '지난주 리뷰' 칸에 표시될 내용을 입력하세요.", False)
        render_summary_row("본인 리뷰", "selfReview", "", False)
        render_summary_row("부서장 리뷰", "managerReview", "", False)
        st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)

save_data(st.session_state.all_data)
