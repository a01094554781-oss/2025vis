import streamlit as st
import pandas as pd
import plotly.express as px
from googletrans import Translator  # 번역 라이브러리 추가

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
        'chart_treemap': "지역별 & 유형별 분포",
        'chart_heatmap': "📅 월별 지역 축제 밀집도 (Heatmap)",
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
        'chart_heatmap': "📅 Best Season to Visit (Heatmap)",
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
# 3. 데이터 로드 및 전처리 (번역 기능 포함)
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
    
    df.columns = df.columns.str.strip()
    if 'foreigner' in df.columns:
        df['foreigner_clean'] = df['foreigner'].apply(clean_currency).fillna(0)
    else:
        df['foreigner_clean'] = 0

    # 영문/한글 매핑 컬럼 생성
    df['Region_En'] = df['state'].map(REGION_MAP).fillna(df['state'])
    df['Type_En'] = df['festivaltype'].map(TYPE_MAP).fillna('Others')
    df['festivalname'] = df['festivalname'].fillna('')
    
    # [핵심] 축제 이름 자동 번역 기능
    # 매번 번역하면 느리므로, unique한 이름만 뽑아서 번역 후 매핑
    translator = Translator()
    unique_names = df['festivalname'].unique()
    name_map = {}
    
    # 간단한 키워드 치환 (속도 향상 및 품질 보정)
    for name in unique_names:
        try:
            # 1단계: 주요 단어 직접 치환 (API 호출 최소화 및 포맷 통일)
            temp_name = name.replace("축제", " Festival").replace("대회", " Contest")
            name_map[name] = temp_name 
            
            # (옵션) 아래 주석을 풀면 구글 번역기를 실제로 돌립니다.
            # 속도가 느려질 수 있어 '축제->Festival' 치환만 우선 적용했습니다.
            # 만약 완벽한 영어를 원하시면 아래 2줄 주석을 해제하세요.
            # translated = translator.translate(name, dest='en').text
            # name_map[name] = translated
        except:
            name_map[name] = name # 에러나면 원본 사용

    df['festivalname_en'] = df['festivalname'].map(name_map)
    
    # Google/Youtube 링크 생성
    df['google_url'] = "https://www.google.com/search?q=" + df['festivalname'] + "+" + df['state']
    df['youtube_url'] = "https://www.youtube.com/results?search_query=" + df['festivalname'] + "+Korea+Festival"

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
    
    # 다국어 설정에 따른 컬럼 자동 선택
    if lang_code == 'EN':
        region_col = 'Region_En'
        type_col = 'Type_En'
        name_col = 'festivalname_en'  # 영어 이름 컬럼 사용
    else:
        region_col = 'state'
        type_col = 'festivaltype'
        name_col = 'festivalname'     # 한글 이름 컬럼 사용

    all_months = list(range(1, 13))
    selected_months = st.multiselect(txt['month_sel'], all_months, default=all_months)
    
    # 필터 옵션도 언어에 맞게 정렬
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
    # 검색은 한글/영어 이름 모두에서 찾도록 설정
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

# --- TAB 1: 차트 ---
with tab1:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader(txt['chart_treemap'])
        if not filtered_df.empty:
            path_list = [px.Constant("Korea"), region_col, type_col, name_col] # name_col이 언어따라 바뀜
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
                top_foreign, x='foreigner_clean', y=name_col, # 언어에 맞는 이름 사용
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

# --- TAB 2: 리스트 ---
with tab2:
    st.subheader(txt['list_header'])
    
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download List (CSV)", data=csv,
            file_name="korea_festivals.csv", mime="text/csv"
        )

    st.caption("👇 Click buttons to explore")
    
    if not filtered_df.empty:
        # 화면에 표시할 컬럼 정의 (언어에 따라 name_col 변동)
        display_cols = [name_col, region_col, type_col, 'startmonth', 'foreigner_clean', 'google_url', 'youtube_url']
        col_labels = [txt['col_name'], txt['col_loc'], txt['col_type'], txt['col_date'], txt['col_for'], "Google", "YouTube"]
            
        display_df = filtered_df[display_cols].copy()
        display_df.columns = col_labels
        
        st.dataframe(
            display_df, hide_index=True, use_container_width=True,
            column_config={
                "Google": st.column_config.LinkColumn(display_text="🔍 Info" if lang_code == 'EN' else "🔍 정보"),
                "YouTube": st.column_config.LinkColumn(display_text="📺 Video" if lang_code == 'EN' else "📺 영상"),
                txt['col_for']: st.column_config.NumberColumn(format="%d")
            },
            height=600
        )
    else:
        st.warning("No festivals found.")
