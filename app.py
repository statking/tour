# streamlit_app.py
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
from streamlit_folium import st_folium

st.set_page_config(page_title="전국 랜덤여행", layout="wide")

# --- 파일 경로 (업로드한 파일 사용) ---
GEO_PATH = "sgg_simple.geojson"
XLSX_PATH = "sigcd_mapping.xlsx"

# --- 상태값 초기화 ---
if "selected_sgg" not in st.session_state:
    st.session_state.selected_sgg = None

# --- 데이터 로드 함수 (엑셀/지오JSON을 매번 새로 읽어 최신 상태 반영) ---
@st.cache_data(show_spinner=False)
def load_geojson(path):
    return json.load(open(path, encoding="utf-8"))

def load_visit_df():
    visit_ = pd.read_excel(XLSX_PATH)
    # 원본 코드 유지: code는 5자리 zero-fill
    visit_["code"] = visit_.code.map(lambda x: str(x).zfill(5))
    return visit_

def save_visit_df(df):
    df.to_excel(XLSX_PATH, index=False)

# --- 데이터 로드 ---
korea = load_geojson(GEO_PATH)
visit = load_visit_df()

# --- UI: 제목 & 버튼들 ---
st.title("전국 랜덤여행 지도")

col1, col2, col3 = st.columns([1,1,1], gap="small")

with col1:
    if st.button("랜덤여행 🎲", use_container_width=True):
        # 요구사항 1: 엑셀의 '시군구명'에서 랜덤 선택 (방문여부 무관, 원문 요구 충실)
        if "시군구명" in visit.columns and len(visit) > 0:
            choice = visit["시군구명"].sample(1).iloc[0]
            st.session_state.selected_sgg = choice
        else:
            st.session_state.selected_sgg = None

with col2:
    if st.button("여행 완료 ✅", use_container_width=True):
        # 요구사항 2: 선택된 시군구명의 방문여부를 1로 저장 후 지도 갱신
        if st.session_state.selected_sgg is not None and "시군구명" in visit.columns:
            mask = visit["시군구명"] == st.session_state.selected_sgg
            if mask.any():
                visit.loc[mask, "방문여부"] = 1
                save_visit_df(visit)
                # 저장 후 최신 데이터로 재로딩
                visit = load_visit_df()
        else:
            st.warning("먼저 '랜덤여행'으로 시군구를 선택하세요.")

with col3:
    if st.button("초기화 ♻️", use_container_width=True):
        # 요구사항 3: 방문여부를 전부 0으로 초기화 후 지도 갱신
        if "방문여부" in visit.columns:
            visit["방문여부"] = 0
            save_visit_df(visit)
            visit = load_visit_df()
            st.session_state.selected_sgg = None

# --- 선택된 여행지 안내 ---
if st.session_state.selected_sgg:
    st.success(f"이번 랜덤 여행지는 **{st.session_state.selected_sgg}** 입니다!")

# --- 원본 코드(지도 생성)는 그대로 두되 Streamlit 렌더링만 추가 ---
# 원본 코드 시작 (최소 수정)
map = folium.Map(
    location=[36.84601435658271, 128.06870778562285],
    zoom_start=8,
    width='700px',
    height='700px'
)

choropleth = folium.Choropleth(
    geo_data=korea,
    data=visit,
    columns=('code', '방문여부'),
    key_on="feature.properties.SIG_CD",
    fill_color="Blues",
).add_to(map)
# 원본 코드 끝

# 보기 편하도록 툴팁(시군구명, 방문여부)만 살짝 추가(지도의 데이터 자체는 변경 없음)
try:
    folium.GeoJson(
        korea,
        name="tooltip",
        tooltip=folium.GeoJsonTooltip(
            fields=["SIG_KOR_NM", "SIG_CD"],
            aliases=["시군구명", "코드"],
            labels=True,
            sticky=False
        )
    ).add_to(map)
except Exception:
    pass

# --- 스트림릿에서 지도 출력 ---
st_folium(map, width=700, height=700)

# --- 요약 표시 (선택사항: 현재 방문여부 집계) ---
visited_cnt = int((visit["방문여부"] == 1).sum()) if "방문여부" in visit.columns else 0
total_cnt = len(visit)
st.caption(f"방문 완료: {visited_cnt} / {total_cnt}")
