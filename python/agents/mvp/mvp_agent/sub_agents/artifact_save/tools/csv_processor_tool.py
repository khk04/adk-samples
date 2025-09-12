import io
import pandas as pd
from typing import Optional, Dict, Any
from google.adk.tools import ToolContext, FunctionTool


def process_csv_content(tool_context: ToolContext, csv_content: str) -> dict:
    """
    CSV 내용을 처리하고 분석합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        csv_content: CSV 파일의 내용
    
    Returns:
        dict: CSV 처리 결과
    """
    try:
        # CSV 내용을 DataFrame으로 변환
        csv_io = io.StringIO(csv_content)
        df = pd.read_csv(csv_io)
        
        # 기본 정보 수집
        total_rows = len(df)
        total_columns = len(df.columns)
        column_names = list(df.columns)
        
        # 숫자형 컬럼 식별
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        # 기본 통계 정보
        basic_stats = {}
        if numeric_columns:
            basic_stats = df[numeric_columns].describe().round(2).to_dict()
        
        # 카테고리형 컬럼 분석
        categorical_analysis = {}
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in categorical_columns:
            if df[col].nunique() < 50:  # 너무 많은 고유값이 아닌 경우만
                categorical_analysis[col] = {
                    "unique_count": df[col].nunique(),
                    "value_counts": df[col].value_counts().head(10).to_dict(),
                    "top_value": df[col].mode().iloc[0] if not df[col].mode().empty else None
                }
        
        # 처리 결과를 세션 상태에 저장
        csv_analysis = {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "column_names": column_names,
            "numeric_columns": numeric_columns,
            "basic_stats": basic_stats,
            "categorical_analysis": categorical_analysis,
            "data_preview": df.head(5).to_dict('records')
        }
        
        tool_context.state["csv_analysis"] = csv_analysis
        tool_context.state["csv_dataframe"] = df.to_json(orient='records')
        
        return {
            "status": "success",
            "message": f"CSV 처리 완료: {total_rows}행, {total_columns}열",
            "analysis": csv_analysis
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CSV 처리 중 오류 발생: {str(e)}"
        }


def validate_csv_format(tool_context: ToolContext, csv_content: str) -> dict:
    """
    CSV 형식을 검증합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        csv_content: CSV 파일의 내용
    
    Returns:
        dict: 검증 결과
    """
    try:
        # CSV 형식 검증
        csv_io = io.StringIO(csv_content)
        
        # 첫 번째 줄을 읽어서 컬럼 수 확인
        first_line = csv_io.readline().strip()
        if not first_line:
            return {
                "status": "error",
                "message": "CSV 파일이 비어있습니다."
            }
        
        # 쉼표로 구분된 컬럼 수 계산
        columns_count = len(first_line.split(','))
        
        # 몇 줄 더 읽어서 일관성 확인
        csv_io.seek(0)
        lines = csv_io.readlines()[:10]  # 처음 10줄만 확인
        
        consistent_columns = True
        for i, line in enumerate(lines):
            line_columns = len(line.strip().split(','))
            if line_columns != columns_count:
                consistent_columns = False
                break
        
        return {
            "status": "success",
            "message": f"CSV 형식 검증 완료: {columns_count}개 컬럼",
            "columns_count": columns_count,
            "consistent_format": consistent_columns,
            "sample_lines": len(lines)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CSV 형식 검증 중 오류 발생: {str(e)}"
        }


def extract_csv_summary(tool_context: ToolContext, csv_content: str) -> dict:
    """
    CSV 내용의 요약 정보를 추출합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        csv_content: CSV 파일의 내용
    
    Returns:
        dict: 요약 정보
    """
    try:
        csv_io = io.StringIO(csv_content)
        df = pd.read_csv(csv_io)
        
        # 요약 정보 생성
        summary = {
            "file_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum()
            },
            "columns": {
                "names": list(df.columns),
                "types": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            },
            "data_quality": {
                "duplicate_rows": df.duplicated().sum(),
                "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            }
        }
        
        # 숫자형 컬럼이 있으면 통계 추가
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_columns:
            summary["numeric_summary"] = {
                "columns": numeric_columns,
                "correlations": df[numeric_columns].corr().round(3).to_dict()
            }
        
        return {
            "status": "success",
            "message": "CSV 요약 정보 추출 완료",
            "summary": summary
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CSV 요약 추출 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
csv_processor_tool = FunctionTool(func=process_csv_content)
csv_validator_tool = FunctionTool(func=validate_csv_format)
csv_summary_tool = FunctionTool(func=extract_csv_summary)
