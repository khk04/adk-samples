import pandas as pd
import json
from pathlib import Path
from typing import Optional
from google.adk.tools import ToolContext, FunctionTool
from ..config import SAMPLE_DATA_PATH


def analyze_csv_data(tool_context: ToolContext, csv_path: Optional[str] = None) -> dict:
    """
    CSV 데이터를 분석하고 통계 정보를 반환합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        csv_path: CSV 파일 경로 (없으면 샘플 데이터 사용)
    
    Returns:
        dict: 분석된 데이터 통계 정보
    """
    try:
        # CSV 파일 경로 설정
        if csv_path is None:
            csv_path = str(SAMPLE_DATA_PATH)
        
        # CSV 데이터 로드
        df = pd.read_csv(csv_path)
        
        # 기본 통계 정보
        total_records = len(df)
        total_revenue = df['총매출'].sum()
        avg_revenue = df['총매출'].mean()
        
        # 제품별 분석
        product_analysis = df.groupby('제품명').agg({
            '판매량': 'sum',
            '총매출': 'sum',
            '단가': 'mean'
        }).round(0).to_dict('index')
        
        # 지역별 분석
        region_analysis = df.groupby('지역').agg({
            '판매량': 'sum',
            '총매출': 'sum'
        }).round(0).to_dict('index')
        
        # 고객등급별 분석
        customer_analysis = df.groupby('고객등급').agg({
            '판매량': 'sum',
            '총매출': 'sum'
        }).round(0).to_dict('index')
        
        # 카테고리별 분석
        category_analysis = df.groupby('카테고리').agg({
            '판매량': 'sum',
            '총매출': 'sum'
        }).round(0).to_dict('index')
        
        # 날짜별 트렌드 (월별 집계)
        df['날짜'] = pd.to_datetime(df['날짜'])
        df['월'] = df['날짜'].dt.to_period('M')
        monthly_trend = df.groupby('월').agg({
            '판매량': 'sum',
            '총매출': 'sum'
        }).round(0).to_dict('index')
        
        # 분석 결과를 세션 상태에 저장
        analysis_result = {
            "total_records": total_records,
            "total_revenue": int(total_revenue),
            "avg_revenue": int(avg_revenue),
            "product_analysis": product_analysis,
            "region_analysis": region_analysis,
            "customer_analysis": customer_analysis,
            "category_analysis": category_analysis,
            "monthly_trend": {str(k): v for k, v in monthly_trend.items()}
        }
        
        tool_context.state["csv_analysis"] = analysis_result
        
        return {
            "status": "success",
            "message": f"CSV 데이터 분석 완료. 총 {total_records}개 레코드, 총 매출: {int(total_revenue):,}원",
            "data": analysis_result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CSV 데이터 분석 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
csv_analysis_tool = FunctionTool(func=analyze_csv_data)