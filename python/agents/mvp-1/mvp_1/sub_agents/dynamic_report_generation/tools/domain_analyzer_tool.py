"""데이터 도메인 분석 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import numpy as np
import re


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


class DomainAnalysisInput(BaseModel):
    """도메인 분석 입력"""
    data_file_path: str = Field(..., description="분석할 데이터 파일 경로")
    data_schema: Dict[str, str] = Field(..., description="데이터 스키마 정보")
    data_summary: Dict[str, Any] = Field(..., description="데이터 요약 통계")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="사용자 응답 정보")


class DomainAnalysisOutput(BaseModel):
    """도메인 분석 출력"""
    domain_type: str = Field(..., description="식별된 비즈니스 도메인")
    domain_confidence: float = Field(..., description="도메인 식별 신뢰도 (0-1)")
    data_characteristics: Dict[str, Any] = Field(..., description="데이터 특성 분석 결과")
    analysis_strategy: Dict[str, Any] = Field(..., description="분석 전략")
    key_metrics: List[str] = Field(..., description="핵심 지표 목록")
    success: bool = Field(..., description="분석 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def analyze_data_domain(
    data_file_path: str,
    data_schema: Dict[str, str],
    data_summary: Dict[str, Any],
    user_responses: Dict[str, Any] = {}
) -> DomainAnalysisOutput:
    """
    데이터의 비즈니스 도메인과 특성을 분석하여 맞춤형 분석 전략을 수립합니다.
    """
    try:
        # 데이터 로드
        df = _load_data(data_file_path)
        if df is None:
            return DomainAnalysisOutput(
                domain_type="Unknown",
                domain_confidence=0.0,
                data_characteristics={},
                analysis_strategy={},
                key_metrics=[],
                success=False,
                message=f"데이터 파일({data_file_path})을 로드할 수 없습니다."
            )
        
        # 도메인 식별
        domain_result = _identify_domain(df, user_responses)
        
        # 데이터 특성 분석
        characteristics = _analyze_data_characteristics(df)
        
        # 분석 전략 수립
        strategy = _create_analysis_strategy(domain_result, characteristics, user_responses)
        
        # 핵심 지표 식별
        key_metrics = _identify_key_metrics(df, domain_result['domain'])
        
        # 모든 결과를 numpy 타입에서 변환
        converted_characteristics = _convert_numpy_types(characteristics)
        converted_strategy = _convert_numpy_types(strategy)
        converted_metrics = _convert_numpy_types(key_metrics)
        
        return DomainAnalysisOutput(
            domain_type=domain_result['domain'],
            domain_confidence=float(domain_result['confidence']),
            data_characteristics=converted_characteristics,
            analysis_strategy=converted_strategy,
            key_metrics=converted_metrics,
            success=True,
            message=f"도메인 분석 완료: {domain_result['domain']} (신뢰도: {domain_result['confidence']:.2f})"
        )
        
    except Exception as e:
        return DomainAnalysisOutput(
            domain_type="Unknown",
            domain_confidence=0.0,
            data_characteristics={},
            analysis_strategy={},
            key_metrics=[],
            success=False,
            message=f"도메인 분석 중 오류가 발생했습니다: {str(e)}"
        )


def _load_data(file_path: str) -> Optional[pd.DataFrame]:
    """데이터 파일을 로드합니다."""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            return None
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return None


def _identify_domain(df: pd.DataFrame, user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """데이터의 비즈니스 도메인을 식별합니다."""
    
    # 컬럼명 기반 도메인 식별
    column_scores = _score_columns_by_domain(df.columns)
    
    # 사용자 응답 기반 도메인 힌트
    user_hints = _extract_domain_hints(user_responses)
    
    # 도메인별 점수 계산
    domain_scores = {
        'sales': 0.0,
        'customer': 0.0,
        'inventory': 0.0,
        'marketing': 0.0,
        'hr': 0.0,
        'finance': 0.0,
        'operations': 0.0
    }
    
    # 컬럼명 기반 점수
    for domain, score in column_scores.items():
        domain_scores[domain] += score * 0.7
    
    # 사용자 힌트 기반 점수
    for domain, score in user_hints.items():
        domain_scores[domain] += score * 0.3
    
    # 최고 점수 도메인 선택
    best_domain = max(domain_scores, key=domain_scores.get)
    confidence = domain_scores[best_domain]
    
    # 도메인명 한국어 변환
    domain_names = {
        'sales': '매출/영업',
        'customer': '고객',
        'inventory': '재고/물류',
        'marketing': '마케팅',
        'hr': 'HR/인사',
        'finance': '재무',
        'operations': '운영'
    }
    
    return {
        'domain': domain_names.get(best_domain, '일반'),
        'confidence': min(confidence, 1.0),
        'scores': domain_scores
    }


def _score_columns_by_domain(columns: List[str]) -> Dict[str, float]:
    """컬럼명을 기반으로 도메인별 점수를 계산합니다."""
    
    domain_keywords = {
        'sales': [
            '매출', 'sales', 'revenue', 'income', '수익', '판매', 'sell', 'order', '주문',
            'amount', '금액', 'price', '가격', 'cost', '비용', 'profit', '이익'
        ],
        'customer': [
            '고객', 'customer', 'client', 'user', '사용자', 'member', '회원', 'name', '이름',
            'email', 'phone', '전화', 'address', '주소', 'age', '나이', 'gender', '성별'
        ],
        'inventory': [
            '재고', 'inventory', 'stock', 'product', '제품', 'item', '상품', 'quantity', '수량',
            'warehouse', '창고', 'supply', '공급', 'demand', '수요'
        ],
        'marketing': [
            '마케팅', 'marketing', 'campaign', '캠페인', 'ad', '광고', 'promotion', '프로모션',
            'channel', '채널', 'conversion', '전환', 'click', '클릭', 'impression', '노출'
        ],
        'hr': [
            '직원', 'employee', 'staff', '인사', 'hr', 'human', '부서', 'department', 'position',
            '직책', 'salary', '급여', 'performance', '성과', 'training', '교육'
        ],
        'finance': [
            '재무', 'finance', 'accounting', '회계', 'budget', '예산', 'expense', '비용',
            'asset', '자산', 'liability', '부채', 'equity', '자본'
        ],
        'operations': [
            '운영', 'operation', 'process', '프로세스', 'workflow', '업무', 'task', '작업',
            'efficiency', '효율', 'productivity', '생산성', 'quality', '품질'
        ]
    }
    
    scores = {domain: 0.0 for domain in domain_keywords.keys()}
    
    for col in columns:
        col_lower = col.lower()
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in col_lower:
                    scores[domain] += 1.0
    
    # 정규화 (컬럼 수로 나누기)
    total_columns = len(columns)
    if total_columns > 0:
        for domain in scores:
            scores[domain] = scores[domain] / total_columns
    
    return scores


def _extract_domain_hints(user_responses: Dict[str, Any]) -> Dict[str, float]:
    """사용자 응답에서 도메인 힌트를 추출합니다."""
    
    hints = {domain: 0.0 for domain in ['sales', 'customer', 'inventory', 'marketing', 'hr', 'finance', 'operations']}
    
    # 리포트 유형에서 힌트 추출
    report_type = user_responses.get('report_type', '').lower()
    analysis_criteria = user_responses.get('analysis_criteria', '').lower()
    
    # 매출 관련 키워드
    if any(keyword in report_type or keyword in analysis_criteria 
           for keyword in ['매출', 'sales', 'revenue', '판매', '영업', '수익']):
        hints['sales'] += 0.8
    
    # 고객 관련 키워드
    if any(keyword in report_type or keyword in analysis_criteria 
           for keyword in ['고객', 'customer', 'client', '회원', '사용자']):
        hints['customer'] += 0.8
    
    # 재고 관련 키워드
    if any(keyword in report_type or keyword in analysis_criteria 
           for keyword in ['재고', 'inventory', 'stock', '제품', '물류']):
        hints['inventory'] += 0.8
    
    # 마케팅 관련 키워드
    if any(keyword in report_type or keyword in analysis_criteria 
           for keyword in ['마케팅', 'marketing', '캠페인', '광고', '프로모션']):
        hints['marketing'] += 0.8
    
    # HR 관련 키워드
    if any(keyword in report_type or keyword in analysis_criteria 
           for keyword in ['직원', 'employee', '인사', 'hr', '성과', '교육']):
        hints['hr'] += 0.8
    
    return hints


def _analyze_data_characteristics(df: pd.DataFrame) -> Dict[str, Any]:
    """데이터의 특성을 분석합니다."""
    
    characteristics = {
        'data_types': {
            'numeric': len(df.select_dtypes(include=[np.number]).columns),
            'categorical': len(df.select_dtypes(include=['object', 'category']).columns),
            'datetime': len(df.select_dtypes(include=['datetime64']).columns)
        },
        'temporal_data': _has_temporal_data(df),
        'hierarchical_data': _has_hierarchical_data(df),
        'transactional_data': _is_transactional_data(df),
        'survey_data': _is_survey_data(df),
        'performance_data': _is_performance_data(df)
    }
    
    return characteristics


def _has_temporal_data(df: pd.DataFrame) -> bool:
    """시계열 데이터가 있는지 확인합니다."""
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        return True
    
    # 날짜 관련 컬럼명 확인
    date_keywords = ['date', 'time', '날짜', '시간', 'created', 'updated', 'timestamp']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in date_keywords):
            return True
    
    return False


def _has_hierarchical_data(df: pd.DataFrame) -> bool:
    """계층적 데이터가 있는지 확인합니다."""
    hierarchical_keywords = ['category', 'subcategory', '부서', '팀', 'level', 'tier', '계층']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in hierarchical_keywords):
            return True
    return False


def _is_transactional_data(df: pd.DataFrame) -> bool:
    """거래 데이터인지 확인합니다."""
    transaction_keywords = ['order', 'transaction', '주문', '거래', 'purchase', '구매', 'payment', '결제']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in transaction_keywords):
            return True
    return False


def _is_survey_data(df: pd.DataFrame) -> bool:
    """설문 데이터인지 확인합니다."""
    survey_keywords = ['survey', 'question', 'answer', '설문', '질문', '응답', 'rating', '평점', 'satisfaction', '만족도']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in survey_keywords):
            return True
    return False


def _is_performance_data(df: pd.DataFrame) -> bool:
    """성과 데이터인지 확인합니다."""
    performance_keywords = ['performance', 'kpi', 'metric', '성과', '지표', 'score', '점수', 'result', '결과']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in performance_keywords):
            return True
    return False


def _create_analysis_strategy(domain_result: Dict[str, Any], characteristics: Dict[str, Any], user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """분석 전략을 수립합니다."""
    
    domain = domain_result['domain']
    strategy = {
        'primary_analysis': [],
        'secondary_analysis': [],
        'visualization_types': [],
        'key_focus_areas': []
    }
    
    # 도메인별 분석 전략
    if '매출' in domain or '영업' in domain:
        strategy['primary_analysis'] = ['매출 트렌드 분석', '제품별 성과 분석', '지역별 매출 분석']
        strategy['secondary_analysis'] = ['계절성 분석', '고객 세그먼트별 매출', '목표 대비 실적']
        strategy['visualization_types'] = ['시계열 차트', '막대 차트', '파이 차트']
        strategy['key_focus_areas'] = ['매출 증대', '수익성 개선', '고객 확대']
    
    elif '고객' in domain:
        strategy['primary_analysis'] = ['고객 세분화', '생애주기 분석', '행동 패턴 분석']
        strategy['secondary_analysis'] = ['충성도 분석', '이탈 예측', '만족도 분석']
        strategy['visualization_types'] = ['산점도', '히트맵', '트리맵']
        strategy['key_focus_areas'] = ['고객 유지', '만족도 향상', '신규 고객 확보']
    
    elif '재고' in domain or '물류' in domain:
        strategy['primary_analysis'] = ['재고 회전율 분석', 'ABC 분석', '수요 예측']
        strategy['secondary_analysis'] = ['공급망 효율성', '배송 성과', '안전재고 최적화']
        strategy['visualization_types'] = ['라인 차트', '히스토그램', '박스 플롯']
        strategy['key_focus_areas'] = ['재고 최적화', '비용 절감', '서비스 수준 향상']
    
    elif '마케팅' in domain:
        strategy['primary_analysis'] = ['캠페인 성과 분석', '채널별 ROI', '고객 획득 비용']
        strategy['secondary_analysis'] = ['브랜드 인지도', '디지털 마케팅 성과', '소셜미디어 분석']
        strategy['visualization_types'] = ['퍼널 차트', '트리맵', '워드 클라우드']
        strategy['key_focus_areas'] = ['마케팅 ROI', '브랜드 강화', '고객 참여도']
    
    elif 'HR' in domain or '인사' in domain:
        strategy['primary_analysis'] = ['직원 만족도 분석', '성과 평가', '이직률 분석']
        strategy['secondary_analysis'] = ['채용 효율성', '교육 효과', '조직 건강도']
        strategy['visualization_types'] = ['레이더 차트', '박스 플롯', '히트맵']
        strategy['key_focus_areas'] = ['직원 만족도', '성과 향상', '조직 효율성']
    
    else:
        # 일반적인 분석 전략
        strategy['primary_analysis'] = ['기본 통계 분석', '트렌드 분석', '분포 분석']
        strategy['secondary_analysis'] = ['상관관계 분석', '이상치 탐지', '패턴 분석']
        strategy['visualization_types'] = ['막대 차트', '라인 차트', '히스토그램']
        strategy['key_focus_areas'] = ['데이터 이해', '패턴 발견', '개선 기회']
    
    return strategy


def _identify_key_metrics(df: pd.DataFrame, domain: str) -> List[str]:
    """핵심 지표를 식별합니다."""
    
    key_metrics = []
    
    # 수치형 컬럼에서 핵심 지표 식별
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        col_lower = col.lower()
        
        # 도메인별 핵심 지표 키워드
        if '매출' in domain or '영업' in domain:
            if any(keyword in col_lower for keyword in ['매출', 'sales', 'revenue', '수익', 'profit']):
                key_metrics.append(col)
        elif '고객' in domain:
            if any(keyword in col_lower for keyword in ['고객', 'customer', 'client', 'member', '회원']):
                key_metrics.append(col)
        elif '재고' in domain:
            if any(keyword in col_lower for keyword in ['재고', 'inventory', 'stock', 'quantity', '수량']):
                key_metrics.append(col)
        elif '마케팅' in domain:
            if any(keyword in col_lower for keyword in ['marketing', 'campaign', '캠페인', 'conversion', '전환']):
                key_metrics.append(col)
        elif 'HR' in domain or '인사' in domain:
            if any(keyword in col_lower for keyword in ['employee', '직원', 'performance', '성과', 'satisfaction', '만족도']):
                key_metrics.append(col)
    
    # 상위 5개 지표만 반환
    return key_metrics[:5]


class DomainAnalyzerTool:
    def __init__(self):
        self.name = "analyze_data_domain"
        self.description = "데이터의 비즈니스 도메인과 특성을 분석하여 맞춤형 분석 전략을 수립합니다."
        self.input_model = DomainAnalysisInput
        self.output_model = DomainAnalysisOutput
        self.execute = analyze_data_domain