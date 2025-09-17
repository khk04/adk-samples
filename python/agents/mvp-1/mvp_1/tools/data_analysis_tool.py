"""데이터 분석 도구"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import json
import os
from ..config import PROJECT_ROOT
from typing import Optional


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


class DataAnalysisInput(BaseModel):
    """데이터 분석 입력"""
    file_path: str = Field(default="", description="분석할 데이터 파일 경로 (비어있으면 자동 탐지)")
    analysis_type: str = Field(default="basic", description="분석 유형 (basic, detailed, schema_only)")


class DataAnalysisOutput(BaseModel):
    """데이터 분석 출력"""
    success: bool = Field(..., description="분석 성공 여부")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="데이터 요약 정보")
    schema_info: Dict[str, str] = Field(default_factory=dict, description="데이터 스키마 정보")
    insights: List[str] = Field(default_factory=list, description="데이터 인사이트")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def analyze_data(file_path: str = "", analysis_type: str = "basic") -> DataAnalysisOutput:
    """
    CSV 또는 Excel 파일을 분석하여 데이터의 구조와 내용을 파악합니다.
    file_path가 제공되지 않으면 vdata 폴더에서 자동으로 찾습니다.
    """
    try:
        # 파일 경로 자동 탐지
        if not file_path:
            print("📂 데이터 파일 자동 탐지 시작...")
            file_path = _find_data_file_for_analysis()
            if not file_path:
                return DataAnalysisOutput(
                    success=False,
                    error_message="분석할 데이터 파일을 찾을 수 없습니다. vdata 폴더에 CSV 또는 Excel 파일이 있는지 확인해주세요."
                )
            else:
                print(f"✅ 데이터 파일 발견: {file_path}")
        
        # 경로 해석 개선 - 상대 경로를 절대 경로로 변환 (config 사용)
        if not os.path.isabs(file_path):
            file_path = str(PROJECT_ROOT / file_path)
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return DataAnalysisOutput(
                success=False,
                error_message=f"파일을 찾을 수 없습니다: {file_path}"
            )
        
        # 파일 확장자에 따른 읽기
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            return DataAnalysisOutput(
                success=False,
                error_message="지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 사용해주세요."
            )
        
        # 기본 분석
        data_summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum()
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
                    insights.append(f"{col}: 평균 {df[col].mean():.2f}, 최대 {df[col].max():.2f}, 최소 {df[col].min():.2f}")
            
            # 범주형 컬럼 분석
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                insights.append(f"범주형 데이터: {', '.join(categorical_cols)}")
                for col in categorical_cols:
                    top_values = df[col].value_counts().head(3)
                    insights.append(f"{col} 상위값: {dict(top_values)}")
        
        return DataAnalysisOutput(
            success=True,
            data_summary=data_summary,
            schema_info=schema_info,
            insights=insights
        )
        
    except Exception as e:
        return DataAnalysisOutput(
            success=False,
            error_message=f"데이터 분석 중 오류가 발생했습니다: {str(e)}"
        )


class DataAnalysisTool:
    def __init__(self):
        self.name = "analyze_data"
        self.description = "CSV 또는 Excel 파일을 분석하여 데이터의 구조와 내용을 파악합니다."
        self.input_model = DataAnalysisInput
        self.output_model = DataAnalysisOutput
        self.execute = analyze_data