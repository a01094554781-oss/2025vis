import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np  # 좌표 계산용
from googletrans import Translator

# 1. 페이지 설정
st.set_page_config(
    page_title="K-Festival Guide Pro",
    page_icon="🌏",
    layout="wide"
)

# ---------------------------------------------------------
# 2. 다국어 지원용 딕셔너리
# ---------------------------------------------------------
UI_TEXT = {
    'KO': {
        'title': "🇰🇷 대한민국 지역 축제 가이드",
        'sidebar_title': "🔍 축제 찾기 (필터)",
        'lang_sel': "언어 / Language",
        'month_sel': "방문 시기 (월)",
        'region_sel': "지역 선택",
        'type_sel': "축제 유형 선택",
        'search_lbl': "이름 검색",
        'search_ph': "예: 벚꽃, 불꽃",
        'kpi_total': "검색된 축제",
        'kpi_visitors': "총 방문객 규모",
        'kpi_foreigner': "외국인 방문객",
        'tab1': "📊 지도 & 차트 분석",
        'tab2': "📋 상세 리스트 (카드 보기)",
        'chart_map': "🗺️ 축제 위치 지도 (지역별 분포)",
        'chart_treemap': "지역별 & 유형별 분포",
        'chart_heatmap': "📅 월별 지역 축제 밀집도 (Heatmap)",
        'chart_top10': "🏆 외국인 방문객 Top 10",
        'list_header': "검색 결과 상세 리스트",
        'col_name': "축제명", 'col_loc': "지역", 'col_type': "유형", 'col_date': "월", 'col_for': "외국인수",
        'btn_google': "🔍 구글 검색",
        'btn_youtube': "📺 유튜브 영상"
    },
    'EN': {
        'title': "🇰🇷 Korea Local Festival Guide",
        'sidebar_title': "🔍 Find Festivals",
        'lang_sel': "Language",
        'month_sel': "Month of Visit",
        'region_sel': "Select Region",
        'type_sel': "Select Category",
        'search_lbl': "Search by Name",
        'search_ph': "e.g., Cherry Blossom",
        'kpi_total': "Festivals Found",
        'kpi_visitors': "Total Visitors",
        'kpi_foreigner': "Foreign Visitors",
        'tab1': "📊 Map & Charts",
        'tab2': "📋 Detailed List (Card View)",
        'chart_map': "🗺️ Festival Map Location",
        'chart_treemap': "Distribution by Region & Type",
        'chart_heatmap': "📅 Best Season to Visit (Heatmap)",
        'chart_top10': "🏆 Top 10 Popular for Foreigners",
        'list_header': "Detailed Search Results",
        'col_name': "Name", 'col_loc': "Region", 'col_type': "Category", 'col_date': "Month", 'col_for': "Foreigners",
        'btn_google': "🔍 Google Info",
        'btn_youtube': "📺 YouTube Video"
    }
}

REGION_MAP = {
    '강원': 'Gangwon', '경기': 'Gyeonggi', '경남': 'Gyeongnam', '경북': 'Gyeongbuk',
    '광주': 'Gwangju', '대구': 'Daegu', '대전': 'Daejeon', '부산': 'Busan',
    '서울': 'Seoul', '세종': 'Sejong', '울산': 'Ulsan', '인천': 'Incheon',
    '전남': 'Jeonnam', '전북': 'Jeonbuk', '제주': 'Jeju', '충남': 'Chungnam', '충북': 'Chungbuk'
}

TYPE_MAP = {
    '문화예술': 'Arts & Culture', '지역특산물': 'Local Specialties', 
    '자연생태': 'Nature', '전통역사': 'History', 
    '주민화합': 'Community', '기타': 'Others'
}

# 지도 좌표 데이터 (지역 중심점)
LOC_COORDS = {
    '서울': [37.5665, 126.9780], '부산': [35.1796, 129.0756], '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052], '광주': [35.1595, 126.8526], '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114], '세종': [36.4800, 127.2890], '경기': [37.4138, 127.5183],
    '강원': [37.8228, 128.1555], '충북': [36.6350, 127.4914], '충남': [36.6588, 126.6728],
    '전북': [35.7175, 127.1530], '전남': [34.8679, 126.9910], '경북': [36.4919, 128.8889],
    '경남': [35.4606, 128.2132], '제주': [33.4996, 126.5312]
}

# ---------------------------------------------------------
# 3. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("festival.CSV", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("festival.CSV", encoding='cp949')

    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace(',', '')
            return pd.to_numeric(x, errors='coerce')
        return x

    df['visitors_clean'] = df['visitors in the previous year'].apply(clean_currency).fillna(0)
    
    df.columns = df.columns.str.strip()
    if 'foreigner' in df.columns:
        df['foreigner_clean'] = df['foreigner'].apply(clean_currency).fillna(0)
    else:
        df['foreigner_clean'] = 0

    df['Region_En'] = df['state'].map(REGION_MAP).fillna(df['state'])
    df['Type_En'] = df['festivaltype'].map(TYPE_MAP).fillna('Others')
    df['festivalname'] = df['festivalname'].fillna('')
    
    # 축제 이름 자동 번역
    translator = Translator()
    unique_names = df['festivalname'].unique()
    name_map = {}
    
    for name in unique_names:
        try:
            temp_name = name.replace("축제", " Festival").replace("대회", " Contest")
            name_map[name] = temp_name 
        except:
            name_map[name] = name

    df['festivalname_en'] = df['festivalname'].map(name_map)
    
    # 링크 생성
    df['google_url'] = "https://www.google.com/search?q=" + df['festivalname'] + "+" + df['state']
    df['youtube_url'] = "https://www.youtube.com/results?search_query=" + df['festivalname'] + "+Korea+Festival"

    # 지도 좌표 생성
    df['lat'] = df['state'].map(lambda x: LOC_COORDS.get(x, [36.5, 127.5])[0])
    df['lon'] = df['state'].map(lambda x: LOC_COORDS.get(x, [36.5, 127.5])[1])
    
    np.random.seed(42)
    noise = 0.04
    df['lat'] = df['lat'] + np.random.uniform(-noise, noise, size=len(df))
    df['lon'] = df['lon'] + np.random.uniform(-noise, noise, size=len(df))

    return df

with st.spinner('Data loading & Translating... (May take a moment)'):
    df = load_data()

# ---------------------------------------------------------
# 4. 사이드바
# ---------------------------------------------------------
with st.sidebar:
    lang_code = st.radio("Language", ['KO', 'EN'], horizontal=True, label_visibility="collapsed")
    txt = UI_TEXT[lang_code]
    
    st.header(txt['sidebar_title'])
    
    if lang_code == 'EN':
        region_col, type_col, name_col = 'Region_En', 'Type_En', 'festivalname_en'
    else:
        region_col, type_col, name_col = 'state', 'festivaltype', 'festivalname'

    all_months = list(range(1, 13))
    selected_months = st.multiselect(txt['month_sel'], all_months, default=all_months)
    
    region_opts = sorted(df[region_col].unique())
    sel_regions = st.multiselect(txt['region_sel'], region_opts, default=region_opts)

    type_opts = sorted(df[type_col].unique())
    sel_types = st.multiselect(txt['type_sel'], type_opts, default=type_opts)
        
    search_query = st.text_input(txt['search_lbl'], placeholder=txt['search_ph'])

# ---------------------------------------------------------
# 5. 데이터 필터링
# ---------------------------------------------------------
filtered_df = df[
    (df['startmonth'].isin(selected_months)) &
    (df[region_col].isin(sel_regions)) &
    (df[type_col].isin(sel_types))
]

if search_query:
    filtered_df = filtered_df[
        filtered_df['festivalname'].str.contains(search_query, case=False) | 
        filtered_df['festivalname_en'].str.contains(search_query, case=False)
    ]

# ---------------------------------------------------------
# 6. 메인 대시보드
# ---------------------------------------------------------
st.title(txt['title'])

c1, c2, c3 = st.columns(3)
c1.metric(txt['kpi_total'], f"{len(filtered_df)}")
c2.metric(txt['kpi_visitors'], f"{int(filtered_df['visitors_clean'].sum()):,}")
c3.metric(txt['kpi_foreigner'], f"{int(filtered_df['foreigner_clean'].sum()):,}")

st.divider()

tab1, tab2 = st.tabs([txt['tab1'], txt['tab2']])

# --- TAB 1: 차트 (지도 및 분석) ---
with tab1:
    st.subheader(txt['chart_map'])
    if not filtered_df.empty:
        fig_map = px.scatter_mapbox(
            filtered_df, lat="lat", lon="lon",
            size="visitors_clean", color=type_col,
            hover_name=name_col,
            hover_data={"lat": False, "lon": False, "visitors_clean": True, region_col: True},
            color_discrete_sequence=px.colors.qualitative.Bold,
            zoom=6, center={"lat": 36.5, "lon": 127.5},
            mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
        st.plotly_chart(fig_map, use_container_width=True)
    
    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader(txt['chart_treemap'])
        if not filtered_df.empty:
            path_list = [px.Constant("Korea"), region_col, type_col, name_col]
            fig_tree = px.treemap(
                filtered_df, path=path_list, values='visitors_clean',
                color=type_col, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)
            
    with col_chart2:
        st.subheader(txt['chart_top10'])
        if not filtered_df.empty:
            top_foreign = filtered_df.nlargest(10, 'foreigner_clean')
            fig_bar = px.bar(
                top_foreign, x='foreigner_clean', y=name_col,
                orientation='h', text_auto=',', color=region_col
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader(txt['chart_heatmap'])
    if not filtered_df.empty:
        heatmap_data = filtered_df.groupby([region_col, 'startmonth']).size().reset_index(name='counts')
        fig_heat = px.density_heatmap(
            heatmap_data, x='startmonth', y=region_col, z='counts', 
            nbinsx=12, text_auto=True, color_continuous_scale='Reds',
            labels={'startmonth': 'Month', region_col: 'Region', 'counts': 'Festivals'}
        )
        fig_heat.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
        st.plotly_chart(fig_heat, use_container_width=True)

# --- TAB 2: 상세 리스트 (카드 뷰 스타일로 업그레이드) ---
with tab2:
    st.subheader(txt['list_header'])
    
    # 다운로드 버튼
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download List (CSV)", data=csv,
            file_name="korea_festivals.csv", mime="text/csv"
        )
        
        st.markdown("---")
        
        # [NEW] 화려한 카드 뷰 스타일 (데이터프레임 대신 사용)
        # 너무 많은 데이터를 렌더링하면 느려질 수 있으므로 최대 50개까지만 카드 형태로 보여주고
        # 그 이상은 필터링을 유도하는 메시지 출력 (또는 그대로 둠)
        
        LIMIT_VIEW = 50
        count = 0
        
        for index, row in filtered_df.iterrows():
            if count >= LIMIT_VIEW:
                st.warning(f"⚠️ {LIMIT_VIEW} items shown. Please filter more to see specific results.")
                break
                
            # 카드 디자인 (컨테이너 + 테두리)
            with st.container(border=True):
                # 1. 헤더 (축제 이름 및 지역 배지)
                col_head1, col_head2 = st.columns([4, 1])
                with col_head1:
                    st.markdown(f"### 🎪 {row[name_col]}")
                    st.caption(f"📍 {row[region_col]}  |  📅 {row['startmonth']}월  |  🏷️ {row[type_col]}")
                with col_head2:
                    # 외국인 방문객 강조 배지
                    st.metric(txt['col_for'], f"{row['foreigner_clean']:,.0f}")
                
                # 2. 내용 (버튼 링크)
                col_link1, col_link2, col_empty = st.columns([1, 1, 3])
                with col_link1:
                    st.link_button(txt['btn_google'], row['google_url'], use_container_width=True)
                with col_link2:
                    st.link_button(txt['btn_youtube'], row['youtube_url'], use_container_width=True)
            
            count += 1
            
    else:
        st.warning("No festivals found.")
