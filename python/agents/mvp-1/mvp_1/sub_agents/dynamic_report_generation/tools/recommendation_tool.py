"""권장사항 생성 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import numpy as np
import pandas as pd


def _convert_numpy_types(obj):
    """NumPy 타입을 Python 기본 타입으로 변환합니다."""
    import numpy as np
    import pandas as pd
    
    def _deep_convert(item):
        try:
            # NumPy 타입 체크 (더 포괄적으로)
            if hasattr(item, 'dtype') and hasattr(item, 'item'):
                # NumPy 스칼라 타입
                return item.item()
            elif isinstance(item, (np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(item)
            elif isinstance(item, (np.float16, np.float32, np.float64)):
                return float(item)
            elif isinstance(item, np.bool_):
                return bool(item)
            elif isinstance(item, np.ndarray):
                return item.tolist()
            elif isinstance(item, pd.Series):
                return item.tolist()
            elif isinstance(item, pd.DataFrame):
                return item.to_dict()
            elif pd.isna(item):
                return None
            elif isinstance(item, dict):
                return {k: _deep_convert(v) for k, v in item.items()}
            elif isinstance(item, (list, tuple)):
                # 리스트와 튜플은 원래 타입을 유지
                return type(item)(_deep_convert(i) for i in item)
            elif hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
                # 다른 iterable 타입들도 처리
                return [_deep_convert(i) for i in item]
            else:
                return item
        except (ValueError, TypeError, OverflowError, AttributeError):
            # 변환 실패 시 원본 반환 (문자열로 변환하지 않음)
            return item
    
    return _deep_convert(obj)


class RecommendationInput(BaseModel):
    """권장사항 생성 입력"""
    business_insights: List[str] = Field(..., description="비즈니스 인사이트")
    actionable_insights: List[str] = Field(..., description="실행 가능한 인사이트")
    risk_insights: List[str] = Field(..., description="리스크 관련 인사이트")
    opportunity_insights: List[str] = Field(..., description="기회 관련 인사이트")
    domain_type: str = Field(..., description="도메인 유형")
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")


class RecommendationOutput(BaseModel):
    """권장사항 생성 출력"""
    immediate_actions: List[str] = Field(..., description="즉시 실행 가능한 액션")
    short_term_recommendations: List[str] = Field(..., description="단기 권장사항 (1-3개월)")
    long_term_recommendations: List[str] = Field(..., description="장기 권장사항 (3-12개월)")
    strategic_recommendations: List[str] = Field(..., description="전략적 권장사항")
    success: bool = Field(..., description="생성 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def generate_recommendations(
    business_insights: List[str],
    actionable_insights: List[str],
    risk_insights: List[str],
    opportunity_insights: List[str],
    domain_type: str,
    analysis_results: Dict[str, Any]
) -> RecommendationOutput:
    """
    인사이트를 바탕으로 실행 가능한 권장사항을 생성합니다.
    """
    try:
        # 우선순위별 권장사항 생성
        immediate_actions = _generate_immediate_actions(domain_type, risk_insights, analysis_results)
        short_term_recommendations = _generate_short_term_recommendations(domain_type, actionable_insights, analysis_results)
        long_term_recommendations = _generate_long_term_recommendations(domain_type, opportunity_insights, analysis_results)
        strategic_recommendations = _generate_strategic_recommendations(domain_type, business_insights, analysis_results)
        
        # 모든 리스트 타입을 보장
        converted_immediate = _convert_numpy_types(immediate_actions)
        if not isinstance(converted_immediate, list):
            converted_immediate = [str(converted_immediate)] if converted_immediate else []
        
        converted_short = _convert_numpy_types(short_term_recommendations)
        if not isinstance(converted_short, list):
            converted_short = [str(converted_short)] if converted_short else []
        
        converted_long = _convert_numpy_types(long_term_recommendations)
        if not isinstance(converted_long, list):
            converted_long = [str(converted_long)] if converted_long else []
        
        converted_strategic = _convert_numpy_types(strategic_recommendations)
        if not isinstance(converted_strategic, list):
            converted_strategic = [str(converted_strategic)] if converted_strategic else []
        
        return RecommendationOutput(
            immediate_actions=converted_immediate,
            short_term_recommendations=converted_short,
            long_term_recommendations=converted_long,
            strategic_recommendations=converted_strategic,
            success=True,
            message=f"권장사항 생성 완료: {domain_type} 도메인 권장사항 {len(immediate_actions + short_term_recommendations + long_term_recommendations + strategic_recommendations)}개 생성"
        )
        
    except Exception as e:
        return RecommendationOutput(
            immediate_actions=[],
            short_term_recommendations=[],
            long_term_recommendations=[],
            strategic_recommendations=[],
            success=False,
            message=f"권장사항 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _generate_immediate_actions(domain_type: str, risk_insights: List[str], analysis_results: Dict[str, Any]) -> List[str]:
    """즉시 실행 가능한 액션을 생성합니다."""
    immediate_actions = []
    
    if '매출' in domain_type or '영업' in domain_type:
        if any('감소세' in insight for insight in risk_insights):
            immediate_actions.append("매출 감소세를 보이는 제품군에 대한 긴급 프로모션 실행")
            immediate_actions.append("영업팀과의 긴급 미팅을 통한 대응 전략 수립")
        
        immediate_actions.append("주간 매출 모니터링 체계 강화")
        immediate_actions.append("고객 만족도 조사 실시")
    
    elif '고객' in domain_type:
        if any('이탈' in insight for insight in risk_insights):
            immediate_actions.append("이탈 위험 고객에 대한 즉시 개입 프로그램 실행")
            immediate_actions.append("고객 서비스 품질 점검 및 개선")
        
        immediate_actions.append("고객 피드백 수집 체계 강화")
        immediate_actions.append("고객 만족도 실시간 모니터링")
    
    elif '재고' in domain_type:
        if any('과다' in insight for insight in risk_insights):
            immediate_actions.append("재고 과다 제품에 대한 할인 프로모션 즉시 실행")
            immediate_actions.append("재고 회전율 개선을 위한 긴급 조치")
        
        immediate_actions.append("일일 재고 현황 모니터링 강화")
        immediate_actions.append("공급업체와의 긴급 협의")
    
    elif '마케팅' in domain_type:
        if any('ROI' in insight for insight in risk_insights):
            immediate_actions.append("저효율 마케팅 채널에 대한 즉시 예산 조정")
            immediate_actions.append("고효율 채널로의 예산 재배분")
        
        immediate_actions.append("마케팅 캠페인 성과 실시간 모니터링")
        immediate_actions.append("고객 반응 분석 및 대응")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        if any('이직률' in insight for insight in risk_insights):
            immediate_actions.append("핵심 인재 이탈 방지를 위한 긴급 대화")
            immediate_actions.append("직원 만족도 긴급 조사 실시")
        
        immediate_actions.append("직원 피드백 수집 체계 강화")
        immediate_actions.append("조직 건강도 모니터링")
    
    else:
        immediate_actions.append("데이터 품질 점검 및 개선")
        immediate_actions.append("주요 지표 모니터링 체계 강화")
    
    return immediate_actions


def _generate_short_term_recommendations(domain_type: str, actionable_insights: List[str], analysis_results: Dict[str, Any]) -> List[str]:
    """단기 권장사항을 생성합니다."""
    short_term_recs = []
    
    if '매출' in domain_type or '영업' in domain_type:
        short_term_recs.append("상위 성과 제품군에 대한 마케팅 투자 확대 (1-2개월 내)")
        short_term_recs.append("저성과 지역에 대한 특별 프로모션 기획 및 실행")
        short_term_recs.append("고객 세그먼트별 맞춤형 영업 전략 수립")
        short_term_recs.append("신규 고객 확보를 위한 리드 생성 프로그램 운영")
    
    elif '고객' in domain_type:
        short_term_recs.append("고객 세그먼트별 맞춤형 서비스 제공 체계 구축")
        short_term_recs.append("고객 생애가치 향상을 위한 프로그램 개발")
        short_term_recs.append("고객 추천 프로그램 설계 및 런칭")
        short_term_recs.append("고객 만족도 개선을 위한 서비스 프로세스 개선")
    
    elif '재고' in domain_type:
        short_term_recs.append("재고 회전율 개선을 위한 할인 프로모션 체계 구축")
        short_term_recs.append("수요 예측 모델 개발 및 적용")
        short_term_recs.append("공급망 효율성 개선을 위한 협력업체와의 협의")
        short_term_recs.append("재고 관리 시스템 고도화")
    
    elif '마케팅' in domain_type:
        short_term_recs.append("ROI 기반 마케팅 예산 배분 체계 구축")
        short_term_recs.append("효과적인 캠페인 요소의 다른 채널 확산")
        short_term_recs.append("디지털 마케팅 채널 확대")
        short_term_recs.append("고객 참여도 향상을 위한 콘텐츠 전략 수립")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        short_term_recs.append("직원 만족도 개선을 위한 조직 문화 프로그램 운영")
        short_term_recs.append("성과 우수 직원의 성공 요인 전파 프로그램")
        short_term_recs.append("직원 역량 개발을 위한 교육 프로그램 설계")
        short_term_recs.append("인사제도 개선을 위한 피드백 수집 및 분석")
    
    else:
        short_term_recs.append("데이터 기반 의사결정 프로세스 구축")
        short_term_recs.append("정기적인 데이터 모니터링 체계 구축")
        short_term_recs.append("프로세스 자동화를 통한 운영 효율성 개선")
        short_term_recs.append("성과 지표 기반 관리 체계 도입")
    
    return short_term_recs


def _generate_long_term_recommendations(domain_type: str, opportunity_insights: List[str], analysis_results: Dict[str, Any]) -> List[str]:
    """장기 권장사항을 생성합니다."""
    long_term_recs = []
    
    if '매출' in domain_type or '영업' in domain_type:
        long_term_recs.append("신규 제품 출시를 통한 매출 다각화 전략 수립")
        long_term_recs.append("온라인 채널 확대를 통한 시장 접근성 개선")
        long_term_recs.append("글로벌 시장 진출을 위한 전략 수립")
        long_term_recs.append("고객 생애가치 극대화를 위한 CRM 시스템 구축")
    
    elif '고객' in domain_type:
        long_term_recs.append("고객 생애가치 향상을 위한 장기 관계 관리 전략")
        long_term_recs.append("고객 추천 생태계 구축을 통한 성장 동력 확보")
        long_term_recs.append("개인화 서비스 플랫폼 구축")
        long_term_recs.append("고객 데이터 기반 예측 분석 시스템 도입")
    
    elif '재고' in domain_type:
        long_term_recs.append("공급망 최적화를 통한 비용 절감 전략")
        long_term_recs.append("수요 예측 정확도 향상을 위한 AI 시스템 도입")
        long_term_recs.append("지속가능한 재고 관리 체계 구축")
        long_term_recs.append("공급업체와의 전략적 파트너십 강화")
    
    elif '마케팅' in domain_type:
        long_term_recs.append("디지털 마케팅 생태계 구축")
        long_term_recs.append("개인화 마케팅을 위한 고객 데이터 플랫폼 구축")
        long_term_recs.append("브랜드 가치 향상을 위한 장기 마케팅 전략")
        long_term_recs.append("마케팅 자동화 시스템 고도화")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        long_term_recs.append("직원 역량 개발을 통한 조직 경쟁력 강화")
        long_term_recs.append("원격근무 확대를 통한 인재 확보 전략")
        long_term_recs.append("조직 문화 혁신을 통한 직원 참여도 향상")
        long_term_recs.append("성과 기반 인사제도 고도화")
    
    else:
        long_term_recs.append("데이터 기반 혁신을 통한 경쟁 우위 확보")
        long_term_recs.append("프로세스 자동화를 통한 운영 효율성 혁신")
        long_term_recs.append("디지털 전환을 통한 비즈니스 모델 혁신")
        long_term_recs.append("지속가능한 성장을 위한 전략적 계획 수립")
    
    return long_term_recs


def _generate_strategic_recommendations(domain_type: str, business_insights: List[str], analysis_results: Dict[str, Any]) -> List[str]:
    """전략적 권장사항을 생성합니다."""
    strategic_recs = []
    
    if '매출' in domain_type or '영업' in domain_type:
        strategic_recs.append("시장 점유율 확대를 위한 전략적 제휴 및 인수합병 검토")
        strategic_recs.append("신사업 영역 진출을 통한 매출 포트폴리오 다각화")
        strategic_recs.append("고객 중심의 비즈니스 모델 혁신")
        strategic_recs.append("글로벌 경쟁력을 위한 기술 혁신 투자")
    
    elif '고객' in domain_type:
        strategic_recs.append("고객 생태계 구축을 통한 플랫폼 비즈니스 전환")
        strategic_recs.append("고객 데이터 자산화를 통한 새로운 수익 모델 창출")
        strategic_recs.append("고객 경험 혁신을 통한 브랜드 가치 향상")
        strategic_recs.append("고객 중심의 조직 문화 및 운영 체계 구축")
    
    elif '재고' in domain_type:
        strategic_recs.append("공급망 디지털 전환을 통한 운영 혁신")
        strategic_recs.append("지속가능한 공급망 구축을 통한 ESG 경영")
        strategic_recs.append("공급망 위험 관리 체계 고도화")
        strategic_recs.append("공급업체와의 전략적 파트너십 강화")
    
    elif '마케팅' in domain_type:
        strategic_recs.append("마케팅 기술(MarTech) 생태계 구축")
        strategic_recs.append("브랜드 가치 향상을 위한 장기 마케팅 전략")
        strategic_recs.append("고객 데이터 기반 개인화 마케팅 플랫폼 구축")
        strategic_recs.append("마케팅 ROI 극대화를 위한 전략적 투자")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        strategic_recs.append("인재 중심의 조직 문화 및 운영 체계 구축")
        strategic_recs.append("직원 역량 개발을 통한 조직 경쟁력 강화")
        strategic_recs.append("다양성과 포용성을 통한 혁신 조직 구축")
        strategic_recs.append("미래 인재 확보를 위한 전략적 인사 계획")
    
    else:
        strategic_recs.append("데이터 기반 의사결정 문화 정착")
        strategic_recs.append("디지털 전환을 통한 비즈니스 모델 혁신")
        strategic_recs.append("지속가능한 성장을 위한 전략적 계획 수립")
        strategic_recs.append("혁신을 통한 경쟁 우위 확보")
    
    return strategic_recs


class RecommendationTool:
    def __init__(self):
        self.name = "generate_recommendations"
        self.description = "인사이트를 바탕으로 실행 가능한 권장사항을 생성합니다."
        self.input_model = RecommendationInput
        self.output_model = RecommendationOutput
        self.execute = generate_recommendations