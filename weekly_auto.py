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
        background-color: #1c4587; /* Dark Cornflower Blue 3 */
    }
    .header-automated {
        background-color: #741b47; /* Dark Magenta 2 */
    }
    /* 헤더 정렬 문제 수정을 위해 padding과 min-height 사용 */
    .header-day { 
        min-height: 65px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .header-time { height: 120px; }
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
</style>
""", unsafe_allow_html=True)


# --- 데이터 및 상수 정의 ---
DATA_FILE = "plans_data.json"
TEAM_ORDER = ["Team종철", "AE/AM", "BDR", "GD", "BSA"]
RANK_ORDER = ["책임", "선임", "대리", "사원", "인턴", "기타"] # 직급 정렬 순서
FONT_FILE = "NanumGothic.ttf"

def load_data():
    """JSON 파일에서 모든 데이터를 불러옵니다."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
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

            # 이번주 계획 그리드
            pdf.set_font('NanumGothic', '
