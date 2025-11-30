import streamlit as st
import pandas as pd
import plotly.express as px

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
        'tab1': "📊 차트 & 분석",
        'tab2': "📋 상세 리스트 (Google 연동)",
        'chart_treemap': "지역별 & 유형별 분포 (Box Size: 방문객 수)",
        'chart_top10': "🏆 외국인 방문객 Top 10",
        'list_header': "검색 결과 상세 리스트",
        'col_name': "축제명", 'col_loc': "지역", 'col_type': "유형", 'col_date': "월", 'col_for': "외국인수",
        'col_link': "구글 검색"
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
        'tab1': "📊 Charts & Analysis",
        'tab2': "📋 Detailed List (with Google)",
        'chart_treemap': "Distribution by Region & Type",
        'chart_top10': "🏆 Top 10 Popular for Foreigners",
        'list_header': "Detailed Search Results",
        'col_name': "Name", 'col_loc': "Region", 'col_type': "Category", 'col_date': "Month", 'col_for': "Foreigners",
        'col_link': "More Info"
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

# ---------------------------------------------------------
# 3. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("festival.CSV", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("festival.CSV", encoding='cp949')

    # 숫자 데이터 정제
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace(',', '')
            return pd.to_numeric(x, errors='coerce')
        return x

    df['visitors_clean'] = df['visitors in the previous year'].apply(clean_currency).fillna(0)
    
    # 컬럼 공백 제거 및 외국인 데이터 처리
    df.columns = df.columns.str.strip()
    if 'foreigner' in df.columns:
        df['foreigner_clean'] = df['foreigner'].apply(clean_currency).fillna(0)
    else:
        df['foreigner_clean'] = 0

    # 영문/한글 매핑 컬럼 생성
    df['Region_En'] = df['state'].map(REGION_MAP).fillna(df['state'])
    df['Type_En'] = df['festivaltype'].map(TYPE_MAP).fillna('Others')
    df['festivalname'] = df['festivalname'].fillna('')
    
    # Google 검색 링크 컬럼 생성 (검색어 = 축제이름 + 지역)
    # 한글/영어 검색 쿼리를 모두 지원하도록 URL 인코딩은 브라우저가 처리
    df['google_url'] = "https://www.google.com/search?q=" + df['festivalname'] + "+" + df['state']

    return df

df = load_data()

# ---------------------------------------------------------
# 4. 사이드바 (핵심 컨트롤 타워)
# ---------------------------------------------------------
with st.sidebar:
    lang_code = st.radio("Language", ['KO', 'EN'], horizontal=True, label_visibility="collapsed")
    txt = UI_TEXT[lang_code]
    
    st.header(txt['sidebar_title'])
    
    # 1. 월 선택
    all_months = list(range(1, 13))
    selected_months = st.multiselect(txt['month_sel'], all_months, default=all_months)
    
    # 2. 지역 선택 (언어에 따라 옵션 변경)
    if lang_code == 'EN':
        region_opts = sorted(df['Region_En'].unique())
        region_col = 'Region_En'
        sel_regions = st.multiselect(txt['region_sel'], region_opts, default=region_opts)
    else:
        region_opts = sorted(df['state'].unique())
        region_col = 'state'
        sel_regions = st.multiselect(txt['region_sel'], region_opts, default=region_opts)

    # 3. 유형 선택 (추가됨!)
    if lang_code == 'EN':
        type_opts = sorted(df['Type_En'].unique())
        type_col = 'Type_En'
        sel_types = st.multiselect(txt['type_sel'], type_opts, default=type_opts)
    else:
        type_opts = sorted(df['festivaltype'].unique())
        type_col = 'festivaltype'
        sel_types = st.multiselect(txt['type_sel'], type_opts, default=type_opts)
        
    # 4. 검색창
    search_query = st.text_input(txt['search_lbl'], placeholder=txt['search_ph'])

# ---------------------------------------------------------
# 5. 데이터 필터링
# ---------------------------------------------------------
# 선택한 조건들이 모두 AND 조건으로 연결됨
filtered_df = df[
    (df['startmonth'].isin(selected_months)) &
    (df[region_col].isin(sel_regions)) &
    (df[type_col].isin(sel_types))
]

if search_query:
    filtered_df = filtered_df[filtered_df['festivalname'].str.contains(search_query, case=False)]

# ---------------------------------------------------------
# 6. 메인 대시보드
# ---------------------------------------------------------
st.title(txt['title'])

# KPI
c1, c2, c3 = st.columns(3)
c1.metric(txt['kpi_total'], f"{len(filtered_df)}")
c2.metric(txt['kpi_visitors'], f"{int(filtered_df['visitors_clean'].sum()):,}")
c3.metric(txt['kpi_foreigner'], f"{int(filtered_df['foreigner_clean'].sum()):,}")

st.divider()

# 레이아웃: 왼쪽 차트, 오른쪽 리스트 (공간 활용)
# 모바일에서는 자동으로 상하 배치됨
col_chart, col_list = st.columns([1, 1])

with col_chart:
    st.subheader(txt['chart_treemap'])
    if not filtered_df.empty:
        # Treemap: 선택된 데이터만 보여줌
        path_list = [px.Constant("Korea"), region_col, type_col]
        fig_tree = px.treemap(
            filtered_df, 
            path=path_list, 
            values='visitors_clean',
            color=type_col,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)
    
    st.markdown("---")
    st.subheader(txt['chart_top10'])
    if not filtered_df.empty:
        top_foreign = filtered_df.nlargest(10, 'foreigner_clean')
        fig_bar = px.bar(
            top_foreign, x='foreigner_clean', y='festivalname', orientation='h',
            text_auto=',', color=region_col
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

with col_list:
    st.subheader(txt['list_header'])
    st.caption("👇 Click the link to see details on Google")
    
    if not filtered_df.empty:
        # 화면에 보여줄 컬럼 정리
        if lang_code == 'EN':
            display_cols = ['festivalname', 'Region_En', 'Type_En', 'startmonth', 'foreigner_clean', 'google_url']
            col_labels = [txt['col_name'], txt['col_loc'], txt['col_type'], txt['col_date'], txt['col_for'], txt['col_link']]
        else:
            display_cols = ['festivalname', 'state', 'festivaltype', 'startmonth', 'foreigner_clean', 'google_url']
            col_labels = [txt['col_name'], txt['col_loc'], txt['col_type'], txt['col_date'], txt['col_for'], txt['col_link']]
            
        display_df = filtered_df[display_cols].copy()
        display_df.columns = col_labels
        
        # 데이터프레임 표시 (LinkColumn 사용)
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                txt['col_link']: st.column_config.LinkColumn(
                    label=txt['col_link'], 
                    display_text="🔍 Search" if lang_code == 'EN' else "🔍 검색"
                ),
                txt['col_for']: st.column_config.NumberColumn(format="%d")
            },
            height=600 # 리스트 높이 고정 (스크롤 가능)
        )
    else:
        st.warning("No festivals found with current filters.")
