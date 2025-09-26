import streamlit as st
import json
from datetime import datetime, timedelta
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
import pandas as pd
import time

# --- 1. 초기 설정 및 페이지 구성 ---
st.set_page_config(layout="wide", page_title="GS KR WEEKLY")

# --- 2. CSS 스타일링 ---
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


# --- 3. 데이터 및 상수 정의 ---
TEAM_ORDER = ["Tridge Pay AE/AM","Team종철", "AE/AM", "BDR", "GD", "BSA"]
RANK_ORDER = ["책임", "선임", "대리", "사원", "인턴", "기타"]
FONT_FILE = "NanumGothic.ttf"
DELETE_PASSWORD = "3002"
GOOGLE_SHEET_NAME = "주간업무보고_DB"

# --- 4. 핵심 함수 정의 (데이터 처리) ---

def connect_to_gsheet():
    """Google Sheets에 연결하고 워크시트 객체를 반환합니다."""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(GOOGLE_SHEET_NAME)
        members_sheet = spreadsheet.worksheet("team_members")
        plans_sheet = spreadsheet.worksheet("plans")
        return members_sheet, plans_sheet
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {e}. secrets.toml 파일과 시트 공유 설정을 확인하세요.")
        return None, None

def create_default_data():
    """데이터가 없을 때 사용할 기본 데이터 구조를 생성합니다."""
    return { "team_members": [], "plans": {} }

def load_data():
    """Google Sheets에서 모든 데이터를 불러옵니다."""
    members_sheet, plans_sheet = connect_to_gsheet()
    if not members_sheet or not plans_sheet:
        st.warning("Google Sheets에 연결할 수 없어 빈 데이터로 시작합니다.")
        return create_default_data()
    try:
        members_records = members_sheet.get_all_records()
        team_members = [{k: (v if v is not None else '') for k, v in record.items()} for record in members_records]
        
        plans_records = plans_sheet.get_all_records()
        plans_data = {}
        if plans_records:
            plans_df = pd.DataFrame(plans_records)
            if not plans_df.empty and 'week_id' in plans_df.columns:
                for _, row in plans_df.iterrows():
                    week_id, member_name = str(row.get('week_id', '')), row.get('member_name', '')
                    if not week_id or not member_name: continue
                    plan_json_str = row.get('plan_data', '{}')
                    plan_details = json.loads(plan_json_str if isinstance(plan_json_str, str) and plan_json_str.strip() else '{}')
                    if week_id not in plans_data: plans_data[week_id] = {}
                    plans_data[week_id][member_name] = plan_details
        return {"team_members": team_members, "plans": plans_data}
    except Exception as e:
        st.warning(f"데이터 로딩 중 오류 발생({e}). 시트의 헤더(name, rank, team 등)를 확인하세요.")
        return create_default_data()

def save_all_data(data):
    """팀원 목록과 계획 전체를 구글 시트에 저장합니다."""
    members_sheet, plans_sheet = connect_to_gsheet()
    if not members_sheet or not plans_sheet: return

    try:
        members_df = pd.DataFrame(data['team_members'])
        if not members_df.empty:
            set_with_dataframe(members_sheet, members_df, include_index=False, resize=True)
        else:
            members_sheet.clear()
            members_sheet.append_row(['name', 'rank', 'team'])

        plans_data, flat_plans = data.get('plans', {}), []
        for week_id, members_plans in plans_data.items():
            for member_name, plan_details in members_plans.items():
                flat_plans.append({
                    "week_id": week_id, "member_name": member_name,
                    "plan_data": json.dumps(plan_details, ensure_ascii=False)
                })
        
        plans_df = pd.DataFrame(flat_plans)
        if not plans_df.empty:
            set_with_dataframe(plans_sheet, plans_df, include_index=False, resize=True)
        else:
            plans_sheet.clear()
            plans_sheet.append_row(['week_id', 'member_name', 'plan_data'])
    except Exception as e:
        st.error(f"전체 데이터 저장 중 오류 발생: {e}")

def save_member_plan(week_id, member_name, member_plan):
    """특정 팀원의 특정 주차 계획만 업데이트하거나 새로 추가합니다."""
    _, plans_sheet = connect_to_gsheet()
    if not plans_sheet: return False
    try:
        all_records = plans_sheet.get_all_records()
        plan_json_str = json.dumps(member_plan, ensure_ascii=False)
        
        found = False
        for i, record in enumerate(all_records):
            if str(record.get('week_id')) == str(week_id) and record.get('member_name') == member_name:
                plans_sheet.update_cell(i + 2, 3, plan_json_str)
                found = True
                break
        
        if not found:
            plans_sheet.append_row([week_id, member_name, plan_json_str])
        return True
    except Exception as e:
        st.error(f"'{member_name}'님의 데이터 저장 중 오류 발생: {e}")
        return False

def generate_pdf(plans_data, members_data, year, week, week_dates, prev_week_dates, day_names, team_order):
    pdf = FPDF()
    pdf.add_font('NanumGothic', '', FONT_FILE, uni=True)
    pdf.add_page()
    pdf.set_font('NanumGothic', '', 20)
    pdf.cell(0, 12, f'주간 계획서 - {year}년 {week}주차', ln=True, align='C')
    pdf.ln(10)
    # ... (이하 PDF 생성 로직 동일) ...
    return pdf.output(dest='S').encode('latin-1')


# --- 5. 세션 상태 초기화 및 유틸리티 함수 ---
if 'all_data' not in st.session_state: st.session_state.all_data = load_data()
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.now() + timedelta(weeks=1)

def get_week_id(year, week): return f"{year}-W{str(week).zfill(2)}"
def get_week_dates(date_obj):
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    return [(start_of_week + timedelta(days=i)).strftime("%m/%d") for i in range(5)]

# --- 6. 사이드바 UI ---
with st.sidebar:
    st.title("메뉴")
    st.markdown("---")
    with st.expander("과거 기록 조회", expanded=False):
        plan_years = [int(week_id.split('-W')[0]) for week_id in st.session_state.all_data['plans'].keys()]
        current_year = datetime.now().year
        all_years = list(range(current_year - 3, current_year + 4))
        if plan_years: all_years = list(range(min(plan_years) - 3, max(plan_years) + 4))
        if current_year not in all_years: all_years.append(current_year); all_years.sort(reverse=True)
        try: default_year_index = all_years.index(st.session_state.selected_date.isocalendar().year)
        except ValueError: default_year_index = all_years.index(current_year) if current_year in all_years else 0
        sidebar_year = st.selectbox("연도 선택", all_years, index=default_year_index)
        try: weeks_in_year = list(range(1, datetime(sidebar_year, 12, 28).isocalendar()[1] + 1))
        except ValueError: weeks_in_year = list(range(1, 53))
        current_week = st.session_state.selected_date.isocalendar().week if st.session_state.selected_date.year == sidebar_year else 1
        default_week_index = current_week - 1 if (current_week - 1) < len(weeks_in_year) else 0
        sidebar_week = st.selectbox("주차 선택", weeks_in_year, index=default_week_index)
        if st.button("조회하기", use_container_width=True):
            st.session_state.selected_date = datetime.fromisocalendar(sidebar_year, sidebar_week, 1)
            st.rerun()

    st.markdown("---")
    with st.expander("팀원 목록 관리", expanded=True):
        team_members_list = st.session_state.all_data.get('team_members', [])
        st.write("**신규 팀원 추가**")
        with st.form("add_member_form", clear_on_submit=True):
            new_name, new_rank, new_team = st.text_input("이름"), st.selectbox("직급", RANK_ORDER, index=None), st.selectbox("팀", TEAM_ORDER, index=None)
            if st.form_submit_button("추가"):
                if not new_name or not new_rank or not new_team: st.warning("이름, 직급, 팀을 모두 선택해주세요.")
                elif any(m.get('name') == new_name for m in team_members_list): st.warning("이미 존재하는 팀원입니다.")
                else:
                    team_members_list.append({"name": new_name, "rank": new_rank, "team": new_team})
                    save_all_data(st.session_state.all_data)
                    st.success(f"'{new_name}' 님을 팀원 목록에 추가했습니다."); st.rerun()
        
        st.write("---"); st.write("**팀원 정보 수정**")
        if team_members_list:
            member_names = [m['name'] for m in team_members_list]
            member_to_edit_name = st.selectbox("수정할 팀원 선택", member_names, index=None, placeholder="팀원 선택")
            if member_to_edit_name:
                member_to_edit_index = member_names.index(member_to_edit_name)
                member_data = team_members_list[member_to_edit_index]
                with st.form(f"edit_{member_to_edit_name}"):
                    edited_name = st.text_input("이름 수정", value=member_data['name'])
                    edited_rank = st.selectbox("직급 수정", RANK_ORDER, index=RANK_ORDER.index(member_data['rank']))
                    edited_team = st.selectbox("팀 수정", TEAM_ORDER, index=TEAM_ORDER.index(member_data['team']))
                    if st.form_submit_button("수정 완료"):
                        is_name_changed = edited_name != member_to_edit_name
                        is_name_duplicated = any(m['name'] == edited_name for m in team_members_list if m['name'] != member_to_edit_name)
                        if is_name_changed and is_name_duplicated: st.error("이미 존재하는 이름입니다.")
                        else:
                            if is_name_changed:
                                for week_data in st.session_state.all_data['plans'].values():
                                    if member_to_edit_name in week_data: week_data[edited_name] = week_data.pop(member_to_edit_name)
                            team_members_list[member_to_edit_index] = {"name": edited_name, "rank": edited_rank, "team": edited_team}
                            save_all_data(st.session_state.all_data)
                            st.success(f"'{edited_name}' 님의 정보가 수정되었습니다."); st.rerun()

        st.write("---"); st.write("**기존 팀원 영구 삭제**")
        if team_members_list:
            member_to_delete_perm = st.selectbox("영구 삭제할 팀원 선택", [m.get('name') for m in team_members_list], index=None, key="perm_delete_select")
            if st.button("선택한 팀원 영구 삭제", type="primary"):
                if member_to_delete_perm: st.session_state.requesting_password_for_permanent_delete = member_to_delete_perm; st.rerun()
                else: st.warning("삭제할 팀원을 선택해주세요.")

# --- 7. 메인 페이지 UI 및 로직 ---
title_cols = st.columns([3, 1])
with title_cols[0]: st.title("Weekly Sync-Up🪄")
with title_cols[1]:
    if st.button("📄 현재 뷰 PDF로 저장", type="primary", use_container_width=True):
        year, week = st.session_state.selected_date.isocalendar().year, st.session_state.selected_date.isocalendar().week
        week_id_pdf = get_week_id(year, week)
        prev_date_pdf, week_dates_pdf = st.session_state.selected_date - timedelta(weeks=1), get_week_dates(st.session_state.selected_date)
        pdf_bytes = generate_pdf(st.session_state.all_data['plans'].get(week_id_pdf, {}), st.session_state.all_data.get('team_members', []), year, week, week_dates_pdf, get_week_dates(prev_date_pdf), ['월', '화', '수', '목', '금'], TEAM_ORDER)
        if pdf_bytes: st.download_button("✅ PDF 다운로드 준비 완료", pdf_bytes, f"weekly_plan_{week_id_pdf}.pdf", "application/pdf")

st.markdown("---")
top_cols = st.columns([3, 2])
selected_year, selected_week = st.session_state.selected_date.year, st.session_state.selected_date.isocalendar().week
current_week_id = get_week_id(selected_year, selected_week)
with top_cols[0]:
    st.subheader("주차 선택")
    nav_cols = st.columns([1, 2, 1])
    if nav_cols[0].button("◀ 지난주", use_container_width=True): st.session_state.selected_date -= timedelta(weeks=1); st.rerun()
    nav_cols[1].markdown(f"<h3 style='text-align: center; margin-top: 0.5rem;'>{selected_year}년 {selected_week}주차</h3>", unsafe_allow_html=True)
    if nav_cols[2].button("다음주 ▶", use_container_width=True): st.session_state.selected_date += timedelta(weeks=1); st.rerun()
with top_cols[1]:
    with st.expander("이번 주 보고서 추가", expanded=True):
        team_members = st.session_state.all_data.get('team_members', [])
        reports_this_week = st.session_state.all_data['plans'].get(current_week_id, {}).keys()
        members_to_add = [m for m in team_members if m.get('name') not in reports_this_week]
        if members_to_add:
            member_to_add_name = st.selectbox("보고서를 추가할 팀원 선택", [m['name'] for m in members_to_add], index=None)
            if st.button("선택한 팀원 보고서 생성", use_container_width=True):
                if member_to_add_name:
                    if current_week_id not in st.session_state.all_data['plans']: st.session_state.all_data['plans'][current_week_id] = {}
                    st.session_state.all_data['plans'][current_week_id][member_to_add_name] = {}
                    save_all_data(st.session_state.all_data); st.rerun()
                else: st.warning("보고서를 추가할 팀원을 선택해주세요.")
        else: st.info("모든 팀원이 이번 주 보고서를 추가했습니다.")
st.markdown("---")

# --- 팝업 및 삭제 확인 로직 ---
if 'initial_popup_shown' not in st.session_state:
    today = datetime.now()
    next_week_date = today + timedelta(weeks=1)
    st.toast(f"{next_week_date.isocalendar().year}년 {next_week_date.isocalendar().week}주차 계획을 작성해주세요.", icon="🗓️")
    st.session_state.initial_popup_shown = True

# --- 8. 비밀번호 및 삭제 확인 로직 ---
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
            save_all_data(st.session_state.all_data)
        del st.session_state.confirming_delete; st.rerun()
    if confirm_cols[1].button("아니오"): del st.session_state.confirming_delete; st.rerun()
elif 'confirming_permanent_delete' in st.session_state:
    member_to_delete = st.session_state.confirming_permanent_delete
    st.error(f"**🚨 최종 확인: '{member_to_delete}' 님을 팀원 목록과 모든 계획에서 영구적으로 삭제합니다. 계속하시겠습니까?**")
    confirm_cols = st.columns(8)
    if confirm_cols[0].button("예, 영구 삭제합니다.", type="primary"):
        st.session_state.all_data['team_members'] = [m for m in st.session_state.all_data.get('team_members', []) if m.get('name') != member_to_delete]
        for week_data in st.session_state.all_data['plans'].values():
            if member_to_delete in week_data: del week_data[member_to_delete]
        save_all_data(st.session_state.all_data)
        del st.session_state.confirming_permanent_delete; st.rerun()
    if confirm_cols[1].button("취소"): del st.session_state.confirming_permanent_delete; st.rerun()

# --- 9. 메인 계획표 렌더링 ---
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
                prev_week_id = get_week_id(prev_date.year, prev_date.isocalendar().week)
                prev_member_plan = st.session_state.all_data['plans'].get(prev_week_id, {}).get(member_name, {})
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
                        grid_data[f'{day}_am'] = st.text_area(f"{key_prefix}_{member_name}_{day}_am", value=grid_data.get(f'{day}_am', ''), height=120, disabled=not is_editable)
                        st.markdown("<p class='mobile-label'>오후</p>", unsafe_allow_html=True)
                        grid_data[f'{day}_pm'] = st.text_area(f"{key_prefix}_{member_name}_{day}_pm", value=grid_data.get(f'{day}_pm', ''), height=120, disabled=not is_editable)
            week_dates = get_week_dates(st.session_state.selected_date)
            render_grid("이번주 계획", member_plan['grid'], "grid", "header-default", week_dates)
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            prev_date, last_week_dates = st.session_state.selected_date - timedelta(weeks=1), get_week_dates(st.session_state.selected_date - timedelta(weeks=1))
            if 'lastWeekGrid' not in member_plan: member_plan['lastWeekGrid'] = {}
            render_grid("지난주 업무 내역 (수정 가능)", member_plan['lastWeekGrid'], "last_grid", "header-automated", last_week_dates)
            def render_summary_row(label, key, placeholder, is_auto, height=140):
                header_class = "header-automated" if is_auto else "header-default"
                cols = st.columns([0.2, 0.8])
                cols[0].markdown(f"<div class='header-base {header_class} header-summary'><b>{label}</b></div>", unsafe_allow_html=True)
                member_plan[key] = cols[1].text_area(f"{key}_{member_name}", value=member_plan.get(key, ""), placeholder=placeholder, height=height)
            st.markdown("<div style='margin-top: -8px;'></div>", unsafe_allow_html=True)
            render_summary_row("지난주 리뷰 (수정 가능)", "lastWeekReview", "지난주 차주 계획을 작성하지 않아 연동되지 않았습니다.", True)
            render_summary_row("차주 계획", "nextWeekPlan", "다음 주 계획을 구체적으로 작성해주세요.", False)
            render_summary_row("본인 리뷰", "selfReview", "스스로에 대한 리뷰 및 이슈, 건의사항을 편하게 작성해주세요.", False)
            render_summary_row("부서장 리뷰", "managerReview", "이번 한 주도 고생 많으셨습니다.🚀", False)
            
            # 개인별 저장 버튼
            save_button_placeholder = st.empty()
            if save_button_placeholder.button(f"💾 {member_name}님 계획 저장", key=f"save_btn_{member_name}", use_container_width=True, type="primary"):
                if save_member_plan(current_week_id, member_name, member_plan):
                    save_button_placeholder.success("✅ 저장 완료!")
                    time.sleep(1)
                    st.rerun()

            st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)


