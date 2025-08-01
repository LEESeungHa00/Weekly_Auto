import streamlit as st
import json
from datetime import datetime, timedelta
import os
from fpdf import FPDF
import time

# --- 초기 설정 및 페이지 구성 ---
st.set_page_config(layout="wide", page_title="자동 주간 계획서")

# --- CSS 스타일링 ---
st.markdown("""
<style>
    /* Streamlit 기본 UI 요소 숨기기 (header 제외) */
    #MainMenu, footer {visibility: hidden;}

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
        border-radius: 4px; /* 모서리 살짝 둥글게 */
    }
    .header-default {
        background-color: #1c4587; /* Dark Cornflower Blue 3 */
    }
    .header-automated {
        background-color: #741b47; /* Dark Magenta 2 */
    }
    /* 헤더 정렬 문제 수정을 위해 padding과 min-height 사용 */
    .header-day { 
        min-height: 55px;
        padding: 8px;
    }
    .header-summary { height: 140px; }

    /* 입력창 레이블 숨기기 */
    div[data-testid="stTextArea"] > label, div[data-testid="stTextInput"] > label, div[data-testid="stSelectbox"] > label, div[data-testid="stDateInput"] > label {
        display: none;
    }
    /* 입력창 기본 스타일 */
    div[data-testid="stTextArea"] > div > textarea {
        background-color: transparent;
        border: none;
        min-height: 100px; /* 최소 높이 지정, 사용자가 수동으로 조절 가능 */
        resize: vertical;
    }
    /* 모바일용 오전/오후 라벨 */
    .mobile-label {
        font-weight: bold;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 0.2rem;
        padding: 0.3rem;
        background-color: #f0f2f6;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터 및 상수 정의 ---
DATA_FILE = "plans_data.json"
TEAM_ORDER = ["Team종철", "AE/AM", "BDR", "GD", "BSA"]
RANK_ORDER = ["책임", "선임", "대리", "사원", "인턴", "기타"] # 직급 정렬 순서
FONT_FILE = "NanumGothic.ttf"
DELETE_PASSWORD = "3002"

def load_data():
    """JSON 파일에서 모든 데이터를 불러옵니다."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
            try:
                content = f.read()
                if not content: return create_default_data()
                return json.loads(content)
            except json.JSONDecodeError:
                return create_default_data()
    else:
        return create_default_data()

def create_default_data():
    """기본 데이터 구조를 생성합니다."""
    return {
        "team_members": [
            {"name": "이종철", "rank": "책임", "team": "Team종철"},
            {"name": "배하란", "rank": "선임", "team": "AE/AM"},
            {"name": "오동민", "rank": "대리", "team": "GD"},
            {"name": "이승하", "rank": "사원", "team": "BSA"}
        ],
        "plans": {}
    }

def save_data(data):
    """모든 데이터를 JSON 파일에 저장합니다."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- PDF 생성 함수 ---
def generate_pdf(plans_data, members_data, year, week, week_dates, prev_week_dates, day_names, team_order):
    """현재 주의 계획 데이터를 팀별, 직급별로 정렬하여 PDF 파일로 생성합니다."""
    pdf = FPDF()
    
    pdf.add_font('NanumGothic', '', FONT_FILE, uni=True)
    pdf.add_page()
    pdf.set_font('NanumGothic', '', 20)
    pdf.cell(0, 12, f'주간 계획서 - {year}년 {week}주차', ln=True, align='C')
    pdf.ln(10)

    for team_name in team_order:
        team_members_in_group = [m for m in members_data if isinstance(m, dict) and m.get('team') == team_name]
        team_members_in_group.sort(key=lambda m: RANK_ORDER.index(m.get('rank', '기타')) if m.get('rank') in RANK_ORDER else len(RANK_ORDER))
        if not team_members_in_group: continue

        if not any(m.get('name') in plans_data for m in team_members_in_group):
            continue

        pdf.set_font('NanumGothic', 'B', 16)
        pdf.set_fill_color(230, 230, 250)
        pdf.cell(0, 10, f'<<< {team_name} >>>', ln=True, align='C', fill=True)
        pdf.ln(5)

        for member_data in team_members_in_group:
            member_name = member_data.get('name')
            if not member_name or member_name not in plans_data: continue

            member_plan = plans_data[member_name]
            member_info = f"[{member_data.get('team', '')}] {member_name} {member_data.get('rank', '')}"

            pdf.set_font('NanumGothic', '', 14)
            pdf.cell(0, 10, member_info, ln=True, align='L')
            pdf.ln(2)

            pdf.set_font('NanumGothic', 'B', 11)
            pdf.set_fill_color(70, 130, 180)
            pdf.cell(0, 8, '이번주 계획', ln=True, fill=True, border=1, align='C')
            pdf.set_font('NanumGothic', '', 10)
            for i, day_key in enumerate(['mon', 'tue', 'wed', 'thu', 'fri']):
                am = member_plan.get('grid', {}).get(f'{day_key}_am', '')
                pm = member_plan.get('grid', {}).get(f'{day_key}_pm', '')
                if am or pm:
                    pdf.set_font('NanumGothic', 'B', 10)
                    pdf.multi_cell(0, 6, f'{day_names[i]}({week_dates[i]})')
                    pdf.set_font('NanumGothic', '', 10)
                    if am: pdf.multi_cell(0, 5, f'  오전: {am}')
                    if pm: pdf.multi_cell(0, 5, f'  오후: {pm}')
            pdf.ln(5)

            pdf.set_font('NanumGothic', 'B', 11)
            pdf.set_fill_color(153, 50, 204)
            pdf.cell(0, 8, '지난주 업무 내역 (수정본)', ln=True, fill=True, border=1, align='C')
            pdf.set_font('NanumGothic', '', 10)
            for i, day_key in enumerate(['mon', 'tue', 'wed', 'thu', 'fri']):
                am = member_plan.get('lastWeekGrid', {}).get(f'{day_key}_am', '')
                pm = member_plan.get('lastWeekGrid', {}).get(f'{day_key}_pm', '')
                if am or pm:
                    pdf.set_font('NanumGothic', 'B', 10)
                    pdf.multi_cell(0, 6, f'{day_names[i]}({prev_week_dates[i]})')
                    pdf.set_font('NanumGothic', '', 10)
                    if am: pdf.multi_cell(0, 5, f'  오전: {am}')
                    if pm: pdf.multi_cell(0, 5, f'  오후: {pm}')
            pdf.ln(5)
            
            def draw_summary_section(label, content, is_automated):
                pdf.set_font('NanumGothic', 'B', 11)
                pdf.set_fill_color(*(153, 50, 204) if is_automated else (70, 130, 180))
                pdf.cell(0, 8, label, ln=True, fill=True, border=1, align='C')
                pdf.set_font('NanumGothic', '', 10)
                pdf.multi_cell(0, 6, content if content else ' ')
                pdf.ln(3)

            draw_summary_section("지난주 리뷰 (수정본)", member_plan.get("lastWeekReview", ""), True)
            draw_summary_section("차주 계획", member_plan.get("nextWeekPlan", ""), False)
            draw_summary_section("본인 리뷰", member_plan.get("selfReview", ""), False)
            draw_summary_section("부서장 리뷰", member_plan.get("managerReview", ""), False)
            pdf.ln(10)

    return pdf.output(dest='S').encode('latin-1')


# --- 세션 상태 초기화 ---
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now()

# --- 유틸리티 함수 ---
def get_week_id(year, week): return f"{year}-W{str(week).zfill(2)}"
def get_week_dates(date_obj):
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    return [(start_of_week + timedelta(days=i)).strftime("%m/%d") for i in range(5)]

# --- 사이드바 ---
with st.sidebar:
    st.title("메뉴")
    st.markdown("---")
    
    with st.expander("과거 기록 조회", expanded=False):
        plan_years = [int(week_id.split('-W')[0]) for week_id in st.session_state.all_data['plans'].keys()]
        current_year = datetime.now().year
        
        if plan_years:
            min_year = min(plan_years)
            max_year = max(plan_years)
            all_years = list(range(min_year - 3, max_year + 4))
        else:
            all_years = list(range(current_year - 3, current_year + 4))
        
        if current_year not in all_years:
            all_years.append(current_year)
            all_years.sort(reverse=True)

        try:
            default_year_index = all_years.index(st.session_state.selected_date.isocalendar().year)
        except ValueError:
            default_year_index = all_years.index(current_year) if current_year in all_years else 0

        sidebar_year = st.selectbox("연도 선택", all_years, index=default_year_index)

        try:
            weeks_in_year_count = datetime(sidebar_year, 12, 28).isocalendar()[1]
            weeks_in_year = list(range(1, weeks_in_year_count + 1))
        except ValueError:
            weeks_in_year = list(range(1, 53))

        current_week_of_selected_year = st.session_state.selected_date.isocalendar().week if st.session_state.selected_date.isocalendar().year == sidebar_year else 1
        default_week_index = current_week_of_selected_year - 1 if (current_week_of_selected_year - 1) < len(weeks_in_year) else 0

        sidebar_week = st.selectbox("주차 선택", weeks_in_year, index=default_week_index)

        if st.button("조회하기", use_container_width=True):
            st.session_state.selected_date = datetime.fromisocalendar(sidebar_year, sidebar_week, 1)
            st.rerun()

    st.markdown("---")
    with st.expander("팀원 목록 관리", expanded=True):
        team_members_list = st.session_state.all_data.get('team_members', [])
        
        st.write("**신규 팀원 추가**")
        with st.form("add_member_form", clear_on_submit=True):
            new_name = st.text_input("이름")
            new_rank = st.selectbox("직급", RANK_ORDER, placeholder="직급 선택")
            new_team = st.selectbox("팀", TEAM_ORDER, placeholder="팀 선택")
            submitted_add = st.form_submit_button("추가")
            if submitted_add:
                if not new_name or not new_rank or not new_team:
                    st.warning("이름, 직급, 팀을 모두 선택해주세요.")
                elif any(m.get('name') == new_name for m in team_members_list):
                    st.warning("이미 존재하는 팀원입니다.")
                else:
                    team_members_list.append({"name": new_name, "rank": new_rank, "team": new_team})
                    save_data(st.session_state.all_data)
                    st.success(f"'{new_name}' 님을 팀원 목록에 추가했습니다.")
                    st.rerun()
        
        st.write("---")
        st.write("**팀원 정보 수정**")
        if team_members_list:
            member_names = [m['name'] for m in team_members_list]
            member_to_edit_name = st.selectbox("수정할 팀원 선택", member_names, placeholder="팀원 선택", index=None)
            if member_to_edit_name:
                member_to_edit_index = member_names.index(member_to_edit_name)
                member_data = team_members_list[member_to_edit_index]
                
                with st.form(f"edit_{member_to_edit_name}"):
                    edited_name = st.text_input("이름 수정", value=member_data['name'])
                    edited_rank = st.selectbox("직급 수정", RANK_ORDER, index=RANK_ORDER.index(member_data['rank']))
                    edited_team = st.selectbox("팀 수정", TEAM_ORDER, index=TEAM_ORDER.index(member_data['team']))
                    submitted_edit = st.form_submit_button("수정 완료")
                    if submitted_edit:
                        is_name_changed = edited_name != member_to_edit_name
                        is_name_duplicated = any(m['name'] == edited_name for m in team_members_list if m['name'] != member_to_edit_name)
                        if is_name_changed and is_name_duplicated: st.error("이미 존재하는 이름입니다.")
                        else:
                            if is_name_changed:
                                for week_id, week_data in st.session_state.all_data['plans'].items():
                                    if member_to_edit_name in week_data: week_data[edited_name] = week_data.pop(member_to_edit_name)
                            
                            team_members_list[member_to_edit_index] = {"name": edited_name, "rank": edited_rank, "team": edited_team}
                            save_data(st.session_state.all_data)
                            st.success(f"'{edited_name}' 님의 정보가 수정되었습니다."); st.rerun()

        st.write("---")
        st.write("**기존 팀원 영구 삭제**")
        if team_members_list:
            member_to_delete_permanently = st.selectbox("영구 삭제할 팀원 선택", member_names, placeholder="팀원 선택", index=None, key="delete_permanent_select")
            if st.button("선택한 팀원 영구 삭제", type="primary"):
                if member_to_delete_permanently:
                    st.session_state.requesting_password_for_permanent_delete = member_to_delete_permanently
                    st.rerun()
                else:
                    st.warning("삭제할 팀원을 선택해주세요.")

# --- 메인 페이지 UI ---
title_cols = st.columns([3, 1])
with title_cols[0]:
    st.title("Weekly Sync-Up🪄")
with title_cols[1]:
    if st.button("📄 현재 뷰 PDF로 저장", type="primary", use_container_width=True):
        if not os.path.exists(FONT_FILE):
            st.error(f"PDF 생성 오류: '{FONT_FILE}' 폰트 파일을 찾을 수 없습니다.")
        else:
            selected_year = st.session_state.selected_date.isocalendar().year
            selected_week = st.session_state.selected_date.isocalendar().week
            current_week_id_for_pdf = get_week_id(selected_year, selected_week)
            prev_date_for_pdf = st.session_state.selected_date - timedelta(weeks=1)
            prev_week_dates = get_week_dates(prev_date_for_pdf)
            pdf_data = generate_pdf(st.session_state.all_data['plans'].get(current_week_id_for_pdf, {}), st.session_state.all_data.get('team_members', []), selected_year, selected_week, get_week_dates(st.session_state.selected_date), prev_week_dates, ['월', '화', '수', '목', '금'], TEAM_ORDER)
            st.download_button("✅ PDF 다운로드 준비 완료", pdf_data, f"weekly_plan_{current_week_id_for_pdf}.pdf", "application/pdf")

st.markdown("---")

top_cols = st.columns([3, 2])
selected_year = st.session_state.selected_date.isocalendar().year
selected_week = st.session_state.selected_date.isocalendar().week
current_week_id = get_week_id(selected_year, selected_week)

with top_cols[0]:
    st.subheader("주차 선택")
    nav_cols = st.columns([1, 2, 1])
    if nav_cols[0].button("◀ 지난주", use_container_width=True):
        st.session_state.selected_date -= timedelta(weeks=1); st.rerun()
    nav_cols[1].markdown(f"<h3 style='text-align: center; margin-top: 0.5rem;'>{selected_year}년 {selected_week}주차</h3>", unsafe_allow_html=True)
    if nav_cols[2].button("다음주 ▶", use_container_width=True):
        st.session_state.selected_date += timedelta(weeks=1); st.rerun()

with top_cols[1]:
    with st.expander("이번 주 보고서 추가", expanded=True):
        team_members_list = st.session_state.all_data.get('team_members', [])
        reports_this_week = st.session_state.all_data['plans'].get(current_week_id, {}).keys()
        members_to_add = [m for m in team_members_list if m.get('name') not in reports_this_week]
        
        if members_to_add:
            member_to_add_name = st.selectbox("보고서를 추가할 팀원 선택", [m['name'] for m in members_to_add], placeholder="팀원 선택", index=None)
            if st.button("선택한 팀원 보고서 생성", use_container_width=True):
                if member_to_add_name:
                    if current_week_id not in st.session_state.all_data['plans']: st.session_state.all_data['plans'][current_week_id] = {}
                    st.session_state.all_data['plans'][current_week_id][member_to_add_name] = {}
                    save_data(st.session_state.all_data); st.rerun()
                else:
                    st.warning("보고서를 추가할 팀원을 선택해주세요.")
        else:
            st.info("모든 팀원이 이번 주 보고서를 추가했습니다.")

st.markdown("---")

# --- 팝업 및 삭제 확인 로직 ---
if 'initial_popup_shown' not in st.session_state:
    today = datetime.now()
    st.toast(f"{today.isocalendar().year}년 {today.isocalendar().week+1}주차 계획을 작성해주세요.", icon="🗓️")
    st.session_state.initial_popup_shown = True

if 'requesting_password_for_report_delete' in st.session_state:
    member_to_delete = st.session_state.requesting_password_for_report_delete
    st.warning(f"'{member_to_delete}' 님의 이번 주 보고서를 삭제하려면 비밀번호를 입력하세요.")
    with st.form("password_form_report"):
        password = st.text_input("비밀번호", type="password")
        if st.form_submit_button("확인"):
            if password == DELETE_PASSWORD: del st.session_state.requesting_password_for_report_delete; st.session_state.confirming_delete = member_to_delete; st.rerun()
            else: st.error("비밀번호가 올바르지 않습니다.")
elif 'requesting_password_for_permanent_delete' in st.session_state:
    member_to_delete = st.session_state.requesting_password_for_permanent_delete
    st.warning(f"'{member_to_delete}' 님을 영구적으로 삭제하려면 비밀번호를 입력하세요.")
    with st.form("password_form_permanent"):
        password = st.text_input("비밀번호", type="password")
        if st.form_submit_button("확인"):
            if password == DELETE_PASSWORD: del st.session_state.requesting_password_for_permanent_delete; st.session_state.confirming_permanent_delete = member_to_delete; st.rerun()
            else: st.error("비밀번호가 올바르지 않습니다.")
elif 'confirming_delete' in st.session_state:
    member_to_delete = st.session_state.confirming_delete
    st.warning(f"**⚠️ 확인: '{member_to_delete}' 님의 이번 주({selected_year}년 {selected_week}주차) 보고서를 삭제하시겠습니까?**")
    confirm_cols = st.columns(8)
    if confirm_cols[0].button("예, 삭제합니다.", type="primary"):
        if current_week_id in st.session_state.all_data['plans'] and member_to_delete in st.session_state.all_data['plans'][current_week_id]:
            del st.session_state.all_data['plans'][current_week_id][member_to_delete]
            save_data(st.session_state.all_data)
        del st.session_state.confirming_delete; st.rerun()
    if confirm_cols[1].button("아니오"):
        del st.session_state.confirming_delete; st.rerun()
elif 'confirming_permanent_delete' in st.session_state:
    member_to_delete = st.session_state.confirming_permanent_delete
    st.error(f"**🚨 최종 확인: '{member_to_delete}' 님을 팀원 목록과 모든 계획에서 영구적으로 삭제합니다. 계속하시겠습니까?**")
    confirm_cols = st.columns(8)
    if confirm_cols[0].button("예, 영구 삭제합니다.", type="primary"):
        st.session_state.all_data['team_members'] = [m for m in st.session_state.all_data.get('team_members', []) if m.get('name') != member_to_delete]
        for week_data in st.session_state.all_data['plans'].values():
            if member_to_delete in week_data: del week_data[member_to_delete]
        save_data(st.session_state.all_data)
        del st.session_state.confirming_permanent_delete; st.rerun()
    if confirm_cols[1].button("취소"):
        del st.session_state.confirming_permanent_delete; st.rerun()

# --- 메인 계획표 렌더링 ---
else:
    members_with_reports_this_week = st.session_state.all_data['plans'].get(current_week_id, {}).keys()
    for team_name in TEAM_ORDER:
        all_team_members = st.session_state.all_data.get('team_members', [])
        team_members_in_group = [m for m in all_team_members if isinstance(m, dict) and m.get('team') == team_name and m.get('name') in members_with_reports_this_week]
        team_members_in_group.sort(key=lambda m: RANK_ORDER.index(m.get('rank', '기타')) if m.get('rank') in RANK_ORDER else len(RANK_ORDER))
        if not team_members_in_group: continue

        st.title(f"<{team_name}>")
        for member_data in team_members_in_group:
            member_name = member_data.get('name')
            if not member_name: continue
            
            member_info_cols = st.columns([4, 1])
            with member_info_cols[0]:
                member_info = f"[{member_data.get('team', '')}] {member_name} {member_data.get('rank', '')}"
                st.subheader(member_info)
            with member_info_cols[1]:
                if st.button("보고서 삭제", key=f"delete_btn_{member_name}", type="secondary"):
                    st.session_state.requesting_password_for_report_delete = member_name; st.rerun()

            member_plan = st.session_state.all_data['plans'][current_week_id][member_name]
            if 'grid' not in member_plan: member_plan['grid'] = {}
            if 'lastWeekGrid' not in member_plan or 'lastWeekReview' not in member_plan:
                prev_date = st.session_state.selected_date - timedelta(weeks=1)
                prev_week_id = get_week_id(prev_date.isocalendar().year, prev_date.isocalendar().week)
                prev_plans = st.session_state.all_data['plans'].get(prev_week_id, {})
                prev_member_plan = prev_plans.get(member_name, {})
                member_plan['lastWeekGrid'] = prev_member_plan.get('grid', {})
                member_plan['lastWeekReview'] = prev_member_plan.get('nextWeekPlan', "")
            
            def render_grid(title, grid_data, key_prefix, header_class, dates, is_editable=True):
                st.markdown(f"<h6>{title}</h6>", unsafe_allow_html=True)
                day_cols = st.columns(5)
                days, day_names = ['mon', 'tue', 'wed', 'thu', 'fri'], ['월', '화', '수', '목', '금']
                for i, day in enumerate(days):
                    with day_cols[i]:
                        st.markdown(f"<div class='header-base {header_class} header-day'><b>{day_names[i]}({dates[i]})</b></div>", unsafe_allow_html=True)
                        st.markdown("<p class='mobile-label'>오전</p>", unsafe_allow_html=True)
                        grid_data[f'{day}_am'] = st.text_area(f"{key_prefix}_{member_name}_{day}_am_{current_week_id}", value=grid_data.get(f'{day}_am', ''), height=120, disabled=not is_editable)
                        st.markdown("<p class='mobile-label'>오후</p>", unsafe_allow_html=True)
                        grid_data[f'{day}_pm'] = st.text_area(f"{key_prefix}_{member_name}_{day}_pm_{current_week_id}", value=grid_data.get(f'{day}_pm', ''), height=120, disabled=not is_editable)

            week_dates = get_week_dates(st.session_state.selected_date)
            render_grid("이번주 계획", member_plan['grid'], "grid", "header-default", week_dates)
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            
            prev_date = st.session_state.selected_date - timedelta(weeks=1)
            last_week_dates = get_week_dates(prev_date)
            if 'lastWeekGrid' not in member_plan: member_plan['lastWeekGrid'] = {}
            render_grid("지난주 업무 내역 (수정 가능)", member_plan['lastWeekGrid'], "last_grid", "header-automated", last_week_dates)

            def render_summary_row(label, key, placeholder, is_auto, height=140):
                header_class = "header-automated" if is_auto else "header-default"
                cols = st.columns([0.2, 0.8])
                cols[0].markdown(f"<div class='header-base {header_class} header-summary'><b>{label}</b></div>", unsafe_allow_html=True)
                member_plan[key] = cols[1].text_area(f"{key}_{member_name}_{current_week_id}", value=member_plan.get(key, ""), placeholder=placeholder, height=height)

            st.markdown("<div style='margin-top: -8px;'></div>", unsafe_allow_html=True)
            render_summary_row("지난주 리뷰 (수정 가능)", "lastWeekReview", "지난주 차주 계획을 작성하지 않아 연동되지 않았습니다.", True)
            render_summary_row("차주 계획", "nextWeekPlan", "다음 주 계획을 구체적으로 작성해주세요. (주요 목표, 예상 산출물, 협업 계획 등)", False)
            render_summary_row("본인 리뷰", "selfReview", "스스로에 대한 리뷰 및 이슈, 건의사항을 편하게 작성해주세요.", False)
            render_summary_row("부서장 리뷰", "managerReview", "이번 한 주도 고생 많으셨습니다.🚀", False)
            
            # --- 개별 저장 버튼 복원 ---
            save_button_placeholder = st.empty()
            if save_button_placeholder.button(f"💾 {member_name}님의 작성 내용 저장", key=f"save_btn_{member_name}", use_container_width=True, type="primary"):
                save_data(st.session_state.all_data)
                save_button_placeholder.success("✅ 저장 완료!")
                time.sleep(1)
                st.rerun()

            st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)
