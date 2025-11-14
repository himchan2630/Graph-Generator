import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import urllib.request
import os
import streamlit as st
import pandas as pd
import io
import numpy as np

# ==========================================
# ① Noto Sans KR 폰트 다운로드 & matplotlib 등록
# ==========================================

FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansKR-Regular.otf"
FONT_PATH = "NotoSansKR-Regular.otf"

# Streamlit Cloud는 매 세션마다 초기화되므로 매번 확인
if not os.path.exists(FONT_PATH):
    urllib.request.urlretrieve(FONT_URL, FONT_PATH)

# 폰트 등록
fm.fontManager.addfont(FONT_PATH)
plt.rc('font', family='Noto Sans KR')
plt.rcParams['axes.unicode_minus'] = False


# ===================================================================
# 데이터 로드 함수
# ===================================================================
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding='cp949')
        else:
            st.error("지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일을 업로드해 주세요.")
            return None
        
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None


# ===================================================================
# 차트 타입 자동 결정
# ===================================================================
def determine_chart_type(df):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(df) > 5 and len(num_cols) >= 1 and len(cat_cols) >= 1:
        return 'Line'
    elif len(cat_cols) >= 1 and len(num_cols) >= 1:
        first_cat = cat_cols[0]
        if df[first_cat].nunique() <= 5 and df[first_cat].nunique() > 1:
            return 'Pie'
        return 'Bar'
    elif len(num_cols) >= 1:
        return 'Line'
    
    return 'Bar'


# ===================================================================
# 차트 생성 함수
# ===================================================================
def generate_chart(df, chart_type, x_col=None, y_col=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        if chart_type == 'Bar':
            if x_col and y_col:
                data = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
                ax.bar(data.index, data.values, color='#4A90E2')
                ax.set_title(f'{x_col} 별 {y_col} 합계 (막대 그래프)')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            else:
                num_col = df.select_dtypes(include=np.number).columns.tolist()[0]
                ax.bar(df.index, df[num_col], color='#4A90E2')
                ax.set_title(f'데이터 ({num_col}) 막대 그래프')
                ax.set_xlabel('Index')
                ax.set_ylabel(num_col)

        elif chart_type == 'Line':
            if x_col and y_col:
                ax.plot(df[x_col], df[y_col], marker='o', color='#50E3C2')
                ax.set_title(f'{x_col} 대비 {y_col} 추이 (꺾은선 그래프)')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            else:
                num_col = df.select_dtypes(include=np.number).columns.tolist()[0]
                ax.plot(df.index, df[num_col], marker='o', color='#50E3C2')
                ax.set_title(f'데이터 ({num_col}) 추이 (꺾은선 그래프)')

        elif chart_type == 'Pie':
            if x_col and y_col:
                data = df.groupby(x_col)[y_col].sum()
                ax.pie(data.values, labels=data.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
                ax.set_title(f'{x_col} 별 {y_col} 분포 (원 그래프)')
                ax.axis('equal')
            else:
                st.warning("원 그래프를 만들 수 있는 데이터가 부족합니다.")
                return None

        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=300)
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        plt.close(fig)
        st.error(f"차트 생성 중 오류 발생: {e}")
        return None


# ===================================================================
# X, Y 컬럼 자동 선택
# ===================================================================
def get_chart_params(df, chart_type):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    x_col = None
    y_col = None
    
    if chart_type in ['Bar', 'Pie']:
        if cat_cols and num_cols:
            x_col = cat_cols[0]
            y_col = num_cols[0]

    elif chart_type == 'Line':
        if num_cols:
            y_col = num_cols[0]
            if len(num_cols) >= 2:
                x_col = num_cols[0]
                y_col = num_cols[1]
            elif cat_cols:
                x_col = cat_cols[0]

    return x_col, y_col


# ===================================================================
# Streamlit UI
# ===================================================================
st.set_page_config(
    page_title="표 → 그래프 변환기",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
.main-header {
    font-size: 30px;
    font-weight: 700;
    color: #1E90FF;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 데이터 표 → 자동 그래프 변환기</div>', unsafe_allow_html=True)
st.markdown("---")


uploaded_file = st.file_uploader(
    "1. 엑셀 또는 CSV 파일을 업로드하세요.",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=False
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        st.success("파일 로드 완료!")

        st.subheader("2. 데이터 미리보기")
        st.dataframe(df.head(), use_container_width=True)

        auto_type = determine_chart_type(df)

        st.subheader("3. 그래프 옵션 선택")
        col1, col2 = st.columns(2)

        with col1:
            options = ['Bar (막대)', 'Line (꺾은선)', 'Pie (원)']
            display = {
                "Bar": "막대",
                "Line": "꺾은선",
                "Pie": "원"
            }

            default_index = options.index(f"{auto_type} ({display[auto_type]})")

            selected_display = st.selectbox(
                f"자동 추천: {auto_type}",
                options=options,
                index=default_index
            )

            selected_type = selected_display.split(' ')[0]

        with col2:
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            all_cols = df.columns.tolist()

            x_default, y_default = get_chart_params(df, selected_type)

            x_col_final = st.selectbox("X축 컬럼", all_cols, index=all_cols.index(x_default) if x_default else 0)
            y_col_final = st.selectbox("Y축 컬럼", num_cols, index=num_cols.index(y_default) if y_default else 0)

        st.subheader("4. 생성된 그래프")

        chart = generate_chart(df, selected_type, x_col_final, y_col_final)

        if chart:
            st.image(chart, use_column_width=True)
            st.download_button(
                label="그래프 다운로드 (PNG)",
                data=chart,
                file_name="chart.png",
                mime="image/png"
            )


st.markdown("---")
st.caption("Streamlit 기반 그래프 생성기")
