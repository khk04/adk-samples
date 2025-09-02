"""
메인 시스템 클래스
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger

from .agents import DocumentQuestionAgent, ReportAgent
from .models import (
    DocumentAnalysis, QuestionSet, SelectedContext, ReportRequest,
    ReportDraft, FinalReport, FeedbackRequest, ProcessingStatus,
    ProcessingTask
)


class DocQuestionReportSystem:
    """문서 질문 및 리포트 생성 시스템의 메인 클래스"""
    
    def __init__(self, openai_client=None):
        self.system_id = f"doc_question_report_system_{uuid.uuid4().hex[:8]}"
        self.doc_question_agent = DocumentQuestionAgent(openai_client)
        self.report_agent = ReportAgent(openai_client)
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.document_cache: Dict[str, DocumentAnalysis] = {}
        self.question_set_cache: Dict[str, QuestionSet] = {}
        
        logger.info(f"DocQuestionReportSystem 초기화: {self.system_id}")
    
    async def process_document_upload(self, file_path: str, filename: str) -> Tuple[DocumentAnalysis, QuestionSet]:
        """문서 업로드 및 처리의 전체 워크플로우를 실행합니다."""
        try:
            logger.info(f"문서 업로드 처리 시작: {filename}")
            
            # 1단계: 문서 분석
            document_analysis = await self.doc_question_agent.analyze_document(file_path, filename)
            
            # 캐시에 저장
            self.document_cache[document_analysis.document_id] = document_analysis
            
            # 2단계: 질문 후보 생성
            question_set = await self.doc_question_agent.generate_question_candidates(document_analysis)
            
            # 캐시에 저장
            self.question_set_cache[question_set.question_set_id] = question_set
            
            logger.info(f"문서 업로드 처리 완료: {filename}")
            return document_analysis, question_set
            
        except Exception as e:
            logger.error(f"문서 업로드 처리 실패: {filename}, 오류: {str(e)}")
            raise
    
    async def select_questions_and_context(self, question_set_id: str, 
                                         selected_question_ids: List[str],
                                         report_type: str,
                                         scope: str,
                                         criteria: List[str],
                                         custom_requirements: Optional[str] = None) -> SelectedContext:
        """사용자가 질문을 선택하고 컨텍스트를 설정합니다."""
        try:
            logger.info(f"질문 선택 및 컨텍스트 설정: 질문 세트 ID {question_set_id}")
            
            # 질문 세트 검증
            if question_set_id not in self.question_set_cache:
                raise ValueError(f"질문 세트를 찾을 수 없습니다: {question_set_id}")
            
            question_set = self.question_set_cache[question_set_id]
            
            # 선택된 질문 ID 검증
            available_question_ids = [q.question_id for q in question_set.questions]
            for q_id in selected_question_ids:
                if q_id not in available_question_ids:
                    raise ValueError(f"유효하지 않은 질문 ID: {q_id}")
            
            # 컨텍스트 생성
            context = SelectedContext(
                context_id=str(uuid.uuid4()),
                question_set_id=question_set_id,
                selected_questions=selected_question_ids,
                report_type=report_type,
                custom_requirements=custom_requirements,
                scope=scope,
                criteria=criteria
            )
            
            logger.info(f"컨텍스트 설정 완료: {context.context_id}")
            return context
            
        except Exception as e:
            logger.error(f"컨텍스트 설정 실패: {str(e)}")
            raise
    
    async def generate_report_draft(self, context: SelectedContext) -> ReportDraft:
        """선택된 컨텍스트를 바탕으로 리포트 초안을 생성합니다."""
        try:
            logger.info(f"리포트 초안 생성 시작: 컨텍스트 ID {context.context_id}")
            
            # 문서 분석 결과 가져오기
            question_set = self.question_set_cache[context.question_set_id]
            document_id = question_set.document_id
            document_analysis = self.document_cache[document_id]
            
            # 리포트 초안 생성
            draft = await self.report_agent.create_report_draft(context, document_analysis)
            
            logger.info(f"리포트 초안 생성 완료: {draft.draft_id}")
            return draft
            
        except Exception as e:
            logger.error(f"리포트 초안 생성 실패: {str(e)}")
            raise
    
    async def generate_final_report(self, draft: ReportDraft, 
                                  context: SelectedContext) -> FinalReport:
        """초안을 바탕으로 최종 리포트를 생성합니다."""
        try:
            logger.info(f"최종 리포트 생성 시작: 초안 ID {draft.draft_id}")
            
            # 문서 분석 결과 가져오기
            question_set = self.question_set_cache[context.question_set_id]
            document_id = question_set.document_id
            document_analysis = self.document_cache[document_id]
            
            # 최종 리포트 생성
            final_report = await self.report_agent.generate_final_report(
                draft, context, document_analysis
            )
            
            logger.info(f"최종 리포트 생성 완료: {final_report.report_id}")
            return final_report
            
        except Exception as e:
            logger.error(f"최종 리포트 생성 실패: {str(e)}")
            raise
    
    async def process_feedback_and_regenerate(self, feedback: FeedbackRequest) -> QuestionSet:
        """사용자 피드백을 처리하고 새로운 질문 세트를 생성합니다."""
        try:
            logger.info(f"피드백 처리 및 질문 재생성 시작: 리포트 ID {feedback.report_id}")
            
            # 리포트 ID로 관련 정보 찾기
            # 실제 구현에서는 데이터베이스에서 관련 정보 조회
            document_analysis = await self._get_document_analysis_from_feedback(feedback)
            current_question_set = await self._get_question_set_from_feedback(feedback)
            
            # 새로운 질문 세트 생성
            new_question_set = await self.doc_question_agent.regenerate_questions(
                document_analysis, feedback, current_question_set
            )
            
            # 캐시 업데이트
            self.question_set_cache[new_question_set.question_set_id] = new_question_set
            
            logger.info(f"질문 재생성 완료: 새로운 질문 세트 ID {new_question_set.question_set_id}")
            return new_question_set
            
        except Exception as e:
            logger.error(f"피드백 처리 및 질문 재생성 실패: {str(e)}")
            raise
    
    async def get_system_status(self) -> Dict[str, any]:
        """시스템 상태를 반환합니다."""
        return {
            "system_id": self.system_id,
            "status": "running",
            "active_tasks": len(self.active_tasks),
            "cached_documents": len(self.document_cache),
            "cached_question_sets": len(self.question_set_cache),
            "uptime": datetime.now().isoformat(),
            "agents": {
                "doc_question_agent": self.doc_question_agent.agent_id,
                "report_agent": self.report_agent.agent_id
            }
        }
    
    async def cleanup_resources(self):
        """시스템 리소스를 정리합니다."""
        try:
            logger.info("시스템 리소스 정리 시작")
            
            # 활성 작업 정리
            for task_id, task in self.active_tasks.items():
                if task.status == ProcessingStatus.COMPLETED:
                    del self.active_tasks[task_id]
            
            # 캐시 정리 (오래된 항목 제거)
            current_time = datetime.now()
            max_age_hours = 24
            
            # 문서 캐시 정리
            expired_docs = []
            for doc_id, doc in self.document_cache.items():
                age = (current_time - doc.analysis_timestamp).total_seconds() / 3600
                if age > max_age_hours:
                    expired_docs.append(doc_id)
            
            for doc_id in expired_docs:
                del self.document_cache[doc_id]
            
            # 질문 세트 캐시 정리
            expired_qsets = []
            for qset_id, qset in self.question_set_cache.items():
                age = (current_time - qset.generated_at).total_seconds() / 3600
                if age > max_age_hours:
                    expired_qsets.append(qset_id)
            
            for qset_id in expired_qsets:
                del self.question_set_cache[qset_id]
            
            logger.info(f"리소스 정리 완료: {len(expired_docs)}개 문서, {len(expired_qsets)}개 질문 세트 제거")
            
        except Exception as e:
            logger.error(f"리소스 정리 실패: {str(e)}")
    
    async def _get_document_analysis_from_feedback(self, feedback: FeedbackRequest) -> DocumentAnalysis:
        """피드백에서 문서 분석 결과를 가져옵니다."""
        # 실제 구현에서는 데이터베이스에서 조회
        # 임시로 캐시에서 첫 번째 문서 반환
        if self.document_cache:
            return list(self.document_cache.values())[0]
        else:
            raise ValueError("문서 분석 결과를 찾을 수 없습니다")
    
    async def _get_question_set_from_feedback(self, feedback: FeedbackRequest) -> QuestionSet:
        """피드백에서 질문 세트를 가져옵니다."""
        # 실제 구현에서는 데이터베이스에서 조회
        # 임시로 캐시에서 첫 번째 질문 세트 반환
        if self.question_set_cache:
            return list(self.question_set_cache.values())[0]
        else:
            raise ValueError("질문 세트를 찾을 수 없습니다")


# 비동기 실행을 위한 메인 함수
async def main():
    """메인 실행 함수"""
    try:
        # 시스템 초기화
        system = DocQuestionReportSystem()
        
        # 시스템 상태 확인
        status = await system.get_system_status()
        logger.info(f"시스템 상태: {status}")
        
        # 예시 사용법
        logger.info("DocQuestionReportSystem이 성공적으로 초기화되었습니다.")
        logger.info("사용 가능한 메서드:")
        logger.info("- process_document_upload(file_path, filename)")
        logger.info("- select_questions_and_context(...)")
        logger.info("- generate_report_draft(context)")
        logger.info("- generate_final_report(draft, context)")
        logger.info("- process_feedback_and_regenerate(feedback)")
        
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {str(e)}")
        raise


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())