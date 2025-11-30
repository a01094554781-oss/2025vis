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
    page_icon="🎆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'festival.CSV')

    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            return pd.DataFrame()

    # 1. 컬럼명 소문자 변환 및 공백 제거
    df.columns = df.columns.str.replace(' ', '').str.strip().str.lower()

    # 2. 컬럼 매핑 (User csv -> Code variable)
    rename_map = {
        'state': 'region', 'festivalname': 'name', 'festivaltype': 'category',
        'startmonth': 'month', 'foreigner': 'visitors', 'venue': 'place'
    }
    df = df.rename(columns=rename_map)

    # 3. 필수 데이터 전처리
    if 'visitors' in df.columns:
        df['visitors'] = df['visitors'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors'] = 0
        
    if 'month' in df.columns:
        df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)
    else:
        df['month'] = 0

    # 4. 구글 검색 링크 생성
    df['link'] = "https://www.google.com/search?q=" + df['name'].astype(str) + "+축제"

    return df

# 좌표 데이터
LAT_LON_DICT = {
    '서울': [37.5665, 126.9780], '부산': [35.1796, 129.0756], '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052], '광주': [35.1595, 126.8526], '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114], '세종': [36.4800, 127.2890], '경기': [37.4138, 127.5183],
    '강원': [37.8228, 128.1555], '충북': [36.6350, 127.4914], '충남': [36.5184, 126.8000],
    '전북': [35.7175, 127.1530], '전남': [34.8161, 126.4629], '경북': [36.5760, 128.5056],
    '경남': [35.2383, 128.6925], '제주': [33.4890, 126.4983]
}

REGION_EN_DICT = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', 
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', 
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam', 
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', 
    '제주': 'Jeju'
}

# 데이터 로딩 실행
try:
    df = load_data()
    if not df.empty and 'region' in df.columns:
        df['region_short'] = df['region'].astype(str).str[:2]
        df['lat_base'] = df['region_short'].map(lambda x: LAT_LON_DICT.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df['region_short'].map(lambda x: LAT_LON_DICT.get(x, [36.5, 127.5])[1])
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.04, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.04, len(df))
        df['region_en'] = df['region_short'].map(REGION_EN_DICT).fillna(df['region'])
        
        # 지도 점 크기 (로그 스케일)
        df['size_scale'] = np.log1p(df['visitors']) + 3 
    else:
        st.error("Data Error: CSV structure mismatch.")
        st.stop()
except Exception as e:
    st.error(f"Critical Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 🧠 AI 가이드 로직
# ---------------------------------------------------------
def get_smart_response(user_input, dataframe, lang='en'):
    user_input = user_input.lower()
    
    # 1. 지역 찾기
    found_region = None
    target_df = dataframe.copy() 
    
    for kor, eng in REGION_EN_DICT.items():
        if eng.lower() in user_input or kor in user_input:
            target_df = target_df[target_df['region_en'] == eng]
            found_region = eng
            break
            
    # 2. 카테고리 찾기
    found_cat = None
    for cat in dataframe['category'].unique():
        if str(cat).lower() in user_input:
            target_df = target_df[target_df['category'] == cat]
            found_cat = cat
            break

    # 3. 결과 도출
    if not target_df.empty:
        pick = target_df.sort_values('visitors', ascending=False).iloc[0]
        visit_fmt = f"{pick['visitors']:,}"
        
        if lang == 'en':
            return f"""
            🤖 **Recommendation based on 2025 Data**
            
            🎉 **{pick['name']}**
            - 📍 **Location:** {pick['region_en']} ({pick['place']})
            - 🗓️ **Month:** {pick['month']}
            - 🎨 **Type:** {pick['category']}
            - 👥 **Foreign Visitors:** {visit_fmt}
            """
        else:
            return f
