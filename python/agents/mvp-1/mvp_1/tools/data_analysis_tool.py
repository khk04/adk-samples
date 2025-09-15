"""데이터 분석 도구"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import json
import os


class DataAnalysisInput(BaseModel):
    """데이터 분석 입력"""
    file_path: str = Field(..., description="분석할 데이터 파일 경로")
    analysis_type: str = Field(default="basic", description="분석 유형 (basic, detailed, schema_only)")


class DataAnalysisOutput(BaseModel):
    """데이터 분석 출력"""
    success: bool = Field(..., description="분석 성공 여부")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="데이터 요약 정보")
    schema_info: Dict[str, str] = Field(default_factory=dict, description="데이터 스키마 정보")
    insights: List[str] = Field(default_factory=list, description="데이터 인사이트")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def analyze_data(input: DataAnalysisInput) -> DataAnalysisOutput:
    """
    CSV 또는 Excel 파일을 분석하여 데이터의 구조와 내용을 파악합니다.
    """
    try:
        file_path = input.file_path
        analysis_type = input.analysis_type
        
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