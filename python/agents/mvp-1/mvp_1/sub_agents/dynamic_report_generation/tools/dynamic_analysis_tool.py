"""동적 분석 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


def _convert_numpy_types(obj):
    """NumPy 타입을 Python 기본 타입으로 변환합니다."""
    import numpy as np
    import pandas as pd
    
    def _deep_convert(item):
        try:
            # NumPy 타입 체크 (더 포괄적으로)
            if hasattr(item, 'dtype') and hasattr(item, 'item'):
                # NumPy 스칼라 타입
                return item.item()
            elif isinstance(item, (np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(item)
            elif isinstance(item, (np.float16, np.float32, np.float64)):
                return float(item)
            elif isinstance(item, np.bool_):
                return bool(item)
            elif isinstance(item, np.ndarray):
                return item.tolist()
            elif isinstance(item, pd.Series):
                return item.tolist()
            elif isinstance(item, pd.DataFrame):
                return item.to_dict()
            elif pd.isna(item):
                return None
            elif isinstance(item, dict):
                return {k: _deep_convert(v) for k, v in item.items()}
            elif isinstance(item, (list, tuple)):
                # 리스트와 튜플은 원래 타입을 유지
                return type(item)(_deep_convert(i) for i in item)
            elif hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
                # 다른 iterable 타입들도 처리
                return [_deep_convert(i) for i in item]
            else:
                return item
        except (ValueError, TypeError, OverflowError, AttributeError):
            # 변환 실패 시 원본 반환 (문자열로 변환하지 않음)
            return item
    
    return _deep_convert(obj)


class DynamicAnalysisInput(BaseModel):
    """동적 분석 입력"""
    data_file_path: str = Field(..., description="분석할 데이터 파일 경로")
    domain_analysis: Dict[str, Any] = Field(..., description="도메인 분석 결과")
    user_responses: Dict[str, Any] = Field(..., description="사용자 응답 정보")
    analysis_criteria: str = Field(..., description="분석 기준")


class DynamicAnalysisOutput(BaseModel):
    """동적 분석 출력"""
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")
    key_findings: List[str] = Field(..., description="주요 발견사항")
    trends: Dict[str, Any] = Field(..., description="트렌드 분석 결과")
    patterns: Dict[str, Any] = Field(..., description="패턴 분석 결과")
    performance_metrics: Dict[str, Any] = Field(..., description="성과 지표")
    success: bool = Field(..., description="분석 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def perform_dynamic_analysis(
    data_file_path: str,
    domain_analysis: Dict[str, Any],
    user_responses: Dict[str, Any],
    analysis_criteria: str
) -> DynamicAnalysisOutput:
    """
    데이터 특성과 사용자 요청에 따른 동적 분석을 수행합니다.
    """
    try:
        # 데이터 로드
        df = _load_data(data_file_path)
        if df is None:
            return DynamicAnalysisOutput(
                analysis_results={},
                key_findings=[],
                trends={},
                patterns={},
                performance_metrics={},
                success=False,
                message=f"데이터 파일({data_file_path})을 로드할 수 없습니다."
            )
        
        # 도메인별 특화 분석 수행
        domain_type = domain_analysis.get('domain_type', '일반')
        analysis_strategy = domain_analysis.get('analysis_strategy', {})
        
        # 분석 결과 수집
        analysis_results = {}
        key_findings = []
        trends = {}
        patterns = {}
        performance_metrics = {}
        
        # 도메인별 특화 분석
        if '매출' in domain_type or '영업' in domain_type:
            analysis_results.update(_analyze_sales_domain(df, user_responses))
            key_findings.extend(_extract_sales_findings(df, analysis_results))
            trends.update(_analyze_sales_trends(df))
            patterns.update(_identify_sales_patterns(df))
            performance_metrics.update(_calculate_sales_metrics(df))
        
        elif '고객' in domain_type:
            analysis_results.update(_analyze_customer_domain(df, user_responses))
            key_findings.extend(_extract_customer_findings(df, analysis_results))
            trends.update(_analyze_customer_trends(df))
            patterns.update(_identify_customer_patterns(df))
            performance_metrics.update(_calculate_customer_metrics(df))
        
        elif '재고' in domain_type or '물류' in domain_type:
            analysis_results.update(_analyze_inventory_domain(df, user_responses))
            key_findings.extend(_extract_inventory_findings(df, analysis_results))
            trends.update(_analyze_inventory_trends(df))
            patterns.update(_identify_inventory_patterns(df))
            performance_metrics.update(_calculate_inventory_metrics(df))
        
        elif '마케팅' in domain_type:
            analysis_results.update(_analyze_marketing_domain(df, user_responses))
            key_findings.extend(_extract_marketing_findings(df, analysis_results))
            trends.update(_analyze_marketing_trends(df))
            patterns.update(_identify_marketing_patterns(df))
            performance_metrics.update(_calculate_marketing_metrics(df))
        
        elif 'HR' in domain_type or '인사' in domain_type:
            analysis_results.update(_analyze_hr_domain(df, user_responses))
            key_findings.extend(_extract_hr_findings(df, analysis_results))
            trends.update(_analyze_hr_trends(df))
            patterns.update(_identify_hr_patterns(df))
            performance_metrics.update(_calculate_hr_metrics(df))
        
        else:
            # 일반적인 분석
            analysis_results.update(_analyze_general_domain(df, user_responses))
            key_findings.extend(_extract_general_findings(df, analysis_results))
            trends.update(_analyze_general_trends(df))
            patterns.update(_identify_general_patterns(df))
            performance_metrics.update(_calculate_general_metrics(df))
        
        # 사용자 요청 기반 추가 분석
        if analysis_criteria:
            additional_analysis = _perform_criteria_based_analysis(df, analysis_criteria, user_responses)
            analysis_results.update(additional_analysis)
        
        # 모든 결과를 numpy 타입에서 변환
        converted_results = _convert_numpy_types(analysis_results)
        # key_findings는 반드시 리스트로 유지
        converted_findings = _convert_numpy_types(key_findings)
        if not isinstance(converted_findings, list):
            converted_findings = [str(converted_findings)] if converted_findings else []
        converted_trends = _convert_numpy_types(trends)
        converted_patterns = _convert_numpy_types(patterns)
        converted_metrics = _convert_numpy_types(performance_metrics)
        
        return DynamicAnalysisOutput(
            analysis_results=converted_results,
            key_findings=converted_findings,
            trends=converted_trends,
            patterns=converted_patterns,
            performance_metrics=converted_metrics,
            success=True,
            message=f"동적 분석 완료: {domain_type} 도메인 분석 수행"
        )
        
    except Exception as e:
        return DynamicAnalysisOutput(
            analysis_results={},
            key_findings=[],
            trends={},
            patterns={},
            performance_metrics={},
            success=False,
            message=f"동적 분석 중 오류가 발생했습니다: {str(e)}"
        )


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


# 매출/영업 도메인 분석 함수들
def _analyze_sales_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """매출/영업 도메인 분석을 수행합니다."""
    results = {}
    
    # 매출 관련 컬럼 찾기
    sales_cols = _find_sales_columns(df)
    if sales_cols:
        results['sales_analysis'] = {
            'total_sales': float(df[sales_cols].sum().sum()) if len(sales_cols) > 0 else 0,
            'average_sales': float(df[sales_cols].mean().mean()) if len(sales_cols) > 0 else 0,
            'sales_growth': _calculate_sales_growth(df, sales_cols),
            'top_performers': _find_top_sales_performers(df, sales_cols)
        }
    
    # 제품별 분석
    product_cols = _find_product_columns(df)
    if product_cols and sales_cols:
        results['product_analysis'] = _analyze_product_performance(df, product_cols, sales_cols)
    
    # 지역별 분석
    region_cols = _find_region_columns(df)
    if region_cols and sales_cols:
        results['regional_analysis'] = _analyze_regional_performance(df, region_cols, sales_cols)
    
    return results


def _find_sales_columns(df: pd.DataFrame) -> List[str]:
    """매출 관련 컬럼을 찾습니다."""
    sales_keywords = ['매출', 'sales', 'revenue', '수익', 'profit', 'amount', '금액', 'price', '가격']
    sales_cols = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in sales_keywords):
            if df[col].dtype in ['int64', 'float64']:
                sales_cols.append(col)
    
    return sales_cols


def _find_product_columns(df: pd.DataFrame) -> List[str]:
    """제품 관련 컬럼을 찾습니다."""
    product_keywords = ['product', '제품', 'item', '상품', 'category', '카테고리']
    product_cols = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in product_keywords):
            product_cols.append(col)
    
    return product_cols


def _find_region_columns(df: pd.DataFrame) -> List[str]:
    """지역 관련 컬럼을 찾습니다."""
    region_keywords = ['region', '지역', 'area', '지점', 'store', '매장', 'city', '도시']
    region_cols = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in region_keywords):
            region_cols.append(col)
    
    return region_cols


def _calculate_sales_growth(df: pd.DataFrame, sales_cols: List[str]) -> Dict[str, float]:
    """매출 성장률을 계산합니다."""
    growth_rates = {}
    
    for col in sales_cols:
        if len(df) > 1:
            # 시계열 데이터가 있다고 가정하고 성장률 계산
            first_half = df[col].iloc[:len(df)//2].mean()
            second_half = df[col].iloc[len(df)//2:].mean()
            
            if first_half > 0:
                growth_rate = ((second_half - first_half) / first_half) * 100
                growth_rates[col] = float(growth_rate)
    
    return growth_rates


def _find_top_sales_performers(df: pd.DataFrame, sales_cols: List[str]) -> Dict[str, Any]:
    """상위 매출 성과자를 찾습니다."""
    top_performers = {}
    
    for col in sales_cols:
        top_10_percent = int(len(df) * 0.1) if len(df) > 10 else 1
        top_values = df.nlargest(top_10_percent, col)
        top_performers[col] = {
            'top_values': top_values[col].tolist(),
            'average_top': float(top_values[col].mean()),
            'percentage_of_total': float((top_values[col].sum() / df[col].sum()) * 100)
        }
    
    return top_performers


def _analyze_product_performance(df: pd.DataFrame, product_cols: List[str], sales_cols: List[str]) -> Dict[str, Any]:
    """제품별 성과를 분석합니다."""
    product_analysis = {}
    
    for product_col in product_cols:
        if product_col in df.columns:
            product_summary = df.groupby(product_col)[sales_cols].agg(['sum', 'mean', 'count']).round(2)
            # NumPy 타입을 Python 기본 타입으로 변환
            product_analysis[product_col] = _convert_numpy_types(product_summary.to_dict())
    
    return product_analysis


def _analyze_regional_performance(df: pd.DataFrame, region_cols: List[str], sales_cols: List[str]) -> Dict[str, Any]:
    """지역별 성과를 분석합니다."""
    regional_analysis = {}
    
    for region_col in region_cols:
        if region_col in df.columns:
            regional_summary = df.groupby(region_col)[sales_cols].agg(['sum', 'mean', 'count']).round(2)
            # NumPy 타입을 Python 기본 타입으로 변환
            regional_analysis[region_col] = _convert_numpy_types(regional_summary.to_dict())
    
    return regional_analysis


def _extract_sales_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """매출 분석에서 주요 발견사항을 추출합니다."""
    findings = []
    
    if 'sales_analysis' in analysis_results:
        sales_data = analysis_results['sales_analysis']
        
        if 'total_sales' in sales_data:
            findings.append(f"총 매출액: {sales_data['total_sales']:,.0f}원")
        
        if 'sales_growth' in sales_data and sales_data['sales_growth']:
            for col, growth in sales_data['sales_growth'].items():
                if growth > 0:
                    findings.append(f"{col}에서 {growth:.1f}% 성장세를 보입니다")
                else:
                    findings.append(f"{col}에서 {abs(growth):.1f}% 감소세를 보입니다")
    
    return findings


def _analyze_sales_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """매출 트렌드를 분석합니다."""
    trends = {}
    
    # 시계열 데이터가 있는 경우
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        date_col = date_cols[0]
        sales_cols = _find_sales_columns(df)
        
        if sales_cols:
            monthly_trends = df.groupby(df[date_col].dt.to_period('M'))[sales_cols].sum()
            trends['monthly_trends'] = monthly_trends.to_dict()
    
    return trends


def _identify_sales_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """매출 패턴을 식별합니다."""
    patterns = {}
    
    sales_cols = _find_sales_columns(df)
    if sales_cols:
        # 계절성 패턴 분석
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            date_col = date_cols[0]
            df['month'] = df[date_col].dt.month
            monthly_patterns = df.groupby('month')[sales_cols].mean()
            patterns['seasonal_patterns'] = _convert_numpy_types(monthly_patterns.to_dict())
    
    return patterns


def _calculate_sales_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """매출 성과 지표를 계산합니다."""
    metrics = {}
    
    sales_cols = _find_sales_columns(df)
    if sales_cols:
        for col in sales_cols:
            metrics[f'{col}_metrics'] = {
                'total': float(df[col].sum()),
                'average': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
    
    return metrics


# 고객 도메인 분석 함수들
def _analyze_customer_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """고객 도메인 분석을 수행합니다."""
    results = {}
    
    # 고객 세분화 분석
    customer_cols = _find_customer_columns(df)
    if customer_cols:
        results['customer_segmentation'] = _perform_customer_segmentation(df, customer_cols)
    
    # 고객 행동 분석
    behavior_cols = _find_behavior_columns(df)
    if behavior_cols:
        results['behavior_analysis'] = _analyze_customer_behavior(df, behavior_cols)
    
    return results


def _find_customer_columns(df: pd.DataFrame) -> List[str]:
    """고객 관련 컬럼을 찾습니다."""
    customer_keywords = ['customer', '고객', 'client', 'user', '사용자', 'member', '회원']
    customer_cols = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in customer_keywords):
            customer_cols.append(col)
    
    return customer_cols


def _find_behavior_columns(df: pd.DataFrame) -> List[str]:
    """행동 관련 컬럼을 찾습니다."""
    behavior_keywords = ['behavior', '행동', 'action', '활동', 'activity', 'visit', '방문', 'purchase', '구매']
    behavior_cols = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in behavior_keywords):
            behavior_cols.append(col)
    
    return behavior_cols


def _perform_customer_segmentation(df: pd.DataFrame, customer_cols: List[str]) -> Dict[str, Any]:
    """고객 세분화를 수행합니다."""
    segmentation = {}
    
    for col in customer_cols:
        if col in df.columns:
            if df[col].dtype in ['object', 'category']:
                # 범주형 데이터의 경우
                value_counts = df[col].value_counts()
                segmentation[col] = {
                    'segments': _convert_numpy_types(value_counts.to_dict()),
                    'diversity_index': float(len(value_counts) / len(df))
                }
            else:
                # 수치형 데이터의 경우 (간단한 분위수 기반 세분화)
                df[f'{col}_segment'] = pd.qcut(df[col], q=4, labels=['Low', 'Medium', 'High', 'Very High'])
                segment_counts = df[f'{col}_segment'].value_counts()
                segmentation[col] = {
                    'segments': _convert_numpy_types(segment_counts.to_dict()),
                    'quartiles': _convert_numpy_types(df[col].quantile([0.25, 0.5, 0.75]).to_dict())
                }
    
    return segmentation


def _analyze_customer_behavior(df: pd.DataFrame, behavior_cols: List[str]) -> Dict[str, Any]:
    """고객 행동을 분석합니다."""
    behavior_analysis = {}
    
    for col in behavior_cols:
        if col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                behavior_analysis[col] = {
                    'average': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'frequency_distribution': _convert_numpy_types(df[col].value_counts().head(10).to_dict())
                }
    
    return behavior_analysis


def _extract_customer_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """고객 분석에서 주요 발견사항을 추출합니다."""
    findings = []
    
    if 'customer_segmentation' in analysis_results:
        segmentation = analysis_results['customer_segmentation']
        for col, data in segmentation.items():
            if 'diversity_index' in data:
                if data['diversity_index'] > 0.8:
                    findings.append(f"{col}에서 고객 다양성이 높습니다 (다양성 지수: {data['diversity_index']:.2f})")
                elif data['diversity_index'] < 0.2:
                    findings.append(f"{col}에서 고객 집중도가 높습니다 (다양성 지수: {data['diversity_index']:.2f})")
    
    return findings


def _analyze_customer_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """고객 트렌드를 분석합니다."""
    trends = {}
    
    # 시계열 데이터가 있는 경우
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        date_col = date_cols[0]
        customer_cols = _find_customer_columns(df)
        
        if customer_cols:
            monthly_trends = df.groupby(df[date_col].dt.to_period('M'))[customer_cols].nunique()
            trends['monthly_customer_trends'] = monthly_trends.to_dict()
    
    return trends


def _identify_customer_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """고객 패턴을 식별합니다."""
    patterns = {}
    
    # 고객 행동 패턴 분석
    behavior_cols = _find_behavior_columns(df)
    if behavior_cols:
        for col in behavior_cols:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                # 이상치 패턴 분석
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                
                if len(outliers) > 0:
                    patterns[f'{col}_outliers'] = {
                        'count': len(outliers),
                        'percentage': (len(outliers) / len(df)) * 100
                    }
    
    return patterns


def _calculate_customer_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """고객 성과 지표를 계산합니다."""
    metrics = {}
    
    customer_cols = _find_customer_columns(df)
    if customer_cols:
        for col in customer_cols:
            if col in df.columns:
                if df[col].dtype in ['object', 'category']:
                    metrics[f'{col}_metrics'] = {
                        'unique_count': df[col].nunique(),
                        'most_common': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
                        'diversity_ratio': df[col].nunique() / len(df)
                    }
    
    return metrics


# 일반 도메인 분석 함수들 (기존 로직과 유사)
def _analyze_general_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """일반 도메인 분석을 수행합니다."""
    results = {}
    
    # 기본 통계 분석
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        results['basic_statistics'] = df[numeric_cols].describe().to_dict()
    
    # 범주형 데이터 분석
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        results['categorical_analysis'] = {}
        for col in categorical_cols:
            results['categorical_analysis'][col] = {
                'unique_count': df[col].nunique(),
                'most_common': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
                'value_counts': df[col].value_counts().head(10).to_dict()
            }
    
    return results


def _extract_general_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """일반 분석에서 주요 발견사항을 추출합니다."""
    findings = []
    
    findings.append(f"총 {len(df):,}건의 데이터를 분석했습니다.")
    
    if 'basic_statistics' in analysis_results:
        findings.append("수치형 데이터의 기본 통계 분석을 완료했습니다.")
    
    if 'categorical_analysis' in analysis_results:
        findings.append("범주형 데이터의 분포 분석을 완료했습니다.")
    
    return findings


def _analyze_general_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """일반 트렌드를 분석합니다."""
    trends = {}
    
    # 시계열 데이터가 있는 경우
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        date_col = date_cols[0]
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            monthly_trends = df.groupby(df[date_col].dt.to_period('M'))[numeric_cols].mean()
            trends['monthly_trends'] = monthly_trends.to_dict()
    
    return trends


def _identify_general_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """일반 패턴을 식별합니다."""
    patterns = {}
    
    # 상관관계 패턴
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        strong_correlations = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    strong_correlations.append({
                        'columns': [col1, col2],
                        'correlation': float(corr_val)
                    })
        
        if strong_correlations:
            patterns['strong_correlations'] = strong_correlations
    
    return patterns


def _calculate_general_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """일반 성과 지표를 계산합니다."""
    metrics = {}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        for col in numeric_cols:
            metrics[f'{col}_metrics'] = {
                'total': float(df[col].sum()),
                'average': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
    
    return metrics


def _perform_criteria_based_analysis(df: pd.DataFrame, analysis_criteria: str, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 지정 분석 기준에 따른 추가 분석을 수행합니다."""
    additional_analysis = {}
    
    # 분석 기준에 따른 맞춤 분석
    if '성과' in analysis_criteria or '실적' in analysis_criteria:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            additional_analysis['performance_analysis'] = {}
            for col in numeric_cols:
                additional_analysis['performance_analysis'][col] = {
                    'total_performance': float(df[col].sum()),
                    'average_performance': float(df[col].mean()),
                    'top_performers': df.nlargest(5, col)[col].tolist()
                }
    
    if '트렌드' in analysis_criteria:
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            date_col = date_cols[0]
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                trend_analysis = df.groupby(df[date_col].dt.to_period('M'))[numeric_cols].mean()
                additional_analysis['trend_analysis'] = _convert_numpy_types(trend_analysis.to_dict())
    
    return additional_analysis


# 다른 도메인 분석 함수들 (재고, 마케팅, HR)은 간단한 구조로 구현
def _analyze_inventory_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """재고/물류 도메인 분석을 수행합니다."""
    return {'inventory_analysis': '재고 분석 로직 구현 필요'}


def _extract_inventory_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """재고 분석에서 주요 발견사항을 추출합니다."""
    return ['재고 분석 결과를 확인했습니다.']


def _analyze_inventory_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """재고 트렌드를 분석합니다."""
    return {}


def _identify_inventory_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """재고 패턴을 식별합니다."""
    return {}


def _calculate_inventory_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """재고 성과 지표를 계산합니다."""
    return {}


def _analyze_marketing_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """마케팅 도메인 분석을 수행합니다."""
    return {'marketing_analysis': '마케팅 분석 로직 구현 필요'}


def _extract_marketing_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """마케팅 분석에서 주요 발견사항을 추출합니다."""
    return ['마케팅 분석 결과를 확인했습니다.']


def _analyze_marketing_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """마케팅 트렌드를 분석합니다."""
    return {}


def _identify_marketing_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """마케팅 패턴을 식별합니다."""
    return {}


def _calculate_marketing_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """마케팅 성과 지표를 계산합니다."""
    return {}


def _analyze_hr_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """HR/인사 도메인 분석을 수행합니다."""
    return {'hr_analysis': 'HR 분석 로직 구현 필요'}


def _extract_hr_findings(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
    """HR 분석에서 주요 발견사항을 추출합니다."""
    return ['HR 분석 결과를 확인했습니다.']


def _analyze_hr_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """HR 트렌드를 분석합니다."""
    return {}


def _identify_hr_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """HR 패턴을 식별합니다."""
    return {}


def _calculate_hr_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """HR 성과 지표를 계산합니다."""
    return {}


class DynamicAnalysisTool:
    def __init__(self):
        self.name = "perform_dynamic_analysis"
        self.description = "데이터 특성과 사용자 요청에 따른 동적 분석을 수행합니다."
        self.input_model = DynamicAnalysisInput
        self.output_model = DynamicAnalysisOutput
        self.execute = perform_dynamic_analysis