import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="K-Festival Guide 2025",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 다국어 UI 텍스트 설정
# ---------------------------------------------------------
UI_TEXT = {
    'ko': {
        'title': "🇰🇷 2025 한국 지역축제 지도",
        'subtitle': "**{}월**에 열리는 **{}개**의 축제를 발견해보세요!",
        'sidebar_title': "🔍 축제 찾기",
        'filter_month': "언제 가시나요? (월)",
        'filter_region': "어디로 갈까요? (지역)",
        'filter_cat': "어떤 축제를 좋아하세요?",
        'tab_map': "🗺️ 축제 지도",
        'tab_list': "📋 리스트",
        'tab_rank': "🏆 외국인 인기 순위",
        'tab_season': "🌸 계절별 추천",
        'tab_ai': "🤖 AI 가이드",
        'metric_total': "검색된 축제",
        'metric_region': "선택된 지역",
        'metric_pop': "인기 1위 (외국인)",
        'no_data': "조건에 맞는 축제가 없습니다.",
        'chart_title': "외국인이 가장 많이 찾은 축제 Top 10",
        'ai_hello': "안녕하세요! 한국 축제에 대해 무엇이든 물어보세요.",
        'ai_placeholder': "예: 서울에서 열리는 음식 축제 추천해줘",
        'season_spring': "🌱 봄 (3~5월)",
        'season_summer': "🌊 여름 (6~8월)",
        'season_autumn': "🍁 가을 (9~11월)",
        'season_winter': "☃️ 겨울 (12~2월)",
        'col_region': '지역',
        'col_name': '축제명',
        'all': '전체'
    },
    'en': {
        'title': "🇰🇷 K-Festival Info Map 2025",
        'subtitle': "Discover **{}** festivals in **{}**!",
        'sidebar_title': "🔍 Festival Finder",
        'filter_month': "When to visit? (Month)",
        'filter_region': "Where to go? (Region)",
        'filter_cat': "What do you like? (Category)",
        'tab_map': "🗺️ Map View",
        'tab_list': "📋 List View",
        'tab_rank': "🏆 Top 10 (Foreigners)",
        'tab_season': "🌸 Seasonal Picks",
        'tab_ai': "🤖 AI Guide",
        'metric_total': "Festivals Found",
        'metric_region': "Selected Region",
        'metric_pop': "Most Popular",
        'no_data': "No festivals found matching your criteria.",
        'chart_title': "Most Popular Festivals Among Foreigners",
        'ai_hello': "Hello! I'm your K-Festival Guide. Ask me anything!",
        'ai_placeholder': "Ex: Recommend a food festival in Seoul",
        'season_spring': "🌱 Spring",
        'season_summer': "🌊 Summer",
        'season_autumn': "🍁 Autumn",
        'season_winter': "☃️ Winter",
        'col_region': 'Region',
        'col_name': 'Festival Name',
        'all': 'All'
    }
}

# ---------------------------------------------------------
# 3. 데이터 로드 및 전처리 (안전한 버전)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'festival.CSV')

    # 파일 읽기
    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except FileNotFoundError:
            # 파일이 없으면 빈 데이터프레임 반환 (에러 방지)
            return pd.DataFrame(), "", ""

    # 컬럼명 정리
    df.columns = df.columns.str.replace(' ', '').str.strip()

    # 방문객 수 전처리
    target_col = '외국인(명)' if '외국인(명)' in df.columns else '외국인'
    if target_col in df.columns:
        df['visitors_foreign'] = df[target_col].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors_foreign'] = pd.to_numeric(df['visitors_foreign'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors_foreign'] = 0

    # 월 전처리
    if '시작월' in df.columns:
        df['month'] = pd.to_numeric(df['시작월'], errors='coerce').fillna(0).astype(int)
    elif '시작일' in df.columns:
