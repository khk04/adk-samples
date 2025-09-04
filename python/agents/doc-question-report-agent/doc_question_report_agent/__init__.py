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

"""
Google ADK 기반 Document Question & Report Agent

2-Agent 시스템으로 문서 처리와 질문 응답, 보고서 생성을 수행하는 AI 에이전트입니다.
Google Agent Development Kit (ADK)를 활용하여 구현되었습니다.
"""

__version__ = "0.1.0"
__author__ = "Google LLC"
__email__ = "support@google.com"

# ADK 에이전트들
from .agents import (
    root_agent,
    main_agent,
    document_question_agent,
    report_agent
)

# 시스템 클래스
from .main import DocQuestionReportSystem, system

# 데이터 모델들
from .models import (
    DocumentAnalysis, QuestionCandidate, QuestionSet, SelectedContext,
    ReportRequest, ReportDraft, FinalReport, FeedbackRequest,
    DocumentType, ReportType, ReportStatus
)

# 유틸리티 클래스들
from .utils import DocumentProcessor, ReportGenerator

# 도구들
from .tools import (
    analyze_document,
    generate_questions,
    regenerate_questions,
    generate_report_draft,
    finalize_report,
    get_document_status,
    list_available_documents,
    export_report_to_pdf
)

__all__ = [
    # ADK 에이전트들
    "root_agent",
    "main_agent", 
    "document_question_agent",
    "report_agent",
    
    # 시스템 클래스
    "DocQuestionReportSystem",
    "system",
    
    # 데이터 모델들
    "DocumentAnalysis",
    "QuestionCandidate",
    "QuestionSet",
    "SelectedContext",
    "ReportRequest",
    "ReportDraft",
    "FinalReport",
    "FeedbackRequest",
    "DocumentType",
    "ReportType",
    "ReportStatus",
    
    # 유틸리티 클래스들
    "DocumentProcessor",
    "ReportGenerator",
    
    # 도구들
    "analyze_document",
    "generate_questions",
    "regenerate_questions",
    "generate_report_draft",
    "finalize_report",
    "get_document_status",
    "list_available_documents",
    "export_report_to_pdf",
]