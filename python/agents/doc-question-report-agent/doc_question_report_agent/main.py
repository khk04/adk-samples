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

"""ADK 기반 문서 질문 및 보고서 생성 에이전트 메인 모듈"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from loguru import logger

from .agents import root_agent, document_question_agent, report_agent
from .tools import (
    document_cache, question_cache, report_cache,
    get_document_status, list_available_documents
)


class DocQuestionReportSystem:
    """ADK 기반 문서 질문 및 보고서 생성 시스템"""
    
    def __init__(self):
        self.main_agent = root_agent
        self.doc_question_agent = document_question_agent
        self.report_agent = report_agent
        logger.info("DocQuestionReportSystem ADK 에이전트 초기화 완료")
    
    async def process_user_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        사용자 요청을 처리합니다.
        
        Args:
            user_input: 사용자 입력
            context: 추가 컨텍스트 정보
            
        Returns:
            str: 에이전트 응답
        """
        try:
            # 메인 에이전트를 통해 사용자 요청 처리
            response = await self.main_agent.run(user_input, context=context)
            return response
            
        except Exception as e:
            logger.error(f"사용자 요청 처리 실패: {str(e)}")
            return f"요청 처리 중 오류가 발생했습니다: {str(e)}"
    
    async def analyze_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        문서를 분석합니다.
        
        Args:
            file_path: 파일 경로
            filename: 파일명
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        try:
            # Document Question Agent를 통해 문서 분석
            response = await self.doc_question_agent.run(
                f"다음 문서를 분석해주세요: {filename}",
                context={"file_path": file_path, "filename": filename}
            )
            
            return {
                "success": True,
                "response": response,
                "document_id": list(document_cache.keys())[-1] if document_cache else None
            }
            
        except Exception as e:
            logger.error(f"문서 분석 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_questions(self, document_id: str, step: int = 1) -> Dict[str, Any]:
        """
        질문을 생성합니다.
        
        Args:
            document_id: 문서 ID
            step: 질문 단계
            
        Returns:
            Dict[str, Any]: 질문 생성 결과
        """
        try:
            # Document Question Agent를 통해 질문 생성
            response = await self.doc_question_agent.run(
                f"문서 {document_id}에 대해 {step}단계 질문을 생성해주세요.",
                context={"document_id": document_id, "step": step}
            )
            
            return {
                "success": True,
                "response": response,
                "question_set_id": list(question_cache.keys())[-1] if question_cache else None
            }
            
        except Exception as e:
            logger.error(f"질문 생성 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_report(self, title: str, report_type: str, document_id: str, selected_questions: List[str]) -> Dict[str, Any]:
        """
        보고서를 생성합니다.
        
        Args:
            title: 보고서 제목
            report_type: 보고서 유형
            document_id: 문서 ID
            selected_questions: 선택된 질문 목록
            
        Returns:
            Dict[str, Any]: 보고서 생성 결과
        """
        try:
            # Report Agent를 통해 보고서 생성
            response = await self.report_agent.run(
                f"'{title}' 제목으로 {report_type} 유형의 보고서를 생성해주세요.",
                context={
                    "title": title,
                    "report_type": report_type,
                    "document_id": document_id,
                    "selected_questions": selected_questions
                }
            )
            
            return {
                "success": True,
                "response": response,
                "draft_id": list(report_cache.keys())[-1] if report_cache else None
            }
            
        except Exception as e:
            logger.error(f"보고서 생성 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        시스템 상태를 조회합니다.
        
        Returns:
            Dict[str, Any]: 시스템 상태 정보
        """
        try:
            # 문서 목록 조회
            documents = list_available_documents()
            
            return {
                "status": "running",
                "agents": {
                    "main_agent": self.main_agent.name,
                    "doc_question_agent": self.doc_question_agent.name,
                    "report_agent": self.report_agent.name
                },
                "cache_stats": {
                    "documents": len(document_cache),
                    "questions": len(question_cache),
                    "reports": len(report_cache)
                },
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"시스템 상태 조회 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


# 시스템 인스턴스
system = DocQuestionReportSystem()


async def main():
    """메인 실행 함수"""
    logger.info("Document Question & Report Agent ADK 시스템 시작")
    
    # 시스템 상태 확인
    status = await system.get_system_status()
    logger.info(f"시스템 상태: {status}")
    
    # 예시 사용법
    try:
        # 사용자 요청 처리 예시
        response = await system.process_user_request(
            "안녕하세요! 문서 분석 및 보고서 생성 시스템입니다."
        )
        logger.info(f"에이전트 응답: {response}")
        
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())