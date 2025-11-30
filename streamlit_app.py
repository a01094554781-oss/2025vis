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

    df.columns = df.columns.str.replace(' ', '').str.strip().str.lower()

    rename_map = {
        'state': 'region', 'festivalname': 'name', 'festivaltype': 'category',
        'startmonth': 'month', 'foreigner': 'visitors', 'venue': 'place'
    }
    df = df.rename(columns=rename_map)

    if 'visitors' in df.columns:
        df['visitors'] = df['visitors'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors'] = 0
        
    if 'month' in df.columns:
        df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)
    else:
        df['month'] = 0

    # 구글 검색 링크
    df['link'] = "https://www.google.com/search?q=" + df['name'].astype(str) + "+Festival+Korea"

    return df

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
        df['size_scale'] = np.log1p(df['visitors']) + 3 
    else:
        st.error("Data Error.")
        st.stop()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. AI 가이드 로직
# ---------------------------------------------------------
def get_smart_response(user_input, dataframe, lang='en'):
    user_input = user_input.lower()
    filtered_ai = dataframe.copy()
    
    found_region = None
    for kor, eng in REGION_EN_DICT.items():
        if eng.lower() in user_input or kor in user_input:
            filtered_ai = filtered_ai[filtered_ai['region_en'] == eng]
            found_region = eng
            break
            
    found_cat = None
    for cat in dataframe['category'].unique():
        if str(cat).lower() in user_input:
            filtered_ai = filtered_ai[filtered_ai['category'] == cat]
            found_cat = cat
            break

    if not filtered_ai.empty:
        pick = filtered_ai.sort_values('visitors', ascending=False).iloc[0]
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
            return f"""
            🤖 **2025 데이터 분석 결과입니다!**
            
            🎉 **{pick['name']}**
            - 📍 **위치:** {pick['region']} ({pick['place']})
            - 🗓️ **개최월:** {pick['month']}월
            - 🎨 **유형:** {pick['category']}
            - 👥 **외국인 방문객:** {visit_fmt}명
            """
    else:
        if lang == 'en':
            msg = "🤔 I couldn't find any festival."
            if found_region: msg += f" (I looked in **{found_region}**, but found nothing.)"
            return msg + " Try asking for 'Seoul' or 'Busan'."
        else:
            msg = "🤔 조건에 맞는 축제가 없네요."
            if found_region: msg += f" (**{found_region}** 지역 데이터를 다 뒤져봤어요!)"
            return msg + " 다른 지역이나 키워드로 물어봐주세요."

# ---------------------------------------------------------
# 4. UI 텍스트
# ---------------------------------------------------------
UI_TEXT = {
    'ko': {
        'title': "🇰🇷 2025 한국 지역축제 가이드",
        'subtitle': "데이터로 만나는 **{}**개의 한국 축제",
        'sidebar_title': "🔍 축제 찾기",
        'filter_month': "월 선택 (다중 선택)",
        'filter_region': "지역 선택",
        'filter_cat': "관심사 (축제 유형)",
        'kpi_total': "검색된 축제",
        'kpi_top_region': "최다 개최지",
        'kpi_visitor': "인기 1위 (외국인)",
        'tab_list': "📋 축제 리스트 & 검색",
        'tab_rank': "🏆 인기 랭킹",
        'tab_season': "🌸 계절별 추천",
        'tab_ai': "🤖 AI 가이드",
        'col_name': '축제명', 'col_cat': '유형', 'col_reg': '지역', 'col_vis': '방문객', 'col_link': '상세 정보',
        'all': '전체'
    },
    'en': {
        'title': "🇰🇷 K-Festival Guide 2025",
        'subtitle': "Explore **{}** Festivals in Korea",
        'sidebar_title': "🔍 Filter Festivals",
        'filter_month': "Select Month(s)",
        'filter_region': "Select Regions",
        'filter_cat': "Select Interests",
        'kpi_total': "Festivals Found",
        'kpi_top_region': "Top Region",
        'kpi_visitor': "Most Popular",
        'tab_list': "📋 Festival List & Search",
        'tab_rank': "🏆 Rankings",
        'tab_season': "🌸 Seasonal",
        'tab_ai': "🤖 AI Guide",
        'col_name': 'Name', 'col_cat': 'Type', 'col_reg': 'Region', 'col_vis': 'Foreign Visitors', 'col_link': 'More Info',
        'all': 'All'
    }
}

# ---------------------------------------------------------
# 5. 레이아웃
# ---------------------------------------------------------
lang_option = st.sidebar.radio("Language", ["English", "한국어"], horizontal=True)
lang = 'en' if lang_option == "English" else 'ko'
txt = UI_TEXT[lang]

st.sidebar.markdown("---")
st.sidebar.header(txt['sidebar_title'])

month_options = list(range(1, 13))
selected_months = st.sidebar.multiselect(txt['filter_month'], month_options, default=[3, 4, 5, 9, 10])

r_col = 'region_en' if lang == 'en' else 'region'
regions = sorted(list(df[r_col].unique()))
selected_regions = st.sidebar.multiselect(txt['filter_region'], regions, default=[])

categories = sorted(list(df['category'].unique()))
selected_categories = st.sidebar.multiselect(txt['filter_cat'], categories, default=[])

if selected_months: filtered_df = df[df['month'].isin(selected_months)]
else: filtered_df = df 
if selected_regions: filtered_df = filtered_df[filtered_df[r_col].isin(selected_regions)]
if selected_categories: filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

st.title(txt['title'])
st.markdown(txt['subtitle'].format(len(filtered_df)))
st.markdown("---")

m1, m2, m3 = st.columns(3)
m1.metric(txt['kpi_total'], f"{len(filtered_df)}")
if not filtered_df.empty:
    top_reg = filtered_df[r_col].mode()[0]
    top_fest = filtered_df.sort_values('visitors', ascending=False).iloc[0]['name']
    m2.metric(txt['kpi_top_region'], top_reg)
    m3.metric(txt['kpi_visitor'], top_fest[:15]+"..")
else:
    m2.metric(txt['kpi_top_region'], "-")
    m3.metric(txt['kpi_visitor'], "-")

# ---------------------------------------------------------
# [Main Visual] 다크 모드 지도 (Dark Matter)
# ---------------------------------------------------------
st.markdown("### 🗺️ Festival Map")
if not filtered_df.empty:
    fig_map = px.scatter_mapbox(
        filtered_df, 
        lat="lat", lon="lon", 
        color="category", 
        size="size_scale",
        hover_name="name", 
        hover_data={r_col:True, "visitors":True, "lat":False, "lon":False, "size_scale":False},
        zoom=6, height=550,
        # [변경] 다크 모드에 어울리는 'carto-darkmatter' 스타일 적용
        mapbox_style="carto-darkmatter",
        # [변경] 형광/비비드 컬러 적용
        color_discrete_sequence=px.colors.qualitative.Vivid 
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No Data found.")

# ---------------------------------------------------------
# [List View]
# ---------------------------------------------------------
with st.expander(txt['tab_list'], expanded=True):
    if not filtered_df.empty:
        list_df = filtered_df[['name', 'category', r_col, 'place', 'month', 'visitors', 'link']].sort_values('visitors', ascending=False)
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
                    txt['col_vis'], format="%d", min_value=0, max_value=int(df['visitors'].max())
                ),
                "link": st.column_config.LinkColumn(txt['col_link'], display_text="🔍 Google")
            }
        )
    else:
        st.info("No Data")

# ---------------------------------------------------------
# [Tabs]
# ---------------------------------------------------------
st.markdown("---")
tab1, tab2, tab3 = st.tabs([txt['tab_rank'], txt['tab_season'], txt['tab_ai']])

# Tab 1: 랭킹 (Plasma 컬러 적용)
with tab1:
    st.subheader(txt['tab_rank'])
    if not filtered_df.empty:
        rank_df = filtered_df[filtered_df['visitors'] > 0].sort_values('visitors', ascending=False).head(10)
        
        col_rank_chart, col_rank_list = st.columns([1, 1])
        
        with col_rank_chart:
            # [변경] 'Plasma' 컬러 스케일 적용 (보라~노랑)
            fig_bar = px.bar(rank_df, x='visitors', y='name', orientation='h', 
                             color='visitors', text='visitors', 
                             color_continuous_scale='Plasma', 
                             title="Top 10 Chart")
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_rank_list:
            st.markdown("#### Top 10 List")
            st.dataframe(
                rank_df[['name', 'visitors', 'link']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": st.column_config.TextColumn(txt['col_name']),
                    "visitors": st.column_config.NumberColumn(txt['col_vis']),
                    "link": st.column_config.LinkColumn(txt['col_link'], display_text="🔍 Go")
                }
            )
    else:
        st.info("No Visitor Data")

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
                    st.markdown(f"[🔍 Google]({row['link']})")

# Tab 3: AI 가이드
with tab3:
    col_ai_L, col_ai_R = st.columns([2, 1])
    with col_ai_L:
        st.subheader(txt['tab_ai'])
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": txt['ai_hello']}]
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("Ex: Food festivals in Seoul"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            ai_response = get_smart_response(prompt, df, lang)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.chat_message("assistant").write(ai_response)
    
    with col_ai_R:
        st.info("💡 **Tip**")
        if lang == 'en':
            st.markdown("- Try **'Seoul'** or **'Busan'**.\n- Try **'Food'** or **'Music'**.\n- AI searches strictly in **2025 Data**.")
        else:
            st.markdown("- **'서울'**이나 **'부산'** 입력.\n- **'음식'**이나 **'음악'** 입력.\n- AI는 **2025 데이터** 내에서만 찾습니다.")
