"""
동적 시각화 생성 도구

분석 목적과 데이터 특성에 따라 차트, 테이블, 시각화 요소를 동적으로 생성하는 도구입니다.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import numpy as np
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    VISUALIZATION_LIBS_AVAILABLE = True
except ImportError:
    # 시각화 라이브러리가 없어도 기본 기능은 동작하도록 함
    VISUALIZATION_LIBS_AVAILABLE = False
    print("Warning: 시각화 라이브러리(matplotlib, seaborn, plotly)가 설치되지 않았습니다. 기본 기능만 사용됩니다.")
import base64
import io
import os
from datetime import datetime
from pathlib import Path
import json


def _convert_numpy_types(obj):
    """NumPy 타입을 Python 기본 타입으로 변환합니다."""
    import numpy as np
    import pandas as pd
    
    def _deep_convert(item):
        try:
            if hasattr(item, 'dtype') and hasattr(item, 'item'):
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
                return type(item)(_deep_convert(i) for i in item)
            elif hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
                return [_deep_convert(i) for i in item]
            else:
                return item
        except (ValueError, TypeError, OverflowError, AttributeError):
            return item
    
    return _deep_convert(obj)


class VisualizationInput(BaseModel):
    """시각화 생성 입력"""
    data_file_path: str = Field(..., description="분석할 데이터 파일 경로")
    domain_type: str = Field(..., description="도메인 유형")
    analysis_purpose: str = Field(..., description="분석 목적")
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")
    visualization_requirements: Dict[str, Any] = Field(default_factory=dict, description="시각화 요구사항")
    output_format: str = Field(default="html", description="출력 형식 (html, markdown, json)")


class VisualizationOutput(BaseModel):
    """시각화 생성 출력"""
    visualizations: List[Dict[str, Any]] = Field(..., description="생성된 시각화 요소들")
    charts_data: Dict[str, Any] = Field(..., description="차트 데이터")
    tables_data: Dict[str, Any] = Field(..., description="테이블 데이터")
    success: bool = Field(..., description="생성 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")
    generated_files: List[str] = Field(default_factory=list, description="생성된 파일 목록")


@FunctionTool
def generate_dynamic_visualizations(
    data_file_path: str,
    domain_type: str,
    analysis_purpose: str,
    analysis_results: Dict[str, Any],
    visualization_requirements: Dict[str, Any] = {},
    output_format: str = "html"
) -> VisualizationOutput:
    """
    분석 목적과 데이터 특성에 따라 동적으로 시각화 요소를 생성합니다.
    """
    try:
        # 데이터 로드
        df = _load_data(data_file_path)
        if df is None:
            return VisualizationOutput(
                visualizations=[],
                charts_data={},
                tables_data={},
                success=False,
                message=f"데이터 파일({data_file_path})을 로드할 수 없습니다.",
                generated_files=[]
            )
        
        # 시각화 라이브러리 사용 가능 여부 확인
        if not VISUALIZATION_LIBS_AVAILABLE:
            # 라이브러리가 없어도 기본 시각화 정보는 제공
            print("Warning: 시각화 라이브러리가 없어서 실제 차트 이미지는 생성되지 않지만, 시각화 설정 정보는 제공됩니다.")
            
            # 기본 시각화 설정 생성
            basic_visualizations = _generate_basic_visualizations(df, domain_type, analysis_purpose)
            
            return VisualizationOutput(
                visualizations=basic_visualizations,
                charts_data=_extract_charts_data(df, domain_type, analysis_purpose),
                tables_data=_generate_tables_data(df, domain_type, analysis_purpose, analysis_results),
                success=True,
                message="시각화 라이브러리가 없어서 실제 차트 이미지는 생성되지 않았지만, 시각화 설정 정보와 데이터 요약이 제공되었습니다. pip install matplotlib seaborn plotly로 설치하면 실제 차트 이미지도 생성됩니다.",
                generated_files=[]
            )
        
        # 시각화 요소 생성
        visualizations = []
        charts_data = {}
        tables_data = {}
        generated_files = []
        
        # 도메인별 시각화 생성
        domain_visualizations = _generate_domain_visualizations(df, domain_type, analysis_purpose, analysis_results)
        visualizations.extend(domain_visualizations)
        
        # 분석 목적별 시각화 생성
        purpose_visualizations = _generate_purpose_visualizations(df, analysis_purpose, analysis_results)
        visualizations.extend(purpose_visualizations)
        
        # 데이터 특성별 시각화 생성
        data_visualizations = _generate_data_characteristic_visualizations(df, analysis_results)
        visualizations.extend(data_visualizations)
        
        # 차트 데이터 추출
        charts_data = _extract_charts_data(df, domain_type, analysis_purpose)
        
        # 테이블 데이터 생성
        tables_data = _generate_tables_data(df, domain_type, analysis_purpose, analysis_results)
        
        # 파일 생성 (필요시)
        if output_format in ["html", "json"]:
            generated_files = _save_visualization_files(visualizations, charts_data, tables_data, output_format, data_file_path)
        
        return VisualizationOutput(
            visualizations=visualizations,
            charts_data=_convert_numpy_types(charts_data),
            tables_data=_convert_numpy_types(tables_data),
            success=True,
            message=f"시각화 요소 {len(visualizations)}개가 성공적으로 생성되었습니다.",
            generated_files=generated_files
        )
        
    except Exception as e:
        return VisualizationOutput(
            visualizations=[],
            charts_data={},
            tables_data={},
            success=False,
            message=f"시각화 생성 중 오류가 발생했습니다: {str(e)}",
            generated_files=[]
        )


def _load_data(file_path: str) -> Optional[pd.DataFrame]:
    """데이터 파일을 로드합니다."""
    try:
        print(f"데이터 파일 로딩 시도: {file_path}")
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            print(f"파일이 존재하지 않음: {file_path}")
            return None
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        print(f"파일 크기: {file_size} bytes")
        
        if file_size == 0:
            print("파일이 비어있음")
            return None
        
        # 파일 확장자에 따른 로딩
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            print(f"지원하지 않는 파일 형식: {file_path}")
            return None
        
        print(f"데이터 로딩 성공: {len(df)}행, {len(df.columns)}컬럼")
        print(f"컬럼명: {list(df.columns)}")
        return df
        
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        print(f"파일 경로: {file_path}")
        return None


def _generate_basic_visualizations(df: pd.DataFrame, domain_type: str, analysis_purpose: str) -> List[Dict[str, Any]]:
    """시각화 라이브러리가 없을 때 기본 시각화 설정을 생성합니다."""
    visualizations = []
    
    # 수치형 컬럼들
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 기본 막대 차트
    if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
        chart_config = {
            "type": "bar_chart",
            "title": f"{categorical_cols[0]}별 {numeric_cols[0]} 분석",
            "data": {
                "x": categorical_cols[0],
                "y": numeric_cols[0]
            },
            "description": f"{categorical_cols[0]}별 {numeric_cols[0]} 값을 보여주는 막대 차트",
            "chart_type": "comparison_analysis"
        }
        visualizations.append(chart_config)
    
    # 기본 선형 차트
    if len(numeric_cols) >= 1:
        chart_config = {
            "type": "line_chart",
            "title": f"{numeric_cols[0]} 트렌드 분석",
            "data": {
                "x": "index",
                "y": numeric_cols[0]
            },
            "description": f"{numeric_cols[0]}의 변화 추이를 보여주는 선형 차트",
            "chart_type": "trend_analysis"
        }
        visualizations.append(chart_config)
    
    # 기본 히스토그램
    if len(numeric_cols) >= 1:
        chart_config = {
            "type": "histogram",
            "title": f"{numeric_cols[0]} 분포 분석",
            "data": {
                "column": numeric_cols[0],
                "bins": 20
            },
            "description": f"{numeric_cols[0]}의 분포를 보여주는 히스토그램",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
    
    # 기본 파이 차트
    if len(categorical_cols) >= 1:
        chart_config = {
            "type": "pie_chart",
            "title": f"{categorical_cols[0]} 분포",
            "data": {
                "category": categorical_cols[0]
            },
            "description": f"{categorical_cols[0]}의 분포를 보여주는 파이 차트",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _generate_domain_visualizations(df: pd.DataFrame, domain_type: str, analysis_purpose: str, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """도메인별 특화 시각화를 생성합니다."""
    visualizations = []
    
    if '매출' in domain_type or '영업' in domain_type:
        visualizations.extend(_create_sales_visualizations(df, analysis_results))
    elif '고객' in domain_type:
        visualizations.extend(_create_customer_visualizations(df, analysis_results))
    elif '재고' in domain_type or '물류' in domain_type:
        visualizations.extend(_create_inventory_visualizations(df, analysis_results))
    elif '마케팅' in domain_type:
        visualizations.extend(_create_marketing_visualizations(df, analysis_results))
    elif 'HR' in domain_type or '인사' in domain_type:
        visualizations.extend(_create_hr_visualizations(df, analysis_results))
    else:
        visualizations.extend(_create_general_visualizations(df, analysis_results))
    
    return visualizations


def _create_sales_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """매출/영업 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # 매출 관련 컬럼 찾기
    sales_cols = _find_sales_columns(df)
    product_cols = _find_product_columns(df)
    region_cols = _find_region_columns(df)
    
    if sales_cols:
        # 1. 매출 트렌드 차트
        if len(sales_cols) > 0:
            chart_config = {
                "type": "line_chart",
                "title": "매출 트렌드 분석",
                "data": {
                    "x": "index",
                    "y": sales_cols[0],
                    "columns": sales_cols
                },
                "description": "시간별 매출 변화 추이를 보여주는 선형 차트",
                "chart_type": "trend_analysis"
            }
            visualizations.append(chart_config)
        
        # 2. 제품별 매출 파이 차트
        if product_cols and sales_cols:
            chart_config = {
                "type": "pie_chart",
                "title": "제품별 매출 비중",
                "data": {
                    "category": product_cols[0],
                    "value": sales_cols[0]
                },
                "description": "제품별 매출 비중을 보여주는 원형 차트",
                "chart_type": "composition_analysis"
            }
            visualizations.append(chart_config)
        
        # 3. 지역별 매출 막대 차트
        if region_cols and sales_cols:
            chart_config = {
                "type": "bar_chart",
                "title": "지역별 매출 현황",
                "data": {
                    "x": region_cols[0],
                    "y": sales_cols[0]
                },
                "description": "지역별 매출 현황을 보여주는 막대 차트",
                "chart_type": "comparison_analysis"
            }
            visualizations.append(chart_config)
    
    return visualizations


def _create_customer_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """고객 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # 고객 관련 컬럼 찾기
    customer_cols = _find_customer_columns(df)
    behavior_cols = _find_behavior_columns(df)
    satisfaction_cols = _find_satisfaction_columns(df)
    
    if satisfaction_cols:
        # 1. 고객 만족도 분포 히스토그램
        chart_config = {
            "type": "histogram",
            "title": "고객 만족도 분포",
            "data": {
                "column": satisfaction_cols[0],
                "bins": 5
            },
            "description": "고객 만족도 점수의 분포를 보여주는 히스토그램",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
        
        # 2. 상담 유형별 만족도 박스 플롯
        if '상담유형' in df.columns or '상담_유형' in df.columns:
            chart_config = {
                "type": "box_plot",
                "title": "상담 유형별 만족도 분포",
                "data": {
                    "x": "상담유형" if '상담유형' in df.columns else "상담_유형",
                    "y": satisfaction_cols[0]
                },
                "description": "상담 유형별 만족도 분포를 보여주는 박스 플롯",
                "chart_type": "comparison_analysis"
            }
            visualizations.append(chart_config)
    
    # 3. 고객 세분화 산점도
    if len(customer_cols) >= 2:
        chart_config = {
            "type": "scatter_plot",
            "title": "고객 세분화 분석",
            "data": {
                "x": customer_cols[0],
                "y": customer_cols[1] if len(customer_cols) > 1 else satisfaction_cols[0]
            },
            "description": "고객 특성에 따른 세분화 분석을 보여주는 산점도",
            "chart_type": "segmentation_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_hr_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """HR/인사 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # HR 관련 컬럼 찾기
    employee_cols = _find_employee_columns(df)
    performance_cols = _find_performance_columns(df)
    department_cols = _find_department_columns(df)
    
    if performance_cols and department_cols:
        # 1. 부서별 성과 비교 막대 차트
        chart_config = {
            "type": "bar_chart",
            "title": "부서별 성과 비교",
            "data": {
                "x": department_cols[0],
                "y": performance_cols[0]
            },
            "description": "부서별 평균 성과를 비교하는 막대 차트",
            "chart_type": "comparison_analysis"
        }
        visualizations.append(chart_config)
        
        # 2. 성과 분포 히스토그램
        chart_config = {
            "type": "histogram",
            "title": "직원 성과 분포",
            "data": {
                "column": performance_cols[0],
                "bins": 10
            },
            "description": "직원들의 성과 점수 분포를 보여주는 히스토그램",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
    
    # 3. 근무년수 vs 성과 산점도
    if '근무년수' in df.columns and performance_cols:
        chart_config = {
            "type": "scatter_plot",
            "title": "근무년수 vs 성과 상관관계",
            "data": {
                "x": "근무년수",
                "y": performance_cols[0]
            },
            "description": "근무년수와 성과 간의 상관관계를 보여주는 산점도",
            "chart_type": "correlation_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_marketing_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """마케팅 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # 마케팅 관련 컬럼 찾기
    campaign_cols = _find_campaign_columns(df)
    channel_cols = _find_channel_columns(df)
    conversion_cols = _find_conversion_columns(df)
    
    if campaign_cols and conversion_cols:
        # 1. 캠페인별 전환율 막대 차트
        chart_config = {
            "type": "bar_chart",
            "title": "캠페인별 전환율",
            "data": {
                "x": campaign_cols[0],
                "y": conversion_cols[0]
            },
            "description": "캠페인별 전환율을 비교하는 막대 차트",
            "chart_type": "performance_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_inventory_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """재고/물류 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # 재고 관련 컬럼 찾기
    inventory_cols = _find_inventory_columns(df)
    product_cols = _find_product_columns(df)
    
    if inventory_cols and product_cols:
        # 1. 제품별 재고 수준 막대 차트
        chart_config = {
            "type": "bar_chart",
            "title": "제품별 재고 수준",
            "data": {
                "x": product_cols[0],
                "y": inventory_cols[0]
            },
            "description": "제품별 재고 수준을 보여주는 막대 차트",
            "chart_type": "inventory_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_general_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """일반 도메인 시각화를 생성합니다."""
    visualizations = []
    
    # 수치형 컬럼들
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) >= 2:
        # 1. 상관관계 히트맵
        chart_config = {
            "type": "heatmap",
            "title": "수치형 변수 간 상관관계",
            "data": {
                "columns": numeric_cols[:10]  # 상위 10개 컬럼만
            },
            "description": "수치형 변수들 간의 상관관계를 보여주는 히트맵",
            "chart_type": "correlation_analysis"
        }
        visualizations.append(chart_config)
        
        # 2. 첫 두 수치형 컬럼의 산점도
        chart_config = {
            "type": "scatter_plot",
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
            "data": {
                "x": numeric_cols[0],
                "y": numeric_cols[1]
            },
            "description": "주요 수치형 변수들 간의 관계를 보여주는 산점도",
            "chart_type": "relationship_analysis"
        }
        visualizations.append(chart_config)
    
    if categorical_cols:
        # 3. 범주형 변수 분포 파이 차트
        chart_config = {
            "type": "pie_chart",
            "title": f"{categorical_cols[0]} 분포",
            "data": {
                "category": categorical_cols[0]
            },
            "description": "주요 범주형 변수의 분포를 보여주는 파이 차트",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _generate_purpose_visualizations(df: pd.DataFrame, analysis_purpose: str, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """분석 목적별 시각화를 생성합니다."""
    visualizations = []
    
    if '트렌드' in analysis_purpose or '트렌드 분석' in analysis_purpose:
        visualizations.extend(_create_trend_visualizations(df))
    elif '비교' in analysis_purpose or '비교 분석' in analysis_purpose:
        visualizations.extend(_create_comparison_visualizations(df))
    elif '분포' in analysis_purpose or '분포 분석' in analysis_purpose:
        visualizations.extend(_create_distribution_visualizations(df))
    elif '상관관계' in analysis_purpose or '상관관계 분석' in analysis_purpose:
        visualizations.extend(_create_correlation_visualizations(df))
    elif '예측' in analysis_purpose or '예측 분석' in analysis_purpose:
        visualizations.extend(_create_forecast_visualizations(df))
    
    return visualizations


def _generate_data_characteristic_visualizations(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """데이터 특성별 시각화를 생성합니다."""
    visualizations = []
    
    # 시계열 데이터가 있는 경우
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        chart_config = {
            "type": "time_series",
            "title": "시계열 데이터 분석",
            "data": {
                "date_column": date_cols[0],
                "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist()[:3]
            },
            "description": "시간에 따른 데이터 변화를 보여주는 시계열 차트",
            "chart_type": "time_series_analysis"
        }
        visualizations.append(chart_config)
    
    # 이상치 탐지
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        chart_config = {
            "type": "box_plot",
            "title": "이상치 탐지 분석",
            "data": {
                "columns": numeric_cols.tolist()[:5]
            },
            "description": "수치형 변수들의 이상치를 탐지하는 박스 플롯",
            "chart_type": "anomaly_detection"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_trend_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """트렌드 분석 시각화를 생성합니다."""
    visualizations = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        chart_config = {
            "type": "line_chart",
            "title": "트렌드 분석",
            "data": {
                "x": "index",
                "y": numeric_cols[0]
            },
            "description": "데이터의 시간적 변화 트렌드를 보여주는 선형 차트",
            "chart_type": "trend_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_comparison_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """비교 분석 시각화를 생성합니다."""
    visualizations = []
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if categorical_cols and numeric_cols:
        chart_config = {
            "type": "bar_chart",
            "title": "그룹별 비교 분석",
            "data": {
                "x": categorical_cols[0],
                "y": numeric_cols[0]
            },
            "description": "그룹별 수치를 비교하는 막대 차트",
            "chart_type": "comparison_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_distribution_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """분포 분석 시각화를 생성합니다."""
    visualizations = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        chart_config = {
            "type": "histogram",
            "title": "데이터 분포 분석",
            "data": {
                "column": numeric_cols[0],
                "bins": 20
            },
            "description": "주요 수치형 변수의 분포를 보여주는 히스토그램",
            "chart_type": "distribution_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_correlation_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """상관관계 분석 시각화를 생성합니다."""
    visualizations = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2:
        chart_config = {
            "type": "heatmap",
            "title": "변수 간 상관관계",
            "data": {
                "columns": numeric_cols[:10]
            },
            "description": "수치형 변수들 간의 상관관계를 보여주는 히트맵",
            "chart_type": "correlation_analysis"
        }
        visualizations.append(chart_config)
        
        chart_config = {
            "type": "scatter_plot",
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
            "data": {
                "x": numeric_cols[0],
                "y": numeric_cols[1]
            },
            "description": "주요 변수들 간의 산점도",
            "chart_type": "correlation_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _create_forecast_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """예측 분석 시각화를 생성합니다."""
    visualizations = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        chart_config = {
            "type": "line_chart",
            "title": "예측 분석",
            "data": {
                "x": "index",
                "y": numeric_cols[0],
                "forecast": True
            },
            "description": "과거 데이터를 바탕으로 한 예측 차트",
            "chart_type": "forecast_analysis"
        }
        visualizations.append(chart_config)
    
    return visualizations


def _extract_charts_data(df: pd.DataFrame, domain_type: str, analysis_purpose: str) -> Dict[str, Any]:
    """차트 데이터를 추출합니다."""
    charts_data = {}
    
    # 기본 통계 데이터
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if numeric_cols:
        charts_data['numeric_summary'] = df[numeric_cols].describe().to_dict()
    
    if categorical_cols:
        charts_data['categorical_summary'] = {}
        for col in categorical_cols[:5]:  # 상위 5개만
            charts_data['categorical_summary'][col] = df[col].value_counts().head(10).to_dict()
    
    # 도메인별 특화 데이터
    if '매출' in domain_type or '영업' in domain_type:
        sales_cols = _find_sales_columns(df)
        if sales_cols:
            charts_data['sales_data'] = {
                'total': float(df[sales_cols[0]].sum()),
                'average': float(df[sales_cols[0]].mean()),
                'top_values': df[sales_cols[0]].nlargest(10).tolist()
            }
    
    elif '고객' in domain_type:
        satisfaction_cols = _find_satisfaction_columns(df)
        if satisfaction_cols:
            charts_data['satisfaction_data'] = {
                'distribution': df[satisfaction_cols[0]].value_counts().to_dict(),
                'average': float(df[satisfaction_cols[0]].mean())
            }
    
    elif 'HR' in domain_type or '인사' in domain_type:
        performance_cols = _find_performance_columns(df)
        department_cols = _find_department_columns(df)
        if performance_cols and department_cols:
            charts_data['hr_data'] = df.groupby(department_cols[0])[performance_cols[0]].agg(['mean', 'count']).to_dict()
    
    return charts_data


def _generate_tables_data(df: pd.DataFrame, domain_type: str, analysis_purpose: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 데이터를 생성합니다."""
    tables_data = {}
    
    # 기본 요약 테이블
    tables_data['data_summary'] = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
        'categorical_columns': len(df.select_dtypes(include=['object', 'category']).columns),
        'missing_values': df.isnull().sum().to_dict()
    }
    
    # 도메인별 특화 테이블
    if '매출' in domain_type or '영업' in domain_type:
        sales_cols = _find_sales_columns(df)
        product_cols = _find_product_columns(df)
        if sales_cols and product_cols:
            tables_data['sales_by_product'] = df.groupby(product_cols[0])[sales_cols[0]].agg(['sum', 'mean', 'count']).to_dict()
    
    elif '고객' in domain_type:
        satisfaction_cols = _find_satisfaction_columns(df)
        if satisfaction_cols and '상담유형' in df.columns:
            tables_data['satisfaction_by_type'] = df.groupby('상담유형')[satisfaction_cols[0]].agg(['mean', 'count']).to_dict()
    
    elif 'HR' in domain_type or '인사' in domain_type:
        performance_cols = _find_performance_columns(df)
        department_cols = _find_department_columns(df)
        if performance_cols and department_cols:
            tables_data['performance_by_department'] = df.groupby(department_cols[0])[performance_cols[0]].agg(['mean', 'std', 'count']).to_dict()
    
    # 상위/하위 성과자 테이블
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        tables_data['top_performers'] = df.nlargest(10, numeric_cols[0])[numeric_cols[:3]].to_dict('records')
        tables_data['bottom_performers'] = df.nsmallest(10, numeric_cols[0])[numeric_cols[:3]].to_dict('records')
    
    return tables_data


def _save_visualization_files(visualizations: List[Dict[str, Any]], charts_data: Dict[str, Any], tables_data: Dict[str, Any], output_format: str, data_file_path: str = None) -> List[str]:
    """시각화 파일을 저장합니다."""
    generated_files = []
    
    try:
        # 시각화 설정 파일 저장
        viz_config = {
            "visualizations": visualizations,
            "charts_data": charts_data,
            "tables_data": tables_data,
            "generated_at": datetime.now().isoformat()
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 실제 차트 이미지 생성
        chart_images = _create_actual_charts(visualizations, charts_data, data_file_path)
        generated_files.extend(chart_images)
        
        if output_format == "html":
            # HTML 시각화 파일 생성
            html_content = _generate_html_visualizations(visualizations, charts_data, tables_data, chart_images)
            html_file = f"/tmp/visualizations_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            generated_files.append(html_file)
        
        elif output_format == "json":
            # JSON 설정 파일 저장
            json_file = f"/tmp/visualization_config_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(viz_config, f, ensure_ascii=False, indent=2)
            generated_files.append(json_file)
    
    except Exception as e:
        print(f"시각화 파일 저장 실패: {e}")
    
    return generated_files


def _create_actual_charts(visualizations: List[Dict[str, Any]], charts_data: Dict[str, Any], data_file_path: str = None) -> List[str]:
    """실제 차트 이미지를 생성합니다."""
    generated_images = []
    
    print(f"차트 생성 시작: {len(visualizations)}개 시각화")
    print(f"시각화 라이브러리 사용 가능: {VISUALIZATION_LIBS_AVAILABLE}")
    
    if not VISUALIZATION_LIBS_AVAILABLE:
        print("시각화 라이브러리가 없어서 차트 이미지를 생성할 수 없습니다.")
        return generated_images
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 데이터 로드 (한 번만)
        df = None
        if data_file_path:
            print(f"데이터 파일에서 데이터 로딩: {data_file_path}")
            try:
                df = _load_data(data_file_path)
                if df is not None:
                    print(f"데이터 로딩 성공: {len(df)}행, {len(df.columns)}컬럼")
                else:
                    print("데이터 로딩 실패 - 샘플 데이터로 차트 생성")
            except Exception as e:
                print(f"데이터 로드 실패: {e}")
        else:
            print("데이터 파일 경로가 없음 - 샘플 데이터로 차트 생성")
        
        for i, viz in enumerate(visualizations[:5]):  # 최대 5개 차트만 생성
            try:
                chart_type = viz.get('type', 'bar_chart')
                title = viz.get('title', f'Chart {i+1}')
                
                print(f"\n차트 {i+1} 생성 시도: {title} ({chart_type})")
                
                if chart_type == 'bar_chart':
                    image_path = _create_bar_chart(viz, title, timestamp, i, df)
                elif chart_type == 'line_chart':
                    image_path = _create_line_chart(viz, title, timestamp, i, df)
                elif chart_type == 'pie_chart':
                    image_path = _create_pie_chart(viz, title, timestamp, i, df)
                elif chart_type == 'histogram':
                    image_path = _create_histogram(viz, title, timestamp, i, df)
                elif chart_type == 'scatter_plot':
                    image_path = _create_scatter_plot(viz, title, timestamp, i, df)
                elif chart_type == 'box_plot':
                    image_path = _create_box_plot(viz, title, timestamp, i, df)
                else:
                    print(f"지원하지 않는 차트 유형: {chart_type}, 기본 막대 차트로 생성")
                    image_path = _create_bar_chart(viz, title, timestamp, i, df)  # 기본값
                
                if image_path and os.path.exists(image_path):
                    generated_images.append(image_path)
                    print(f"✅ 차트 생성 성공: {image_path}")
                else:
                    print(f"❌ 차트 생성 실패: {title}")
                    
            except Exception as e:
                print(f"❌ 차트 {i+1} 생성 실패: {e}")
                continue
        
        print(f"\n총 {len(generated_images)}개 차트 이미지 생성 완료")
        
    except Exception as e:
        print(f"❌ 차트 생성 중 전체 오류: {e}")
    
    return generated_images


def _create_bar_chart(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """막대 차트를 생성합니다."""
    try:
        print(f"막대 차트 생성 시작: {title}")
        
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        x_column = data_config.get('x')
        y_column = data_config.get('y')
        
        print(f"차트 설정: x={x_column}, y={y_column}")
        
        # 실제 데이터 사용 시도
        if df is not None and x_column and y_column and x_column in df.columns and y_column in df.columns:
            print(f"실제 데이터 사용: {x_column}, {y_column}")
            try:
                # 실제 데이터로 차트 생성
                categories = df[x_column].tolist()
                values = df[y_column].tolist()
                
                # 데이터 타입 변환 (numpy 타입 처리)
                values = [float(v) if pd.notna(v) else 0 for v in values]
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F39C12', '#9B59B6'])
                plt.title(title, fontsize=14, fontweight='bold')
                plt.xlabel(x_column, fontsize=12)
                plt.ylabel(y_column, fontsize=12)
                plt.xticks(rotation=45)
                
                # 값 표시
                for bar, value in zip(bars, values):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01, 
                            f'{value:.1f}', ha='center', va='bottom')
                
                plt.tight_layout()
                
                # 이미지 저장 (reports 디렉토리에 저장)
                from pathlib import Path
                reports_dir = Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports")
                reports_dir.mkdir(parents=True, exist_ok=True)
                image_path = str(reports_dir / f"chart_{timestamp}_{index}.png")
                plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                
                print(f"차트 이미지 저장 완료: {image_path}")
                return image_path
                
            except Exception as e:
                print(f"❌ 실제 데이터로 막대 차트 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"⚠️ 실제 데이터 사용 실패, 샘플 데이터로 막대 차트 생성: {title}")
        categories = ['개발팀', '마케팅팀', '영업팀', '인사팀']
        values = [15, 10, 20, 5]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        plt.xlabel('부서', fontsize=12)
        plt.ylabel('이탈률 (%)', fontsize=12)
        plt.xticks(rotation=45)
        
        # 값 표시
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value}%', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 이미지 저장 (reports 디렉토리에 저장)
        from pathlib import Path
        reports_dir = Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        image_path = str(reports_dir / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"차트 이미지 저장 완료 (샘플 데이터): {image_path}")
        return image_path
        
    except Exception as e:
        print(f"막대 차트 생성 실패: {e}")
        plt.close()
        return None


def _create_line_chart(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """선형 차트를 생성합니다."""
    try:
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        x_column = data_config.get('x')
        y_column = data_config.get('y')
        
        # 실제 데이터 사용 시도
        if df is not None and x_column and y_column and x_column in df.columns and y_column in df.columns:
            try:
                # 실제 데이터로 차트 생성
                if x_column == 'index':
                    # 인덱스 기반 차트
                    x_data = list(range(len(df)))
                    y_data = df[y_column].tolist()
                else:
                    x_data = df[x_column].tolist()
                    y_data = df[y_column].tolist()
                
                # 데이터 타입 변환 (numpy 타입 처리)
                y_data = [float(v) if pd.notna(v) else 0 for v in y_data]
                
                plt.figure(figsize=(10, 6))
                plt.plot(x_data, y_data, marker='o', linewidth=2, markersize=6, color='#4ECDC4')
                plt.title(title, fontsize=14, fontweight='bold')
                plt.xlabel(x_column if x_column != 'index' else '순서', fontsize=12)
                plt.ylabel(y_column, fontsize=12)
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                
                return image_path
                
            except Exception as e:
                print(f"실제 데이터로 선형 차트 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"실제 데이터 사용 실패, 샘플 데이터로 선형 차트 생성: {title}")
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [10, 12, 15, 13, 17, 20, 18, 22, 25, 23]
        
        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker='o', linewidth=2, markersize=6, color='#4ECDC4')
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        plt.xlabel('월', fontsize=12)
        plt.ylabel('이탈자 수', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return image_path
        
    except Exception as e:
        print(f"선형 차트 생성 실패: {e}")
        plt.close()
        return None


def _create_pie_chart(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """파이 차트를 생성합니다."""
    try:
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        category_column = data_config.get('category')
        value_column = data_config.get('value')
        
        # 실제 데이터 사용 시도
        if df is not None and category_column and value_column and category_column in df.columns and value_column in df.columns:
            try:
                # 실제 데이터로 차트 생성
                category_data = df[category_column].tolist()
                value_data = df[value_column].tolist()
                
                # 데이터 타입 변환 (numpy 타입 처리)
                value_data = [float(v) if pd.notna(v) else 0 for v in value_data]
                
                # 상위 10개만 표시 (너무 많으면 가독성 저하)
                if len(category_data) > 10:
                    # 값 기준으로 정렬하여 상위 10개 선택
                    sorted_data = sorted(zip(category_data, value_data), key=lambda x: x[1], reverse=True)
                    category_data = [item[0] for item in sorted_data[:10]]
                    value_data = [item[1] for item in sorted_data[:10]]
                
                colors = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#96CEB4', '#F39C12', '#9B59B6', '#E74C3C', '#2ECC71', '#F1C40F', '#8E44AD']
                
                plt.figure(figsize=(8, 8))
                wedges, texts, autotexts = plt.pie(value_data, labels=category_data, colors=colors[:len(category_data)], 
                                                  autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
                plt.title(title, fontsize=14, fontweight='bold')
                
                # 텍스트 스타일 조정
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                plt.axis('equal')
                
                image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                
                return image_path
                
            except Exception as e:
                print(f"실제 데이터로 파이 차트 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"실제 데이터 사용 실패, 샘플 데이터로 파이 차트 생성: {title}")
        labels = ['재직자', '퇴사자']
        sizes = [80, 20]
        colors = ['#4ECDC4', '#FF6B6B']
        
        plt.figure(figsize=(8, 8))
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                          startangle=90, textprops={'fontsize': 12})
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        
        # 텍스트 스타일 조정
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.axis('equal')
        
        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return image_path
        
    except Exception as e:
        print(f"파이 차트 생성 실패: {e}")
        plt.close()
        return None


def _create_histogram(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """히스토그램을 생성합니다."""
    try:
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        column = data_config.get('column')
        bins = data_config.get('bins', 30)
        
        # 실제 데이터 사용 시도
        if df is not None and column and column in df.columns:
            try:
                # 실제 데이터로 차트 생성
                data = df[column].dropna().tolist()
                
                # 데이터 타입 변환 (numpy 타입 처리)
                data = [float(v) if pd.notna(v) else 0 for v in data]
                
                if len(data) > 0:
                    plt.figure(figsize=(10, 6))
                    plt.hist(data, bins=bins, color='#45B7D1', alpha=0.7, edgecolor='black')
                    plt.title(title, fontsize=14, fontweight='bold')
                    plt.xlabel(column, fontsize=12)
                    plt.ylabel('빈도', fontsize=12)
                    plt.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    
                    image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                    plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                    plt.close()
                    
                    return image_path
                else:
                    print(f"히스토그램용 데이터가 없음: {column}")
                    plt.close()
                    
            except Exception as e:
                print(f"실제 데이터로 히스토그램 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"실제 데이터 사용 실패, 샘플 데이터로 히스토그램 생성: {title}")
        data = np.random.normal(85, 15, 1000)  # 평균 85, 표준편차 15
        
        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=30, color='#45B7D1', alpha=0.7, edgecolor='black')
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        plt.xlabel('성과점수', fontsize=12)
        plt.ylabel('빈도', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return image_path
        
    except Exception as e:
        print(f"히스토그램 생성 실패: {e}")
        plt.close()
        return None


def _create_scatter_plot(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """산점도를 생성합니다."""
    try:
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        x_column = data_config.get('x')
        y_column = data_config.get('y')
        
        # 실제 데이터 사용 시도
        if df is not None and x_column and y_column and x_column in df.columns and y_column in df.columns:
            try:
                # 실제 데이터로 차트 생성
                x_data = df[x_column].dropna().tolist()
                y_data = df[y_column].dropna().tolist()
                
                # 데이터 타입 변환 (numpy 타입 처리)
                x_data = [float(v) if pd.notna(v) else 0 for v in x_data]
                y_data = [float(v) if pd.notna(v) else 0 for v in y_data]
                
                # 길이가 다른 경우 짧은 쪽에 맞춤
                min_len = min(len(x_data), len(y_data))
                x_data = x_data[:min_len]
                y_data = y_data[:min_len]
                
                if len(x_data) > 0 and len(y_data) > 0:
                    plt.figure(figsize=(10, 6))
                    plt.scatter(x_data, y_data, alpha=0.6, color='#96CEB4', s=50)
                    plt.title(title, fontsize=14, fontweight='bold')
                    plt.xlabel(x_column, fontsize=12)
                    plt.ylabel(y_column, fontsize=12)
                    plt.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    
                    image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                    plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                    plt.close()
                    
                    return image_path
                else:
                    print(f"산점도용 데이터가 없음: {x_column}, {y_column}")
                    plt.close()
                    
            except Exception as e:
                print(f"실제 데이터로 산점도 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"실제 데이터 사용 실패, 샘플 데이터로 산점도 생성: {title}")
        np.random.seed(42)
        x = np.random.normal(5, 2, 100)
        y = x * 0.8 + np.random.normal(0, 5, 100)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(x, y, alpha=0.6, color='#96CEB4', s=50)
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        plt.xlabel('근무년수', fontsize=12)
        plt.ylabel('성과점수', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return image_path
        
    except Exception as e:
        print(f"산점도 생성 실패: {e}")
        plt.close()
        return None


def _create_box_plot(viz_config: Dict[str, Any], title: str, timestamp: str, index: int, df: pd.DataFrame = None) -> str:
    """박스 플롯을 생성합니다."""
    try:
        # viz_config에서 실제 데이터 정보 추출
        data_config = viz_config.get('data', {})
        x_column = data_config.get('x')
        y_column = data_config.get('y')
        columns = data_config.get('columns', [])
        
        # 실제 데이터 사용 시도
        if df is not None:
            try:
                # 방법 1: x, y 컬럼이 있는 경우 (그룹별 박스플롯)
                if x_column and y_column and x_column in df.columns and y_column in df.columns:
                    # 그룹별 데이터 추출
                    groups = df[x_column].unique()
                    data = []
                    labels = []
                    
                    for group in groups[:5]:  # 최대 5개 그룹만
                        group_data = df[df[x_column] == group][y_column].dropna().tolist()
                        if len(group_data) > 0:
                            data.append([float(v) if pd.notna(v) else 0 for v in group_data])
                            labels.append(str(group))
                    
                    if len(data) > 0:
                        plt.figure(figsize=(8, 6))
                        box_plot = plt.boxplot(data, labels=labels, patch_artist=True)
                        
                        # 박스 색상 설정
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F39C12']
                        for patch, color in zip(box_plot['boxes'], colors[:len(data)]):
                            patch.set_facecolor(color)
                            patch.set_alpha(0.7)
                        
                        plt.title(title, fontsize=14, fontweight='bold')
                        plt.xlabel(x_column, fontsize=12)
                        plt.ylabel(y_column, fontsize=12)
                        plt.xticks(rotation=45)
                        plt.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        
                        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                        plt.close()
                        
                        return image_path
                
                # 방법 2: 여러 수치형 컬럼이 있는 경우
                elif columns and len(columns) > 0:
                    numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
                    
                    if len(numeric_cols) > 0:
                        data = []
                        labels = []
                        
                        for col in numeric_cols[:5]:  # 최대 5개 컬럼만
                            col_data = df[col].dropna().tolist()
                            if len(col_data) > 0:
                                data.append([float(v) if pd.notna(v) else 0 for v in col_data])
                                labels.append(col)
                        
                        if len(data) > 0:
                            plt.figure(figsize=(8, 6))
                            box_plot = plt.boxplot(data, labels=labels, patch_artist=True)
                            
                            # 박스 색상 설정
                            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F39C12']
                            for patch, color in zip(box_plot['boxes'], colors[:len(data)]):
                                patch.set_facecolor(color)
                                patch.set_alpha(0.7)
                            
                            plt.title(title, fontsize=14, fontweight='bold')
                            plt.ylabel('값', fontsize=12)
                            plt.xticks(rotation=45)
                            plt.grid(True, alpha=0.3)
                            
                            plt.tight_layout()
                            
                            image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
                            plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
                            plt.close()
                            
                            return image_path
                
            except Exception as e:
                print(f"실제 데이터로 박스 플롯 생성 실패: {e}")
                plt.close()
        
        # 실제 데이터 사용 실패 시 샘플 데이터 사용 (fallback)
        print(f"실제 데이터 사용 실패, 샘플 데이터로 박스 플롯 생성: {title}")
        data = [
            np.random.normal(70, 10, 100),  # 퇴사자 성과
            np.random.normal(85, 8, 100)    # 재직자 성과
        ]
        
        plt.figure(figsize=(8, 6))
        box_plot = plt.boxplot(data, labels=['퇴사자', '재직자'], patch_artist=True)
        
        # 박스 색상 설정
        colors = ['#FF6B6B', '#4ECDC4']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        plt.title(f"{title} (샘플 데이터)", fontsize=14, fontweight='bold')
        plt.ylabel('성과점수', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        image_path = str(Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/reports") / f"chart_{timestamp}_{index}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return image_path
        
    except Exception as e:
        print(f"박스 플롯 생성 실패: {e}")
        plt.close()
        return None


def _generate_html_visualizations(visualizations: List[Dict[str, Any]], charts_data: Dict[str, Any], tables_data: Dict[str, Any], chart_images: List[str] = None) -> str:
    """HTML 시각화를 생성합니다."""
    if chart_images is None:
        chart_images = []
        
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>동적 시각화 리포트</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background-color: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 30px;
        }}
        .chart-container {{ 
            margin: 30px 0; 
            text-align: center;
            background-color: #fafafa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        .chart-image {{ 
            max-width: 100%; 
            height: auto; 
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .table-container {{ 
            margin: 20px 0; 
            overflow-x: auto;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #3498db; 
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{ 
            background-color: #f8f9fa;
        }}
        .stats-grid {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{ 
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{ 
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .chart-title {{ 
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 동적 시각화 리포트</h1>
        <p><strong>생성 시간:</strong> {datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(visualizations)}</div>
                <div>생성된 시각화</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(chart_images)}</div>
                <div>차트 이미지</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(charts_data)}</div>
                <div>차트 데이터</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(tables_data)}</div>
                <div>테이블 데이터</div>
            </div>
        </div>
        
        <h2>📈 생성된 차트 이미지</h2>
"""
    
    # 실제 차트 이미지 표시
    for i, image_path in enumerate(chart_images):
        if i < len(visualizations):
            viz = visualizations[i]
            title = viz.get('title', f'Chart {i+1}')
            description = viz.get('description', '')
            
            html_content += f"""
        <div class="chart-container">
            <div class="chart-title">{title}</div>
            <img src="file://{image_path}" alt="{title}" class="chart-image">
            <p style="margin-top: 10px; color: #7f8c8d; font-style: italic;">{description}</p>
        </div>
"""
    
    html_content += """
        <h2>📋 시각화 설정 정보</h2>
        <div class="table-container">
            <table>
                <tr><th>시각화 제목</th><th>타입</th><th>설명</th><th>차트 유형</th></tr>
"""
    
    for viz in visualizations:
        html_content += f"""
                <tr>
                    <td><strong>{viz.get('title', 'N/A')}</strong></td>
                    <td>{viz.get('type', 'N/A')}</td>
                    <td>{viz.get('description', 'N/A')}</td>
                    <td>{viz.get('chart_type', 'N/A')}</td>
                </tr>
"""
    
    html_content += """
            </table>
        </div>
        
        <h2>📈 차트 데이터 요약</h2>
        <div class="table-container">
            <table>
                <tr><th>데이터 유형</th><th>요약 정보</th></tr>
"""
    
    for key, value in charts_data.items():
        summary = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        html_content += f"                <tr><td><strong>{key}</strong></td><td>{summary}</td></tr>\n"
    
    html_content += """
            </table>
        </div>
        
        <h2>📋 테이블 데이터 요약</h2>
        <div class="table-container">
            <table>
                <tr><th>테이블 유형</th><th>행 수</th><th>설명</th></tr>
"""
    
    for key, value in tables_data.items():
        if isinstance(value, dict):
            row_count = len(value) if isinstance(value, dict) else 1
            html_content += f"                <tr><td><strong>{key}</strong></td><td>{row_count}</td><td>데이터 요약</td></tr>\n"
        else:
            html_content += f"                <tr><td><strong>{key}</strong></td><td>1</td><td>단일 값</td></tr>\n"
    
    html_content += """
            </table>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em;">
            <p><strong>리포트 생성 정보:</strong></p>
            <ul>
                <li>생성 도구: Dynamic Report Generation Agent</li>
                <li>시각화 엔진: Matplotlib, Seaborn, Plotly</li>
                <li>이미지 형식: PNG (고해상도)</li>
                <li>생성 시간: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</li>
            </ul>
            <p>이 리포트는 사용자의 요구사항에 따라 동적으로 생성되었으며, 실제 차트 이미지가 포함되어 있습니다.</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


# 헬퍼 함수들
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

def _find_satisfaction_columns(df: pd.DataFrame) -> List[str]:
    """만족도 관련 컬럼을 찾습니다."""
    satisfaction_keywords = ['satisfaction', '만족도', 'rating', '평점', 'score', '점수']
    satisfaction_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in satisfaction_keywords):
            if df[col].dtype in ['int64', 'float64']:
                satisfaction_cols.append(col)
    return satisfaction_cols

def _find_employee_columns(df: pd.DataFrame) -> List[str]:
    """직원 관련 컬럼을 찾습니다."""
    employee_keywords = ['employee', '직원', 'staff', '인사', 'hr', 'human']
    employee_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in employee_keywords):
            employee_cols.append(col)
    return employee_cols

def _find_performance_columns(df: pd.DataFrame) -> List[str]:
    """성과 관련 컬럼을 찾습니다."""
    performance_keywords = ['performance', '성과', 'kpi', 'metric', '지표', 'score', '점수', 'result', '결과']
    performance_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in performance_keywords):
            if df[col].dtype in ['int64', 'float64']:
                performance_cols.append(col)
    return performance_cols

def _find_department_columns(df: pd.DataFrame) -> List[str]:
    """부서 관련 컬럼을 찾습니다."""
    department_keywords = ['department', '부서', 'team', '팀', 'division', '부문']
    department_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in department_keywords):
            department_cols.append(col)
    return department_cols

def _find_campaign_columns(df: pd.DataFrame) -> List[str]:
    """캠페인 관련 컬럼을 찾습니다."""
    campaign_keywords = ['campaign', '캠페인', 'marketing', '마케팅']
    campaign_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in campaign_keywords):
            campaign_cols.append(col)
    return campaign_cols

def _find_channel_columns(df: pd.DataFrame) -> List[str]:
    """채널 관련 컬럼을 찾습니다."""
    channel_keywords = ['channel', '채널', 'medium', '매체']
    channel_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in channel_keywords):
            channel_cols.append(col)
    return channel_cols

def _find_conversion_columns(df: pd.DataFrame) -> List[str]:
    """전환 관련 컬럼을 찾습니다."""
    conversion_keywords = ['conversion', '전환', 'rate', '비율']
    conversion_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in conversion_keywords):
            if df[col].dtype in ['int64', 'float64']:
                conversion_cols.append(col)
    return conversion_cols

def _find_inventory_columns(df: pd.DataFrame) -> List[str]:
    """재고 관련 컬럼을 찾습니다."""
    inventory_keywords = ['inventory', '재고', 'stock', 'quantity', '수량']
    inventory_cols = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in inventory_keywords):
            if df[col].dtype in ['int64', 'float64']:
                inventory_cols.append(col)
    return inventory_cols


class VisualizationGeneratorTool:
    def __init__(self):
        self.name = "generate_dynamic_visualizations"
        self.description = "분석 목적과 데이터 특성에 따라 차트, 테이블, 시각화 요소를 동적으로 생성합니다."
        self.input_model = VisualizationInput
        self.output_model = VisualizationOutput
        self.execute = generate_dynamic_visualizations