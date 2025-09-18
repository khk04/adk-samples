"""인사이트 생성 도구"""

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
                return type(item)(_deep_convert(i) for i in item)
            elif hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
                # 다른 iterable 타입들도 처리
                return [_deep_convert(i) for i in item]
            else:
                return item
        except (ValueError, TypeError, OverflowError, AttributeError):
            # 모든 변환 실패 시 문자열로 변환
            try:
                return str(item)
            except:
                return None
    
    return _deep_convert(obj)


class InsightGenerationInput(BaseModel):
    """인사이트 생성 입력"""
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")
    domain_type: str = Field(..., description="도메인 유형")
    key_findings: List[str] = Field(..., description="주요 발견사항")
    trends: Dict[str, Any] = Field(..., description="트렌드 분석 결과")
    patterns: Dict[str, Any] = Field(..., description="패턴 분석 결과")


class InsightGenerationOutput(BaseModel):
    """인사이트 생성 출력"""
    business_insights: List[str] = Field(..., description="비즈니스 인사이트")
    actionable_insights: List[str] = Field(..., description="실행 가능한 인사이트")
    risk_insights: List[str] = Field(..., description="리스크 관련 인사이트")
    opportunity_insights: List[str] = Field(..., description="기회 관련 인사이트")
    success: bool = Field(..., description="생성 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def generate_business_insights(
    analysis_results: Dict[str, Any],
    domain_type: str,
    key_findings: List[str],
    trends: Dict[str, Any],
    patterns: Dict[str, Any]
) -> InsightGenerationOutput:
    """
    분석 결과를 바탕으로 비즈니스 인사이트를 생성합니다.
    """
    try:
        # 도메인별 인사이트 생성
        business_insights = _generate_domain_insights(domain_type, analysis_results, key_findings)
        actionable_insights = _generate_actionable_insights(domain_type, analysis_results, trends)
        risk_insights = _generate_risk_insights(domain_type, analysis_results, patterns)
        opportunity_insights = _generate_opportunity_insights(domain_type, analysis_results, trends)
        
        return InsightGenerationOutput(
            business_insights=_convert_numpy_types(business_insights),
            actionable_insights=_convert_numpy_types(actionable_insights),
            risk_insights=_convert_numpy_types(risk_insights),
            opportunity_insights=_convert_numpy_types(opportunity_insights),
            success=True,
            message=f"인사이트 생성 완료: {domain_type} 도메인 인사이트 {len(business_insights)}개 생성"
        )
        
    except Exception as e:
        return InsightGenerationOutput(
            business_insights=[],
            actionable_insights=[],
            risk_insights=[],
            opportunity_insights=[],
            success=False,
            message=f"인사이트 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _generate_domain_insights(domain_type: str, analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """도메인별 비즈니스 인사이트를 생성합니다."""
    insights = []
    
    if '매출' in domain_type or '영업' in domain_type:
        insights.extend(_generate_sales_insights(analysis_results, key_findings))
    elif '고객' in domain_type:
        insights.extend(_generate_customer_insights(analysis_results, key_findings))
    elif '재고' in domain_type:
        insights.extend(_generate_inventory_insights(analysis_results, key_findings))
    elif '마케팅' in domain_type:
        insights.extend(_generate_marketing_insights(analysis_results, key_findings))
    elif 'HR' in domain_type or '인사' in domain_type:
        insights.extend(_generate_hr_insights(analysis_results, key_findings))
    else:
        insights.extend(_generate_general_insights(analysis_results, key_findings))
    
    return insights


def _generate_sales_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """매출 관련 인사이트를 생성합니다."""
    insights = []
    
    if 'sales_analysis' in analysis_results:
        sales_data = analysis_results['sales_analysis']
        
        if 'total_sales' in sales_data:
            insights.append(f"총 매출액 {sales_data['total_sales']:,.0f}원으로 비즈니스 규모를 파악할 수 있습니다.")
        
        if 'sales_growth' in sales_data:
            for col, growth in sales_data['sales_growth'].items():
                if growth > 10:
                    insights.append(f"{col}에서 강한 성장세({growth:.1f}%)를 보여 시장 기회가 확대되고 있습니다.")
                elif growth < -10:
                    insights.append(f"{col}에서 감소세({growth:.1f}%)를 보여 개선이 필요한 영역입니다.")
    
    if 'product_analysis' in analysis_results:
        insights.append("제품별 성과 분석을 통해 수익성 높은 제품군을 식별할 수 있습니다.")
    
    if 'regional_analysis' in analysis_results:
        insights.append("지역별 매출 분석을 통해 지역별 시장 특성을 파악할 수 있습니다.")
    
    return insights


def _generate_customer_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """고객 관련 인사이트를 생성합니다."""
    insights = []
    
    if 'customer_segmentation' in analysis_results:
        insights.append("고객 세분화 분석을 통해 맞춤형 마케팅 전략을 수립할 수 있습니다.")
    
    if 'behavior_analysis' in analysis_results:
        insights.append("고객 행동 패턴 분석을 통해 서비스 개선 포인트를 발견할 수 있습니다.")
    
    return insights


def _generate_inventory_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """재고 관련 인사이트를 생성합니다."""
    insights = []
    insights.append("재고 회전율 분석을 통해 효율적인 재고 관리 방안을 도출할 수 있습니다.")
    insights.append("수요 예측 분석을 통해 적정 재고 수준을 설정할 수 있습니다.")
    return insights


def _generate_marketing_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """마케팅 관련 인사이트를 생성합니다."""
    insights = []
    insights.append("캠페인 성과 분석을 통해 ROI가 높은 마케팅 채널을 식별할 수 있습니다.")
    insights.append("고객 획득 비용 분석을 통해 효율적인 마케팅 예산 배분이 가능합니다.")
    return insights


def _generate_hr_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """HR 관련 인사이트를 생성합니다."""
    insights = []
    insights.append("직원 만족도 분석을 통해 조직 건강도를 파악할 수 있습니다.")
    insights.append("성과 평가 분석을 통해 인사제도 개선 방향을 제시할 수 있습니다.")
    return insights


def _generate_general_insights(analysis_results: Dict[str, Any], key_findings: List[str]) -> List[str]:
    """일반적인 인사이트를 생성합니다."""
    insights = []
    
    if 'basic_statistics' in analysis_results:
        insights.append("기본 통계 분석을 통해 데이터의 전반적인 특성을 파악했습니다.")
    
    if 'categorical_analysis' in analysis_results:
        insights.append("범주형 데이터 분석을 통해 주요 분포 패턴을 발견했습니다.")
    
    return insights


def _generate_actionable_insights(domain_type: str, analysis_results: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
    """실행 가능한 인사이트를 생성합니다."""
    actionable_insights = []
    
    if '매출' in domain_type or '영업' in domain_type:
        actionable_insights.append("상위 성과 제품군에 대한 마케팅 투자를 확대하여 매출 증대를 도모할 수 있습니다.")
        actionable_insights.append("저성과 지역에 대한 특별 프로모션을 통해 시장 점유율을 확대할 수 있습니다.")
    
    elif '고객' in domain_type:
        actionable_insights.append("고객 세그먼트별 맞춤형 서비스를 제공하여 고객 만족도를 향상시킬 수 있습니다.")
        actionable_insights.append("이탈 위험 고객에 대한 사전 개입 프로그램을 운영할 수 있습니다.")
    
    elif '재고' in domain_type:
        actionable_insights.append("재고 회전율이 낮은 제품에 대한 할인 프로모션을 실시할 수 있습니다.")
        actionable_insights.append("수요 예측 모델을 활용하여 적정 재고 수준을 설정할 수 있습니다.")
    
    elif '마케팅' in domain_type:
        actionable_insights.append("ROI가 높은 마케팅 채널에 예산을 집중 투자할 수 있습니다.")
        actionable_insights.append("효과적인 캠페인 요소를 다른 채널에 확산 적용할 수 있습니다.")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        actionable_insights.append("직원 만족도가 낮은 부서에 대한 개선 프로그램을 운영할 수 있습니다.")
        actionable_insights.append("성과 우수 직원의 성공 요인을 다른 직원들에게 전파할 수 있습니다.")
    
    else:
        actionable_insights.append("데이터 기반 의사결정을 통해 운영 효율성을 개선할 수 있습니다.")
        actionable_insights.append("정기적인 데이터 모니터링 체계를 구축할 수 있습니다.")
    
    return actionable_insights


def _generate_risk_insights(domain_type: str, analysis_results: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
    """리스크 관련 인사이트를 생성합니다."""
    risk_insights = []
    
    if '매출' in domain_type or '영업' in domain_type:
        if 'sales_analysis' in analysis_results and 'sales_growth' in analysis_results['sales_analysis']:
            for col, growth in analysis_results['sales_analysis']['sales_growth'].items():
                if growth < -5:
                    risk_insights.append(f"{col}에서 지속적인 감소세로 인한 매출 위험이 있습니다.")
        
        risk_insights.append("특정 제품군에 대한 의존도가 높을 경우 매출 변동 위험이 있습니다.")
    
    elif '고객' in domain_type:
        risk_insights.append("고객 이탈률이 높은 세그먼트에 대한 리텐션 전략이 필요합니다.")
        risk_insights.append("고객 만족도 하락 시 브랜드 이미지 손상 위험이 있습니다.")
    
    elif '재고' in domain_type:
        risk_insights.append("재고 과다 보유 시 자금 회전율 저하 위험이 있습니다.")
        risk_insights.append("재고 부족 시 고객 서비스 수준 하락 위험이 있습니다.")
    
    elif '마케팅' in domain_type:
        risk_insights.append("마케팅 ROI 하락 시 비용 효율성 저하 위험이 있습니다.")
        risk_insights.append("특정 채널 의존도가 높을 경우 마케팅 리스크가 증가합니다.")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        risk_insights.append("직원 이직률 증가 시 조직 역량 손실 위험이 있습니다.")
        risk_insights.append("성과 격차 확대 시 조직 내 갈등 위험이 있습니다.")
    
    else:
        risk_insights.append("데이터 품질 저하 시 의사결정 오류 위험이 있습니다.")
        risk_insights.append("시장 변화에 대한 대응 지연 시 경쟁력 저하 위험이 있습니다.")
    
    return risk_insights


def _generate_opportunity_insights(domain_type: str, analysis_results: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
    """기회 관련 인사이트를 생성합니다."""
    opportunity_insights = []
    
    if '매출' in domain_type or '영업' in domain_type:
        if 'sales_analysis' in analysis_results and 'sales_growth' in analysis_results['sales_analysis']:
            for col, growth in analysis_results['sales_analysis']['sales_growth'].items():
                if growth > 5:
                    opportunity_insights.append(f"{col}에서 성장세를 활용하여 시장 확대 기회가 있습니다.")
        
        opportunity_insights.append("신규 제품 출시를 통한 매출 다각화 기회가 있습니다.")
        opportunity_insights.append("온라인 채널 확대를 통한 시장 접근성 개선 기회가 있습니다.")
    
    elif '고객' in domain_type:
        opportunity_insights.append("고객 생애가치 향상을 통한 수익성 개선 기회가 있습니다.")
        opportunity_insights.append("고객 추천 프로그램을 통한 신규 고객 확보 기회가 있습니다.")
    
    elif '재고' in domain_type:
        opportunity_insights.append("공급망 최적화를 통한 비용 절감 기회가 있습니다.")
        opportunity_insights.append("수요 예측 정확도 향상을 통한 재고 효율성 개선 기회가 있습니다.")
    
    elif '마케팅' in domain_type:
        opportunity_insights.append("디지털 마케팅 확대를 통한 고객 접점 증가 기회가 있습니다.")
        opportunity_insights.append("개인화 마케팅을 통한 고객 참여도 향상 기회가 있습니다.")
    
    elif 'HR' in domain_type or '인사' in domain_type:
        opportunity_insights.append("직원 역량 개발을 통한 조직 경쟁력 강화 기회가 있습니다.")
        opportunity_insights.append("원격근무 확대를 통한 인재 확보 기회가 있습니다.")
    
    else:
        opportunity_insights.append("데이터 기반 혁신을 통한 경쟁 우위 확보 기회가 있습니다.")
        opportunity_insights.append("프로세스 자동화를 통한 운영 효율성 개선 기회가 있습니다.")
    
    return opportunity_insights


class InsightGeneratorTool:
    def __init__(self):
        self.name = "generate_business_insights"
        self.description = "분석 결과를 바탕으로 비즈니스 인사이트를 생성합니다."
        self.input_model = InsightGenerationInput
        self.output_model = InsightGenerationOutput
        self.execute = generate_business_insights