import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

    # 컬럼명 소문자 변환 및 공백 제거
    df.columns = df.columns.str.replace(' ', '').str.strip().str.lower()

    # 컬럼 매핑 (User csv 헤더 기준)
    rename_map = {
        'state': 'region', 'festivalname': 'name', 'festivaltype': 'category',
        'startmonth': 'month', 'foreigner': 'visitors', 'venue': 'place'
    }
    df = df.rename(columns=rename_map)

    # 데이터 타입 변환
    if 'visitors' in df.columns:
        df['visitors'] = df['visitors'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors'] = 0
        
    if 'month' in df.columns:
        df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)
    else:
        df['month'] = 0

    return df

# 좌표 및 지역명 데이터
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
        df['size_scale'] = np.log1p(df['visitors']) + 1
    else:
        st.error("Data Error: CSV structure mismatch.")
        st.stop()
except Exception as e:
    st.error(f"Critical Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 🧠 AI 가이드 로직 (엄격한 필터링 적용)
# ---------------------------------------------------------
def get_smart_response(user_input, dataframe, lang='en'):
    user_input = user_input.lower()
    filtered_ai = dataframe.copy()
    
    # 1. 지역 필터링 (명시적 언급 시 해당 지역만 남김)
    found_region = None
    for kor, eng in REGION_EN_DICT.items():
        if eng.lower() in user_input or kor in user_input:
            found_region = eng
            filtered_ai = filtered_ai[filtered_ai['region_en'] == eng]
            break # 첫 번째 발견된 지역으로 한정
    
    # 2. 카테고리 필터링
    found_cat = None
    for cat in dataframe['category'].unique():
        if str(cat).lower() in user_input:
            found_cat = cat
            filtered_ai = filtered_ai[filtered_ai['category'] == cat]
            break

    # 3. 결과 선택
    if not filtered_ai.empty:
        # 방문객 수 기준 상위 3개 중 하나 랜덤 추천
        top_picks = filtered_ai.sort_values('visitors', ascending=False).head(3)
        pick = top_picks.sample(1).iloc[0]
        
        visit_fmt = f"{pick['visitors']:,}"
        
        if lang == 'en':
            return f"""
            🤖 **I found the best match!**
            
            🎉 **{pick['name']}**
            - 📍 **Location:** {pick['region_en']} ({pick['place']})
            - 🗓️ **Month:** {pick['month']}
            - 🎨 **Type:** {pick['category']}
            - 👥 **Foreign Visitors:** {visit_fmt}
            
            *(Selected from {len(filtered_ai)} festivals matching your request)*
            """
        else:
            return f"""
            🤖 **딱 맞는 축제를 찾았습니다!**
            
            🎉 **{pick['name']}**
            - 📍 **위치:** {pick['region']} ({pick['place']})
            - 🗓️ **개최월:** {pick['month']}월
            - 🎨 **유형:** {pick['category']}
            - 👥 **외국인 방문객:** {visit_fmt}명
            
            *(질문하신 조건에 맞는 {len(filtered_ai)}개 축제 중 추천)*
            """
    else:
        if lang == 'en':
            return "🤔 I couldn't find any festival matching that specific location or type. Try asking for 'Seoul' or 'Busan'."
        else:
            return "🤔 해당 지역이나 유형에 맞는 축제를 찾지 못했어요. '서울'이나 '부산'처럼 큰 지역명으로 물어봐주세요!"


# ---------------------------------------------------------
# 4. UI 텍스트 사전
# ---------------------------------------------------------
UI_TEXT = {
    'ko': {
        'title': "🇰🇷 2025 한국 지역축제 대시보드",
        'subtitle': "데이터로 만나는 **{}**개의 한국 축제",
        'sidebar_title': "🔍 필터 설정",
        'filter_month': "월 선택",
        'filter_region': "지역 선택",
        'filter_cat': "유형 선택",
        'kpi_total': "전체 축제",
        'kpi_top_region': "최다 개최지",
        'kpi_top_month': "축제의 달",
        'kpi_visitor': "인기 1위(외국인)",
        'chart_map': "🗺️ 축제 지도",
        'chart_pie': "축제 유형 비율",
        'chart_line': "월별 축제 개최 추이",
        'tab_rank': "🏆 인기 랭킹",
        'tab_season': "🌸 계절별 추천",
        'tab_ai': "🤖 AI 가이드",
        'col_name': '축제명', 'col_cat': '유형', 'col_reg': '지역', 'col_vis': '방문객',
        'all': '전체'
    },
    'en': {
        'title': "🇰🇷 K-Festival Analytics 2025",
        'subtitle': "Explore **{}** Festivals with Data",
        'sidebar_title': "🔍 Filter Settings",
        'filter_month': "Select Month",
        'filter_region': "Select Region",
        'filter_cat': "Select Category",
        'kpi_total': "Total Festivals",
        'kpi_top_region': "Top Region",
        'kpi_top_month': "Peak Month",
        'kpi_visitor': "Most Popular",
        'chart_map': "🗺️ Festival Map",
        'chart_pie': "Category Distribution",
        'chart_line': "Monthly Trend",
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

# 필터
selected_month = st.sidebar.slider(txt['filter_month'], 1, 12, (1, 12))
r_col = 'region_en' if lang == 'en' else 'region'
regions = [txt['all']] + sorted(list(df[r_col].unique()))
selected_region = st.sidebar.selectbox(txt['filter_region'], regions)
categories = [txt['all']] + list(df['category'].unique())
selected_category = st.sidebar.multiselect(txt['filter_cat'], categories, default=txt['all'])

# 데이터 필터링
filtered_df = df[(df['month'] >= selected_month[0]) & (df['month'] <= selected_month[1])]
if selected_region != txt['all']: filtered_df = filtered_df[filtered_df[r_col] == selected_region]
if txt['all'] not in selected_category and selected_category: filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]

# ---------------------------------------------------------
# 6. 메인 대시보드 (Rich Visuals)
# ---------------------------------------------------------
st.title(txt['title'])
st.markdown(txt['subtitle'].format(len(filtered_df)))
st.markdown("---")

# [KPI Metrics] 상단 요약 통계
m1, m2, m3, m4 = st.columns(4)
m1.metric(txt['kpi_total'], f"{len(filtered_df)}")
if not filtered_df.empty:
    top_reg = filtered_df[r_col].mode()[0] if not filtered_df.empty else "-"
    peak_mo = filtered_df['month'].mode()[0] if not filtered_df.empty else "-"
    top_fest = filtered_df.sort_values('visitors', ascending=False).iloc[0]['name']
    m2.metric(txt['kpi_top_region'], top_reg)
    m3.metric(txt['kpi_top_month'], f"{peak_mo} Month")
    m4.metric(txt['kpi_visitor'], top_fest[:10]+"..")
else:
    m2.metric(txt['kpi_top_region'], "-")
    m3.metric(txt['kpi_top_month'], "-")
    m4.metric(txt['kpi_visitor'], "-")

# [Row 1] 지도 + 도넛 차트
st.markdown("### 📊 Overview")
row1_1, row1_2 = st.columns([3, 2])

with row1_1:
    st.markdown(f"**{txt['chart_map']}**")
    if not filtered_df.empty:
        fig_map = px.scatter_mapbox(
            filtered_df, lat="lat", lon="lon", color="category", size="size_scale",
            hover_name="name", hover_data={r_col:True, "visitors":True, "lat":False, "lon":False, "size_scale":False},
            zoom=6, height=450, mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No Data")

with row1_2:
    st.markdown(f"**{txt['chart_pie']}**")
    if not filtered_df.empty:
        pie_df = filtered_df['category'].value_counts().reset_index()
        pie_df.columns = ['category', 'count']
        fig_pie = px.donut(pie_df, values='count', names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin={"r":0,"t":20,"l":0,"b":0}, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No Data")

# [Row 2] 월별 트렌드 (Area Chart)
st.markdown(f"**{txt['chart_line']}**")
if not filtered_df.empty:
    trend_df = filtered_df.groupby('month').size().reset_index(name='counts')
    # 모든 월 채우기 (1~12월)
    all_months = pd.DataFrame({'month': range(1, 13)})
    trend_df = pd.merge(all_months, trend_df, on='month', how='left').fillna(0)
    
    fig_area = px.area(trend_df, x='month', y='counts', markers=True, 
                       color_discrete_sequence=['#FF4B4B'])
    fig_area.update_xaxes(dtick=1)
    fig_area.update_layout(height=300, margin={"r":0,"t":10,"l":0,"b":0})
    st.plotly_chart(fig_area, use_container_width=True)

# [Tabs] 상세 분석
st.markdown("---")
tab1, tab2, tab3 = st.tabs([txt['tab_rank'], txt['tab_season'], txt['tab_ai']])

# Tab 1: 랭킹 (컬러풀한 바 차트)
with tab1:
    st.subheader(txt['tab_rank'])
    if not filtered_df.empty:
        rank_df = filtered_df[filtered_df['visitors'] > 0].sort_values('visitors', ascending=False).head(10)
        fig_bar = px.bar(rank_df, x='visitors', y='name', orientation='h', 
                         color='visitors', text='visitors', 
                         color_continuous_scale='Bluered')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No Data")

# Tab 2: 계절별 카드 (풍성한 디자인)
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
                    st.progress(min(row['visitors'] / (df['visitors'].max()+1), 1.0))

# Tab 3: 똑똑해진 AI
with tab3:
    col_ai_L, col_ai_R = st.columns([2, 1])
    with col_ai_L:
        st.subheader(txt['tab_ai'])
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I analyze data to find the best festival for you."}]
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("Ex: Seoul Food Festival"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # 개선된 로직 호출
            ai_response = get_smart_response(prompt, df, lang)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.chat_message("assistant").write(ai_response)
    
    with col_ai_R:
        st.info("💡 **Tip**")
        if lang == 'en':
            st.markdown("""
            - Try typing **'Seoul'** or **'Busan'** to find local festivals.
            - Type **'Food'** or **'Music'** to filter by category.
            - The AI strictly follows the **2025 Database**.
            """)
        else:
            st.markdown("""
            - **'서울'**이나 **'부산'** 같은 지역명을 입력해보세요.
            - **'음식'**이나 **'음악'** 같은 키워드로 찾아보세요.
            - AI는 철저하게 **2025년 데이터** 내에서만 추천합니다.
            """)
