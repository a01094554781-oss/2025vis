import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import random

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
# 2. 데이터 로드 (영어 컬럼 적용 버전)
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

    df.columns = df.columns.str.replace(' ', '').str.strip().str.lower()

    # 컬럼 매핑
    rename_map = {
        'state': 'region',
        'festivalname': 'name',
        'festivaltype': 'category',
        'startmonth': 'month',
        'foreigner': 'visitors',
        'venue': 'place'
    }
    df = df.rename(columns=rename_map)

    # 방문객 수 전처리
    if 'visitors' in df.columns:
        df['visitors'] = df['visitors'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors'] = 0
        
    # 월 전처리
    if 'month' in df.columns:
        df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)
    else:
        df['month'] = 0

    return df

# 좌표 및 지역명 매핑 데이터
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
    if df.empty:
        st.error("CSV File Error.")
        st.stop()

    if 'region' in df.columns:
        df['region_short'] = df['region'].astype(str).str[:2]
        df['lat_base'] = df['region_short'].map(lambda x: LAT_LON_DICT.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df['region_short'].map(lambda x: LAT_LON_DICT.get(x, [36.5, 127.5])[1])
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.04, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.04, len(df))
        df['region_en'] = df['region_short'].map(REGION_EN_DICT).fillna(df['region'])
    else:
        st.error("Region column missing.")
        st.stop()

except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 스마트 AI 답변 로직 (데이터 기반 검색)
# ---------------------------------------------------------
def get_smart_response(user_input, dataframe, lang='en'):
    user_input = user_input.lower()
    
    # 1. 지역 검색 (User가 'Seoul'이라고 물어봤을 때)
    found_regions = [r for r in dataframe['region_en'].unique() if r.lower() in user_input]
    
    # 2. 카테고리 검색 (User가 'Food'라고 물어봤을 때)
    found_cats = [c for c in dataframe['category'].unique() if str(c).lower() in user_input]
    
    # 필터링 로직
    filtered_ai = dataframe.copy()
    
    if found_regions:
        filtered_ai = filtered_ai[filtered_ai['region_en'].str.lower() == found_regions[0].lower()]
    
    if found_cats:
        # 부분 일치 검색
        filtered_ai = filtered_ai[filtered_ai['category'].astype(str).str.contains(found_cats[0], case=False)]
    
    # 결과 생성
    if not filtered_ai.empty:
        # 인기순 정렬 후 상위 3개 중 랜덤 추천
        top_picks = filtered_ai.sort_values('visitors', ascending=False).head(5)
        pick = top_picks.sample(1).iloc[0]
        
        if lang == 'en':
            return f"🎉 I found a perfect festival for you!\n\n**[{pick['name']}]**\n- 📍 Location: {pick['region_en']} ({pick['place']})\n- 🎨 Type: {pick['category']}\n- 👥 Visitors: {pick['visitors']:,}\n\nIt matches your interest!"
        else:
            return f"🎉 딱 맞는 축제를 찾았어요!\n\n**[{pick['name']}]**\n- 📍 위치: {pick['region']} ({pick['place']})\n- 🎨 유형: {pick['category']}\n- 👥 방문객: {pick['visitors']:,}명\n\n이 축제 어떠세요?"
            
    else:
        # 검색 결과가 없을 때
        if lang == 'en':
            return "🤔 I couldn't find a specific match in the 2025 database. Try asking for a region (e.g., 'Seoul') or a type (e.g., 'Culture')."
        else:
            return "🤔 2025년 데이터베이스에서 일치하는 정보를 못 찾았어요. 지역명(예: 서울)이나 유형(예: 문화)으로 다시 물어봐주세요!"

# ---------------------------------------------------------
# 4. UI 텍스트 설정
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
        'ai_hello': "안녕하세요! 저는 데이터 기반 AI 가이드입니다. \n'서울 축제 추천해줘' 또는 '음식 축제 있어?' 처럼 물어보세요!",
        'ai_placeholder': "질문 예시: 부산에서 열리는 축제 추천해줘",
        'season_spring': "🌱 봄 (Spring)",
        'season_summer': "🌊 여름 (Summer)",
        'season_autumn': "🍁 가을 (Autumn)",
        'season_winter': "☃️ 겨울 (Winter)",
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
        'ai_hello': "Hello! I'm your Data-driven AI Guide. \nAsk me like 'Recommend festivals in Seoul' or 'Any food festivals?'",
        'ai_placeholder': "Ex: Festivals in Busan",
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
# 5. 사이드바 및 필터링
# ---------------------------------------------------------
lang_option = st.sidebar.radio("🌐 Language / 언어", ["English", "한국어"], horizontal=True)
lang = 'en' if lang_option == "English" else 'ko'
txt = UI_TEXT[lang]

st.sidebar.header(txt['sidebar_title'])

selected_month = st.sidebar.slider(txt['filter_month'], 1, 12, (3, 10))

r_display_col = 'region_en' if lang == 'en' else 'region'
regions = [txt['all']] + sorted(list(df[r_display_col].unique()))
selected_region = st.sidebar.selectbox(txt['filter_region'], regions)

categories = [txt['all']] + list(df['category'].unique())
selected_category = st.sidebar.multiselect(txt['filter_cat'], categories, default=txt['all'])

filtered_df = df[(df['month'] >= selected_month[0]) & (df['month'] <= selected_month[1])]

if selected_region != txt['all']:
    filtered_df = filtered_df[filtered_df[r_display_col] == selected_region]

if txt['all'] not in selected_category and selected_category:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]

# ---------------------------------------------------------
# 6. 메인 대시보드
# ---------------------------------------------------------
st.title(txt['title'])
if lang == 'en':
    st.markdown(txt['subtitle'].format(len(filtered_df), f"{selected_month[0]}~{selected_month[1]} Month"))
else:
    st.markdown(txt['subtitle'].format(f"{selected_month[0]}~{selected_month[1]}", len(filtered_df)))

c1, c2, c3 = st.columns(3)
c1.metric(txt['metric_total'], f"{len(filtered_df)}")
c2.metric(txt['metric_region'], selected_region)
if not filtered_df.empty:
    top_name = filtered_df.sort_values(by='visitors', ascending=False).iloc[0]['name']
    c3.metric(txt['metric_pop'], top_name)

tab1, tab2, tab3, tab4 = st.tabs([txt['tab_map'], txt['tab_rank'], txt['tab_season'], txt['tab_ai']])

# [Tab 1] 지도
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        if not filtered_df.empty:
            st.map(filtered_df, latitude='lat', longitude='lon', color='#FF4B4B', size=20)
        else:
            st.warning(txt['no_data'])
    with col2:
        st.subheader(txt['tab_list'])
        if not filtered_df.empty:
            display_cols = ['name', r_display_col, 'place']
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)

# [Tab 2] 랭킹
with tab2:
    st.subheader(f"🔥 {txt['chart_title']}")
    ranking_df = df[df['visitors'] > 0].sort_values(by='visitors', ascending=False).head(10)
    
    if not ranking_df.empty:
        fig = px.bar(
            ranking_df,
            x='visitors',
            y='name',
            orientation='h',
            text='visitors',
            color='category',
            labels={'visitors': 'Visitors', 'name': txt['col_name']},
            title=txt['chart_title']
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(txt['no_data'])

# [Tab 3] 계절 추천 (풍성해진 버전)
with tab3:
    st.subheader(f"📅 {txt['tab_season']}")
    
    # 계절별 Top 5 추출 함수
    def get_season_top5(months):
        return df[df['month'].isin(months)].sort_values('visitors', ascending=False).head(5)

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    seasons = {txt['season_spring']: [3,4,5], txt['season_summer']: [6,7,8], 
               txt['season_autumn']: [9,10,11], txt['season_winter']: [12,1,2]}
    
    for i, (name, months) in enumerate(seasons.items()):
        # 컬럼 선택
        target_col = [col_s1, col_s2, col_s3, col_s4][i]
        with target_col:
            st.markdown(f"### {name}")
            top_festivals = get_season_top5(months)
            
            for _, row in top_festivals.iterrows():
                # 카드 형태로 보여주기 (Expander 사용)
                with st.expander(f"**{row['name']}**"):
                    st.caption(f"📍 {row[r_display_col]}")
                    st.caption(f"🎨 {row['category']}")
                    st.write(f"👥 {row['visitors']:,}")

# [Tab 4] 스마트 AI 가이드
with tab4:
    st.subheader(txt['tab_ai'])
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": txt['ai_hello']}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input(txt['ai_placeholder']):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # 스마트 답변 함수 호출
        ai_response = get_smart_response(prompt, df, lang)
            
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.chat_message("assistant").write(ai_response)
