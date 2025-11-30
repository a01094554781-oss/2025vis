import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 (영어 제목 및 아이콘)
st.set_page_config(
    page_title="Discover Korea: Festival Guide",
    page_icon="✈️",
    layout="wide"
)

# 2. 한글 -> 영어 변환 딕셔너리 정의
REGION_MAP = {
    '강원': 'Gangwon-do', '경기': 'Gyeonggi-do', '경남': 'Gyeongsangnam-do', 
    '경북': 'Gyeongsangbuk-do', '광주': 'Gwangju', '대구': 'Daegu', 
    '대전': 'Daejeon', '부산': 'Busan', '서울': 'Seoul', 
    '세종': 'Sejong', '울산': 'Ulsan', '인천': 'Incheon', 
    '전남': 'Jeollanam-do', '전북': 'Jeollabuk-do', 
    '제주': 'Jeju Island', '충남': 'Chungcheongnam-do', 
    '충북': 'Chungcheongbuk-do'
}

TYPE_MAP = {
    '문화예술': 'Arts & Culture', 
    '지역특산물': 'Local Food & Specialties', 
    '자연생태': 'Nature & Ecology', 
    '전통역사': 'History & Tradition', 
    '주민화합': 'Community', 
    '기타': 'Others'
}

# 3. 데이터 로드 및 전처리 (영어 컬럼 생성)
@st.cache_data
def load_and_prep_data():
    try:
        df = pd.read_csv("festival.CSV", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("festival.CSV", encoding='cp949')

    # 숫자 데이터 정제 (방문객 수)
    target_col = 'visitors in the previous year'
    if df[target_col].dtype == 'object':
        df['visitors_clean'] = df[target_col].astype(str).str.replace(',', '')
        df['visitors_clean'] = pd.to_numeric(df['visitors_clean'], errors='coerce').fillna(0)
    else:
        df['visitors_clean'] = df[target_col].fillna(0)

    # 영어 컬럼 추가 (매핑 적용)
    df['Region_En'] = df['state'].map(REGION_MAP).fillna(df['state'])
    df['Type_En'] = df['festivaltype'].map(TYPE_MAP).fillna('Others')
    
    # NaN 처리 (축제 이름이 비어있을 경우 대비)
    df['festivalname'] = df['festivalname'].fillna('Unknown Festival')
    
    return df

df = load_and_prep_data()

# 4. 사이드바 (영어 메뉴)
st.sidebar.header("✈️ Trip Planner")
st.sidebar.markdown("Find the best festivals for your trip!")

# 월 선택 (슬라이더)
selected_month = st.sidebar.slider("Select Month", 1, 12, (1, 12))

# 지역 선택
all_regions = sorted(df['Region_En'].unique())
selected_regions = st.sidebar.multiselect("Select Region", all_regions, default=all_regions)

# 필터링 로직
filtered_df = df[
    (df['startmonth'] >= selected_month[0]) & 
    (df['startmonth'] <= selected_month[1]) &
    (df['Region_En'].isin(selected_regions))
]

# 5. 메인 대시보드 UI
st.title("🇰🇷 Discover Korea: Local Festivals")
st.markdown("Explore the vibrant culture, food, and nature of Korea through local festivals.")
st.markdown("---")

# Key Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Festivals Found", f"{len(filtered_df)}")
m2.metric("Total Visitors (Est.)", f"{int(filtered_df['visitors_clean'].sum()):,}")
m3.metric("Top Category", filtered_df['Type_En'].mode()[0] if not filtered_df.empty else "-")

# 시각화 영역
st.markdown("### 📍 Where to Go?")

col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown("**Festival Distribution by Region**")
    if not filtered_df.empty:
        # Treemap: 지역 -> 도시 -> 축제 계층 구조 시각화 (외국인이 지역 구조 이해하기 좋음)
        fig_tree = px.treemap(
            filtered_df, 
            path=[px.Constant("Korea"), 'Region_En', 'city', 'Type_En'], 
            values='visitors_clean',
            color='Type_En',
            hover_data=['festivalname'],
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_tree.update_traces(root_color="lightgrey")
        fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)

with col2:
    st.markdown("**Festivals by Category**")
    if not filtered_df.empty:
        type_counts = filtered_df['Type_En'].value_counts().reset_index()
        type_counts.columns = ['Category', 'Count']
        fig_bar = px.bar(
            type_counts, x='Category', y='Count', 
            color='Category', 
            text_auto=True,
            title=""
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# Top Lists
st.markdown("### 🏆 Top 5 Most Popular Festivals")
st.markdown("Based on last year's visitor data.")

if not filtered_df.empty:
    top5 = filtered_df.nlargest(5, 'visitors_clean')[['festivalname', 'Region_En', 'Type_En', 'startmonth', 'visitors_clean']]
    # 데이터프레임 컬럼명 영어로 변경
    top5.columns = ['Festival Name', 'Region', 'Category', 'Month', 'Visitors']
    st.dataframe(
        top5,
        hide_index=True,
        column_config={
            "Visitors": st.column_config.NumberColumn(format="%d")
        },
        use_container_width=True
    )

# 상세 리스트 보기
with st.expander("📂 View All Festivals (Detailed List)"):
    display_df = filtered_df[['festivalname', 'Region_En', 'city', 'Type_En', 'startmonth', 'address']]
    display_df.columns = ['Name', 'Province', 'City', 'Type', 'Month', 'Address']
    st.dataframe(display_df, use_container_width=True)
