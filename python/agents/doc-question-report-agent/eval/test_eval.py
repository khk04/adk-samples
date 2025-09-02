"""
평가 테스트 스크립트
"""

import asyncio
import json
import sys
from pathlib import Path
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from doc_question_report_agent import DocQuestionReportSystem
from doc_question_report_agent.models import ReportType


class DocQuestionReportEvaluator:
    """DocQuestionReport 시스템 평가 클래스"""
    
    def __init__(self):
        self.system = DocQuestionReportSystem()
        self.test_results = []
    
    async def evaluate_document_processing(self) -> dict:
        """문서 처리 성능 평가"""
        logger.info("문서 처리 성능 평가 시작...")
        
        test_cases = [
            {
                "name": "간단한 텍스트 문서",
                "content": "이것은 간단한 테스트 문서입니다. 주요 내용은 테스트입니다.",
                "expected_topics": ["테스트", "문서"]
            },
            {
                "name": "복잡한 구조 문서",
                "content": """
                제목: 복잡한 구조 문서
                
                섹션 1: 소개
                이 문서는 복잡한 구조를 가지고 있습니다.
                
                섹션 2: 주요 내용
                - 항목 1: 첫 번째 항목
                - 항목 2: 두 번째 항목
                - 항목 3: 세 번째 항목
                
                섹션 3: 결론
                복잡한 구조의 문서 분석이 완료되었습니다.
                """,
                "expected_topics": ["구조", "문서", "분석"]
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                # 테스트 파일 생성
                test_file = Path(f"test_{test_case['name'].replace(' ', '_')}.txt")
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_case['content'])
                
                # 문서 처리 실행
                start_time = asyncio.get_event_loop().time()
                document_analysis, question_set = await self.system.process_document_upload(
                    str(test_file), test_file.name
                )
                processing_time = asyncio.get_event_loop().time() - start_time
                
                # 결과 평가
                success = True
                score = 0
                feedback = []
                
                # 텍스트 추출 성공 여부
                if document_analysis.content and len(document_analysis.content) > 0:
                    score += 30
                else:
                    success = False
                    feedback.append("텍스트 추출 실패")
                
                # 요약 생성 성공 여부
                if document_analysis.summary and len(document_analysis.summary) > 0:
                    score += 20
                else:
                    feedback.append("요약 생성 실패")
                
                # 질문 생성 성공 여부
                if question_set.questions and len(question_set.questions) > 0:
                    score += 30
                else:
                    success = False
                    feedback.append("질문 생성 실패")
                
                # 처리 시간 평가
                if processing_time < 5.0:  # 5초 이내
                    score += 20
                else:
                    feedback.append(f"처리 시간이 너무 김: {processing_time:.2f}초")
                
                results.append({
                    "test_case": test_case["name"],
                    "success": success,
                    "score": score,
                    "processing_time": processing_time,
                    "feedback": feedback,
                    "document_id": document_analysis.document_id,
                    "questions_count": len(question_set.questions)
                })
                
                # 테스트 파일 정리
                test_file.unlink()
                
            except Exception as e:
                results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "score": 0,
                    "processing_time": 0,
                    "feedback": [f"오류 발생: {str(e)}"],
                    "document_id": None,
                    "questions_count": 0
                })
        
        # 전체 결과 계산
        total_score = sum(r["score"] for r in results)
        max_score = len(results) * 100
        overall_score = (total_score / max_score) * 100 if max_score > 0 else 0
        
        evaluation_result = {
            "test_type": "document_processing",
            "overall_score": overall_score,
            "total_score": total_score,
            "max_score": max_score,
            "test_count": len(results),
            "success_count": sum(1 for r in results if r["success"]),
            "results": results
        }
        
        logger.info(f"문서 처리 평가 완료: 전체 점수 {overall_score:.1f}%")
        return evaluation_result
    
    async def evaluate_question_generation(self) -> dict:
        """질문 생성 품질 평가"""
        logger.info("질문 생성 품질 평가 시작...")
        
        # 먼저 테스트 문서로 질문 생성
        test_content = """
        인공지능(AI)은 컴퓨터 시스템이 인간의 지능을 모방하여 학습하고, 
        추론하고, 문제를 해결할 수 있도록 하는 기술입니다. 
        머신러닝, 딥러닝, 자연어 처리 등 다양한 하위 분야를 포함합니다.
        """
        
        test_file = Path("test_ai_document.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        try:
            document_analysis, question_set = await self.system.process_document_upload(
                str(test_file), test_file.name
            )
            
            # 질문 품질 평가
            quality_scores = []
            feedback = []
            
            for question in question_set.questions:
                question_score = 0
                question_feedback = []
                
                # 질문 길이 평가
                if 10 <= len(question.question) <= 100:
                    question_score += 20
                else:
                    question_feedback.append("질문 길이가 부적절함")
                
                # 카테고리 분류 평가
                if question.category and question.category != "":
                    question_score += 20
                else:
                    question_feedback.append("카테고리 분류 누락")
                
                # 우선순위 평가
                if 1 <= question.priority <= 5:
                    question_score += 20
                else:
                    question_feedback.append("우선순위 범위 오류")
                
                # 컨텍스트 평가
                if question.context and len(question.context) > 0:
                    question_score += 20
                else:
                    question_feedback.append("컨텍스트 누락")
                
                # 신뢰도 평가
                if 0.0 <= question.confidence_score <= 1.0:
                    question_score += 20
                else:
                    question_feedback.append("신뢰도 범위 오류")
                
                quality_scores.append(question_score)
                if question_feedback:
                    feedback.extend(question_feedback)
            
            # 전체 질문 품질 점수
            avg_question_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            overall_score = (avg_question_score / 100) * 100
            
            evaluation_result = {
                "test_type": "question_generation",
                "overall_score": overall_score,
                "questions_count": len(question_set.questions),
                "average_question_score": avg_question_score,
                "quality_distribution": {
                    "excellent": sum(1 for s in quality_scores if s >= 90),
                    "good": sum(1 for s in quality_scores if 70 <= s < 90),
                    "fair": sum(1 for s in quality_scores if 50 <= s < 70),
                    "poor": sum(1 for s in quality_scores if s < 50)
                },
                "feedback": list(set(feedback))  # 중복 제거
            }
            
            # 테스트 파일 정리
            test_file.unlink()
            
            logger.info(f"질문 생성 품질 평가 완료: 전체 점수 {overall_score:.1f}%")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"질문 생성 품질 평가 실패: {str(e)}")
            return {
                "test_type": "question_generation",
                "overall_score": 0,
                "error": str(e)
            }
    
    async def evaluate_report_generation(self) -> dict:
        """리포트 생성 품질 평가"""
        logger.info("리포트 생성 품질 평가 시작...")
        
        # 테스트 문서 생성
        test_content = """
        시장 분석 보고서
        
        시장 현황:
        - 전체 시장 규모: 100억 달러
        - 연평균 성장률: 15%
        - 주요 플레이어: A사, B사, C사
        
        시장 트렌드:
        1. 디지털 전환 가속화
        2. AI 기술 도입 증가
        3. 지속가능성 강화
        
        전망:
        향후 5년간 연평균 20% 성장 예상
        """
        
        test_file = Path("test_market_report.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        try:
            # 문서 처리 및 질문 생성
            document_analysis, question_set = await self.system.process_document_upload(
                str(test_file), test_file.name
            )
            
            # 컨텍스트 설정
            selected_questions = [question_set.questions[0].question_id]
            context = await self.system.select_questions_and_context(
                question_set.question_set_id,
                selected_questions,
                ReportType.MARKET_RESEARCH,
                "시장 분석 및 전망",
                ["시장 규모", "성장률", "트렌드"]
            )
            
            # 리포트 초안 생성
            start_time = asyncio.get_event_loop().time()
            draft = await self.system.generate_report_draft(context)
            draft_time = asyncio.get_event_loop().time() - start_time
            
            # 최종 리포트 생성
            start_time = asyncio.get_event_loop().time()
            final_report = await self.system.generate_final_report(draft, context)
            final_time = asyncio.get_event_loop().time() - start_time
            
            # 품질 평가
            quality_score = 0
            feedback = []
            
            # 초안 품질
            if draft.title and len(draft.title) > 0:
                quality_score += 15
            else:
                feedback.append("초안 제목 누락")
            
            if draft.content and len(draft.content) > 100:
                quality_score += 20
            else:
                feedback.append("초안 내용 부족")
            
            if draft.outline and len(draft.outline) > 0:
                quality_score += 15
            else:
                feedback.append("초안 아웃라인 누락")
            
            # 최종 리포트 품질
            if final_report.executive_summary and len(final_report.executive_summary) > 50:
                quality_score += 20
            else:
                feedback.append("집행 요약 부족")
            
            if final_report.methodology and len(final_report.methodology) > 30:
                quality_score += 15
            else:
                feedback.append("방법론 설명 부족")
            
            if final_report.conclusions and len(final_report.conclusions) > 0:
                quality_score += 15
            else:
                feedback.append("결론 누락")
            
            # 성능 평가
            if draft_time < 10.0:  # 10초 이내
                quality_score += 10
            else:
                feedback.append(f"초안 생성 시간이 너무 김: {draft_time:.2f}초")
            
            if final_time < 15.0:  # 15초 이내
                quality_score += 10
            else:
                feedback.append(f"최종 리포트 생성 시간이 너무 김: {final_time:.2f}초")
            
            overall_score = quality_score
            
            evaluation_result = {
                "test_type": "report_generation",
                "overall_score": overall_score,
                "quality_score": quality_score,
                "performance": {
                    "draft_generation_time": draft_time,
                    "final_report_generation_time": final_time
                },
                "feedback": feedback,
                "draft_id": draft.draft_id,
                "final_report_id": final_report.report_id
            }
            
            # 테스트 파일 정리
            test_file.unlink()
            
            logger.info(f"리포트 생성 품질 평가 완료: 전체 점수 {overall_score:.1f}%")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"리포트 생성 품질 평가 실패: {str(e)}")
            return {
                "test_type": "report_generation",
                "overall_score": 0,
                "error": str(e)
            }
    
    async def run_comprehensive_evaluation(self) -> dict:
        """종합 평가 실행"""
        logger.info("=== DocQuestionReport 시스템 종합 평가 시작 ===")
        
        evaluation_results = []
        
        # 1. 문서 처리 성능 평가
        doc_eval = await self.evaluate_document_processing()
        evaluation_results.append(doc_eval)
        
        # 2. 질문 생성 품질 평가
        question_eval = await self.evaluate_question_generation()
        evaluation_results.append(question_eval)
        
        # 3. 리포트 생성 품질 평가
        report_eval = await self.evaluate_report_generation()
        evaluation_results.append(report_eval)
        
        # 종합 점수 계산
        valid_scores = [eval_result.get("overall_score", 0) for eval_result in evaluation_results 
                       if "overall_score" in eval_result and eval_result["overall_score"] > 0]
        
        if valid_scores:
            comprehensive_score = sum(valid_scores) / len(valid_scores)
        else:
            comprehensive_score = 0
        
        comprehensive_result = {
            "evaluation_type": "comprehensive",
            "comprehensive_score": comprehensive_score,
            "evaluation_date": asyncio.get_event_loop().time(),
            "system_version": "1.0.0",
            "evaluation_results": evaluation_results,
            "summary": {
                "total_tests": len(evaluation_results),
                "successful_tests": len([r for r in evaluation_results if r.get("overall_score", 0) > 0]),
                "average_score": comprehensive_score
            }
        }
        
        # 결과 저장
        output_file = Path("evaluation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"=== 종합 평가 완료: 전체 점수 {comprehensive_score:.1f}% ===")
        logger.info(f"평가 결과가 {output_file}에 저장되었습니다.")
        
        return comprehensive_result


async def main():
    """메인 평가 함수"""
    try:
        evaluator = DocQuestionReportEvaluator()
        results = await evaluator.run_comprehensive_evaluation()
        
        # 결과 요약 출력
        print("\n" + "="*50)
        print("평가 결과 요약")
        print("="*50)
        print(f"종합 점수: {results['comprehensive_score']:.1f}%")
        print(f"총 테스트 수: {results['summary']['total_tests']}")
        print(f"성공한 테스트 수: {results['summary']['successful_tests']}")
        print(f"평균 점수: {results['summary']['average_score']:.1f}%")
        print("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"평가 실행 실패: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)