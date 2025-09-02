"""
에이전트 테스트
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from doc_question_report_agent.agents import DocumentQuestionAgent, ReportAgent
from doc_question_report_agent.models import (
    DocumentAnalysis, QuestionSet, SelectedContext, ReportDraft, FinalReport,
    DocumentType, ReportType, ReportStatus
)


class TestDocumentQuestionAgent:
    """DocumentQuestionAgent 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 에이전트 인스턴스 생성"""
        return DocumentQuestionAgent()
    
    @pytest.fixture
    def sample_document_analysis(self):
        """샘플 문서 분석 결과"""
        return DocumentAnalysis(
            document_id="test_doc_123",
            filename="test.txt",
            document_type=DocumentType.TXT,
            content="이것은 테스트 문서입니다. 주요 내용은 테스트입니다.",
            summary="테스트 문서 요약",
            key_topics=["테스트", "문서"],
            entities=[],
            metadata={},
            confidence_score=0.9
        )
    
    def test_agent_initialization(self, agent):
        """에이전트 초기화 테스트"""
        assert agent.agent_id.startswith("doc_question_agent_")
        assert agent.document_processor is not None
    
    def test_document_type_detection(self, agent):
        """문서 타입 감지 테스트"""
        assert agent._detect_document_type("test.pdf") == DocumentType.PDF
        assert agent._detect_document_type("test.docx") == DocumentType.DOCX
        assert agent._detect_document_type("test.txt") == DocumentType.TXT
        assert agent._detect_document_type("test.html") == DocumentType.HTML
        assert agent._detect_document_type("test.md") == DocumentType.MARKDOWN
        assert agent._detect_document_type("test.csv") == DocumentType.CSV
        assert agent._detect_document_type("test.xlsx") == DocumentType.EXCEL
        assert agent._detect_document_type("test.unknown") == DocumentType.UNKNOWN
    
    def test_metadata_generation(self, agent):
        """메타데이터 생성 테스트"""
        metadata = agent._generate_metadata("test.txt", DocumentType.TXT, 100)
        
        assert metadata["original_filename"] == "test.txt"
        assert metadata["content_length"] == 100
        assert "processing_timestamp" in metadata
        assert metadata["agent_version"] == "1.0.0"
    
    def test_question_prioritization(self, agent):
        """질문 우선순위 정렬 테스트"""
        from doc_question_report_agent.models import QuestionCandidate
        
        questions = [
            QuestionCandidate(
                question_id="q1", question="질문1", category="일반", priority=3,
                context="컨텍스트1", suggested_report_type=ReportType.EXECUTIVE_SUMMARY,
                confidence_score=0.8
            ),
            QuestionCandidate(
                question_id="q2", question="질문2", category="데이터", priority=5,
                context="컨텍스트2", suggested_report_type=ReportType.TECHNICAL_ANALYSIS,
                confidence_score=0.9
            ),
            QuestionCandidate(
                question_id="q3", question="질문3", category="분석", priority=1,
                context="컨텍스트3", suggested_report_type=ReportType.MARKET_RESEARCH,
                confidence_score=0.7
            )
        ]
        
        sorted_questions = agent._prioritize_questions(questions)
        
        assert sorted_questions[0].priority == 5
        assert sorted_questions[1].priority == 3
        assert sorted_questions[2].priority == 1


class TestReportAgent:
    """ReportAgent 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 에이전트 인스턴스 생성"""
        return ReportAgent()
    
    @pytest.fixture
    def sample_context(self):
        """샘플 선택된 컨텍스트"""
        return SelectedContext(
            context_id="context_123",
            question_set_id="qset_123",
            selected_questions=["q1", "q2"],
            report_type=ReportType.EXECUTIVE_SUMMARY,
            scope="전체 문서 분석",
            criteria=["주요 내용", "핵심 포인트"]
        )
    
    @pytest.fixture
    def sample_document_analysis(self):
        """샘플 문서 분석 결과"""
        return DocumentAnalysis(
            document_id="test_doc_123",
            filename="test.txt",
            document_type=DocumentType.TXT,
            content="테스트 문서 내용",
            summary="테스트 요약",
            key_topics=["테스트"],
            entities=[],
            metadata={},
            confidence_score=0.9
        )
    
    def test_agent_initialization(self, agent):
        """에이전트 초기화 테스트"""
        assert agent.agent_id.startswith("report_agent_")
        assert agent.report_generator is not None
    
    @pytest.mark.asyncio
    async def test_outline_generation(self, agent, sample_context, sample_document_analysis):
        """아웃라인 생성 테스트"""
        outline = await agent._analyze_context_and_create_outline(
            sample_context, sample_document_analysis
        )
        
        assert isinstance(outline, list)
        assert len(outline) > 0
        assert all(isinstance(item, str) for item in outline)
    
    @pytest.mark.asyncio
    async def test_draft_content_generation(self, agent, sample_context, sample_document_analysis):
        """초안 내용 생성 테스트"""
        outline = ["1. 개요", "2. 분석", "3. 결론"]
        content = await agent._generate_draft_content(
            sample_context, sample_document_analysis, outline
        )
        
        assert isinstance(content, str)
        assert len(content) > 0
        assert sample_context.report_type.value in content
        assert sample_context.scope in content
    
    @pytest.mark.asyncio
    async def test_insight_extraction(self, agent):
        """인사이트 추출 테스트"""
        content = "테스트 내용입니다. 주요 발견사항과 권장사항이 포함되어 있습니다."
        
        key_findings, recommendations = await agent._extract_key_insights(content)
        
        assert isinstance(key_findings, list)
        assert isinstance(recommendations, list)
        assert len(key_findings) > 0
        assert len(recommendations) > 0


class TestIntegration:
    """통합 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_agent_interaction(self):
        """에이전트 간 상호작용 테스트"""
        doc_agent = DocumentQuestionAgent()
        report_agent = ReportAgent()
        
        # 문서 분석 시뮬레이션
        mock_document_analysis = DocumentAnalysis(
            document_id="test_doc",
            filename="test.txt",
            document_type=DocumentType.TXT,
            content="테스트 내용",
            summary="테스트 요약",
            key_topics=["테스트"],
            entities=[],
            metadata={},
            confidence_score=0.9
        )
        
        # 질문 생성
        question_set = await doc_agent.generate_question_candidates(mock_document_analysis)
        assert len(question_set.questions) > 0
        
        # 컨텍스트 생성
        context = SelectedContext(
            context_id="test_context",
            question_set_id=question_set.question_set_id,
            selected_questions=[question_set.questions[0].question_id],
            report_type=ReportType.EXECUTIVE_SUMMARY,
            scope="테스트 분석",
            criteria=["테스트"]
        )
        
        # 리포트 초안 생성
        draft = await report_agent.create_report_draft(context, mock_document_analysis)
        assert draft.draft_id is not None
        assert draft.title is not None


# 비동기 테스트를 위한 pytest 설정
pytest_plugins = ['pytest_asyncio']