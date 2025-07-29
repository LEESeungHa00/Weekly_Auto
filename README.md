<p align="center">
 <em> #Weekly Sync-Up 🪄 </em>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python" alt="Python Version">
<img src="https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b?style=for-the-badge&logo=streamlit" alt="Streamlit Version">
<img src="https://img.shields.io/badge/Made%20for-Agile%20Teams-764ABC?style=for-the-badge&logo=slack" alt="For Agile Teams">
</p>

<p align="center">
<em>"구글 시트의 수동 복붙과 충돌 지옥에서 벗어나, 우리 팀의 주간 동기화를 자동화하세요."</em>
</p>

</p>

🤔**Why This Project?**

기존의 공유 문서(Google Docs/Sheet) 기반 주간 보고 방식은 여러 문제를 야기했습니다.

수동 복붙의 늪: 매주 지난주 계획을 이번 주 리뷰로 옮기는 반복적이고 실수하기 쉬운 작업.

데이터 충돌: 여러 명이 동시에 수정할 때 발생하는 내용 유실 및 충돌.

버전 관리의 어려움: 매주 새로운 파일을 생성하고 관리해야 하는 번거로움.

불필요한 커뮤니케이션: 사소한 양식 변경이나 요청사항으로 인한 커뮤니케이션 비용 증가.

이러한 비효율을 해결하고, 팀이 핵심 업무에만 집중할 수 있도록 돕는 자동화 툴을 만들었습니다.

✨ Key Features
🔄 **자동 데이터 연동**: 버튼 하나로 지난주 계획이 이번 주 리뷰로, 차주 계획이 다음 주 리뷰로 자동 연동됩니다.

👥 **팀/직급별 정렬 뷰**: 팀별, 그리고 팀 내 직급 순으로 보고서가 자동 정렬되어 가독성과 체계성을 극대화했습니다.

📄 **원클릭 PDF 보고서**: 현재 보고 있는 주차의 모든 내용을 클릭 한 번으로 깔끔한 PDF 파일로 다운로드할 수 있습니다.

🗓️ **직관적인 UI/UX:** 복잡한 메뉴를 없애고, 현재 주차에 집중하면서도 사이드바를 통해 과거 기록을 쉽게 조회할 수 있습니다.

💾 **영구 데이터 저장**: 모든 내용은 plans_data.json 파일에 안전하게 저장되어 언제든지 다시 작업을 이어갈 수 있습니다.

🤖 **슬랙 알림 자동화:** GitHub Actions를 통해 매주 금요일, 지정된 슬랙 채널로 주간 보고 작성 알림을 자동으로 보냅니다.

🛠️ Tech Stack
Core: Python, Streamlit

Data: JSON

PDF Export: FPDF2

Automation: GitHub Actions

🚀 **Getting Started**
1. 로컬에서 실행하기
Prerequisites:

Python 3.9 이상

NanumGothic.ttf 폰트 파일 (PDF 한글 지원)

# 1. 저장소를 복제합니다.
git clone https://github.com/your-username/weekly-sync-up.git
cd weekly-sync-up

# 2. 필요한 라이브러리를 설치합니다.
pip install -r requirements.txt

# 3. 나눔고딕 폰트 파일을 프로젝트 폴더에 다운로드합니다.
 https://hangeul.naver.com/font

# 4. Streamlit 앱을 실행합니다.
streamlit run app.py

2. Streamlit Community Cloud에 배포하기
이 저장소를 당신의 GitHub 계정으로 Fork 하세요.

Streamlit Community Cloud에 GitHub 계정으로 로그인합니다.

'New app' 버튼을 클릭하고, Fork한 저장소를 선택하세요.

배포가 완료되면 팀원들과 공유할 수 있는 영구적인 URL이 생성됩니다.

중요: requirements.txt 파일에 streamlit과 fpdf2가 포함되어 있는지, NanumGothic.ttf 폰트 파일이 저장소에 함께 업로드되었는지 반드시 확인하세요!

🤖 **Slack Notification Setup**
- Slack Incoming Webhooks를 통해 Webhook URL을 발급받으세요.

- 당신의 GitHub 저장소 > Settings > Secrets and variables > Actions 로 이동합니다.

- New repository secret 버튼을 눌러, 이름은 SLACK_WEBHOOK_URL 로, 값은 위에서 발급받은 Webhook URL로 저장하세요.

- .github/workflows/slack_notifier.yml 파일이 매주 금요일 오전 10시에 자동으로 알림을 보냅니다.
