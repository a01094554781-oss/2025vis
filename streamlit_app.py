import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(
    page_title="국내 축제 데이터 대시보드",
    page_icon="🎉",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    # CSV 파일 로드 (파일명이 정확해야 합니다)
    try:
        df = pd.read_csv("festival.CSV", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("festival.CSV", encoding='cp949')

    # 방문객 수 데이터 정제 (쉼표 제거 및 문자를 0으로 변환)
    # 컬럼명이 파일과 정확히 일치해야 합니다. 파일 내 컬럼명을 기준으로 수정했습니다.
    target_col = 'visitors in the previous year'
    
    # 데이터가 문자열일 경우 쉼표 제거
    if df[target_col].dtype == 'object':
        df['visitors_clean'] = df[target_col].astype(str).str.replace(',', '')
        # 숫자로 변환 불가능한 값(미집계 등)은 NaN 처리 후 0으로 변환
        df['visitors_clean'] = pd.to_numeric(df['visitors_clean'], errors='coerce').fillna(0)
    else:
        df['visitors_clean'] = df[target_col].fillna(0)

    return df

df = load_data()

# 3. 사이드바 (필터링 옵션)
st.sidebar.header("🔍 검색 옵션")

# 지역 선택 (state)
region_list = df['state'].unique().tolist()
selected_region = st.sidebar.multiselect("광역지자체 선택", region_list, default=region_list)

# 축제 유형 선택 (festivaltype)
type_list = df['festivaltype'].unique().tolist()
selected_type = st.sidebar.multiselect("축제 유형 선택", type_list, default=type_list)

# 데이터 필터링
filtered_df = df[
    (df['state'].isin(selected_region)) & 
    (df['festivaltype'].isin(selected_type))
]

# 4. 메인 대시보드 레이아웃
st.title("🎉 전국 축제 현황 대시보드")
st.markdown("---")

# KPI 지표 표시
col1, col2, col3 = st.columns(3)
col1.metric("총 검색된 축제 수", f"{len(filtered_df)}개")
col2.metric("총 예상 방문객 규모", f"{int(filtered_df['visitors_clean'].sum()):,}명")
col3.metric("가장 많은 축제 유형", filtered_df['festivaltype'].mode()[0] if not filtered_df.empty else "-")

st.markdown("### 📊 데이터 시각화")

# 차트 영역 1: 월별 축제 개최 현황 & 축제 유형 비율
c1, c2 = st.columns(2)

with c1:
    st.subheader("월별 축제 개최 빈도")
    if not filtered_df.empty:
        # startmonth 기준으로 집계
        monthly_counts = filtered_df['startmonth'].value_counts().sort_index().reset_index()
        monthly_counts.columns = ['월', '축제 수']
        fig_month = px.bar(monthly_counts, x='월', y='축제 수', text_auto=True, color='축제 수', color_continuous_scale='Blues')
        st.plotly_chart(fig_month, use_container_width=True)

with c2:
    st.subheader("축제 유형별 비율")
    if not filtered_df.empty:
        fig_pie = px.pie(filtered_df, names='festivaltype', values='visitors_clean', title='방문객 수 기준 유형 점유율')
        st.plotly_chart(fig_pie, use_container_width=True)

# 차트 영역 2: 방문객 수가 가장 많은 축제 Top 10
st.subheader("🏆 작년 방문객 수 Top 10 축제")
if not filtered_df.empty:
    top_festivals = filtered_df.nlargest(10, 'visitors_clean')
    fig_bar = px.bar(
        top_festivals, 
        x='visitors_clean', 
        y='festivalname', 
        orientation='h',
        text_auto=',',
        color='state',
        labels={'visitors_clean': '방문객 수', 'festivalname': '축제명'}
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}) # 내림차순 정렬
    st.plotly_chart(fig_bar, use_container_width=True)

# 5. 원본 데이터 보기
with st.expander("원본 데이터 보기"):
    st.dataframe(filtered_df)
