import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

fm.fontManager.addfont("fonts/NanumGothic.ttf")
plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np

# Matplotlib 한글 폰트 설정 (Mac/Linux/Windows 환경에 맞게 조정 가능)
# Streamlit 클라우드 환경에서는 폰트 설정이 복잡하므로, 여기서는 기본 폰트를 사용합니다.
# 로컬에서 한글을 사용하려면 아래 주석을 풀고 폰트 경로를 설정하세요.
# from matplotlib import font_manager, rc
# font_path = 'C:/Windows/Fonts/malgun.ttf'  # 예: 맑은 고딕
# font = font_manager.FontProperties(fname=font_path).get_name()
# rc('font', family=font)
# plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지

def load_data(uploaded_file):
    """업로드된 파일을 Pandas DataFrame으로 읽어옵니다."""
    try:
        # 파일 확장자 확인
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            # 엑셀 파일 로드
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            # CSV 파일 로드 (인코딩을 utf-8로 시도, 실패 시 'cp949' 또는 'euc-kr' 시도)
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding='cp949')
        else:
            st.error("지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일을 업로드해 주세요.")
            return None
        
        # 컬럼 이름에서 불필요한 공백 제거
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

def determine_chart_type(df):
    """데이터프레임 구조를 분석하여 최적의 차트 타입을 결정하는 간단한 휴리스틱."""
    
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 1. 시계열 데이터 추정 -> 꺾은선 그래프
    # 첫 번째 컬럼이 날짜/시간 타입이고, 데이터가 충분히 많을 경우
    if len(df) > 5 and len(num_cols) >= 1 and len(cat_cols) >= 1:
        # 간단히 첫 번째 컬럼을 x축, 두 번째(숫자) 컬럼을 y축으로 사용
        return 'Line'
        
    # 2. 범주형 vs 수치형 -> 막대 그래프 또는 원 그래프
    elif len(cat_cols) >= 1 and len(num_cols) >= 1:
        first_cat_col = cat_cols[0]
        first_num_col = num_cols[0]
        
        # 범주형 컬럼의 고유값이 적을 경우 (ex: 20개 이하)
        if df[first_cat_col].nunique() <= 20:
            # 고유값이 5개 이하일 경우 원 그래프 고려, 아니면 막대 그래프
            return 'Pie' if df[first_cat_col].nunique() <= 5 and df[first_cat_col].nunique() > 1 else 'Bar'
        
        # 고유값이 많으면 막대 그래프로 처리
        return 'Bar'
        
    # 3. 그 외 (단순 수치 데이터) -> 꺾은선 그래프 (인덱스 vs 값)
    elif len(num_cols) >= 1:
        return 'Line'
    
    # 기본값
    return 'Bar'

def generate_chart(df, chart_type, x_col=None, y_col=None):
    """Matplotlib을 사용하여 지정된 타입의 차트를 생성하고 저장합니다."""
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        if chart_type == 'Bar':
            # 막대 그래프 (범주형 vs 수치형)
            if x_col and y_col:
                data = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
                ax.bar(data.index, data.values, color='#4A90E2')
                ax.set_title(f'{x_col} 별 {y_col} 합계 (막대 그래프)')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            else:
                 # 컬럼을 찾지 못하면 기본 막대 그래프 (첫 번째 수치 컬럼의 값)
                num_col = df.select_dtypes(include=np.number).columns.tolist()[0]
                ax.bar(df.index, df[num_col], color='#4A90E2')
                ax.set_title(f'데이터 ({num_col}) 막대 그래프')
                ax.set_xlabel('Index')
                ax.set_ylabel(num_col)

        elif chart_type == 'Line':
            # 꺾은선 그래프 (시계열 또는 단순 추이)
            if y_col and df.index.dtype == 'int64':
                # 단순 인덱스 기반 꺾은선
                ax.plot(df.index, df[y_col], marker='o', color='#50E3C2')
                ax.set_title(f'데이터 ({y_col}) 추이 (꺾은선 그래프)')
                ax.set_xlabel('Index')
                ax.set_ylabel(y_col)
            elif x_col and y_col:
                # 두 컬럼을 사용한 꺾은선
                ax.plot(df[x_col], df[y_col], marker='o', color='#50E3C2')
                ax.set_title(f'{x_col} 대비 {y_col} 추이 (꺾은선 그래프)')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            else:
                 # 첫 번째 수치 컬럼의 값
                num_col = df.select_dtypes(include=np.number).columns.tolist()[0]
                ax.plot(df.index, df[num_col], marker='o', color='#50E3C2')
                ax.set_title(f'데이터 ({num_col}) 추이 (꺾은선 그래프)')
                ax.set_xlabel('Index')
                ax.set_ylabel(num_col)


        elif chart_type == 'Pie':
            # 원 그래프 (범주형 분포)
            if x_col and y_col:
                data = df.groupby(x_col)[y_col].sum()
                ax.pie(data.values, labels=data.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
                ax.set_title(f'{x_col} 별 {y_col} 분포 (원 그래프)')
                ax.axis('equal')  # 원형을 유지
            else:
                st.warning("원 그래프를 생성할 수 있는 적절한 범주형 및 수치형 데이터가 부족합니다.")
                return None

        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        # 차트를 PNG 이미지로 메모리에 저장
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=300)
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        plt.close(fig)
        st.error(f"차트 생성 중 오류가 발생했습니다: {e}")
        return None

def get_chart_params(df, chart_type):
    """차트 타입에 따라 사용할 x, y 컬럼을 찾습니다."""
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    x_col, y_col = None, None
    
    if chart_type in ['Bar', 'Pie']:
        # 막대/원 그래프는 범주 vs 수치형 쌍을 선호
        if cat_cols and num_cols:
            x_col = cat_cols[0]
            y_col = num_cols[0]
    elif chart_type == 'Line':
        # 꺾은선 그래프는 인덱스 vs 수치형, 또는 수치 vs 수치형을 선호
        if num_cols:
            y_col = num_cols[0]
            if len(num_cols) >= 2:
                # 두 개의 수치 컬럼이 있다면 첫 번째를 x축으로 사용
                x_col = num_cols[0]
                y_col = num_cols[1]
            elif cat_cols:
                # 인덱스 대신 범주형 컬럼을 x축으로 사용하는 것도 고려
                x_col = cat_cols[0]

    return x_col, y_col

# ==============================================================================
# Streamlit UI 구성 시작
# ==============================================================================

st.set_page_config(
    page_title="표 -> 그래프 변환기",
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
    margin-bottom: 10px;
}
.stFileUploader > div > div {
    border: 3px dashed #1E90FF;
    border-radius: 10px;
    padding: 20px;
    background-color: #F8F8FF;
    text-align: center;
}
.stButton>button {
    background-color: #4A90E2;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px 20px;
    transition: all 0.2s;
}
.stButton>button:hover {
    background-color: #357ABD;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 데이터 표 -> 자동 그래프 변환기</div>', unsafe_allow_html=True)
st.markdown("---")

uploaded_file = st.file_uploader(
    "1. 엑셀 파일 (.xlsx, .xls) 또는 CSV 파일을 업로드하세요.",
    type=["xlsx", "xls", "csv"],
    help="파일을 드래그 앤 드롭하거나 클릭하여 선택하세요.",
    accept_multiple_files=False
)

if uploaded_file is not None:
    # 2. 데이터 로드
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        st.success("✅ 파일 업로드 및 로드 완료!")
        
        # 3. 데이터 미리보기
        st.subheader("2. 업로드된 데이터 미리보기 (상위 5개 행)")
        st.dataframe(df.head(), use_container_width=True)
        
        # 4. 최적 그래프 타입 결정
        auto_chart_type = determine_chart_type(df)
        
        # 5. 사용자에게 타입 선택 권한 부여
        st.subheader("3. 그래프 옵션 선택")
        col1, col2 = st.columns(2)
        
        with col1:
            chart_type_options = ['Bar (막대)', 'Line (꺾은선)', 'Pie (원)']
            chart_name_map = {"Bar": "막대", "Line": "꺾은선", "Pie": "원"}
            chart_kor = chart_name_map.get(auto_chart_type, "막대")

            # 자동 결정된 타입을 기본값으로 설정
            default_index = chart_type_options.index(f"{auto_chart_type} ({chart_kor})")

            selected_chart_display = st.selectbox(
                f"자동 결정: **{auto_chart_type}** | 그래프 유형 선택",
                options=chart_type_options,
                index=default_index,
                key='chart_select'
                )

            # 괄호 안의 한글 부분을 제거하여 순수 타입만 추출
            selected_chart_type = selected_chart_display.split(' ')[0]

        # 6. x, y 축 컬럼 설정
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        all_cols = df.columns.tolist()
        
        # 결정된 타입에 따른 기본 x, y 컬럼 찾기
        x_default, y_default = get_chart_params(df, selected_chart_type)
        
        with col2:
            x_options = all_cols
            y_options = num_cols

            # x축 선택
            default_x_index = x_options.index(x_default) if x_default in x_options else 0
            x_col_final = st.selectbox("X축 (범주 또는 기준) 선택", options=x_options, index=default_x_index, key='x_col')
            
            # y축 선택 (수치형만)
            default_y_index = y_options.index(y_default) if y_default in y_options else (y_options.index(num_cols[0]) if num_cols else 0)
            y_col_final = st.selectbox("Y축 (값, 수치형) 선택", options=y_options, index=default_y_index, key='y_col')
            
            # 최종 데이터를 차트 생성 함수에 전달
            if selected_chart_type in ['Bar', 'Pie']:
                # 막대/원 그래프는 집계가 필요하므로 x_col이 범주형인지 확인
                if x_col_final not in cat_cols:
                    st.warning("경고: 막대/원 그래프의 X축은 범주형 데이터(텍스트)를 선택하는 것이 일반적입니다.")
            
            elif selected_chart_type == 'Line':
                # 꺾은선 그래프는 x, y 모두 수치형이거나, x축이 시간/순서일 때 적합
                if x_col_final not in num_cols and x_col_final not in cat_cols:
                    st.warning("경고: 꺾은선 그래프의 X축은 수치형 또는 시간/순서 데이터가 적합합니다.")

        # 7. 그래프 생성 및 표시
        st.subheader("4. 생성된 그래프")
        
        # 차트 생성 및 PNG 버퍼 받기
        chart_buffer = generate_chart(df, selected_chart_type, x_col_final, y_col_final)

        if chart_buffer:
            # 이미지 표시
            st.image(chart_buffer, caption=f"생성된 {selected_chart_type} 그래프", use_column_width=True)
            
            # 다운로드 버튼
            st.markdown("---")
            st.download_button(
                label="🖼️ 그래프 이미지 (PNG) 다운로드",
                data=chart_buffer,
                file_name=f"Chart_{uploaded_file.name.split('.')[0]}_{selected_chart_type}.png",
                mime="image/png",
                key='download_button'
            )
            st.info("다운로드 버튼을 클릭하면 그래프 이미지 파일을 저장할 수 있습니다.")
        else:
            st.error("선택된 옵션으로는 그래프를 생성할 수 없습니다. 다른 X, Y 축을 선택해 보세요.")

    elif df is not None:
        st.warning("파일은 성공적으로 로드되었으나 데이터프레임이 비어 있습니다.")

# Streamlit 앱 종료 후 사용자 피드백
st.markdown("---")
st.caption("파이썬 Streamlit을 이용하여 구축되었습니다.")
