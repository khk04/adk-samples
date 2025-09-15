#!/usr/bin/env python3
"""
MVP-1: 사용자 데이터 기반 질의 생성 에이전트

이 스크립트는 사용자 데이터를 분석하여 최적의 리포트를 생성하기 위한 5단계 질의를 자동 생성하는 에이전트입니다.

주요 기능:
- CSV/Excel 파일 자동 분석
- 5단계 질의 자동 생성 (리포트 유형 → 분석 기준 → 데이터 범위 → 스타일 → 형식)
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
    print("데이터 파일을 분석하고 최적의 리포트 생성을 위한 5단계 질의를 시작합니다.")

    # 초기 질의 시작 (1단계)
    initial_query_output = await agent.tools[1].execute(
        current_step=1,
        user_responses={},
        data_schema={}, # 실제 데이터 스키마는 DataAnalysisTool을 통해 얻어야 함
        data_summary={} # 실제 데이터 요약은 DataAnalysisTool을 통해 얻어야 함
    )
    print(f"에이전트: {initial_query_output.next_query}")

    # 이후 상호작용은 ADK 런타임 또는 웹 UI를 통해 진행됩니다.
    # 이 main.py는 에이전트의 기본적인 시작점을 보여줍니다.

if __name__ == "__main__":
    asyncio.run(main())