"""
통합 데이터 처리 도구

검증과 분석을 한 번에 수행하고 결과를 세션에 저장하는 통합 도구입니다.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import numpy as np
import time
import logging
import os
import glob
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
        possible_paths = [
            "/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/vdata",
            "data/vdata",
            "./data/vdata",
            "../data/vdata",
            "../../data/vdata",
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


class IntegratedDataProcessingInput(BaseModel):
    """통합 데이터 처리 입력"""
    session_id: str = Field(..., description="세션 ID")
    operation: str = Field(default="validate_and_analyze", description="수행할 작업 (validate_and_analyze, validate_only, analyze_only)")
    file_path: str = Field(default="", description="처리할 데이터 파일 경로 (비어있으면 자동 탐지)")
    analysis_type: str = Field(default="basic", description="분석 유형 (basic, detailed, schema_only)")
    required_columns: List[str] = Field(default=[], description="필수 컬럼 목록")
    min_rows: int = Field(default=1, description="최소 행 수")
    force_refresh: bool = Field(default=False, description="캐시 무시하고 새로 처리할지 여부")


class IntegratedDataProcessingOutput(BaseModel):
    """통합 데이터 처리 출력"""
    success: bool = Field(..., description="처리 성공 여부")
    session_id: str = Field(..., description="세션 ID")
    operation: str = Field(..., description="수행된 작업")
    file_path: str = Field(..., description="처리된 파일 경로")
    
    # 검증 결과
    validation_result: Optional[Dict[str, Any]] = Field(None, description="데이터 검증 결과")
    
    # 분석 결과
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="데이터 분석 결과")
    
    # 통합 정보
    integrated_summary: Dict[str, Any] = Field(default_factory=dict, description="통합 요약 정보")
    cache_info: Dict[str, Any] = Field(default_factory=dict, description="캐시 사용 정보")
    performance_info: Dict[str, Any] = Field(default_factory=dict, description="성능 정보")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def process_data_intelligently(
    session_id: str,
    operation: str = "validate_and_analyze",
    file_path: str = "",
    analysis_type: str = "basic",
    required_columns: List[str] = [],
    min_rows: int = 1,
    force_refresh: bool = False
) -> IntegratedDataProcessingOutput:
    """
    지능형 통합 데이터 처리 도구
    
    검증과 분석을 한 번에 수행하고 결과를 세션에 저장합니다.
    캐싱 시스템을 활용하여 API 키 낭비를 방지하고 성능을 향상시킵니다.
    """
    start_time = time.time()
    cache_hit = False
    data_source = "unknown"
    
    try:
        logger.info(f"통합 데이터 처리 시작: 세션={session_id}, 작업={operation}, 파일={file_path}")
        
        # 세션 확인
        session = session_manager.get_session(session_id)
        if not session:
            return IntegratedDataProcessingOutput(
                success=False,
                session_id=session_id,
                operation=operation,
                file_path=file_path,
                error_message="유효하지 않은 세션 ID입니다."
            )
        
        # 파일 경로 자동 탐지
        if not file_path:
            logger.info("데이터 파일 자동 탐지 시작...")
            file_path = _find_data_file_for_analysis()
            if not file_path:
                return IntegratedDataProcessingOutput(
                    success=False,
                    session_id=session_id,
                    operation=operation,
                    file_path="",
                    error_message="분석할 데이터 파일을 찾을 수 없습니다. vdata 폴더에 CSV 또는 Excel 파일이 있는지 확인해주세요."
                )
            else:
                logger.info(f"데이터 파일 발견: {file_path}")
        
        # 경로 해석 개선 - 상대 경로를 절대 경로로 변환
        if not os.path.isabs(file_path):
            file_path = str(PROJECT_ROOT / file_path)
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return IntegratedDataProcessingOutput(
                success=False,
                session_id=session_id,
                operation=operation,
                file_path=file_path,
                error_message=f"파일을 찾을 수 없습니다: {file_path}"
            )
        
        # 캐시된 통합 처리 결과 확인
        if not force_refresh:
            cache_params = {
                "operation": operation,
                "analysis_type": analysis_type,
                "required_columns": required_columns,
                "min_rows": min_rows
            }
            cached_result = analysis_cache.get_cached_analysis(file_path, "integrated_processing", cache_params)
            
            if cached_result:
                logger.info(f"캐시된 통합 처리 결과 사용: {file_path}")
                session_manager.increment_cache_hits(session_id)
                cache_hit = True
                data_source = "analysis_cache"
                
                # 세션에 결과 저장
                session_manager.store_analysis_result(
                    session_id, "integrated_processing", cached_result, file_path
                )
                
                return IntegratedDataProcessingOutput(
                    success=True,
                    session_id=session_id,
                    operation=operation,
                    file_path=file_path,
                    validation_result=cached_result.get("validation_result"),
                    analysis_result=cached_result.get("analysis_result"),
                    integrated_summary=cached_result.get("integrated_summary", {}),
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
                return IntegratedDataProcessingOutput(
                    success=False,
                    session_id=session_id,
                    operation=operation,
                    file_path=file_path,
                    error_message="지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 사용해주세요."
                )
            
            # 데이터 캐시에 저장
            data_cache.cache_data(file_path, df)
        else:
            logger.info(f"캐시된 데이터 사용: {file_path}")
            data_source = "data_cache"
            cache_hit = True
            session_manager.increment_cache_hits(session_id)
        
        # 통합 처리 수행
        validation_result = None
        analysis_result = None
        
        # 검증 수행
        if operation in ["validate_and_analyze", "validate_only"]:
            logger.info("데이터 검증 수행 중...")
            validation_result = _perform_validation(df, required_columns, min_rows)
        
        # 분석 수행
        if operation in ["validate_and_analyze", "analyze_only"]:
            logger.info("데이터 분석 수행 중...")
            analysis_result = _perform_analysis(df, analysis_type)
        
        # 통합 요약 생성
        integrated_summary = _generate_integrated_summary(
            file_path, validation_result, analysis_result, operation
        )
        
        # 결과 구성
        result = {
            "validation_result": validation_result,
            "analysis_result": analysis_result,
            "integrated_summary": integrated_summary,
            "operation": operation,
            "analysis_timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "analysis_type": analysis_type
        }
        
        # 분석 결과 캐시에 저장
        cache_params = {
            "operation": operation,
            "analysis_type": analysis_type,
            "required_columns": required_columns,
            "min_rows": min_rows
        }
        analysis_cache.cache_analysis(file_path, "integrated_processing", cache_params, result)
        
        # 세션에 결과 저장
        session_manager.store_analysis_result(session_id, "integrated_processing", result, file_path)
        
        # API 호출 횟수 증가 (실제 처리 수행)
        session_manager.increment_api_calls(session_id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"통합 데이터 처리 완료: {processing_time:.2f}초, 캐시 히트: {cache_hit}")
        
        return IntegratedDataProcessingOutput(
            success=True,
            session_id=session_id,
            operation=operation,
            file_path=file_path,
            validation_result=validation_result,
            analysis_result=analysis_result,
            integrated_summary=integrated_summary,
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
        logger.error(f"통합 데이터 처리 실패: {e}")
        
        # 오류 정보를 세션에 저장
        session_manager.store_analysis_result(
            session_id, "integrated_processing", {}, file_path, 
            success=False, error_message=str(e)
        )
        
        return IntegratedDataProcessingOutput(
            success=False,
            session_id=session_id,
            operation=operation,
            file_path=file_path,
            error_message=f"데이터 처리 중 오류가 발생했습니다: {str(e)}",
            performance_info={
                "processing_time": time.time() - start_time,
                "error_occurred": True
            }
        )


def _perform_validation(df: pd.DataFrame, required_columns: List[str], min_rows: int) -> Dict[str, Any]:
    """데이터 검증 수행"""
    try:
        validation_result = {
            "is_data_ready": True,
            "validation_summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data_types": _convert_numpy_types(df.dtypes.astype(str).to_dict()),
                "missing_values": _convert_numpy_types(df.isnull().sum().to_dict())
            },
            "file_analysis": [{
                "file_name": "current_file",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "missing_values": _convert_numpy_types(df.isnull().sum().to_dict()),
                "data_types": _convert_numpy_types(df.dtypes.astype(str).to_dict())
            }],
            "issues": [],
            "recommendations": []
        }
        
        # 행 수 검증
        if len(df) < min_rows:
            validation_result["is_data_ready"] = False
            validation_result["issues"].append(f"행 수가 부족합니다 (최소 {min_rows}행 필요, 현재 {len(df)}행)")
            validation_result["recommendations"].append(f"데이터 행 수를 {min_rows}행 이상으로 늘려주세요")
        
        # 필수 컬럼 검증
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                validation_result["is_data_ready"] = False
                validation_result["issues"].append(f"필수 컬럼 누락: {list(missing_columns)}")
                validation_result["recommendations"].append("필수 컬럼을 추가해주세요")
        
        # 데이터 품질 평가
        if validation_result["is_data_ready"]:
            validation_result["recommendations"].append("데이터가 준비되었습니다. 분석을 시작할 수 있습니다.")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"데이터 검증 실패: {e}")
        return {
            "is_data_ready": False,
            "issues": [f"검증 중 오류 발생: {str(e)}"],
            "recommendations": ["데이터 파일을 확인해주세요"]
        }


def _perform_analysis(df: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
    """데이터 분석 수행"""
    try:
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
        
        return {
            "data_summary": data_summary,
            "schema_info": schema_info,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"데이터 분석 실패: {e}")
        return {
            "data_summary": {},
            "schema_info": {},
            "insights": [f"분석 중 오류 발생: {str(e)}"]
        }


def _generate_integrated_summary(
    file_path: str, 
    validation_result: Optional[Dict[str, Any]], 
    analysis_result: Optional[Dict[str, Any]], 
    operation: str
) -> Dict[str, Any]:
    """통합 요약 정보 생성"""
    summary = {
        "file_path": file_path,
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "validation_completed": validation_result is not None,
        "analysis_completed": analysis_result is not None
    }
    
    if validation_result:
        summary["validation_summary"] = {
            "is_data_ready": validation_result.get("is_data_ready", False),
            "total_rows": validation_result.get("validation_summary", {}).get("total_rows", 0),
            "total_columns": validation_result.get("validation_summary", {}).get("total_columns", 0),
            "issues_count": len(validation_result.get("issues", [])),
            "recommendations_count": len(validation_result.get("recommendations", []))
        }
    
    if analysis_result:
        summary["analysis_summary"] = {
            "total_rows": analysis_result.get("data_summary", {}).get("total_rows", 0),
            "total_columns": analysis_result.get("data_summary", {}).get("total_columns", 0),
            "insights_count": len(analysis_result.get("insights", [])),
            "schema_columns": len(analysis_result.get("schema_info", {}))
        }
    
    return summary


class IntegratedDataProcessingTool:
    def __init__(self):
        self.name = "process_data_intelligently"
        self.description = "검증과 분석을 한 번에 수행하는 통합 데이터 처리 도구. 캐싱 시스템을 활용하여 API 키 낭비를 방지합니다."
        self.input_model = IntegratedDataProcessingInput
        self.output_model = IntegratedDataProcessingOutput
        self.execute = process_data_intelligently