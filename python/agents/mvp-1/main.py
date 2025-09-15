#!/usr/bin/env python3
"""
MVP-1: 사용자 데이터 기반 질의 생성 에이전트

이 스크립트는 사용자 데이터를 분석하여 최적의 리포트를 생성하기 위한 5단계 질의를 단계별로 처리하는 에이전트입니다.

주요 기능:
- CSV/Excel 파일 자동 분석
- 5단계 질의 단계별 처리 (리포트 유형 → 분석 기준 → 데이터 범위 → 스타일 → 형식)
- 사용자 응답 기반 맞춤형 질의 진행
- 최종 리포트 생성 가이드 제공

사용법:
    python main.py

예시:
    python main.py
"""

import asyncio
from mvp_1.agent import query_generation_agent
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    agent = query_generation_agent()
    print("MVP-1: 사용자 데이터 기반 질의 생성 에이전트가 시작되었습니다.")
    print("데이터 파일을 분석하고 최적의 리포트 생성을 위한 5단계 질의를 단계별로 진행합니다.")
    print("=" * 60)

    # 질의 생성 도구 (인덱스 3)
    query_tool = agent.tools[3]
    
    # 단계별 질의 진행을 위한 변수
    current_step = 1
    user_responses = {}
    data_schema = {
        "월": "string",
        "지역": "string", 
        "상품군": "string",
        "매출액": "number",
        "거래건수": "number",
        "고객유형": "string",
        "고객만족도": "number"
    }
    data_summary = {
        "total_rows": 100,
        "columns": list(data_schema.keys()),
        "date_range": "2025-01 ~ 2025-02"
    }
    
    # 5단계 질의 진행
    while current_step <= 5:
        print(f"\n[단계 {current_step}/5]")
        
        # 현재 단계 질의 생성
        query_output = await query_tool.execute(
            current_step=current_step,
            user_responses=user_responses,
            data_schema=data_schema,
            data_summary=data_summary
        )
        
        print(f"에이전트: {query_output.next_query}")
        
        # 사용자 입력 받기
        user_input = input("\n사용자: ").strip()
        
        if not user_input:
            print("입력이 없습니다. 다시 시도해주세요.")
            continue
            
        # 사용자 응답을 다음 단계로 전달
        next_query_output = await query_tool.execute(
            current_step=current_step,
            user_responses=user_responses,
            data_schema=data_schema,
            data_summary=data_summary,
            user_input=user_input
        )
        
        # 수집된 응답 업데이트
        user_responses = next_query_output.collected_responses
        
        # 다음 단계로 이동
        if next_query_output.next_step:
            current_step = next_query_output.next_step
        else:
            # 최종 단계 완료
            print(f"\n{next_query_output.next_query}")
            if next_query_output.report_guide:
                print(next_query_output.report_guide)
            break
    
    print("\n" + "=" * 60)
    print("5단계 질의가 완료되었습니다. 리포트 생성 가이드가 제공되었습니다.")
    print("이제 실제 리포트 생성을 진행할 수 있습니다.")

if __name__ == "__main__":
    asyncio.run(main())