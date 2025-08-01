import streamlit as st
import json
from datetime import datetime, timedelta
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
import pandas as pd
import time # 저장 피드백을 위한 라이브러리 추가

# --- 초기 설정 및 페이지 구성 ---
st.set_page_config(layout="wide", page_title="Weekly")

# --- CSS 스타일링 (변경 없음) ---
st.markdown("""
<style>
    /* ... (기존 CSS와 동일) ... */
</style>
""", unsafe_allow_html=True)


# --- 데이터 및 상수 정의 ---
TEAM_ORDER = ["Team종철", "AE/AM", "BDR", "GD", "BSA"]
RANK_ORDER = ["책임", "선임", "대리", "사원", "인턴", "기타"]
FONT_FILE = "NanumGothic.ttf"
DELETE_PASSWORD = "3002"
GOOGLE_SHEET_NAME = "주간업무보고_DB" 

# --- Google Sheets 연결 함수 (변경 없음) ---
@st.cache_resource(ttl=600)
def connect_to_gsheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(GOOGLE_SHEET_NAME)
        members_sheet = spreadsheet.worksheet("team_members")
        plans_sheet = spreadsheet.worksheet("plans")
        return members_sheet, plans_sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"'{GOOGLE_SHEET_NAME}' 이름의 구글 시트를 찾을 수 없습니다. 시트 이름을 확인하거나 새 시트를 만들어주세요.")
        return None, None
    except gspread.exceptions.WorksheetNotFound:
        st.error("구글 시트에서 'team_members' 또는 'plans' 탭을 찾을 수 없습니다. 탭 이름을 확인해주세요.")
        return None, None
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {e}. 'secrets.toml' 파일과 시트 공유 설정을 확인하세요.")
        return None, None

def create_default_data():
    return {
        "team_members": [],
        "plans": {}
    }

# --- 데이터 로딩 함수 (변경 없음) ---
def load_data():
    members_sheet, plans_sheet = connect_to_gsheet()
    if not members_sheet or not plans_sheet:
        st.warning("Google Sheets에 연결할 수 없어 기본 데이터를 표시합니다.")
        return create_default_data()
    try:
        members_records = members_sheet.get_all_records()
        team_members = [{k: (v if v is not None else '') for k, v in record.items()} for record in members_records]
        
        plans_df = pd.DataFrame(plans_sheet.get_all_records())
        plans_data = {}
        if not plans_df.empty:
            if 'week_id' not in plans_df.columns:
                 return {"team_members": team_members, "plans": {}}
            for _, row in plans_df.iterrows():
                week_id = str(row.get('week_id', ''))
                member_name = row.get('member_name', '')
                if not week_id or not member_name: continue
                plan_json_str = row.get('plan_data', '{}')
                if not isinstance(plan_json_str, str) or not plan_json_str.strip():
                    plan_json_str = '{}'
                plan_details = json.loads(plan_json_str)
                if week_id not in plans_data:
                    plans_data[week_id] = {}
                plans_data[week_id][member_name] = plan_details
        return {"team_members": team_members, "plans": plans_data}
    except Exception as e:
        st.warning(f"데이터 로딩 중 오류 발생({e}). 시트의 헤더(name, rank, team 등)가 올바른지 확인하세요.")
        return create_default_data()

# --- !!! 수정됨: 특정 멤버의 데이터만 저장하는 함수 ---
def save_member_plan(week_id, member_name, member_plan):
    """특정 팀원의 특정 주차 계획만 찾아서 업데이트하거나 새로 추가합니다."""
    _, plans_sheet = connect_to_gsheet()
    if not plans_sheet:
        st.error("데이터 저장 실패: 'plans' 시트에 연결할 수 없습니다.")
        return False

    try:
        # 전체 데이터를 DataFrame으로 변환 (gspread의 find보다 빠름)
        all_plans_df = pd.DataFrame(plans_sheet.get_all_records())
        plan_json_str = json.dumps(member_plan, ensure_ascii=False)

        # 업데이트할 행 찾기
        if not all_plans_df.empty:
            row_index_list = all_plans_df.index[
                (all_plans_df['week_id'].astype(str) == str(week_id)) & 
                (all_plans_df['member_name'] == member_name)
            ].tolist()
        else:
            row_index_list = []

        if row_index_list:
            # 행이 존재하면 해당 셀 업데이트 (gspread는 1-based index, 헤더 포함 +2)
            gspread_row_index = row_index_list[0] + 2
            # 'plan_data'는 3번째 열
            plans_sheet.update_cell(gspread_row_index, 3, plan_json_str)
        else:
            # 행이 없으면 새로 추가
            plans_sheet.append_row([week_id, member_name, plan_json_str])
        
        return True
    except Exception as e:
        st.error(f"'{member_name}'님의 데이터 저장 중 오류 발생: {e}")
        return False

# --- !!! 수정됨: 전체 데이터를 저장하는 함수 (팀원 관리용) ---
def save_all_data(data):
    """팀원 목록 전체를 저장합니다. (팀원 추가/수정/삭제 시에만 사용)"""
    members_sheet, _ = connect_to_gsheet()
    if not members_sheet:
        st.error("팀원 목록 저장 실패: 'team_members' 시트에 연결할 수 없습니다.")
        return
    try:
        members_df = pd.DataFrame(data['team_members'])
        if members_df.empty:
            members_sheet.clear()
            members_sheet.append_row(["name", "rank", "team"])
        else:
            set_with_dataframe(members_sheet, members_df)
    except Exception as e:
        st.error(f"팀원 목록 저장 중 오류 발생: {e}")


# --- PDF 생성 함수 (변경 없음) ---
def generate_pdf(plans_data, members_data, year, week, week_dates, prev_week_dates, day_names, team_order):
    # ... (기존 PDF 생성 코드와 동일)
    pass

# --- 세션 상태 초기화 ---
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now()

# --- 유틸리티 함수 (변경 없음) ---
def get_week_id(year, week): return f"{year}-W{str(week).zfill(2)}"
def get_week_dates(date_obj):
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    return [(start_of_week + timedelta(days=i)).strftime("%m/%d") for i in range(5)]

# --- 사이드바 ---
with st.sidebar:
    st.title("메뉴")
    st.markdown("---")
    
    # 과거 기록 조회 (변경 없음)
    # ...
    
    st.markdown("---")
    with st.expander("팀원 목록 관리", expanded=True):
        team_members_list = st.session_state.all_data.get('team_members', [])
        
        st.write("**신규 팀원 추가**")
        with st.form("add_member_form", clear_on_submit=True):
            # ... (기존 폼과 동일)
            submitted_add = st.form_submit_button("추가")
            if submitted_add:
                # ... (기존 로직과 동일)
                # --- !!! 수정: save_all_data 호출 ---
                save_all_data(st.session_state.all_data)
                st.success(f"'{new_name}' 님을 팀원 목록에 추가했습니다.")
                st.rerun()
        
        st.write("---")
        st.write("**팀원 정보 수정**")
        if team_members_list:
            # ... (기존 로직과 동일)
            # --- !!! 수정: save_all_data 호출 ---
            # ...
            #       save_all_data(st.session_state.all_data)
            #       st.success(f"'{edited_name}' 님의 정보가 수정되었습니다.")
            #       st.rerun()

        st.write("---")
        st.write("**기존 팀원 영구 삭제**")
        # ... (기존 로직과 동일)


# --- 메인 페이지 UI ---
# ... (기존 UI와 동일)


# --- 비밀번호 입력 및 삭제 확인 로직 ---
# ... (기존 로직과 동일)
# --- !!! 수정: 보고서 삭제 시 save_member_plan 대신 전체 plans를 다시 저장해야 함 ---
# ...
#   del st.session_state.all_data['plans'][current_week_id][member_to_delete]
#   # 이 부분은 전체 plans를 다시 저장하는 것이 더 간단하고 안전함
#   save_all_data(st.session_state.all_data) 
# ...


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
            
            # ... (기존 정보 표시 로직과 동일)

            member_plan = st.session_state.all_data['plans'][current_week_id][member_name]
            
            # ... (render_grid, render_summary_row 등 기존 렌더링 함수 호출은 동일)

            # --- !!! 신규: 개인별 저장 버튼 추가 ---
            st.markdown("<div style='text-align: right; margin-top: 1rem;'></div>", unsafe_allow_html=True)
            save_button_placeholder = st.empty()
            
            if save_button_placeholder.button(f"💾 {member_name}님 계획 저장", key=f"save_btn_{member_name}_{current_week_id}", use_container_width=True, type="primary"):
                success = save_member_plan(current_week_id, member_name, member_plan)
                if success:
                    # 성공 메시지를 잠시 보여주고 버튼을 다시 활성화
                    save_button_placeholder.success("✅ 저장 완료!")
                    time.sleep(2)
                    save_button_placeholder.empty() # 메시지 지우기 (버튼이 다시 나타남)
                    st.rerun() # 최신 데이터로 화면 갱신

            st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)

    # --- !!! 삭제: 스크립트 마지막의 전체 저장 로직 ---
    # save_data(st.session_state.all_data) # 이 줄을 삭제하거나 주석 처리
