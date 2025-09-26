"""실제 리포트 생성 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import os
import json
from datetime import datetime


class ReportGenerationInput(BaseModel):
    """리포트 생성 입력"""
    data_file_path: str = Field(..., description="분석할 데이터 파일 경로")
    query_responses: Dict[str, Any] = Field(..., description="5단계 질의에서 수집된 사용자 응답")
    analysis_context: Dict[str, Any] = Field(default_factory=dict, description="분석 컨텍스트")
    report_type: str = Field(default="comprehensive", description="리포트 유형")


class ReportGenerationOutput(BaseModel):
    """리포트 생성 출력"""
    success: bool = Field(..., description="리포트 생성 성공 여부")
    report_content: str = Field(..., description="생성된 리포트 내용")
    report_summary: Dict[str, Any] = Field(default_factory=dict, description="리포트 요약")
    file_path: str = Field(default="", description="저장된 리포트 파일 경로")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def generate_report(
    data_file_path: str,
    query_responses: Dict[str, Any],
    analysis_context: Dict[str, Any] = {},
    report_type: str = "comprehensive"
) -> ReportGenerationOutput:
    """
    수집된 질의 응답을 바탕으로 실제 데이터를 분석하여 포괄적인 리포트를 생성합니다.
    """
    try:
        # 데이터 파일 읽기
        if not os.path.exists(data_file_path):
            return ReportGenerationOutput(
                success=False,
                report_content="",
                error_message=f"데이터 파일을 찾을 수 없습니다: {data_file_path}"
            )
        
        # 데이터 로드
        if data_file_path.endswith('.csv'):
            df = pd.read_csv(data_file_path)
        elif data_file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(data_file_path)
        else:
            return ReportGenerationOutput(
                success=False,
                report_content="",
                error_message="지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 사용해주세요."
            )
        
        # 분석 컨텍스트에서 도메인 정보 추출
        domain_info = analysis_context.get("domain_info", {})
        primary_domain = domain_info.get("primary_domain", "general")
        
        # 도메인별 특화 분석 수행
        analysis_results = _perform_domain_specific_analysis(df, primary_domain, query_responses)
        
        # 리포트 생성
        report_content = _generate_comprehensive_report(
            df, 
            analysis_results, 
            query_responses, 
            primary_domain,
            analysis_context
        )
        
        # 리포트 요약 생성
        report_summary = _generate_report_summary(analysis_results, query_responses)
        
        # 리포트 파일 저장
        file_path = _save_report_to_file(report_content, primary_domain)
        
        return ReportGenerationOutput(
            success=True,
            report_content=report_content,
            report_summary=report_summary,
            file_path=file_path
        )
        
    except Exception as e:
        return ReportGenerationOutput(
            success=False,
            report_content="",
            error_message=f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _perform_domain_specific_analysis(df: pd.DataFrame, domain: str, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """도메인별 특화 분석을 수행합니다."""
    analysis_results = {
        "data_overview": _get_data_overview(df),
        "domain_analysis": {},
        "key_insights": [],
        "recommendations": []
    }
    
    # 도메인별 특화 분석
    if domain == "ecommerce":
        analysis_results["domain_analysis"] = _analyze_ecommerce_data(df, query_responses)
    elif domain == "finance":
        analysis_results["domain_analysis"] = _analyze_finance_data(df, query_responses)
    elif domain == "hr":
        analysis_results["domain_analysis"] = _analyze_hr_data(df, query_responses)
    elif domain == "retail":
        analysis_results["domain_analysis"] = _analyze_retail_data(df, query_responses)
    else:
        analysis_results["domain_analysis"] = _analyze_general_data(df, query_responses)
    
    # 공통 분석
    analysis_results["statistical_summary"] = _get_statistical_summary(df)
    analysis_results["key_insights"] = _extract_key_insights(df, analysis_results["domain_analysis"])
    analysis_results["recommendations"] = _generate_recommendations(analysis_results["key_insights"], domain)
    
    return analysis_results


def _get_data_overview(df: pd.DataFrame) -> Dict[str, Any]:
    """데이터 개요 정보를 생성합니다."""
    return {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }


def _analyze_ecommerce_data(df: pd.DataFrame, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """이커머스 데이터 분석"""
    analysis = {}
    
    # 매출 관련 분석
    revenue_cols = [col for col in df.columns if any(word in col.lower() for word in ['revenue', 'sales', 'amount', 'price'])]
    if revenue_cols:
        analysis["revenue_analysis"] = {
            "total_revenue": df[revenue_cols[0]].sum() if len(revenue_cols) > 0 else 0,
            "average_order_value": df[revenue_cols[0]].mean() if len(revenue_cols) > 0 else 0,
            "revenue_trend": "상승" if len(revenue_cols) > 0 and df[revenue_cols[0]].iloc[-1] > df[revenue_cols[0]].iloc[0] else "하락"
        }
    
    # 제품별 분석
    product_cols = [col for col in df.columns if any(word in col.lower() for word in ['product', 'item', 'category'])]
    if product_cols:
        analysis["product_analysis"] = df[product_cols[0]].value_counts().head(10).to_dict()
    
    # 고객 분석
    customer_cols = [col for col in df.columns if any(word in col.lower() for word in ['customer', 'client', 'user'])]
    if customer_cols:
        analysis["customer_analysis"] = {
            "total_customers": df[customer_cols[0]].nunique(),
            "repeat_customers": len(df[customer_cols[0]].value_counts()[df[customer_cols[0]].value_counts() > 1])
        }
    
    return analysis


def _analyze_finance_data(df: pd.DataFrame, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """금융 데이터 분석"""
    analysis = {}
    
    # 거래 분석
    transaction_cols = [col for col in df.columns if any(word in col.lower() for word in ['transaction', 'amount', 'balance'])]
    if transaction_cols:
        analysis["transaction_analysis"] = {
            "total_transactions": len(df),
            "average_amount": df[transaction_cols[0]].mean() if len(transaction_cols) > 0 else 0,
            "total_volume": df[transaction_cols[0]].sum() if len(transaction_cols) > 0 else 0
        }
    
    return analysis


def _analyze_hr_data(df: pd.DataFrame, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """HR 데이터 분석"""
    analysis = {}
    
    # 직원 성과 분석
    performance_cols = [col for col in df.columns if any(word in col.lower() for word in ['performance', 'rating', 'score'])]
    if performance_cols:
        analysis["performance_analysis"] = {
            "average_performance": df[performance_cols[0]].mean() if len(performance_cols) > 0 else 0,
            "high_performers": len(df[df[performance_cols[0]] >= df[performance_cols[0]].quantile(0.8)]) if len(performance_cols) > 0 else 0,
            "performance_distribution": df[performance_cols[0]].describe().to_dict() if len(performance_cols) > 0 else {}
        }
    
    # 부서별 분석
    department_cols = [col for col in df.columns if any(word in col.lower() for word in ['department', 'team', 'division'])]
    if department_cols:
        analysis["department_analysis"] = df[department_cols[0]].value_counts().to_dict()
    
    return analysis


def _analyze_retail_data(df: pd.DataFrame, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """리테일 데이터 분석"""
    analysis = {}
    
    # 매장별 분석
    store_cols = [col for col in df.columns if any(word in col.lower() for word in ['store', 'location', 'branch'])]
    if store_cols:
        analysis["store_analysis"] = df[store_cols[0]].value_counts().to_dict()
    
    return analysis


def _analyze_general_data(df: pd.DataFrame, query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """일반 데이터 분석"""
    analysis = {}
    
    # 수치형 컬럼 분석
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        analysis["numeric_analysis"] = {}
        for col in numeric_cols:
            analysis["numeric_analysis"][col] = {
                "mean": df[col].mean(),
                "median": df[col].median(),
                "std": df[col].std(),
                "min": df[col].min(),
                "max": df[col].max()
            }
    
    # 범주형 컬럼 분석
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        analysis["categorical_analysis"] = {}
        for col in categorical_cols:
            analysis["categorical_analysis"][col] = df[col].value_counts().head(10).to_dict()
    
    return analysis


def _get_statistical_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """통계 요약 정보를 생성합니다."""
    return {
        "descriptive_stats": df.describe().to_dict(),
        "correlation_matrix": df.corr().to_dict() if len(df.select_dtypes(include=['number']).columns) > 1 else {},
        "data_quality": {
            "completeness": (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))),
            "uniqueness": df.nunique().to_dict()
        }
    }


def _extract_key_insights(df: pd.DataFrame, domain_analysis: Dict[str, Any]) -> List[str]:
    """주요 인사이트를 추출합니다."""
    insights = []
    
    # 데이터 크기 인사이트
    insights.append(f"데이터셋은 총 {len(df):,}개의 레코드와 {len(df.columns)}개의 컬럼으로 구성되어 있습니다.")
    
    # 도메인별 인사이트
    if "revenue_analysis" in domain_analysis:
        revenue_info = domain_analysis["revenue_analysis"]
        insights.append(f"총 매출액은 {revenue_info.get('total_revenue', 0):,.0f}원이며, 평균 주문 가치는 {revenue_info.get('average_order_value', 0):,.0f}원입니다.")
    
    if "performance_analysis" in domain_analysis:
        perf_info = domain_analysis["performance_analysis"]
        insights.append(f"평균 성과 점수는 {perf_info.get('average_performance', 0):.1f}점이며, 고성과자는 {perf_info.get('high_performers', 0)}명입니다.")
    
    if "transaction_analysis" in domain_analysis:
        trans_info = domain_analysis["transaction_analysis"]
        insights.append(f"총 {trans_info.get('total_transactions', 0):,}건의 거래가 발생했으며, 평균 거래 금액은 {trans_info.get('average_amount', 0):,.0f}원입니다.")
    
    return insights


def _generate_recommendations(key_insights: List[str], domain: str) -> List[str]:
    """권장사항을 생성합니다."""
    recommendations = []
    
    # 도메인별 권장사항
    if domain == "ecommerce":
        recommendations.extend([
            "고객 세분화를 통한 맞춤형 마케팅 전략 수립을 권장합니다.",
            "제품별 성과 분석을 통해 수익성 높은 제품에 대한 투자를 늘려보세요.",
            "고객 생애 가치 분석을 통해 장기 고객 확보 전략을 수립하세요."
        ])
    elif domain == "hr":
        recommendations.extend([
            "성과 기반 인센티브 시스템 도입을 검토해보세요.",
            "부서별 성과 차이 분석을 통해 우수 사례를 공유하세요.",
            "직원 만족도 조사를 정기적으로 실시하여 조직 건강도를 관리하세요."
        ])
    elif domain == "finance":
        recommendations.extend([
            "거래 패턴 분석을 통한 리스크 관리 체계를 강화하세요.",
            "고객별 거래 행동 분석을 통해 맞춤형 금융 상품을 개발하세요.",
            "이상 거래 탐지를 위한 모니터링 시스템을 구축하세요."
        ])
    else:
        recommendations.extend([
            "데이터 품질 개선을 통해 분석의 정확성을 높이세요.",
            "정기적인 데이터 분석을 통해 비즈니스 인사이트를 지속적으로 도출하세요.",
            "시각화를 통해 이해관계자들과의 소통을 개선하세요."
        ])
    
    return recommendations


def _generate_comprehensive_report(
    df: pd.DataFrame, 
    analysis_results: Dict[str, Any], 
    query_responses: Dict[str, Any],
    domain: str,
    analysis_context: Dict[str, Any]
) -> str:
    """포괄적인 리포트를 생성합니다."""
    
    report_sections = []
    
    # 리포트 헤더
    report_sections.append(f"# {domain.upper()} 데이터 분석 리포트")
    report_sections.append(f"**생성 일시:** {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
    report_sections.append(f"**분석 대상:** {len(df):,}개 레코드, {len(df.columns)}개 컬럼")
    report_sections.append("")
    
    # 요약 섹션
    report_sections.append("## 📊 요약")
    report_sections.append("본 리포트는 제공된 데이터를 종합적으로 분석하여 비즈니스 인사이트와 실행 가능한 권장사항을 제시합니다.")
    report_sections.append("")
    
    # 데이터 개요
    data_overview = analysis_results.get("data_overview", {})
    report_sections.append("## 📈 데이터 개요")
    report_sections.append(f"- **총 레코드 수:** {data_overview.get('total_records', 0):,}개")
    report_sections.append(f"- **총 컬럼 수:** {data_overview.get('total_columns', 0)}개")
    report_sections.append(f"- **컬럼명:** {', '.join(data_overview.get('column_names', []))}")
    report_sections.append("")
    
    # 주요 발견사항
    report_sections.append("## 🔍 주요 발견사항")
    key_insights = analysis_results.get("key_insights", [])
    for i, insight in enumerate(key_insights, 1):
        report_sections.append(f"{i}. {insight}")
    report_sections.append("")
    
    # 도메인별 분석
    domain_analysis = analysis_results.get("domain_analysis", {})
    if domain_analysis:
        report_sections.append("## 📊 도메인별 분석")
        for analysis_type, results in domain_analysis.items():
            report_sections.append(f"### {analysis_type.replace('_', ' ').title()}")
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        report_sections.append(f"- **{key}:** {value:,.2f}")
                    else:
                        report_sections.append(f"- **{key}:** {value}")
            report_sections.append("")
    
    # 통계 요약
    statistical_summary = analysis_results.get("statistical_summary", {})
    if statistical_summary.get("descriptive_stats"):
        report_sections.append("## 📈 통계 요약")
        report_sections.append("주요 수치형 컬럼들의 기술통계량:")
        report_sections.append("")
        # 간단한 통계 요약만 포함
        numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
        if numeric_cols:
            report_sections.append("| 컬럼 | 평균 | 중앙값 | 표준편차 | 최솟값 | 최댓값 |")
            report_sections.append("|------|------|--------|----------|--------|--------|")
            for col in numeric_cols[:5]:  # 처음 5개 컬럼만 표시
                stats = df[col].describe()
                report_sections.append(f"| {col} | {stats['mean']:.2f} | {stats['50%']:.2f} | {stats['std']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |")
        report_sections.append("")
    
    # 결론 및 권장사항
    report_sections.append("## 💡 결론 및 권장사항")
    recommendations = analysis_results.get("recommendations", [])
    for i, recommendation in enumerate(recommendations, 1):
        report_sections.append(f"{i}. {recommendation}")
    report_sections.append("")
    
    # 추가 분석 제안
    report_sections.append("## 🔮 추가 분석 제안")
    report_sections.append("1. **시계열 분석:** 시간에 따른 트렌드 분석을 통해 계절성과 추세를 파악하세요.")
    report_sections.append("2. **상관관계 분석:** 변수 간 관계를 분석하여 숨겨진 패턴을 발견하세요.")
    report_sections.append("3. **예측 모델링:** 기존 데이터를 바탕으로 미래 값을 예측하는 모델을 구축하세요.")
    report_sections.append("")
    
    report_sections.append("---")
    report_sections.append(f"*본 리포트는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}에 자동 생성되었습니다.*")
    
    return "\n".join(report_sections)


def _generate_report_summary(analysis_results: Dict[str, Any], query_responses: Dict[str, Any]) -> Dict[str, Any]:
    """리포트 요약 정보를 생성합니다."""
    return {
        "total_sections": 6,
        "key_metrics_count": len(analysis_results.get("key_insights", [])),
        "recommendations_count": len(analysis_results.get("recommendations", [])),
        "analysis_depth": "comprehensive",
        "data_quality_score": analysis_results.get("statistical_summary", {}).get("data_quality", {}).get("completeness", 0.0)
    }


def _save_report_to_file(report_content: str, domain: str) -> str:
    """리포트를 파일로 저장합니다."""
    # reports 디렉토리 생성
    reports_dir = "data/reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{domain}_{timestamp}.md"
    file_path = os.path.join(reports_dir, filename)
    
    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return file_path


class ReportGenerationTool:
    def __init__(self):
        self.name = "generate_report"
        self.description = "수집된 질의 응답을 바탕으로 실제 데이터를 분석하여 포괄적인 리포트를 생성하고 파일로 저장합니다."
        self.input_model = ReportGenerationInput
        self.output_model = ReportGenerationOutput
        self.execute = generate_report
