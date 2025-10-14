"""
세션 데이터 모델

세션에서 사용되는 데이터 구조를 정의합니다.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class SessionAnalysisResult(BaseModel):
    """세션 분석 결과 모델"""
    analysis_type: str = Field(..., description="분석 유형")
    result: Dict[str, Any] = Field(..., description="분석 결과")
    timestamp: datetime = Field(default_factory=datetime.now, description="분석 시간")
    file_path: str = Field(..., description="분석된 파일 경로")
    success: bool = Field(True, description="분석 성공 여부")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class SessionData(BaseModel):
    """세션 데이터 모델"""
    session_id: str = Field(..., description="세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="세션 생성 시간")
    last_accessed: datetime = Field(default_factory=datetime.now, description="마지막 접근 시간")
    
    # 세션 데이터
    data: Dict[str, Any] = Field(default_factory=dict, description="세션별 데이터 저장")
    analysis_results: Dict[str, SessionAnalysisResult] = Field(default_factory=dict, description="분석 결과 저장")
    file_paths: List[str] = Field(default_factory=list, description="사용된 파일 경로들")
    
    # 세션 메타데이터
    current_step: int = Field(default=1, description="현재 질의 단계")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="사용자 응답 저장")
    conversation_context: Dict[str, Any] = Field(default_factory=dict, description="대화 맥락")
    
    # 성능 메트릭
    api_call_count: int = Field(default=0, description="API 호출 횟수")
    cache_hit_count: int = Field(default=0, description="캐시 히트 횟수")
    total_processing_time: float = Field(default=0.0, description="총 처리 시간")
    
    def update_access_time(self):
        """접근 시간 업데이트"""
        self.last_accessed = datetime.now()
    
    def add_analysis_result(self, analysis_type: str, result: Dict[str, Any], 
                          file_path: str, success: bool = True, error_message: Optional[str] = None):
        """분석 결과 추가"""
        self.analysis_results[analysis_type] = SessionAnalysisResult(
            analysis_type=analysis_type,
            result=result,
            file_path=file_path,
            success=success,
            error_message=error_message
        )
        self.update_access_time()
    
    def get_analysis_result(self, analysis_type: str) -> Optional[SessionAnalysisResult]:
        """분석 결과 조회"""
        return self.analysis_results.get(analysis_type)
    
    def increment_api_calls(self, count: int = 1):
        """API 호출 횟수 증가"""
        self.api_call_count += count
        self.update_access_time()
    
    def increment_cache_hits(self, count: int = 1):
        """캐시 히트 횟수 증가"""
        self.cache_hit_count += count
    
    def add_processing_time(self, time_seconds: float):
        """처리 시간 추가"""
        self.total_processing_time += time_seconds
    
    def get_cache_efficiency(self) -> float:
        """캐시 효율성 계산 (캐시 히트율)"""
        total_requests = self.api_call_count + self.cache_hit_count
        if total_requests == 0:
            return 0.0
        return (self.cache_hit_count / total_requests) * 100
    
    def get_session_summary(self) -> Dict[str, Any]:
        """세션 요약 정보 반환"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'current_step': self.current_step,
            'file_count': len(self.file_paths),
            'analysis_count': len(self.analysis_results),
            'api_call_count': self.api_call_count,
            'cache_hit_count': self.cache_hit_count,
            'cache_efficiency': self.get_cache_efficiency(),
            'total_processing_time': self.total_processing_time
        }