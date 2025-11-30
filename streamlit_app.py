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
# 2. 데이터 로드 (오류 원천 차단)
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

    # 2. [중요] 컬럼명 강제 매핑 (사용자 파일 기준)
    # 파일의 'foreigner' 컬럼을 'visitors'로 명확하게 바꿉니다.
    rename_map = {
        'state': 'region',
        'festivalname': 'name',
        'festivaltype': 'category',
        'startmonth': 'month',
        'foreigner': 'visitors',  # 여기서 visitors 정의
        'venue': 'place'
    }
    df = df.rename(columns=rename_map)

    # 3. 필수 컬럼이 없으면 생성 (에러 방지)
    required_cols = ['name', 'category', 'region', 'month', 'visitors', 'place']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col in ['month', 'visitors'] else 'Unknown'

    # 4. 데이터 타입 변환
    # 방문객 수 (쉼표 제거 후 숫자 변환)
    df['visitors'] = df['visitors'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
    df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    
    # 월 (숫자 변환)
    df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)

    return df

# 좌표 매핑 데이터
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
        
        # 지도 점 크기 (로그 스케일) - 방문객이 0이어도 기본 크기는 갖도록
        df['size_scale'] = np.log1p(df['visitors']) + 3 
    else:
        st.error("Data Error: CSV structure mismatch. Please check your columns.")
        st.stop()
except Exception as e:
    st.error(f"Critical Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 🧠 AI 가이드 로직
# ---------------------------------------------------------
def get_smart_response(user_input, dataframe, lang='en'):
    user_input = user_input.lower()
    filtered_ai = dataframe.copy()
    
    # 지역 필터링
    found_region = None
    for kor, eng in REGION_EN_DICT.items():
        if eng.lower() in user_input or kor in user_input:
            filtered_ai = filtered_ai[filtered_ai['region_en'] == eng]
            break 
    
    # 카테고리 필터링
    for cat in dataframe['category'].unique():
        if str(cat).lower() in user_input:
            filtered_ai = filtered_ai[filtered_ai['category'] == cat]
            break

    # 결과 선택
    if not filtered_ai.empty:
        top_picks = filtered_ai.sort_values('visitors', ascending=False).head(3)
        pick = top_picks.sample(1).iloc[0]
        visit_fmt = f"{pick['visitors']:,}"
        
        if lang == 'en':
            return f"🤖 **I found it!**\n\n🎉 **{pick['name']}**\n- 📍 {pick['region_en']} ({pick['place']})\n- 🗓️ Month: {pick['month']}\n- 🎨 Type: {pick['category']}\n- 👥 Foreigners: {visit_fmt}"
        else:
            return f"🤖 **찾았습니다!**\n\n🎉 **{pick['name']}**\n- 📍 {pick['region']} ({pick['place']})\n- 🗓️ 개최월: {pick['month']}월\n- 🎨 유형: {pick['category']}\n- 👥 외국인: {visit_fmt}명"
    else:
        return "🤔 No matching festivals found." if lang == 'en' else "🤔 조건에 맞는 축제를 찾지 못했어요."

# ---------------------------------------------------------
# 4. UI 텍스트 사전
# ---------------------------------------------------------
UI_TEXT = {
    'ko': {
        'title': "🇰🇷 2025 한국 지역축제 가이드",
        'subtitle': "데이터로 만나는 **{}**개의 한국 축제",
        'sidebar_title': "🔍 축제 찾기",
        'filter_month': "개최 월 (기간)",
        'filter_region': "지역 선택 (다중 선택 가능)",
        'filter_cat': "관심사 (축제 유형)",
        'kpi_total': "검색된 축제",
        'kpi_top_region': "최다 개최지",
        'kpi_visitor': "인기 1위 (외국인)",
        'tab_list': "📋 축제 리스트 상세",
        'tab_rank': "🏆 인기 랭킹",
        'tab_season': "🌸 계절별 추천",
        'tab_ai': "🤖 AI 가이드",
        'col_name': '축제명', 'col_cat': '유형', 'col_reg': '지역', 'col_vis': '방문객',
        'all': '전체'
    },
    'en': {
        'title': "🇰🇷 K-Festival Guide 2025",
        'subtitle': "Explore **{}** Festivals in Korea",
        'sidebar_title': "🔍 Filter Festivals",
        'filter_month': "Select Period (Month)",
        'filter_region': "Select Regions",
        'filter_cat': "Select Interests",
        'kpi_total': "Festivals Found",
        'kpi_top_region': "Top Region",
        'kpi_visitor': "Most Popular",
        'tab_list': "📋 Festival List",
        'tab_rank': "🏆 Rankings",
        'tab_season': "🌸 Seasonal",
        'tab_ai': "🤖 AI Guide",
        'col_name': 'Name', 'col_cat': 'Type', 'col_reg': 'Region', 'col_vis': 'Visitors',
        'all': 'All'
    }
}

# ---------------------------------------------------------
# 5. 레이아웃 & 필터링
# ---------------------------------------------------------
lang_option = st.sidebar.radio("Language", ["English", "한국어"], horizontal=True)
lang = 'en' if lang_option == "English" else 'ko'
txt = UI_TEXT[lang]

st.sidebar.markdown("---")
st.sidebar.header(txt['sidebar_title'])

# 필터 개선: 월(Range Slider), 지역(Multiselect), 카테고리(Multiselect)
selected_month = st.sidebar.slider(txt['filter_month'], 1, 12, (1, 12))

r_col = 'region_en' if lang == 'en' else 'region'
regions = sorted(list(df[r_col].unique()))
selected_regions = st.sidebar.multiselect(txt['filter_region'], regions, default=[])

categories = sorted(list(df['category'].unique()))
selected_categories = st.sidebar.multiselect(txt['filter_cat'], categories, default=[])

# 데이터 필터링
filtered_df = df[(df['month'] >= selected_month[0]) & (df['month'] <= selected_month[1])]
if selected_regions:
    filtered_df = filtered_df[filtered_df[r_col].isin(selected_regions)]
if selected_categories:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

# ---------------------------------------------------------
# 6. 메인 대시보드
# ---------------------------------------------------------
st.title(txt['title'])
st.markdown(txt['subtitle'].format(len(filtered_df)))
st.markdown("---")

# [KPI Metrics]
m1, m2, m3 = st.columns(3)
m1.metric(txt['kpi_total'], f"{len(filtered_df)}")
if not filtered_df.empty:
    top_reg = filtered_df[r_col].mode()[0]
    top_fest = filtered_df.sort_values('visitors', ascending=False).iloc[0]['name']
    m2.metric(txt['kpi_top_region'], top_reg)
    m3.metric(txt['kpi_visitor'], top_fest[:10]+"..")
else:
    m2.metric(txt['kpi_top_region'], "-")
    m3.metric(txt['kpi_visitor'], "-")

# ---------------------------------------------------------
# [Main Visual] 화려한 지도 (Plotly Mapbox)
# ---------------------------------------------------------
st.markdown("### 🗺️ Festival Map")
if not filtered_df.empty:
    # 지도 색상 팔레트 설정
    fig_map = px.scatter_mapbox(
        filtered_df, 
        lat="lat", 
        lon="lon", 
        color="category",  # 카테고리별 다른 색상
        size="size_scale", # 방문객 수에 따라 크기 조절
        hover_name="name", 
        hover_data={r_col:True, "visitors":True, "lat":False, "lon":False, "size_scale":False},
        zoom=6, 
        height=500,
        mapbox_style="carto-positron", # 깔끔하고 밝은 지도 스타일
        color_discrete_sequence=px.colors.qualitative.Bold # 화려한 색감
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No Data found. Please adjust filters.")

# ---------------------------------------------------------
# [List View] 리스트를 지도 밑으로 이동
# ---------------------------------------------------------
with st.expander(txt['tab_list'], expanded=True):
    if not filtered_df.empty:
        # 보여줄 컬럼 선택
        list_df = filtered_df[['name', 'category', r_col, 'place', 'month', 'visitors']].sort_values('visitors', ascending=False)
        
        st.dataframe(
            list_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn(txt['col_name'], width="medium"),
                "category": st.column_config.TextColumn(txt['col_cat'], width="small"),
                r_col: st.column_config.TextColumn(txt['col_reg'], width="small"),
                "place": "Location",
                "month": "Month",
                "visitors": st.column_config.ProgressColumn(
                    txt['col_vis'],
                    format="%d",
                    min_value=0,
                    max_value=int(df['visitors'].max()),
                ),
            }
        )
    else:
        st.info("No Data")

# ---------------------------------------------------------
# [Tabs] 상세 분석 & AI
# ---------------------------------------------------------
st.markdown("---")
tab1, tab2, tab3 = st.tabs([txt['tab_rank'], txt['tab_season'], txt['tab_ai']])

# Tab 1: 랭킹
with tab1:
    st.subheader(txt['tab_rank'])
    if not filtered_df.empty:
        rank_df = filtered_df[filtered_df['visitors'] > 0].sort_values('visitors', ascending=False).head(10)
        fig_bar = px.bar(rank_df, x='visitors', y='name', orientation='h', 
                         color='visitors', text='visitors', 
                         color_continuous_scale='Viridis') # 세련된 색감
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No Data")

# Tab 2: 계절별 카드
with tab2:
    st.subheader(txt['tab_season'])
    seasons = {'Spring': [3,4,5], 'Summer': [6,7,8], 'Autumn': [9,10,11], 'Winter': [12,1,2]} if lang=='en' else {'봄': [3,4,5], '여름': [6,7,8], '가을': [9,10,11], '겨울': [12,1,2]}
    
    cols = st.columns(4)
    for i, (s_name, s_months) in enumerate(seasons.items()):
        with cols[i]:
            st.markdown(f"#### {s_name}")
            s_data = df[df['month'].isin(s_months)].sort_values('visitors', ascending=False).head(3)
            for _, row in s_data.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['name']}**")
                    st.caption(f"📍 {row[r_col]}")
                    st.write(f"👥 {row['visitors']:,}")

# Tab 3: AI 가이드
with tab3:
    col_ai_L, col_ai_R = st.columns([2, 1])
    with col_ai_L:
        st.subheader(txt['tab_ai'])
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": txt['ai_hello']}]
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("Ex: Seoul Food Festival"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            ai_response = get_smart_response(prompt, df, lang)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.chat_message("assistant").write(ai_response)
    
    with col_ai_R:
        st.info("💡 **Tip**")
        if lang == 'en':
            st.markdown("- Try **'Seoul'** or **'Busan'**.\n- Try **'Food'** or **'Music'**.")
        else:
            st.markdown("- **'서울'**이나 **'부산'** 입력.\n- **'음식'**이나 **'음악'** 입력.")
