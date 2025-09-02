"""
데이터 모델 정의
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """문서 타입 열거형"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    CSV = "csv"
    EXCEL = "xlsx"
    UNKNOWN = "unknown"


class ReportType(str, Enum):
    """리포트 유형 열거형"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_ANALYSIS = "technical_analysis"
    MARKET_RESEARCH = "market_research"
    FINANCIAL_REPORT = "financial_report"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    RECOMMENDATION = "recommendation"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """리포트 상태 열거형"""
    DRAFT = "draft"
    FINAL = "final"
    REVIEW = "review"
    APPROVED = "approved"


class DocumentAnalysis(BaseModel):
    """문서 분석 결과 모델"""
    document_id: str = Field(..., description="문서 고유 식별자")
    filename: str = Field(..., description="원본 파일명")
    document_type: DocumentType = Field(..., description="문서 타입")
    content: str = Field(..., description="추출된 텍스트 내용")
    summary: str = Field(..., description="문서 요약")
    key_topics: List[str] = Field(default_factory=list, description="주요 토픽")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="추출된 엔티티")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="분석 시간")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuestionCandidate(BaseModel):
    """질문 후보 모델"""
    question_id: str = Field(..., description="질문 고유 식별자")
    question: str = Field(..., description="질문 내용")
    category: str = Field(..., description="질문 카테고리")
    priority: int = Field(..., ge=1, le=5, description="우선순위 (1-5)")
    context: str = Field(..., description="질문의 컨텍스트")
    suggested_report_type: ReportType = Field(..., description="제안하는 리포트 유형")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="질문 품질 신뢰도")


class QuestionSet(BaseModel):
    """질문 세트 모델"""
    question_set_id: str = Field(..., description="질문 세트 고유 식별자")
    document_id: str = Field(..., description="연관된 문서 ID")
    questions: List[QuestionCandidate] = Field(..., description="질문 후보 리스트")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    version: int = Field(default=1, description="질문 세트 버전")


class SelectedContext(BaseModel):
    """사용자가 선택한 컨텍스트 모델"""
    context_id: str = Field(..., description="컨텍스트 고유 식별자")
    question_set_id: str = Field(..., description="선택된 질문 세트 ID")
    selected_questions: List[str] = Field(..., description="선택된 질문 ID 리스트")
    report_type: ReportType = Field(..., description="요청한 리포트 유형")
    custom_requirements: Optional[str] = Field(None, description="추가 요구사항")
    scope: str = Field(..., description="리포트 범위")
    criteria: List[str] = Field(default_factory=list, description="분석 기준")
    selected_at: datetime = Field(default_factory=datetime.now, description="선택 시간")


class ReportRequest(BaseModel):
    """리포트 생성 요청 모델"""
    request_id: str = Field(..., description="요청 고유 식별자")
    context: SelectedContext = Field(..., description="선택된 컨텍스트")
    report_type: ReportType = Field(..., description="리포트 유형")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="리포트 상태")
    include_charts: bool = Field(default=True, description="차트 포함 여부")
    include_summary: bool = Field(default=True, description="요약 포함 여부")
    custom_styling: Optional[Dict[str, Any]] = Field(None, description="커스텀 스타일링")
    output_options: Optional[Dict[str, Any]] = Field(None, description="추가 출력 옵션")


class ReportDraft(BaseModel):
    """리포트 초안 모델"""
    draft_id: str = Field(..., description="초안 고유 식별자")
    request_id: str = Field(..., description="연관된 요청 ID")
    title: str = Field(..., description="리포트 제목")
    outline: List[str] = Field(..., description="리포트 아웃라인")
    content: str = Field(..., description="초안 내용")
    key_findings: List[str] = Field(default_factory=list, description="주요 발견사항")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")
    data_sources: List[str] = Field(default_factory=list, description="데이터 소스")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="상태")


class FinalReport(BaseModel):
    """최종 리포트 모델"""
    report_id: str = Field(..., description="리포트 고유 식별자")
    draft_id: str = Field(..., description="연관된 초안 ID")
    title: str = Field(..., description="리포트 제목")
    content: str = Field(..., description="최종 내용")
    executive_summary: str = Field(..., description="집행 요약")
    methodology: str = Field(..., description="방법론")
    findings: List[Dict[str, Any]] = Field(..., description="주요 발견사항")
    conclusions: List[str] = Field(default_factory=list, description="결론")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")
    appendices: List[Dict[str, Any]] = Field(default_factory=list, description="부록")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    status: ReportStatus = Field(default=ReportStatus.FINAL, description="상태")


class FeedbackRequest(BaseModel):
    """피드백 요청 모델"""
    feedback_id: str = Field(..., description="피드백 고유 식별자")
    report_id: str = Field(..., description="연관된 리포트 ID")
    user_feedback: str = Field(..., description="사용자 피드백")
    satisfaction_score: int = Field(..., ge=1, le=5, description="만족도 점수 (1-5)")
    improvement_areas: List[str] = Field(default_factory=list, description="개선 영역")
    new_requirements: Optional[str] = Field(None, description="새로운 요구사항")
    submitted_at: datetime = Field(default_factory=datetime.now, description="제출 시간")


class ProcessingStatus(str, Enum):
    """처리 상태 열거형"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingTask(BaseModel):
    """처리 작업 모델"""
    task_id: str = Field(..., description="작업 고유 식별자")
    task_type: str = Field(..., description="작업 타입")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="처리 상태")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="진행률 (%)")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    result: Optional[Dict[str, Any]] = Field(None, description="처리 결과")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }