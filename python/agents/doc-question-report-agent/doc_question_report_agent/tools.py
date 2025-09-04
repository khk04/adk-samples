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

"""MCP 도구들을 활용한 ADK 에이전트 도구 모음"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from google.adk.tools import Tool
from pydantic import BaseModel, Field

from .models import (
    DocumentAnalysis, QuestionCandidate, QuestionSet, SelectedContext,
    ReportRequest, ReportDraft, FinalReport, FeedbackRequest,
    DocumentType, ReportType, ReportStatus
)
from .utils import DocumentProcessor


class DocumentUploadInput(BaseModel):
    """문서 업로드 입력 모델"""
    file_path: str = Field(description="업로드된 파일의 경로")
    filename: str = Field(description="파일명")


class DocumentUploadOutput(BaseModel):
    """문서 업로드 출력 모델"""
    document_id: str = Field(description="문서 ID")
    analysis: DocumentAnalysis = Field(description="문서 분석 결과")


class QuestionGenerationInput(BaseModel):
    """질문 생성 입력 모델"""
    document_id: str = Field(description="문서 ID")
    step: int = Field(default=1, description="질문 단계")


class QuestionGenerationOutput(BaseModel):
    """질문 생성 출력 모델"""
    question_set: QuestionSet = Field(description="생성된 질문 세트")


class ReportGenerationInput(BaseModel):
    """보고서 생성 입력 모델"""
    title: str = Field(description="보고서 제목")
    report_type: ReportType = Field(description="보고서 유형")
    document_analysis: DocumentAnalysis = Field(description="문서 분석 결과")
    selected_context: SelectedContext = Field(description="선택된 컨텍스트")


class ReportGenerationOutput(BaseModel):
    """보고서 생성 출력 모델"""
    draft: ReportDraft = Field(description="보고서 초안")


# 전역 변수로 문서 캐시 관리
document_cache: Dict[str, DocumentAnalysis] = {}
question_cache: Dict[str, QuestionSet] = {}
report_cache: Dict[str, ReportDraft] = {}


@Tool
def analyze_document(file_path: str, filename: str) -> DocumentUploadOutput:
    """
    문서를 분석하고 텍스트를 추출합니다.
    
    Args:
        file_path: 업로드된 파일의 경로
        filename: 파일명
        
    Returns:
        DocumentUploadOutput: 문서 분석 결과
    """
    try:
        # 문서 타입 감지
        ext = filename.lower().split('.')[-1]
        type_mapping = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'doc': DocumentType.DOCX,
            'txt': DocumentType.TXT,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'md': DocumentType.MARKDOWN,
            'csv': DocumentType.CSV,
            'xlsx': DocumentType.EXCEL,
            'xls': DocumentType.EXCEL
        }
        doc_type = type_mapping.get(ext, DocumentType.UNKNOWN)
        
        # 문서 처리
        processor = DocumentProcessor()
        content = processor.process_document(file_path)
        
        # 문서 분석 생성
        analysis = DocumentAnalysis(
            document_id=str(uuid.uuid4()),
            filename=filename,
            document_type=doc_type,
            content=content,
            summary=f"{filename} 문서 분석 완료",
            key_topics=["문서분석", "내용추출"],
            entities=[],
            metadata={
                "filename": filename,
                "document_type": doc_type.value,
                "content_length": len(content),
                "processing_time": datetime.now().isoformat()
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 캐시에 저장
        document_cache[analysis.document_id] = analysis
        
        return DocumentUploadOutput(
            document_id=analysis.document_id,
            analysis=analysis
        )
        
    except Exception as e:
        raise Exception(f"문서 분석 실패: {str(e)}")


@Tool
def generate_questions(document_id: str, step: int = 1) -> QuestionGenerationOutput:
    """
    문서를 바탕으로 질문 후보들을 생성합니다.
    
    Args:
        document_id: 문서 ID
        step: 질문 단계 (기본값: 1)
        
    Returns:
        QuestionGenerationOutput: 생성된 질문 세트
    """
    try:
        # 문서 조회
        document = document_cache.get(document_id)
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 질문 후보 생성 (Mock 데이터)
        candidates = []
        for i in range(3):
            candidate = QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question_text=f"문서의 {i+1}번째 주요 내용은 무엇인가요?",
                category="general",
                priority=i + 1,
                context_required=True,
                estimated_complexity="medium",
                related_topics=["문서분석", "내용이해"],
                created_at=datetime.now()
            )
            candidates.append(candidate)
        
        # 질문 세트 생성
        question_set = QuestionSet(
            set_id=str(uuid.uuid4()),
            document_id=document_id,
            step=step,
            questions=candidates,
            total_questions=len(candidates),
            generated_at=datetime.now(),
            context_summary=f"Step {step} 질문 생성"
        )
        
        # 캐시에 저장
        question_cache[question_set.set_id] = question_set
        
        return QuestionGenerationOutput(question_set=question_set)
        
    except Exception as e:
        raise Exception(f"질문 생성 실패: {str(e)}")


@Tool
def regenerate_questions(document_id: str, selected_questions: List[str], next_step: int) -> QuestionGenerationOutput:
    """
    선택된 질문들을 바탕으로 다음 단계 질문들을 재생성합니다.
    
    Args:
        document_id: 문서 ID
        selected_questions: 선택된 질문 목록
        next_step: 다음 단계 번호
        
    Returns:
        QuestionGenerationOutput: 재생성된 질문 세트
    """
    try:
        # 문서 조회
        document = document_cache.get(document_id)
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 후속 질문 생성 (Mock 데이터)
        candidates = []
        for i, selected_q in enumerate(selected_questions[:2]):
            candidate = QuestionCandidate(
                question_id=str(uuid.uuid4()),
                question_text=f"'{selected_q}'에 대한 구체적인 예시는 무엇인가요?",
                category="follow_up",
                priority=i + 1,
                context_required=True,
                estimated_complexity="high",
                related_topics=["심화분석", "구체화"],
                created_at=datetime.now()
            )
            candidates.append(candidate)
        
        # 질문 세트 생성
        question_set = QuestionSet(
            set_id=str(uuid.uuid4()),
            document_id=document_id,
            step=next_step,
            questions=candidates,
            total_questions=len(candidates),
            generated_at=datetime.now(),
            context_summary=f"Step {next_step} - 이전 선택: {', '.join(selected_questions[:2])}"
        )
        
        # 캐시에 저장
        question_cache[question_set.set_id] = question_set
        
        return QuestionGenerationOutput(question_set=question_set)
        
    except Exception as e:
        raise Exception(f"질문 재생성 실패: {str(e)}")


@Tool
def generate_report_draft(title: str, report_type: str, document_id: str, selected_questions: List[str]) -> ReportGenerationOutput:
    """
    선택된 컨텍스트를 바탕으로 보고서 초안을 생성합니다.
    
    Args:
        title: 보고서 제목
        report_type: 보고서 유형
        document_id: 문서 ID
        selected_questions: 선택된 질문 목록
        
    Returns:
        ReportGenerationOutput: 생성된 보고서 초안
    """
    try:
        # 문서 조회
        document = document_cache.get(document_id)
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 선택된 컨텍스트 생성
        selected_context = SelectedContext(
            context_id=str(uuid.uuid4()),
            document_id=document_id,
            context_items=selected_questions,
            summary=f"선택된 질문들: {', '.join(selected_questions)}",
            relevance_score=0.9,
            created_at=datetime.now()
        )
        
        # 보고서 요청 생성
        report_request = ReportRequest(
            title=title,
            report_type=ReportType(report_type),
            document_analysis=document,
            selected_context=selected_context,
            created_at=datetime.now()
        )
        
        # 보고서 초안 생성
        draft = ReportDraft(
            draft_id=str(uuid.uuid4()),
            title=title,
            report_type=ReportType(report_type),
            outline=[
                "1. 문서 개요",
                "2. 주요 내용 분석", 
                "3. 핵심 발견사항",
                "4. 결론 및 권장사항"
            ],
            content=f"""
# {title}

## 문서 개요
이 보고서는 {document.filename} 문서를 분석한 결과를 바탕으로 작성되었습니다.

## 주요 내용 분석
{', '.join(selected_questions)}

## 핵심 발견사항
- 문서에서 중요한 정보가 발견되었습니다
- 분석 결과 의미있는 패턴이 확인되었습니다

## 결론 및 권장사항
- 추가적인 데이터 수집을 권장합니다
- 정기적인 모니터링이 필요합니다
            """,
            key_findings=[
                "문서에서 중요한 정보가 발견되었습니다",
                "분석 결과 의미있는 패턴이 확인되었습니다"
            ],
            recommendations=[
                "추가적인 데이터 수집을 권장합니다",
                "정기적인 모니터링이 필요합니다"
            ],
            status=ReportStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                "agent_id": "report_agent",
                "context_count": len(selected_questions),
                "document_id": document_id
            }
        )
        
        # 캐시에 저장
        report_cache[draft.draft_id] = draft
        
        return ReportGenerationOutput(draft=draft)
        
    except Exception as e:
        raise Exception(f"보고서 초안 생성 실패: {str(e)}")


@Tool
def finalize_report(draft_id: str, feedback: Optional[str] = None) -> FinalReport:
    """
    피드백을 바탕으로 최종 보고서를 완성합니다.
    
    Args:
        draft_id: 초안 ID
        feedback: 피드백 내용 (선택사항)
        
    Returns:
        FinalReport: 최종 보고서
    """
    try:
        # 초안 조회
        draft = report_cache.get(draft_id)
        if not draft:
            raise ValueError(f"초안을 찾을 수 없습니다: {draft_id}")
        
        # 피드백 반영
        final_content = draft.content
        if feedback:
            final_content += f"\n\n[피드백 반영]\n{feedback}"
        
        # 최종 보고서 생성
        final_report = FinalReport(
            report_id=str(uuid.uuid4()),
            draft_id=draft_id,
            title=draft.title,
            report_type=draft.report_type,
            content=final_content,
            key_findings=draft.key_findings,
            recommendations=draft.recommendations,
            status=ReportStatus.FINAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                "agent_id": "report_agent",
                "feedback_applied": feedback is not None,
                "version": "1.0"
            }
        )
        
        return final_report
        
    except Exception as e:
        raise Exception(f"최종 보고서 생성 실패: {str(e)}")


@Tool
def get_document_status(document_id: str) -> Dict[str, Any]:
    """
    문서 처리 상태를 조회합니다.
    
    Args:
        document_id: 문서 ID
        
    Returns:
        Dict[str, Any]: 문서 상태 정보
    """
    document = document_cache.get(document_id)
    if not document:
        return {"status": "not_found", "message": f"문서를 찾을 수 없습니다: {document_id}"}
    
    return {
        "status": "found",
        "document_id": document_id,
        "filename": document.filename,
        "document_type": document.document_type.value,
        "content_length": len(document.content),
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat()
    }


@Tool
def list_available_documents() -> List[Dict[str, Any]]:
    """
    사용 가능한 문서 목록을 조회합니다.
    
    Returns:
        List[Dict[str, Any]]: 문서 목록
    """
    documents = []
    for doc_id, document in document_cache.items():
        documents.append({
            "document_id": doc_id,
            "filename": document.filename,
            "document_type": document.document_type.value,
            "content_length": len(document.content),
            "created_at": document.created_at.isoformat()
        })
    
    return documents


@Tool
def export_report_to_pdf(report_id: str, output_path: str) -> Dict[str, Any]:
    """
    보고서를 PDF 형식으로 내보냅니다.
    
    Args:
        report_id: 보고서 ID
        output_path: 출력 파일 경로
        
    Returns:
        Dict[str, Any]: 내보내기 결과
    """
    try:
        # 실제 구현에서는 reportlab 등을 사용하여 PDF 생성
        # 여기서는 Mock 구현
        return {
            "success": True,
            "message": f"보고서가 PDF로 내보내졌습니다: {output_path}",
            "file_path": output_path,
            "file_size": "1.2MB"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"PDF 내보내기 실패: {str(e)}"
        }