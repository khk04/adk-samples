"""
지능형 데이터 분석 도구

캐싱 시스템을 활용하여 API 키 낭비를 방지하고 성능을 향상시키는 개선된 데이터 분석 도구입니다.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime

from ..cache import data_cache, analysis_cache, cache_manager
from ..session import session_manager
from ..config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _convert_numpy_types(obj):
    """numpy 타입을 Python 기본 타입으로 변환하여 JSON 직렬화 오류를 방지합니다."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: _convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    else:
        return obj


def _find_data_file_for_analysis() -> Optional[str]:
    """vdata 폴더에서 분석할 데이터 파일을 자동으로 찾습니다."""
    try:
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
            # 기타 가능한 경로
            "vdata",
            "./vdata"
        ]
        
        for base_path in possible_paths:
            abs_path = os.path.abspath(base_path)
            
            if os.path.exists(abs_path):
                try:
                    files = os.listdir(abs_path)
                    
                    # CSV 파일 우선 검색
                    for file in files:
                        if file.endswith('.csv'):
                            return os.path.join(abs_path, file)
                    
                    # Excel 파일 검색
                    for file in files:
                        if file.endswith(('.xlsx', '.xls')):
                            return os.path.join(abs_path, file)
                            
                except Exception:
                    continue
        
        return None
        
    except Exception:
        return None


class SmartDataAnalysisInput(BaseModel):
    """지능형 데이터 분석 입력"""
    session_id: str = Field(..., description="세션 ID")
    file_path: str = Field(default="", description="분석할 데이터 파일 경로 (비어있으면 자동 탐지)")
    analysis_type: str = Field(default="basic", description="분석 유형 (basic, detailed, schema_only)")
    force_refresh: bool = Field(default=False, description="캐시 무시하고 새로 분석할지 여부")


class SmartDataAnalysisOutput(BaseModel):
    """지능형 데이터 분석 출력"""
    success: bool = Field(..., description="분석 성공 여부")
    session_id: str = Field(..., description="세션 ID")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="데이터 요약 정보")
    schema_info: Dict[str, str] = Field(default_factory=dict, description="데이터 스키마 정보")
    insights: List[str] = Field(default_factory=list, description="데이터 인사이트")
    cache_info: Dict[str, Any] = Field(default_factory=dict, description="캐시 사용 정보")
    performance_info: Dict[str, Any] = Field(default_factory=dict, description="성능 정보")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def smart_analyze_data(
    session_id: str,
    file_path: str = "",
    analysis_type: str = "basic",
    force_refresh: bool = False
) -> SmartDataAnalysisOutput:
    """
    지능형 데이터 분석 도구
    
    캐싱 시스템을 활용하여 API 키 낭비를 방지하고 성능을 향상시킵니다.
    세션 기반으로 분석 결과를 관리하여 중복 분석을 방지합니다.
    """
    start_time = time.time()
    cache_hit = False
    data_source = "unknown"
    
    try:
        logger.info(f"지능형 데이터 분석 시작: 세션={session_id}, 파일={file_path}, 유형={analysis_type}")
        
        # 세션 확인
        session = session_manager.get_session(session_id)
        if not session:
            return SmartDataAnalysisOutput(
                success=False,
                session_id=session_id,
                error_message="유효하지 않은 세션 ID입니다."
            )
        
        # 파일 경로 자동 탐지
        if not file_path:
            logger.info("데이터 파일 자동 탐지 시작...")
            file_path = _find_data_file_for_analysis()
            if not file_path:
                return SmartDataAnalysisOutput(
                    success=False,
                    session_id=session_id,
                    error_message="분석할 데이터 파일을 찾을 수 없습니다. vdata 폴더에 CSV 또는 Excel 파일이 있는지 확인해주세요."
                )
            else:
                logger.info(f"데이터 파일 발견: {file_path}")
        
        # 경로 해석 개선 - 상대 경로를 절대 경로로 변환
        if not os.path.isabs(file_path):
            file_path = str(PROJECT_ROOT / file_path)
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return SmartDataAnalysisOutput(
                success=False,
                session_id=session_id,
                error_message=f"파일을 찾을 수 없습니다: {file_path}"
            )
        
        # 캐시된 분석 결과 확인 (force_refresh가 False인 경우)
        if not force_refresh:
            cache_params = {"analysis_type": analysis_type}
            cached_result = analysis_cache.get_cached_analysis(file_path, "smart_analysis", cache_params)
            
            if cached_result:
                logger.info(f"캐시된 분석 결과 사용: {file_path}")
                session_manager.increment_cache_hits(session_id)
                cache_hit = True
                data_source = "analysis_cache"
                
                # 세션에 결과 저장
                session_manager.store_analysis_result(
                    session_id, "smart_analysis", cached_result, file_path
                )
                
                return SmartDataAnalysisOutput(
                    success=True,
                    session_id=session_id,
                    data_summary=cached_result.get("data_summary", {}),
                    schema_info=cached_result.get("schema_info", {}),
                    insights=cached_result.get("insights", []),
                    cache_info={
                        "cache_hit": True,
                        "data_source": data_source,
                        "cache_type": "analysis_cache"
                    },
                    performance_info={
                        "processing_time": time.time() - start_time,
                        "cache_efficiency": session.get_cache_efficiency()
                    }
                )
        
        # 캐시된 데이터 확인
        df = data_cache.get_cached_data(file_path)
        
        if df is None:
            logger.info(f"데이터를 로드하고 캐시에 저장: {file_path}")
            data_source = "file_system"
            
            # 파일 읽기
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return SmartDataAnalysisOutput(
                    success=False,
                    session_id=session_id,
                    error_message="지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 사용해주세요."
                )
            
            # 데이터 캐시에 저장
            data_cache.cache_data(file_path, df)
        else:
            logger.info(f"캐시된 데이터 사용: {file_path}")
            data_source = "data_cache"
            cache_hit = True
            session_manager.increment_cache_hits(session_id)
        
        # 분석 수행
        logger.info("데이터 분석 수행 중...")
        
        # 기본 분석
        data_summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": _convert_numpy_types(df.dtypes.astype(str).to_dict()),
            "missing_values": _convert_numpy_types(df.isnull().sum().to_dict()),
            "memory_usage": _convert_numpy_types(df.memory_usage(deep=True).sum())
        }
        
        # 스키마 정보
        schema_info = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            unique_count = df[col].nunique()
            schema_info[col] = f"{dtype} (고유값: {unique_count}개)"
        
        insights = []
        
        # 상세 분석
        if analysis_type in ["detailed", "basic"]:
            # 수치형 컬럼 분석
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                insights.append(f"수치형 데이터: {', '.join(numeric_cols)}")
                for col in numeric_cols:
                    mean_val = _convert_numpy_types(df[col].mean())
                    max_val = _convert_numpy_types(df[col].max())
                    min_val = _convert_numpy_types(df[col].min())
                    insights.append(f"{col}: 평균 {mean_val:.2f}, 최대 {max_val:.2f}, 최소 {min_val:.2f}")
            
            # 범주형 컬럼 분석
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                insights.append(f"범주형 데이터: {', '.join(categorical_cols)}")
                for col in categorical_cols:
                    top_values = df[col].value_counts().head(3)
                    insights.append(f"{col} 상위값: {_convert_numpy_types(dict(top_values))}")
        
        # 결과 구성
        result = {
            "data_summary": data_summary,
            "schema_info": schema_info,
            "insights": insights,
            "analysis_timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "analysis_type": analysis_type
        }
        
        # 분석 결과 캐시에 저장
        cache_params = {"analysis_type": analysis_type}
        analysis_cache.cache_analysis(file_path, "smart_analysis", cache_params, result)
        
        # 세션에 결과 저장
        session_manager.store_analysis_result(session_id, "smart_analysis", result, file_path)
        
        # API 호출 횟수 증가 (실제 분석 수행)
        session_manager.increment_api_calls(session_id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"지능형 데이터 분석 완료: {processing_time:.2f}초, 캐시 히트: {cache_hit}")
        
        return SmartDataAnalysisOutput(
            success=True,
            session_id=session_id,
            data_summary=data_summary,
            schema_info=schema_info,
            insights=insights,
            cache_info={
                "cache_hit": cache_hit,
                "data_source": data_source,
                "cache_type": "data_cache" if data_source == "data_cache" else "analysis_cache"
            },
            performance_info={
                "processing_time": processing_time,
                "cache_efficiency": session.get_cache_efficiency(),
                "api_calls_saved": 1 if cache_hit else 0
            }
        )
        
    except Exception as e:
        logger.error(f"지능형 데이터 분석 실패: {e}")
        
        # 오류 정보를 세션에 저장
        session_manager.store_analysis_result(
            session_id, "smart_analysis", {}, file_path, 
            success=False, error_message=str(e)
        )
        
        return SmartDataAnalysisOutput(
            success=False,
            session_id=session_id,
            error_message=f"데이터 분석 중 오류가 발생했습니다: {str(e)}",
            performance_info={
                "processing_time": time.time() - start_time,
                "error_occurred": True
            }
        )


class SmartDataAnalysisTool:
    def __init__(self):
        self.name = "smart_analyze_data"
        self.description = "캐싱 시스템을 활용한 지능형 데이터 분석 도구. API 키 낭비를 방지하고 성능을 향상시킵니다."
        self.input_model = SmartDataAnalysisInput
        self.output_model = SmartDataAnalysisOutput
        self.execute = smart_analyze_data