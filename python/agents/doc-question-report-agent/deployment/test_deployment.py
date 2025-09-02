"""
배포 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from doc_question_report_agent import DocQuestionReportSystem
from doc_question_report_agent.models import DocumentType, ReportType


async def test_system_initialization():
    """시스템 초기화 테스트"""
    try:
        logger.info("시스템 초기화 테스트 시작...")
        
        system = DocQuestionReportSystem()
        status = await system.get_system_status()
        
        assert status["status"] == "running"
        assert "doc_question_agent" in status["agents"]
        assert "report_agent" in status["agents"]
        
        logger.info("✅ 시스템 초기화 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 테스트 실패: {e}")
        return False


async def test_document_processing():
    """문서 처리 테스트"""
    try:
        logger.info("문서 처리 테스트 시작...")
        
        system = DocQuestionReportSystem()
        
        # 테스트용 텍스트 파일 생성
        test_file_path = Path("test_document.txt")
        test_content = """
        이것은 테스트 문서입니다.
        
        주요 내용:
        1. 테스트 목적
        2. 테스트 방법
        3. 예상 결과
        
        결론: 테스트가 성공적으로 완료되어야 합니다.
        """
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # 문서 처리 테스트
        document_analysis, question_set = await system.process_document_upload(
            str(test_file_path), "test_document.txt"
        )
        
        # 결과 검증
        assert document_analysis.document_id
        assert document_analysis.filename == "test_document.txt"
        assert document_analysis.document_type == DocumentType.TXT
        assert len(document_analysis.content) > 0
        assert len(question_set.questions) > 0
        
        # 테스트 파일 정리
        test_file_path.unlink()
        
        logger.info("✅ 문서 처리 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 문서 처리 테스트 실패: {e}")
        return False


async def test_question_selection():
    """질문 선택 테스트"""
    try:
        logger.info("질문 선택 테스트 시작...")
        
        system = DocQuestionReportSystem()
        
        # 먼저 문서 처리
        test_file_path = Path("test_document.txt")
        test_content = "테스트 문서 내용입니다."
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        document_analysis, question_set = await system.process_document_upload(
            str(test_file_path), "test_document.txt"
        )
        
        # 질문 선택 및 컨텍스트 설정
        selected_question_ids = [question_set.questions[0].question_id]
        context = await system.select_questions_and_context(
            question_set.question_set_id,
            selected_question_ids,
            ReportType.EXECUTIVE_SUMMARY,
            "전체 문서 분석",
            ["주요 내용", "핵심 포인트"]
        )
        
        # 결과 검증
        assert context.context_id
        assert context.question_set_id == question_set.question_set_id
        assert len(context.selected_questions) == 1
        assert context.report_type == ReportType.EXECUTIVE_SUMMARY
        
        # 테스트 파일 정리
        test_file_path.unlink()
        
        logger.info("✅ 질문 선택 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 질문 선택 테스트 실패: {e}")
        return False


async def test_report_generation():
    """리포트 생성 테스트"""
    try:
        logger.info("리포트 생성 테스트 시작...")
        
        system = DocQuestionReportSystem()
        
        # 테스트 문서 생성 및 처리
        test_file_path = Path("test_document.txt")
        test_content = "리포트 생성 테스트를 위한 문서 내용입니다."
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        document_analysis, question_set = await system.process_document_upload(
            str(test_file_path), "test_document.txt"
        )
        
        # 컨텍스트 설정
        selected_question_ids = [question_set.questions[0].question_id]
        context = await system.select_questions_and_context(
            question_set.question_set_id,
            selected_question_ids,
            ReportType.EXECUTIVE_SUMMARY,
            "문서 요약",
            ["핵심 내용"]
        )
        
        # 리포트 초안 생성
        draft = await system.generate_report_draft(context)
        
        # 결과 검증
        assert draft.draft_id
        assert draft.title
        assert len(draft.content) > 0
        assert len(draft.outline) > 0
        
        # 최종 리포트 생성
        final_report = await system.generate_final_report(draft, context)
        
        # 결과 검증
        assert final_report.report_id
        assert final_report.title
        assert len(final_report.content) > 0
        assert final_report.executive_summary
        
        # 테스트 파일 정리
        test_file_path.unlink()
        
        logger.info("✅ 리포트 생성 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 리포트 생성 테스트 실패: {e}")
        return False


async def test_feedback_and_regeneration():
    """피드백 및 재생성 테스트"""
    try:
        logger.info("피드백 및 재생성 테스트 시작...")
        
        system = DocQuestionReportSystem()
        
        # 테스트 문서 생성 및 처리
        test_file_path = Path("test_document.txt")
        test_content = "피드백 테스트를 위한 문서 내용입니다."
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        document_analysis, question_set = await system.process_document_upload(
            str(test_file_path), "test_document.txt"
        )
        
        # 피드백 생성
        from doc_question_report_agent.models import FeedbackRequest
        feedback = FeedbackRequest(
            feedback_id="test_feedback",
            report_id="test_report",
            user_feedback="더 구체적인 분석이 필요합니다",
            satisfaction_score=3,
            improvement_areas=["데이터 분석", "시각화"],
            new_requirements="차트와 그래프 포함"
        )
        
        # 새로운 질문 세트 생성
        new_question_set = await system.process_feedback_and_regenerate(feedback)
        
        # 결과 검증
        assert new_question_set.question_set_id
        assert new_question_set.version > question_set.version
        assert len(new_question_set.questions) > 0
        
        # 테스트 파일 정리
        test_file_path.unlink()
        
        logger.info("✅ 피드백 및 재생성 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 피드백 및 재생성 테스트 실패: {e}")
        return False


async def run_all_tests():
    """모든 테스트를 실행합니다."""
    logger.info("=== DocQuestionReportAgent 배포 테스트 시작 ===")
    
    tests = [
        test_system_initialization,
        test_document_processing,
        test_question_selection,
        test_report_generation,
        test_feedback_and_regeneration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            logger.error(f"테스트 실행 중 오류 발생: {e}")
    
    logger.info(f"=== 테스트 결과: {passed}/{total} 통과 ===")
    
    if passed == total:
        logger.info("🎉 모든 테스트 통과! 배포 준비 완료")
        return True
    else:
        logger.warning(f"⚠️  {total - passed}개 테스트 실패")
        return False


def main():
    """메인 함수"""
    try:
        success = asyncio.run(run_all_tests())
        return success
    except Exception as e:
        logger.error(f"테스트 실행 중 치명적 오류: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)