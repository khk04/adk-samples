"""
에이전트 클래스 정의
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from .models import (
    DocumentAnalysis, QuestionCandidate, QuestionSet, SelectedContext,
    ReportRequest, ReportDraft, FinalReport, FeedbackRequest,
    DocumentType, ReportType, ReportStatus
)
from .utils import DocumentProcessor, ReportGenerator


class DocumentQuestionAgent:
    """문서 분석 및 질문 생성 에이전트"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.document_processor = DocumentProcessor()
        self.agent_id = f"doc_question_agent_{uuid.uuid4().hex[:8]}"
        logger.info(f"DocumentQuestionAgent 초기화: {self.agent_id}")
    
    async def analyze_document(self, file_path: str, filename: str) -> DocumentAnalysis:
        """문서를 분석하고 텍스트를 추출합니다."""
        try:
            logger.info(f"문서 분석 시작: {filename}")
            
            # 문서 타입 감지
            doc_type = self._detect_document_type(filename)
            
            # 텍스트 추출
            content = await self.document_processor.extract_text(file_path, doc_type)
            
            # 문서 요약 및 키 토픽 추출
            summary, key_topics = await self._generate_summary_and_topics(content)
            
            # 엔티티 추출
            entities = await self._extract_entities(content)
            
            # 메타데이터 생성
            metadata = self._generate_metadata(filename, doc_type, len(content))
            
            analysis = DocumentAnalysis(
                document_id=str(uuid.uuid4()),
                filename=filename,
                document_type=doc_type,
                content=content,
                summary=summary,
                key_topics=key_topics,
                entities=entities,
                metadata=metadata,
                confidence_score=0.95  # 기본 신뢰도
            )
            
            logger.info(f"문서 분석 완료: {filename}, ID: {analysis.document_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"문서 분석 실패: {filename}, 오류: {str(e)}")
            raise
    
    async def generate_question_candidates(self, document_analysis: DocumentAnalysis) -> QuestionSet:
        """문서 분석 결과를 바탕으로 질문 후보를 생성합니다."""
        try:
            logger.info(f"질문 후보 생성 시작: 문서 ID {document_analysis.document_id}")
            
            # AI를 사용하여 질문 후보 생성
            questions = await self._generate_questions_with_ai(document_analysis)
            
            # 질문 후보 정렬 및 우선순위 부여
            sorted_questions = self._prioritize_questions(questions)
            
            question_set = QuestionSet(
                question_set_id=str(uuid.uuid4()),
                document_id=document_analysis.document_id,
                questions=sorted_questions,
                version=1
            )
            
            logger.info(f"질문 후보 생성 완료: {len(sorted_questions)}개 질문")
            return question_set
            
        except Exception as e:
            logger.error(f"질문 후보 생성 실패: {str(e)}")
            raise
    
    async def regenerate_questions(self, document_analysis: DocumentAnalysis, 
                                 feedback: FeedbackRequest, 
                                 current_question_set: QuestionSet) -> QuestionSet:
        """피드백을 바탕으로 새로운 질문 세트를 생성합니다."""
        try:
            logger.info(f"질문 재생성 시작: 문서 ID {document_analysis.document_id}")
            
            # 피드백을 바탕으로 개선된 질문 생성
            improved_questions = await self._generate_improved_questions(
                document_analysis, feedback, current_question_set
            )
            
            # 새로운 버전의 질문 세트 생성
            new_question_set = QuestionSet(
                question_set_id=str(uuid.uuid4()),
                document_id=document_analysis.document_id,
                questions=improved_questions,
                version=current_question_set.version + 1
            )
            
            logger.info(f"질문 재생성 완료: 버전 {new_question_set.version}")
            return new_question_set
            
        except Exception as e:
            logger.error(f"질문 재생성 실패: {str(e)}")
            raise
    
    def _detect_document_type(self, filename: str) -> DocumentType:
        """파일명을 기반으로 문서 타입을 감지합니다."""
        extension = filename.lower().split('.')[-1]
        
        type_mapping = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'txt': DocumentType.TXT,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'md': DocumentType.MARKDOWN,
            'csv': DocumentType.CSV,
            'xlsx': DocumentType.EXCEL,
            'xls': DocumentType.EXCEL
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)
    
    async def _generate_summary_and_topics(self, content: str) -> Tuple[str, List[str]]:
        """AI를 사용하여 문서 요약과 키 토픽을 생성합니다."""
        # 실제 구현에서는 OpenAI API 호출
        summary = f"문서 내용 요약: {content[:200]}..."
        key_topics = ["주제1", "주제2", "주제3"]
        return summary, key_topics
    
    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """문서에서 엔티티를 추출합니다."""
        # 실제 구현에서는 NER 모델 사용
        entities = [
            {"text": "엔티티1", "type": "PERSON", "confidence": 0.9},
            {"text": "엔티티2", "type": "ORGANIZATION", "confidence": 0.8}
        ]
        return entities
    
    def _generate_metadata(self, filename: str, doc_type: DocumentType, content_length: int) -> Dict[str, Any]:
        """문서 메타데이터를 생성합니다."""
        return {
            "original_filename": filename,
            "content_length": content_length,
            "processing_timestamp": datetime.now().isoformat(),
            "agent_version": "1.0.0"
        }
    
    async def _generate_questions_with_ai(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """AI를 사용하여 질문 후보를 생성합니다."""
        # 실제 구현에서는 OpenAI API 호출
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="이 문서의 주요 내용은 무엇인가요?",
                category="일반",
                priority=5,
                context="문서 전체 내용 파악",
                suggested_report_type=ReportType.EXECUTIVE_SUMMARY,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="주요 데이터와 통계는 무엇인가요?",
                category="데이터",
                priority=4,
                context="정량적 정보 분석",
                suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.85
            )
        ]
        return questions
    
    def _prioritize_questions(self, questions: List[QuestionCandidate]) -> List[QuestionCandidate]:
        """질문을 우선순위에 따라 정렬합니다."""
        return sorted(questions, key=lambda x: x.priority, reverse=True)
    
    async def _generate_improved_questions(self, document_analysis: DocumentAnalysis,
                                        feedback: FeedbackRequest,
                                        current_question_set: QuestionSet) -> List[QuestionCandidate]:
        """피드백을 바탕으로 개선된 질문을 생성합니다."""
        # 실제 구현에서는 피드백을 분석하여 개선된 질문 생성
        improved_questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="사용자 요구사항에 맞는 맞춤형 질문",
                category="맞춤형",
                priority=5,
                context=f"피드백 기반: {feedback.user_feedback}",
                suggested_report_type=ReportType.CUSTOM,
                confidence_score=0.9
            )
        ]
        return improved_questions


class ReportAgent:
    """리포트 생성 에이전트"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.report_generator = ReportGenerator()
        self.agent_id = f"report_agent_{uuid.uuid4().hex[:8]}"
        logger.info(f"ReportAgent 초기화: {self.agent_id}")
    
    async def create_report_draft(self, context: SelectedContext, 
                                document_analysis: DocumentAnalysis) -> ReportDraft:
        """선택된 컨텍스트를 바탕으로 리포트 초안을 생성합니다."""
        try:
            logger.info(f"리포트 초안 생성 시작: 컨텍스트 ID {context.context_id}")
            
            # 컨텍스트 분석
            report_outline = await self._analyze_context_and_create_outline(context, document_analysis)
            
            # 초안 내용 생성
            draft_content = await self._generate_draft_content(context, document_analysis, report_outline)
            
            # 주요 발견사항 및 권장사항 추출
            key_findings, recommendations = await self._extract_key_insights(draft_content)
            
            draft = ReportDraft(
                draft_id=str(uuid.uuid4()),
                request_id=context.context_id,
                title=f"{context.report_type.value.replace('_', ' ').title()} 리포트",
                outline=report_outline,
                content=draft_content,
                key_findings=key_findings,
                recommendations=recommendations,
                data_sources=[document_analysis.document_id]
            )
            
            logger.info(f"리포트 초안 생성 완료: {draft.draft_id}")
            return draft
            
        except Exception as e:
            logger.error(f"리포트 초안 생성 실패: {str(e)}")
            raise
    
    async def generate_final_report(self, draft: ReportDraft, 
                                  context: SelectedContext,
                                  document_analysis: DocumentAnalysis) -> FinalReport:
        """초안을 바탕으로 최종 리포트를 생성합니다."""
        try:
            logger.info(f"최종 리포트 생성 시작: 초안 ID {draft.draft_id}")
            
            # 초안을 바탕으로 최종 내용 생성
            final_content = await self._generate_final_content(draft, context, document_analysis)
            
            # 집행 요약 생성
            executive_summary = await self._generate_executive_summary(final_content)
            
            # 방법론 및 결론 생성
            methodology, conclusions = await self._generate_methodology_and_conclusions(
                final_content, context
            )
            
            # 부록 생성
            appendices = await self._generate_appendices(draft, document_analysis)
            
            final_report = FinalReport(
                report_id=str(uuid.uuid4()),
                draft_id=draft.draft_id,
                title=draft.title,
                content=final_content,
                executive_summary=executive_summary,
                methodology=methodology,
                findings=draft.key_findings,
                conclusions=conclusions,
                recommendations=draft.recommendations,
                appendices=appendices
            )
            
            logger.info(f"최종 리포트 생성 완료: {final_report.report_id}")
            return final_report
            
        except Exception as e:
            logger.error(f"최종 리포트 생성 실패: {str(e)}")
            raise
    
    async def _analyze_context_and_create_outline(self, context: SelectedContext,
                                                document_analysis: DocumentAnalysis) -> List[str]:
        """컨텍스트를 분석하여 리포트 아웃라인을 생성합니다."""
        # 실제 구현에서는 AI를 사용하여 컨텍스트 기반 아웃라인 생성
        outline = [
            "1. 개요 및 배경",
            "2. 분석 방법론",
            "3. 주요 발견사항",
            "4. 상세 분석",
            "5. 결론 및 권장사항"
        ]
        return outline
    
    async def _generate_draft_content(self, context: SelectedContext,
                                    document_analysis: DocumentAnalysis,
                                    outline: List[str]) -> str:
        """초안 내용을 생성합니다."""
        # 실제 구현에서는 AI를 사용하여 컨텍스트 기반 내용 생성
        content = f"""
        {context.report_type.value.replace('_', ' ').title()} 리포트
        
        분석 범위: {context.scope}
        분석 기준: {', '.join(context.criteria)}
        
        문서 요약: {document_analysis.summary}
        
        선택된 질문들에 대한 분석 결과...
        """
        return content
    
    async def _extract_key_insights(self, content: str) -> Tuple[List[str], List[str]]:
        """내용에서 주요 발견사항과 권장사항을 추출합니다."""
        # 실제 구현에서는 AI를 사용하여 인사이트 추출
        key_findings = ["발견사항 1", "발견사항 2"]
        recommendations = ["권장사항 1", "권장사항 2"]
        return key_findings, recommendations
    
    async def _generate_final_content(self, draft: ReportDraft,
                                    context: SelectedContext,
                                    document_analysis: DocumentAnalysis) -> str:
        """최종 내용을 생성합니다."""
        # 실제 구현에서는 초안을 바탕으로 최종 내용 생성
        final_content = f"""
        {draft.content}
        
        추가 분석 및 검증을 거친 최종 내용...
        """
        return final_content
    
    async def _generate_executive_summary(self, content: str) -> str:
        """집행 요약을 생성합니다."""
        # 실제 구현에서는 AI를 사용하여 집행 요약 생성
        return "이 리포트는 주요 분석 결과와 권장사항을 요약한 것입니다."
    
    async def _generate_methodology_and_conclusions(self, content: str,
                                                  context: SelectedContext) -> Tuple[str, List[str]]:
        """방법론과 결론을 생성합니다."""
        # 실제 구현에서는 AI를 사용하여 방법론과 결론 생성
        methodology = "문서 분석 및 AI 기반 질문 생성 방법론을 사용했습니다."
        conclusions = ["결론 1", "결론 2"]
        return methodology, conclusions
    
    async def _generate_appendices(self, draft: ReportDraft,
                                  document_analysis: DocumentAnalysis) -> List[Dict[str, Any]]:
        """부록을 생성합니다."""
        # 실제 구현에서는 관련 데이터 및 차트를 부록으로 생성
        appendices = [
            {
                "title": "원본 문서 정보",
                "content": f"문서 ID: {document_analysis.document_id}",
                "type": "metadata"
            }
        ]
        return appendices