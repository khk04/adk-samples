"""
메인 시스템 클래스
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

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
        
        logger.info(f"DocQuestionReportSystem 초기화 완료: {self.system_id}")
    
    async def process_document(self, document_path: str) -> DocumentAnalysis:
        """문서를 처리하고 분석 결과를 반환"""
        try:
            logger.info(f"문서 처리 시작: {document_path}")
            
            # DocumentQuestionAgent를 사용하여 문서 분석
            analysis = await self.doc_question_agent.analyze_document(document_path)
            
            # 캐시에 저장
            self.document_cache[analysis.document_id] = analysis
            
            logger.info(f"문서 처리 완료: {analysis.document_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"문서 처리 실패: {str(e)}")
            raise
    
    async def generate_questions(self, document_id: str) -> QuestionSet:
        """문서에 대한 질문 세트를 생성"""
        try:
            logger.info(f"질문 생성 시작: {document_id}")
            
            if document_id not in self.document_cache:
                raise ValueError(f"문서 ID {document_id}를 찾을 수 없습니다")
            
            document = self.document_cache[document_id]
            questions = await self.doc_question_agent.generate_questions(document)
            
            logger.info(f"질문 생성 완료: {len(questions.questions)}개")
            return questions
            
        except Exception as e:
            logger.error(f"질문 생성 실패: {str(e)}")
            raise
    
    async def generate_report(self, request: ReportRequest) -> ReportDraft:
        """선택된 질문을 기반으로 리포트 초안 생성"""
        try:
            logger.info(f"리포트 생성 시작: {request.request_id}")
            
            # ReportAgent를 사용하여 리포트 생성
            draft = await self.report_agent.generate_draft(request)
            
            logger.info(f"리포트 초안 생성 완료: {draft.draft_id}")
            return draft
            
        except Exception as e:
            logger.error(f"리포트 생성 실패: {str(e)}")
            raise
    
    async def finalize_report(self, draft_id: str, feedback: str = "") -> FinalReport:
        """리포트 초안을 최종본으로 완성"""
        try:
            logger.info(f"리포트 최종화 시작: {draft_id}")
            
            # ReportAgent를 사용하여 최종 리포트 생성
            final_report = await self.report_agent.finalize_report(draft_id, feedback)
            
            logger.info(f"리포트 최종화 완료: {final_report.report_id}")
            return final_report
            
        except Exception as e:
            logger.error(f"리포트 최종화 실패: {str(e)}")
            raise
    
    async def regenerate_questions(self, document_id: str, feedback: str) -> QuestionSet:
        """피드백을 기반으로 새로운 질문 세트 생성"""
        try:
            logger.info(f"질문 재생성 시작: {document_id}")
            
            if document_id not in self.document_cache:
                raise ValueError(f"문서 ID {document_id}를 찾을 수 없습니다")
            
            document = self.document_cache[document_id]
            new_questions = await self.doc_question_agent.regenerate_questions(
                document, feedback
            )
            
            logger.info(f"질문 재생성 완료: {len(new_questions.questions)}개")
            return new_questions
            
        except Exception as e:
            logger.error(f"질문 재생성 실패: {str(e)}")
            raise
    
    def get_system_status(self) -> Dict:
        """시스템 상태 정보 반환"""
        return {
            "system_id": self.system_id,
            "status": "running",
            "active_tasks": len(self.active_tasks),
            "cached_documents": len(self.document_cache),
            "timestamp": datetime.now().isoformat()
        }


# FastAPI 앱 생성
app = FastAPI(
    title="Document Question & Report Agent",
    description="2-Agent 시스템으로 문서 처리와 질문 응답, 보고서 생성을 수행하는 AI 에이전트",
    version="0.1.0"
)

# 시스템 인스턴스 생성
system = DocQuestionReportSystem()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Document Question & Report Agent API", "status": "running"}


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def get_status():
    """시스템 상태 조회"""
    return system.get_system_status()


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """문서 업로드 및 분석"""
    try:
        # 임시 파일로 저장
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 문서 처리
        analysis = await system.process_document(tmp_file_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        
        return {
            "message": "문서 업로드 및 분석 완료",
            "document_id": analysis.document_id,
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{document_id}")
async def get_questions(document_id: str):
    """문서에 대한 질문 세트 생성"""
    try:
        questions = await system.generate_questions(document_id)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report")
async def create_report(request: ReportRequest):
    """리포트 생성"""
    try:
        draft = await system.generate_report(request)
        return draft
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report/{draft_id}/finalize")
async def finalize_report(draft_id: str, feedback: str = ""):
    """리포트 최종화"""
    try:
        final_report = await system.finalize_report(draft_id, feedback)
        return final_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/questions/{document_id}/regenerate")
async def regenerate_questions(document_id: str, feedback: str):
    """질문 재생성"""
    try:
        new_questions = await system.regenerate_questions(document_id, feedback)
        return new_questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def main():
    """메인 함수"""
    logger.info("DocQuestionReportSystem 시작 중...")
    
    # 시스템 초기화
    logger.info("시스템 초기화 완료")
    
    return system


if __name__ == "__main__":
    # FastAPI 서버 실행
    logger.info("FastAPI 서버 시작 중...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )