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

# 2. 데이터 로드

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

        

        # 지도 점 크기를 위한 로그 스케일 (방문객 수가 너무 차이나서 로그 적용)

        df['size_scale'] = np.log1p(df['visitors']) + 1

    else:

        st.error("Data Error.")

        st.stop()

except Exception as e:

    st.error(f"Error: {e}")

    st.stop()



# ---------------------------------------------------------

# 3. UI 텍스트 & 스마트 응답

# ---------------------------------------------------------

def get_smart_response(user_input, dataframe, lang='en'):

    user_input = user_input.lower()

    found_regions = [r for r in dataframe['region_en'].unique() if r.lower() in user_input]

    found_cats = [c for c in dataframe['category'].unique() if str(c).lower() in user_input]

    filtered_ai = dataframe.copy()

    if found_regions: filtered_ai = filtered_ai[filtered_ai['region_en'].str.lower() == found_regions[0].lower()]

    if found_cats: filtered_ai = filtered_ai[filtered_ai['category'].astype(str).str.contains(found_cats[0], case=False)]

    

    if not filtered_ai.empty:

        top_picks = filtered_ai.sort_values('visitors', ascending=False).head(5)

        pick = top_picks.sample(1).iloc[0]

        if lang == 'en':

            return f"🎉 Found it!\n\n**[{pick['name']}]**\n- 📍 {pick['region_en']} ({pick['place']})\n- 🎨 {pick['category']}\n- 👥 Visitors: {pick['visitors']:,}\n\nCheck the map for details!"

        else:

            return f"🎉 찾았어요!\n\n**[{pick['name']}]**\n- 📍 {pick['region']} ({pick['place']})\n- 🎨 {pick['category']}\n- 👥 방문객: {pick['visitors']:,}명\n\n지도 탭에서 위치를 확인해보세요!"

    else:

        return "Not found in database." if lang == 'en' else "데이터베이스에서 찾을 수 없습니다."



UI_TEXT = {

    'ko': {

        'title': "🇰🇷 2025 한국 지역축제 지도",

        'subtitle': "**{}월**에 열리는 **{}개**의 축제를 발견해보세요!",

        'sidebar_title': "🔍 축제 찾기",

        'filter_month': "월 선택",

        'filter_region': "지역 선택",

        'filter_cat': "관심사 선택",

        'tab_map': "🗺️ 축제 지도",

        'tab_list': "📋 리스트",

        'tab_rank': "🏆 인기 순위",

        'tab_season': "🌸 계절 추천",

        'tab_ai': "🤖 AI 가이드",

        'col_name': '축제명', 'col_cat': '유형', 'col_reg': '지역', 'col_vis': '외국인 방문객', 'col_place': '장소',

        'all': '전체'

    },

    'en': {

        'title': "🇰🇷 K-Festival Info Map 2025",

        'subtitle': "Discover **{}** festivals in **{}**!",

        'sidebar_title': "🔍 Festival Finder",

        'filter_month': "Select Month",

        'filter_region': "Select Region",

        'filter_cat': "Select Interest",

        'tab_map': "🗺️ Map View",

        'tab_list': "📋 List View",

        'tab_rank': "🏆 Top 10",

        'tab_season': "🌸 Seasonal",

        'tab_ai': "🤖 AI Guide",

        'col_name': 'Festival Name', 'col_cat': 'Type', 'col_reg': 'Region', 'col_vis': 'Foreign Visitors', 'col_place': 'Location',

        'all': 'All'

    }

}



# ---------------------------------------------------------

# 4. 사이드바

# ---------------------------------------------------------

lang_option = st.sidebar.radio("🌐 Language", ["English", "한국어"], horizontal=True)

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

if selected_region != txt['all']: filtered_df = filtered_df[filtered_df[r_display_col] == selected_region]

if txt['all'] not in selected_category and selected_category: filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]



# ---------------------------------------------------------

# 5. 메인 대시보드

# ---------------------------------------------------------

st.title(txt['title'])

if lang == 'en': st.markdown(txt['subtitle'].format(len(filtered_df), f"{selected_month[0]}~{selected_month[1]} Month"))

else: st.markdown(txt['subtitle'].format(f"{selected_month[0]}~{selected_month[1]}", len(filtered_df)))



c1, c2, c3 = st.columns(3)

c1.metric("Total", f"{len(filtered_df)}")

c2.metric("Region", selected_region)

top_n = filtered_df.sort_values(by='visitors', ascending=False).iloc[0]['name'] if not filtered_df.empty else "-"

c3.metric("No.1 Popular", top_n)



tab1, tab2, tab3, tab4 = st.tabs([txt['tab_map'], txt['tab_list'], txt['tab_season'], txt['tab_ai']])



# [Tab 1] 풍부해진 지도 (Plotly Mapbox)

with tab1:

    if not filtered_df.empty:

        # Plotly를 사용한 고급 지도 시각화

        fig = px.scatter_mapbox(

            filtered_df,

            lat="lat", 

            lon="lon",

            color="category",      # 축제 유형별 다른 색상

            size="size_scale",     # 방문객 수에 따라 점 크기 다름 (로그스케일 적용)

            hover_name="name",     # 마우스 올리면 축제 이름 표시

            hover_data={

                "lat": False, "lon": False, "size_scale": False,

                r_display_col: True, "place": True, "visitors": True

            },

            zoom=6,

            height=600,

            mapbox_style="carto-positron" # 깔끔한 지도 스타일

        )

        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        st.plotly_chart(fig, use_container_width=True)

    else:

        st.warning(txt['no_data'])



# [Tab 2] 보기 편한 리스트 (Progress Bar 적용)

with tab2:

    if not filtered_df.empty:

        # 표시할 컬럼 정리

        list_df = filtered_df[['name', 'category', r_display_col, 'place', 'visitors']].sort_values('visitors', ascending=False)

        

        # 컬럼 설정 (Column Config) 적용

        st.dataframe(

            list_df,

            use_container_width=True,

            hide_index=True,

            column_config={

                "name": st.column_config.TextColumn(txt['col_name'], width="medium"),

                "category": st.column_config.TextColumn(txt['col_cat'], width="small"),

                r_display_col: st.column_config.TextColumn(txt['col_reg'], width="small"),

                "place": st.column_config.TextColumn(txt['col_place'], width="medium"),

                "visitors": st.column_config.ProgressColumn(

                    txt['col_vis'],

                    format="%d",

                    min_value=0,

                    max_value=int(df['visitors'].max()), # 전체 데이터 기준 최대값

                ),

            }

        )

    else:

        st.info(txt['no_data'])



# [Tab 3] 계절 추천 (카드형)

with tab3:

    def get_season_top5(months): return df[df['month'].isin(months)].sort_values('visitors', ascending=False).head(5)

    cols = st.columns(4)

    seasons = {'Spring': [3,4,5], 'Summer': [6,7,8], 'Autumn': [9,10,11], 'Winter': [12,1,2]} if lang=='en' else {'봄': [3,4,5], '여름': [6,7,8], '가을': [9,10,11], '겨울': [12,1,2]}

    

    for i, (name, months) in enumerate(seasons.items()):

        with cols[i]:

            st.markdown(f"### {name}")

            for _, row in get_season_top5(months).iterrows():

                with st.container(border=True): # 카드 디자인

                    st.markdown(f"**{row['name']}**")

                    st.caption(f"📍 {row[r_display_col]}")

                    st.caption(f"👥 {row['visitors']:,}")



# [Tab 4] AI 가이드

with tab4:

    if "messages" not in st.session_state:

        st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me anything."}]

    for msg in st.session_state.messages: st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: Food festivals in Seoul"):

        st.session_state.messages.append({"role": "user", "content": prompt})

        st.chat_message("user").write(prompt)

        ai_response = get_smart_response(prompt, df, lang)

        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        st.chat_message("assistant").write(ai_response)
