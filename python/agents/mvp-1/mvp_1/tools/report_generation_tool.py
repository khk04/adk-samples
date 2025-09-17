"""리포트 생성 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import json
import os
from datetime import datetime
import numpy as np


class ReportGenerationInput(BaseModel):
    """리포트 생성 입력"""
    user_responses: Dict[str, Any] = Field(..., description="5단계 질의에서 수집된 사용자 응답")
    data_file_path: str = Field(..., description="분석할 데이터 파일 경로")
    data_schema: Dict[str, str] = Field(..., description="데이터 스키마 정보")
    data_summary: Dict[str, Any] = Field(..., description="데이터 요약 통계")
    output_format: str = Field(default="markdown", description="출력 형식 (markdown, html, txt)")


class ReportGenerationOutput(BaseModel):
    """리포트 생성 출력"""
    report_content: str = Field(..., description="생성된 리포트 내용")
    report_file_path: str = Field(..., description="저장된 리포트 파일 경로")
    charts_generated: List[str] = Field(default_factory=list, description="생성된 차트 파일 경로들")
    success: bool = Field(..., description="리포트 생성 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def generate_comprehensive_report(
    user_responses: Dict[str, Any],
    data_file_path: str = "",
    data_schema: Dict[str, str] = {},
    data_summary: Dict[str, Any] = {},
    output_format: str = "markdown"
) -> ReportGenerationOutput:
    """
    사용자 응답과 데이터를 바탕으로 포괄적인 분석 리포트를 생성합니다.
    data_file_path가 비어있으면 자동으로 vdata 폴더에서 CSV 파일을 찾습니다.
    """
    try:
        # 데이터 파일 경로 자동 탐지
        if not data_file_path:
            print("📂 데이터 파일 자동 탐지 시작...")
            data_file_path = _find_data_file()
            if not data_file_path:
                # 현재 작업 디렉토리와 예상 경로 정보 제공
                current_dir = os.getcwd()
                expected_path = os.path.join(current_dir, "data", "vdata")
                
                return ReportGenerationOutput(
                    report_content="",
                    report_file_path="",
                    success=False,
                    message=f"""❌ 데이터 파일을 찾을 수 없습니다.

현재 작업 디렉토리: {current_dir}
예상 데이터 경로: {expected_path}

다음을 확인해주세요:
1. data/vdata 폴더가 존재하는지 확인
2. vdata 폴더에 CSV 또는 Excel 파일이 있는지 확인
3. 파일 권한이 읽기 가능한지 확인

사용 가능한 파일 형식: .csv, .xlsx, .xls"""
                )
            else:
                print(f"✅ 데이터 파일 발견: {data_file_path}")
        
        # 데이터 로드
        df = _load_data(data_file_path)
        if df is None:
            return ReportGenerationOutput(
                report_content="",
                report_file_path="",
                success=False,
                message=f"데이터 파일({data_file_path})을 로드할 수 없습니다."
            )
        
        # 데이터 스키마와 요약 정보가 없으면 자동 생성
        if not data_schema:
            print("📊 데이터 스키마 자동 생성...")
            data_schema = {col: str(df[col].dtype) for col in df.columns}
        
        if not data_summary:
            print("📈 데이터 요약 정보 자동 생성...")
            data_summary = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data_types": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict()
            }
        
        # 리포트 내용 생성
        report_content = _generate_report_content(
            df, user_responses, data_schema, data_summary, data_file_path
        )
        
        # 리포트 파일 저장
        report_file_path = _save_report(report_content, output_format)
        
        # 차트 생성 (선택적)
        charts_generated = _generate_charts(df, user_responses)
        
        return ReportGenerationOutput(
            report_content=report_content,
            report_file_path=report_file_path,
            charts_generated=charts_generated,
            success=True,
            message=f"리포트가 성공적으로 생성되었습니다. 파일 위치: {report_file_path}"
        )
        
    except Exception as e:
        return ReportGenerationOutput(
            report_content="",
            report_file_path="",
            success=False,
            message=f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _find_data_file() -> Optional[str]:
    """vdata 폴더에서 분석할 데이터 파일을 자동으로 찾습니다."""
    try:
        # 현재 작업 디렉토리 확인
        current_dir = os.getcwd()
        print(f"현재 작업 디렉토리: {current_dir}")
        
        # vdata 폴더 경로들 확인 (우선순위 순)
        possible_paths = [
            # 절대 경로
            "/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/vdata",
            # 현재 디렉토리 기준 상대 경로
            "data/vdata",
            "./data/vdata",
            # 상위 디렉토리 기준
            "../data/vdata",
            "../../data/vdata",
            # mvp_1 폴더 내에서 실행되는 경우
            "../data/vdata",
            "data/vdata",
            # 기타 가능한 경로
            "vdata",
            "./vdata"
        ]
        
        for base_path in possible_paths:
            abs_path = os.path.abspath(base_path)
            print(f"경로 확인 중: {base_path} -> {abs_path}")
            
            if os.path.exists(abs_path):
                print(f"✅ 경로 발견: {abs_path}")
                
                # 디렉토리 내 파일 목록 확인
                try:
                    files = os.listdir(abs_path)
                    print(f"파일 목록: {files}")
                    
                    # CSV 파일 우선 검색
                    for file in files:
                        if file.endswith('.csv'):
                            full_path = os.path.join(abs_path, file)
                            print(f"✅ CSV 파일 발견: {full_path}")
                            return full_path
                    
                    # Excel 파일 검색
                    for file in files:
                        if file.endswith(('.xlsx', '.xls')):
                            full_path = os.path.join(abs_path, file)
                            print(f"✅ Excel 파일 발견: {full_path}")
                            return full_path
                            
                except Exception as e:
                    print(f"❌ 디렉토리 읽기 실패 ({abs_path}): {e}")
                    continue
            else:
                print(f"❌ 경로 없음: {abs_path}")
        
        print("❌ 데이터 파일을 찾을 수 없습니다.")
        return None
        
    except Exception as e:
        print(f"❌ _find_data_file 실행 중 오류: {e}")
        return None


def _load_data(file_path: str) -> Optional[pd.DataFrame]:
    """데이터 파일을 로드합니다."""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            return None
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return None


def _generate_report_content(
    df: pd.DataFrame,
    user_responses: Dict[str, Any],
    data_schema: Dict[str, str],
    data_summary: Dict[str, Any],
    data_file_path: str = ""
) -> str:
    """리포트 내용을 생성합니다."""
    
    # 기본 정보 추출
    report_type = user_responses.get("report_type", "종합 분석 리포트")
    analysis_criteria = user_responses.get("analysis_criteria", "전체 데이터")
    data_scope = user_responses.get("data_scope_and_filtering", "전체 범위")
    report_style = user_responses.get("report_style", "상세 분석")
    
    # 현재 시간
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    # 데이터 필터링 적용
    filtered_df = _apply_data_filtering(df, data_scope)
    
    # 리포트 시작
    report = f"""# {report_type}

**생성 일시:** {current_time}
**데이터 소스:** {os.path.basename(data_file_path) if data_file_path else "분석 데이터"}
**분석 범위:** {data_scope}
**분석 기준:** {analysis_criteria}

---

## 📊 데이터 개요

### 기본 정보
- **전체 데이터 건수:** {len(df):,}개
- **분석 대상 건수:** {len(filtered_df):,}개
- **컬럼 수:** {len(df.columns)}개
- **데이터 기간:** {_get_date_range(df)}

### 데이터 구조
"""
    
    # 컬럼 정보 추가
    report += "\n| 컬럼명 | 데이터 타입 | 결측값 | 설명 |\n"
    report += "|--------|-------------|--------|------|\n"
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        missing_count = df[col].isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        description = _get_column_description(col)
        report += f"| {col} | {dtype} | {missing_count}개 ({missing_pct:.1f}%) | {description} |\n"
    
    # 분석 결과 섹션
    report += "\n---\n\n## 📈 주요 분석 결과\n\n"
    
    # 수치형 컬럼 분석
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        report += "### 수치 데이터 요약\n\n"
        for col in numeric_cols:
            stats = df[col].describe()
            report += f"**{col}:**\n"
            report += f"- 평균: {stats['mean']:.2f}\n"
            report += f"- 중앙값: {stats['50%']:.2f}\n"
            report += f"- 최솟값: {stats['min']:.2f}\n"
            report += f"- 최댓값: {stats['max']:.2f}\n"
            report += f"- 표준편차: {stats['std']:.2f}\n\n"
    
    # 범주형 컬럼 분석
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        report += "### 범주형 데이터 분석\n\n"
        for col in categorical_cols:
            if col not in df.columns:
                continue
            value_counts = df[col].value_counts().head(10)
            total_unique = df[col].nunique()
            
            report += f"**{col}:** (총 {total_unique}개 고유값)\n"
            for idx, (value, count) in enumerate(value_counts.items()):
                pct = (count / len(df)) * 100
                report += f"{idx+1}. {value}: {count}개 ({pct:.1f}%)\n"
            report += "\n"
    
    # 사용자 지정 분석 기준에 따른 추가 분석
    report += _generate_custom_analysis(filtered_df, analysis_criteria, user_responses)
    
    # 인사이트 및 결론
    report += "\n---\n\n## 💡 주요 인사이트\n\n"
    insights = _generate_insights(filtered_df, user_responses)
    for i, insight in enumerate(insights, 1):
        report += f"{i}. {insight}\n"
    
    # 결론 및 권장사항
    report += "\n---\n\n## 📝 결론 및 권장사항\n\n"
    recommendations = _generate_recommendations(filtered_df, user_responses)
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"
    
    # 보고서 스타일에 따른 추가 정보
    if "상세" in report_style:
        report += "\n---\n\n## 📋 상세 분석 정보\n\n"
        report += _generate_detailed_analysis(filtered_df, user_responses)
    
    report += f"\n---\n\n**리포트 생성 완료:** {current_time}"
    
    return report


def _apply_data_filtering(df: pd.DataFrame, data_scope: str) -> pd.DataFrame:
    """데이터 범위 및 필터링을 적용합니다."""
    # 간단한 필터링 로직 - 실제로는 사용자 응답을 파싱해서 적용
    if "최근" in data_scope:
        # 날짜 컬럼이 있으면 최근 데이터만 필터링
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            df = df.sort_values(date_cols[0]).tail(int(len(df) * 0.3))
    
    return df


def _get_date_range(df: pd.DataFrame) -> str:
    """데이터의 날짜 범위를 반환합니다."""
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        date_col = date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        if pd.notna(min_date) and pd.notna(max_date):
            return f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
    
    return "날짜 정보 없음"


def _get_column_description(col_name: str) -> str:
    """컬럼명을 바탕으로 설명을 생성합니다."""
    col_lower = col_name.lower()
    
    if any(word in col_lower for word in ['id', 'key']):
        return "식별자"
    elif any(word in col_lower for word in ['name', 'title']):
        return "명칭"
    elif any(word in col_lower for word in ['date', 'time']):
        return "날짜/시간"
    elif any(word in col_lower for word in ['amount', 'price', 'cost', 'value']):
        return "금액/가격"
    elif any(word in col_lower for word in ['count', 'number', 'qty']):
        return "수량"
    elif any(word in col_lower for word in ['status', 'state']):
        return "상태"
    else:
        return "기타"


def _generate_custom_analysis(df: pd.DataFrame, analysis_criteria: str, user_responses: Dict[str, Any]) -> str:
    """사용자 지정 분석 기준에 따른 추가 분석을 생성합니다."""
    analysis = "\n### 맞춤 분석\n\n"
    
    # 간단한 예시 분석들
    if "성과" in analysis_criteria or "실적" in analysis_criteria:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis += "**성과 지표 분석:**\n"
            for col in numeric_cols[:3]:  # 상위 3개 수치 컬럼
                total = df[col].sum()
                avg = df[col].mean()
                analysis += f"- {col}: 총합 {total:.2f}, 평균 {avg:.2f}\n"
    
    if "트렌드" in analysis_criteria:
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            analysis += "\n**트렌드 분석:**\n"
            analysis += "- 시계열 데이터 기반 트렌드 분석이 가능합니다.\n"
    
    return analysis


def _generate_insights(df: pd.DataFrame, user_responses: Dict[str, Any]) -> List[str]:
    """데이터 기반 인사이트를 생성합니다."""
    insights = []
    
    # 데이터 규모 인사이트
    insights.append(f"총 {len(df):,}건의 데이터를 분석했습니다.")
    
    # 결측값 인사이트
    missing_ratio = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    if missing_ratio > 10:
        insights.append(f"전체 데이터의 {missing_ratio:.1f}%가 결측값으로, 데이터 품질 개선이 필요합니다.")
    elif missing_ratio < 1:
        insights.append("데이터 품질이 우수하며 결측값이 거의 없습니다.")
    
    # 수치형 데이터 인사이트
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        high_var_cols = []
        for col in numeric_cols:
            if df[col].std() / df[col].mean() > 1:  # 변동계수가 1 이상
                high_var_cols.append(col)
        
        if high_var_cols:
            insights.append(f"{', '.join(high_var_cols)} 항목에서 높은 변동성이 관찰됩니다.")
    
    # 범주형 데이터 인사이트
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        for col in categorical_cols[:2]:  # 상위 2개만
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio > 0.8:
                insights.append(f"{col} 항목은 매우 다양한 값들을 가지고 있습니다.")
            elif unique_ratio < 0.1:
                insights.append(f"{col} 항목은 소수의 값들에 집중되어 있습니다.")
    
    return insights


def _generate_recommendations(df: pd.DataFrame, user_responses: Dict[str, Any]) -> List[str]:
    """데이터 분석 결과를 바탕으로 권장사항을 생성합니다."""
    recommendations = []
    
    # 데이터 품질 관련 권장사항
    missing_cols = df.columns[df.isnull().any()].tolist()
    if missing_cols:
        recommendations.append(f"결측값이 있는 컬럼({', '.join(missing_cols[:3])})에 대한 데이터 수집 개선을 권장합니다.")
    
    # 분석 관련 권장사항
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        recommendations.append("수치형 변수들 간의 상관관계 분석을 통해 추가 인사이트를 얻을 수 있습니다.")
    
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        recommendations.append("시계열 분석을 통해 트렌드와 계절성 패턴을 파악할 수 있습니다.")
    
    # 비즈니스 관련 권장사항
    report_type = user_responses.get("report_type", "")
    if "성과" in report_type:
        recommendations.append("핵심 성과 지표(KPI) 설정을 통한 정기적인 모니터링을 권장합니다.")
    
    if "고객" in report_type:
        recommendations.append("고객 세분화 분석을 통한 맞춤형 서비스 전략 수립을 고려해보세요.")
    
    return recommendations


def _generate_detailed_analysis(df: pd.DataFrame, user_responses: Dict[str, Any]) -> str:
    """상세 분석 정보를 생성합니다."""
    detailed = ""
    
    # 상관관계 분석
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        detailed += "### 상관관계 분석\n\n"
        corr_matrix = df[numeric_cols].corr()
        
        # 강한 상관관계 찾기
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    strong_corr.append(f"- {col1} ↔ {col2}: {corr_val:.3f}")
        
        if strong_corr:
            detailed += "**강한 상관관계:**\n"
            detailed += "\n".join(strong_corr) + "\n\n"
        else:
            detailed += "수치형 변수들 간에 강한 상관관계는 발견되지 않았습니다.\n\n"
    
    # 이상치 분석
    detailed += "### 이상치 분석\n\n"
    outlier_info = []
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        if len(outliers) > 0:
            pct = (len(outliers) / len(df)) * 100
            outlier_info.append(f"- {col}: {len(outliers)}개 ({pct:.1f}%)")
    
    if outlier_info:
        detailed += "**발견된 이상치:**\n"
        detailed += "\n".join(outlier_info) + "\n\n"
    else:
        detailed += "주요 수치형 변수에서 이상치가 발견되지 않았습니다.\n\n"
    
    return detailed


def _generate_charts(df: pd.DataFrame, user_responses: Dict[str, Any]) -> List[str]:
    """차트를 생성합니다 (선택적 기능)."""
    # 이 부분은 matplotlib/seaborn을 사용하여 실제 차트 생성
    # 현재는 빈 리스트 반환
    return []


def _save_report(content: str, output_format: str) -> str:
    """리포트를 파일로 저장합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # reports 디렉토리 생성 (절대 경로 사용)
    current_dir = os.getcwd()
    reports_dir = os.path.join(current_dir, "data", "reports")
    
    print(f"📁 리포트 저장 디렉토리: {reports_dir}")
    os.makedirs(reports_dir, exist_ok=True)
    
    if output_format.lower() == "markdown":
        file_path = os.path.join(reports_dir, f"report_{timestamp}.md")
    elif output_format.lower() == "html":
        file_path = os.path.join(reports_dir, f"report_{timestamp}.html")
        # 마크다운을 HTML로 변환 (간단한 변환)
        content = _markdown_to_html(content)
    else:
        file_path = os.path.join(reports_dir, f"report_{timestamp}.txt")
    
    print(f"💾 리포트 파일 저장: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def _markdown_to_html(markdown_content: str) -> str:
    """간단한 마크다운을 HTML로 변환합니다."""
    html = markdown_content
    
    # 헤더 변환
    html = html.replace('### ', '<h3>').replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>')
    
    # 굵은 글씨
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    
    # 테이블 (간단한 변환)
    lines = html.split('\n')
    in_table = False
    result_lines = []
    
    for line in lines:
        if '|' in line and not in_table:
            in_table = True
            result_lines.append('<table border="1">')
            result_lines.append('<tr>')
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            for cell in cells:
                result_lines.append(f'<th>{cell}</th>')
            result_lines.append('</tr>')
        elif '|' in line and in_table:
            if '---' in line:
                continue
            result_lines.append('<tr>')
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            for cell in cells:
                result_lines.append(f'<td>{cell}</td>')
            result_lines.append('</tr>')
        elif in_table and '|' not in line:
            in_table = False
            result_lines.append('</table>')
            result_lines.append(line)
        else:
            result_lines.append(line)
    
    if in_table:
        result_lines.append('</table>')
    
    return '\n'.join(result_lines)


class ReportGenerationTool:
    def __init__(self):
        self.name = "generate_comprehensive_report"
        self.description = "사용자 응답과 데이터를 바탕으로 포괄적인 분석 리포트를 생성합니다."
        self.input_model = ReportGenerationInput
        self.output_model = ReportGenerationOutput
        self.execute = generate_comprehensive_report