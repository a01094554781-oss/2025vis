import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(
    page_title="K-Festival Guide & Analytics",
    page_icon="🌏",
    layout="wide"
)

# ---------------------------------------------------------
# 2. 다국어 지원용 딕셔너리 (UI 텍스트 관리)
# ---------------------------------------------------------
UI_TEXT = {
    'KO': {
        'title': "🇰🇷 대한민국 지역 축제 가이드",
        'sidebar_title': "검색 옵션",
        'lang_sel': "언어 선택 (Language)",
        'month_sel': "방문 시기 (월)",
        'search_lbl': "축제 검색 (이름)",
        'search_ph': "예: 벚꽃, 불꽃",
        'kpi_total': "검색된 축제",
        'kpi_visitors': "총 방문객 규모",
        'kpi_foreigner': "총 외국인 방문객",
        'tab1': "📊 외국인 인기 랭킹",
        'tab2': "🗺️ 지역별/유형별 분포",
        'chart_top10_title': "🏆 외국인이 가장 많이 방문한 축제 Top 10",
        'chart_top10_x': "외국인 방문객 수",
        'chart_top10_y': "축제명",
        'df_expander': "📄 전체 리스트 보기 (상세 정보)",
        'col_name': "축제명", 'col_loc': "지역", 'col_type': "유형", 'col_date': "월", 'col_for': "외국인수"
    },
    'EN': {
        'title': "🇰🇷 Korea Local Festival Guide",
        'sidebar_title': "Search Options",
        'lang_sel': "Language",
        'month_sel': "Month of Visit",
        'search_lbl': "Search Festival",
        'search_ph': "e.g., Cherry Blossom, Firework",
        'kpi_total': "Festivals Found",
        'kpi_visitors': "Total Visitors (Est.)",
        'kpi_foreigner': "Total Foreign Visitors",
        'tab1': "📊 Top Choices for Foreigners",
        'tab2': "🗺️ Distribution by Region",
        'chart_top10_title': "🏆 Top 10 Festivals Most Visited by Foreigners",
        'chart_top10_x': "Foreign Visitors",
        'chart_top10_y': "Festival Name",
        'df_expander': "📄 View Full List (Details)",
        'col_name': "Name", 'col_loc': "Region", 'col_type': "Category", 'col_date': "Month", 'col_for': "Foreigners"
    }
}

# 영문 변환 매핑 (데이터용)
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

    # 숫자 데이터 정제 함수
    def clean_currency(x):
        if isinstance(x, str):
            # 쉼표 제거 및 숫자가 아닌 문자(미집계 등)는 0으로 처리
            x = x.replace(',', '')
            return pd.to_numeric(x, errors='coerce')
        return x

    # 전체 방문객 정제
    df['visitors_clean'] = df['visitors in the previous year'].apply(clean_currency).fillna(0)
    
    # 외국인 방문객 정제 ('foreigner' 컬럼 확인 필요, 파일에 'foreigner' 컬럼이 있다고 가정)
    # 파일 헤더가 'foreigner'인지 확인. 만약 공백이 있다면 strip() 처리
    df.columns = df.columns.str.strip()
    if 'foreigner' in df.columns:
        df['foreigner_clean'] = df['foreigner'].apply(clean_currency).fillna(0)
    else:
        df['foreigner_clean'] = 0 # 컬럼이 없을 경우 대비

    # 영문 컬럼 생성
    df['Region_En'] = df['state'].map(REGION_MAP).fillna(df['state'])
    df['Type_En'] = df['festivaltype'].map(TYPE_MAP).fillna('Others')
    df['festivalname'] = df['festivalname'].fillna('')

    return df

df = load_data()

# ---------------------------------------------------------
# 4. 사이드바 (필터링 & 언어 설정)
# ---------------------------------------------------------
with st.sidebar:
    # 언어 선택
    lang_code = st.radio("Language / 언어", ['KO', 'EN'], horizontal=True)
    txt = UI_TEXT[lang_code] # 선택된 언어 딕셔너리 가져오기
    
    st.header(txt['sidebar_title'])
    
    # 검색 기능 (텍스트 입력)
    search_query = st.text_input(txt['search_lbl'], placeholder=txt['search_ph'])
    
    # 월 선택 (멀티 셀렉트가 더 직관적일 수 있음)
    all_months = list(range(1, 13))
    selected_months = st.multiselect(txt['month_sel'], all_months, default=all_months)

    # (추가) 지역 필터는 언어에 따라 다르게 표시
    if lang_code == 'EN':
        region_opts = sorted(df['Region_En'].unique())
        sel_regions = st.multiselect("Select Region", region_opts, default=region_opts)
        region_col = 'Region_En'
    else:
        region_opts = sorted(df['state'].unique())
        sel_regions = st.multiselect("지역 선택", region_opts, default=region_opts)
        region_col = 'state'

# ---------------------------------------------------------
# 5. 데이터 필터링 로직
# ---------------------------------------------------------
filtered_df = df[
    (df['startmonth'].isin(selected_months)) &
    (df[region_col].isin(sel_regions))
]

# 검색어가 있다면 필터링 (축제명 기준)
if search_query:
    filtered_df = filtered_df[filtered_df['festivalname'].str.contains(search_query, case=False)]

# ---------------------------------------------------------
# 6. 메인 대시보드
# ---------------------------------------------------------
st.title(txt['title'])
st.markdown("---")

# KPI 지표
c1, c2, c3 = st.columns(3)
c1.metric(txt['kpi_total'], f"{len(filtered_df)}")
c2.metric(txt['kpi_visitors'], f"{int(filtered_df['visitors_clean'].sum()):,}")
c3.metric(txt['kpi_foreigner'], f"{int(filtered_df['foreigner_clean'].sum()):,}")

st.markdown("---")

# 탭 구성 (랭킹 vs 분포)
tab1, tab2 = st.tabs([txt['tab1'], txt['tab2']])

with tab1:
    # 외국인 인기 랭킹 차트
    st.subheader(txt['chart_top10_title'])
    
    if not filtered_df.empty:
        # 외국인 방문객 기준으로 내림차순 정렬
        top_foreign = filtered_df.nlargest(10, 'foreigner_clean')
        
        # 차트 그리기
        fig_bar = px.bar(
            top_foreign,
            x='foreigner_clean',
            y='festivalname',
            orientation='h',
            text_auto=',',
            color=region_col,
            labels={
                'foreigner_clean': txt['chart_top10_x'],
                'festivalname': txt['chart_top10_y']
            }
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data found.")

with tab2:
    # 파이 차트 (유형별) & 트리맵 (지역별)
    col_a, col_b = st.columns(2)
    
    with col_a:
        type_col = 'Type_En' if lang_code == 'EN' else 'festivaltype'
        if not filtered_df.empty:
            fig_pie = px.pie(filtered_df, names=type_col, title="Type Distribution", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with col_b:
        if not filtered_df.empty:
            path_list = [px.Constant("Korea"), region_col, type_col]
            fig_tree = px.treemap(
                filtered_df, path=path_list, values='visitors_clean',
                color=type_col
            )
            st.plotly_chart(fig_tree, use_container_width=True)

# ---------------------------------------------------------
# 7. 데이터프레임 (리스트)
# ---------------------------------------------------------
with st.expander(txt['df_expander'], expanded=True):
    # 보여줄 컬럼 선택 및 이름 변경
    if lang_code == 'EN':
        cols_to_show = ['festivalname', 'Region_En', 'city', 'Type_En', 'startmonth', 'foreigner_clean']
        col_names = [txt['col_name'], txt['col_loc'], 'City', txt['col_type'], txt['col_date'], txt['col_for']]
    else:
        cols_to_show = ['festivalname', 'state', 'city', 'festivaltype', 'startmonth', 'foreigner_clean']
        col_names = [txt['col_name'], txt['col_loc'], '도시', txt['col_type'], txt['col_date'], txt['col_for']]
        
    display_df = filtered_df[cols_to_show].copy()
    display_df.columns = col_names
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            txt['col_for']: st.column_config.NumberColumn(format="%d")
        }
    )
