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
    """문서 스캔 + 질문 생성 에이전트
    
    역할: 문서 스캔 + 질문 생성
    기능:
    - 문서 업로드 처리 (텍스트 추출) - 백엔드에서 수행
    - 문서 내용을 바탕으로 Step 별 질문 후보 생성 
    - iteration 시, 기존 컨텍스트를 유지하고 새로운 질문생성
    - 출력: 사용자가 선택할 수 있는 질의 리스트
    """
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.document_processor = DocumentProcessor()
        self.agent_id = f"doc_question_agent_{uuid.uuid4().hex[:8]}"
        self.question_contexts = {}  # 질문 생성 컨텍스트 저장
        self.iteration_history = {}  # iteration 히스토리 저장
        logger.info(f"DocumentQuestionAgent 초기화: {self.agent_id}")
    
    async def analyze_document(self, file_path: str, filename: str) -> DocumentAnalysis:
        """문서를 분석하고 텍스트를 추출합니다."""
        try:
            logger.info(f"문서 분석 시작: {filename}")
            
            # 문서 타입 감지
            doc_type = self._detect_document_type(filename)
            
            # 텍스트 추출
            content = self.document_processor.process_document(file_path)
            
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
    
    async def generate_question_candidates(self, document_analysis: DocumentAnalysis, step: int = 1) -> QuestionSet:
        """문서 분석 결과를 바탕으로 Step별 질문 후보를 생성합니다."""
        try:
            logger.info(f"Step {step} 질문 후보 생성 시작: 문서 ID {document_analysis.document_id}")
            
            # Step별 질문 생성 전략 적용
            questions = await self._generate_step_based_questions(document_analysis, step)
            
            # 질문 후보 정렬 및 우선순위 부여
            sorted_questions = self._prioritize_questions(questions)
            
            # 컨텍스트 저장
            self.question_contexts[document_analysis.document_id] = {
                'step': step,
                'current_questions': sorted_questions,
                'document_summary': document_analysis.summary,
                'key_topics': document_analysis.key_topics
            }
            
            question_set = QuestionSet(
                question_set_id=str(uuid.uuid4()),
                document_id=document_analysis.document_id,
                questions=sorted_questions,
                version=step,
                step=step
            )
            
            logger.info(f"Step {step} 질문 후보 생성 완료: {len(sorted_questions)}개 질문")
            return question_set
            
        except Exception as e:
            logger.error(f"Step {step} 질문 후보 생성 실패: {str(e)}")
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
                version=current_question_set.version + 1,
                step=getattr(current_question_set, 'step', 1)
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
    
    async def _generate_step_based_questions(self, document_analysis: DocumentAnalysis, step: int) -> List[QuestionCandidate]:
        """Step별 질문 생성 전략을 적용하여 질문 후보를 생성합니다."""
        try:
            logger.info(f"Step {step} 기반 질문 생성 시작")
            
            if step == 1:
                # Step 1: 기본 이해 및 개요 파악
                questions = await self._generate_basic_understanding_questions(document_analysis)
            elif step == 2:
                # Step 2: 상세 분석 및 심화 질문
                questions = await self._generate_detailed_analysis_questions(document_analysis)
            elif step == 3:
                # Step 3: 특정 영역 집중 분석
                questions = await self._generate_focused_analysis_questions(document_analysis)
            elif step == 4:
                # Step 4: 실행 가능한 인사이트 도출
                questions = await self._generate_actionable_insight_questions(document_analysis)
            else:
                # Step 5+: 맞춤형 심화 질문
                questions = await self._generate_custom_deep_questions(document_analysis, step)
            
            logger.info(f"Step {step} 질문 생성 완료: {len(questions)}개")
            return questions
            
        except Exception as e:
            logger.error(f"Step {step} 질문 생성 실패: {str(e)}")
            # 기본 질문으로 폴백
            return await self._generate_fallback_questions(document_analysis)
    
    async def _generate_basic_understanding_questions(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """Step 1: 기본 이해 및 개요 파악 질문 생성"""
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="이 문서의 주요 내용과 핵심 메시지는 무엇인가요?",
                category="개요",
                priority=5,
                context="문서 전체 내용 파악",
                suggested_report_type=ReportType.EXECUTIVE_SUMMARY,
                confidence_score=0.95
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서의 목적과 대상 독자는 누구인가요?",
                category="목적",
                priority=4,
                context="문서 작성 의도 파악",
                suggested_report_type=ReportType.EXECUTIVE_SUMMARY,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서에서 다루는 주요 주제와 범위는 무엇인가요?",
                category="범위",
                priority=4,
                context="분석 범위 정의",
                suggested_report_type=ReportType.EXECUTIVE_SUMMARY,
                confidence_score=0.9
            )
        ]
        return questions
    
    async def _generate_detailed_analysis_questions(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """Step 2: 상세 분석 및 심화 질문 생성"""
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서에서 제시된 주요 데이터와 통계는 무엇인가요?",
                category="데이터",
                priority=5,
                context="정량적 정보 분석",
                suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서의 구조와 논리적 흐름은 어떻게 구성되어 있나요?",
                category="구조",
                priority=4,
                context="문서 구성 분석",
                suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.85
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="주요 인용문과 참고 자료는 무엇인가요?",
                category="참고자료",
                priority=3,
                context="정보 출처 분석",
                suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.8
            )
        ]
        return questions
    
    async def _generate_focused_analysis_questions(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """Step 3: 특정 영역 집중 분석 질문 생성"""
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서에서 언급된 주요 이해관계자와 조직은 누구인가요?",
                category="엔티티",
                priority=4,
                context="관련 조직 및 인물",
                suggested_report_type=ReportType.MARKET_RESEARCH,
                confidence_score=0.85
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서의 방법론과 분석 접근법은 무엇인가요?",
                category="방법론",
                priority=4,
                context="분석 과정 및 도구",
                suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.85
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서에서 다루는 시장 동향과 경쟁 환경은 어떠한가요?",
                category="시장분석",
                priority=3,
                context="외부 환경 분석",
                suggested_report_type=ReportType.MARKET_RESEARCH,
                confidence_score=0.8
            )
        ]
        return questions
    
    async def _generate_actionable_insight_questions(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """Step 4: 실행 가능한 인사이트 도출 질문 생성"""
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서의 결론과 권장사항은 무엇인가요?",
                category="결론",
                priority=5,
                context="실행 가능한 인사이트",
                suggested_report_type=ReportType.RECOMMENDATION,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="이 문서의 내용을 바탕으로 어떤 행동을 취해야 하나요?",
                category="행동",
                priority=5,
                context="실행 계획 수립",
                suggested_report_type=ReportType.RECOMMENDATION,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="문서의 내용이 현재 상황에 어떤 영향을 미칠 수 있나요?",
                category="영향",
                priority=4,
                context="미래 전망 분석",
                suggested_report_type=ReportType.RECOMMENDATION,
                confidence_score=0.85
            )
        ]
        return questions
    
    async def _generate_custom_deep_questions(self, document_analysis: DocumentAnalysis, step: int) -> List[QuestionCandidate]:
        """Step 5+: 맞춤형 심화 질문 생성"""
        questions = [
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question=f"Step {step}에서 추가로 분석이 필요한 특정 영역은 무엇인가요?",
                category="맞춤형",
                priority=4,
                context=f"Step {step} 심화 분석",
                suggested_report_type=ReportType.CUSTOM,
                confidence_score=0.85
            ),
            QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question="이전 단계에서 놓친 중요한 관점이나 정보가 있나요?",
                category="보완",
                priority=3,
                context="누락 정보 보완",
                suggested_report_type=ReportType.CUSTOM,
                confidence_score=0.8
            )
        ]
        return questions
    
    async def _generate_fallback_questions(self, document_analysis: DocumentAnalysis) -> List[QuestionCandidate]:
        """기본 폴백 질문 생성"""
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
    
    async def _generate_context_aware_questions(self, document_analysis: DocumentAnalysis,
                                              feedback: FeedbackRequest,
                                              current_question_set: QuestionSet,
                                              context: Dict) -> List[QuestionCandidate]:
        """컨텍스트를 유지하며 피드백 기반 질문을 생성합니다."""
        try:
            logger.info("컨텍스트 인식 질문 생성 시작")
            
            # 기존 컨텍스트 정보 활용
            step = context.get('step', 1)
            previous_questions = context.get('current_questions', [])
            document_summary = context.get('document_summary', '')
            key_topics = context.get('key_topics', [])
            
            # 피드백 분석
            feedback_analysis = self._analyze_feedback(feedback.user_feedback)
            
            # 컨텍스트를 고려한 개선된 질문 생성
            improved_questions = []
            
            # 1. 피드백에서 언급된 영역에 대한 심화 질문
            if feedback_analysis.get('specific_areas'):
                for area in feedback_analysis['specific_areas']:
                    improved_questions.append(
                        QuestionCandidate(
                            question_id=str(uuid.uuid4()),
                            question=f"'{area}' 영역에 대해 더 자세히 분석할 수 있는 질문은 무엇인가요?",
                            category="심화분석",
                            priority=5,
                            context=f"피드백 기반 심화 분석: {area}",
                            suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                            confidence_score=0.9
                        )
                    )
            
            # 2. 이전 질문과 연계된 후속 질문
            if previous_questions:
                for prev_q in previous_questions[:3]:  # 최근 3개 질문만 고려
                    improved_questions.append(
                        QuestionCandidate(
                            question_id=str(uuid.uuid4()),
                            question=f"'{prev_q.question}'에 대한 후속 질문으로 어떤 것이 있을까요?",
                            category="후속질문",
                            priority=4,
                            context=f"이전 질문 연계: {prev_q.question[:50]}...",
                            suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                            confidence_score=0.85
                        )
                    )
            
            # 3. 문서의 키 토픽을 활용한 새로운 관점 질문
            if key_topics:
                for topic in key_topics[:2]:  # 상위 2개 토픽만 활용
                    improved_questions.append(
                        QuestionCandidate(
                            question_id=str(uuid.uuid4()),
                            question=f"'{topic}' 관점에서 문서를 다시 분석하면 어떤 새로운 인사이트를 얻을 수 있을까요?",
                            category="새로운관점",
                            priority=4,
                            context=f"키 토픽 활용: {topic}",
                            suggested_report_type=ReportType.CUSTOM,
                            confidence_score=0.8
                        )
                    )
            
            # 4. 피드백에서 제시된 개선 방향에 따른 질문
            if feedback_analysis.get('improvement_direction'):
                direction = feedback_analysis['improvement_direction']
                improved_questions.append(
                    QuestionCandidate(
                        question_id=str(uuid.uuid4()),
                        question=f"'{direction}' 방향으로 질문을 개선하면 어떤 구체적인 질문을 할 수 있을까요?",
                        category="개선방향",
                        priority=5,
                        context=f"피드백 기반 개선: {direction}",
                        suggested_report_type=ReportType.CUSTOM,
                        confidence_score=0.9
                    )
                )
            
            # 기본 질문이 없으면 폴백 질문 생성
            if not improved_questions:
                improved_questions = await self._generate_fallback_questions(document_analysis)
            
            logger.info(f"컨텍스트 인식 질문 생성 완료: {len(improved_questions)}개")
            return improved_questions
            
        except Exception as e:
            logger.error(f"컨텍스트 인식 질문 생성 실패: {str(e)}")
            # 오류 시 기본 질문으로 폴백
            return await self._generate_fallback_questions(document_analysis)
    
    def _analyze_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """피드백 텍스트를 분석하여 구조화된 정보를 추출합니다."""
        try:
            analysis = {
                'specific_areas': [],
                'improvement_direction': '',
                'satisfaction_level': 'neutral'
            }
            
            # 간단한 키워드 기반 분석 (실제로는 NLP 모델 사용)
            feedback_lower = feedback_text.lower()
            
            # 특정 영역 언급 감지
            area_keywords = ['데이터', '통계', '분석', '결론', '방법론', '시장', '경쟁', '재무']
            for keyword in area_keywords:
                if keyword in feedback_lower:
                    analysis['specific_areas'].append(keyword)
            
            # 개선 방향 감지
            if '더 자세히' in feedback_lower or '심화' in feedback_lower:
                analysis['improvement_direction'] = '심화 분석'
            elif '간단히' in feedback_lower or '요약' in feedback_lower:
                analysis['improvement_direction'] = '간소화'
            elif '새로운 관점' in feedback_lower or '다른 각도' in feedback_lower:
                analysis['improvement_direction'] = '새로운 관점'
            
            # 만족도 감지
            if any(word in feedback_lower for word in ['좋다', '만족', '훌륭']):
                analysis['satisfaction_level'] = 'positive'
            elif any(word in feedback_lower for word in ['부족', '아쉽', '개선']):
                analysis['satisfaction_level'] = 'negative'
            
            return analysis
            
        except Exception as e:
            logger.error(f"피드백 분석 실패: {str(e)}")
            return {'specific_areas': [], 'improvement_direction': '', 'satisfaction_level': 'neutral'}


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