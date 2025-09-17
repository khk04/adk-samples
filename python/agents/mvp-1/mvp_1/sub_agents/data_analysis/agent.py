# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data analysis sub-agent for analyzing user data."""

from google.adk import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import pandas as pd
import os
from ...config import VDATA_DIR
from . import prompt


class DataAnalysisInput(BaseModel):
    """데이터 분석 입력"""
    file_path: str = Field(..., description="분석할 데이터 파일 경로")
    analysis_type: str = Field(default="comprehensive", description="분석 유형")


class DataAnalysisOutput(BaseModel):
    """데이터 분석 출력"""
    success: bool = Field(..., description="분석 성공 여부")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="데이터 요약 정보")
    business_insights: List[str] = Field(default_factory=list, description="비즈니스 인사이트")
    analysis_recommendations: List[str] = Field(default_factory=list, description="분석 권장사항")
    data_quality_issues: List[str] = Field(default_factory=list, description="데이터 품질 이슈")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def analyze_user_data(file_path: str, analysis_type: str = "comprehensive") -> DataAnalysisOutput:
    """
    사용자 데이터를 분석하여 비즈니스 인사이트와 리포트 생성 권장사항을 제공합니다.
    """
    try:
        # 경로 처리
        if not os.path.isabs(file_path):
            file_path = str(VDATA_DIR / file_path)
        
        if not os.path.exists(file_path):
            return DataAnalysisOutput(
                success=False,
                error_message=f"파일을 찾을 수 없습니다: {file_path}"
            )
        
        # 데이터 로드
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
        
        # 비즈니스 인사이트 도출
        business_insights = []
        analysis_recommendations = []
        data_quality_issues = []
        
        # 수치형 데이터 분석
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['sales', 'revenue', 'amount', 'price']):
                    business_insights.append(f"매출 관련 데이터: {col} (평균: {df[col].mean():.2f})")
                    analysis_recommendations.append(f"{col} 기준 매출 분석 및 트렌드 파악")
                elif any(keyword in col_lower for keyword in ['quantity', 'count', 'volume']):
                    business_insights.append(f"수량 관련 데이터: {col} (총합: {df[col].sum():.0f})")
                    analysis_recommendations.append(f"{col} 기준 수량 분석 및 패턴 파악")
        
        # 범주형 데이터 분석
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            for col in categorical_cols:
                col_lower = col.lower()
                unique_count = df[col].nunique()
                if any(keyword in col_lower for keyword in ['product', 'category', 'item']):
                    business_insights.append(f"제품 관련 데이터: {col} ({unique_count}개 카테고리)")
                    analysis_recommendations.append(f"{col} 기준 제품별 성과 분석")
                elif any(keyword in col_lower for keyword in ['region', 'area', 'location']):
                    business_insights.append(f"지역 관련 데이터: {col} ({unique_count}개 지역)")
                    analysis_recommendations.append(f"{col} 기준 지역별 분석")
                elif any(keyword in col_lower for keyword in ['customer', 'client', 'user']):
                    business_insights.append(f"고객 관련 데이터: {col} ({unique_count}명 고객)")
                    analysis_recommendations.append(f"{col} 기준 고객 세분화 분석")
        
        # 데이터 품질 이슈 확인
        missing_data = df.isnull().sum()
        high_missing = missing_data[missing_data > 0]
        if len(high_missing) > 0:
            for col, count in high_missing.items():
                percentage = (count / len(df)) * 100
                data_quality_issues.append(f"{col}: {count}개 결측값 ({percentage:.1f}%)")
        
        # 이상치 검출 (수치형 데이터)
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                data_quality_issues.append(f"{col}: {len(outliers)}개 이상치 발견")
        
        return DataAnalysisOutput(
            success=True,
            data_summary=data_summary,
            business_insights=business_insights,
            analysis_recommendations=analysis_recommendations,
            data_quality_issues=data_quality_issues
        )
        
    except Exception as e:
        return DataAnalysisOutput(
            success=False,
            error_message=f"데이터 분석 중 오류가 발생했습니다: {str(e)}"
        )


MODEL = "gemini-2.0-flash"

data_analysis_agent = Agent(
    model=MODEL,
    name="data_analysis_agent",
    instruction=prompt.DATA_ANALYSIS_PROMPT,
    tools=[analyze_user_data],
    output_key="analysis_results"
)