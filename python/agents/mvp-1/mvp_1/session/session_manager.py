"""
세션 관리자

사용자 세션을 관리하고 세션별 데이터를 저장/조회합니다.
"""

import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from .session_data import SessionData, SessionAnalysisResult

logger = logging.getLogger(__name__)


class SessionManager:
    """세션 관리자 클래스"""
    
    def __init__(self, session_dir: str = "data/cache/sessions"):
        """
        세션 관리자 초기화
        
        Args:
            session_dir: 세션 데이터 저장 디렉토리
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, SessionData] = {}
        self.session_ttl = timedelta(hours=2)  # 2시간 세션 유지
        self.max_sessions = 100  # 최대 세션 수
        
        # 자동 정리 설정
        self.auto_cleanup_enabled = True
        self.cleanup_interval = timedelta(minutes=30)  # 30분마다 정리
        self.last_cleanup = datetime.now()
        
        logger.info(f"SessionManager 초기화 완료: {self.session_dir}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        새 세션 생성
        
        Args:
            user_id: 사용자 ID (선택사항)
            
        Returns:
            생성된 세션 ID
        """
        try:
            session_id = str(uuid.uuid4())
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id
            )
            
            self.sessions[session_id] = session_data
            
            # 세션 데이터를 디스크에 저장
            self._save_session_to_disk(session_data)
            
            logger.info(f"새 세션 생성: {session_id} (사용자: {user_id})")
            return session_id
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        세션 데이터 반환
        
        Args:
            session_id: 세션 ID
            
        Returns:
            세션 데이터 또는 None
        """
        try:
            # 메모리에서 먼저 확인
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if datetime.now() - session.last_accessed < self.session_ttl:
                    session.update_access_time()
                    return session
                else:
                    # 만료된 세션 삭제
                    self._remove_session(session_id)
                    return None
            
            # 디스크에서 로드 시도
            session = self._load_session_from_disk(session_id)
            if session:
                if datetime.now() - session.last_accessed < self.session_ttl:
                    # 메모리에 로드
                    self.sessions[session_id] = session
                    session.update_access_time()
                    return session
                else:
                    # 만료된 세션 삭제
                    self._remove_session(session_id)
            
            return None
            
        except Exception as e:
            logger.error(f"세션 조회 실패: {session_id}, 오류: {e}")
            return None
    
    def store_data(self, session_id: str, key: str, data: Any):
        """
        세션에 데이터 저장
        
        Args:
            session_id: 세션 ID
            key: 데이터 키
            data: 저장할 데이터
        """
        try:
            session = self.get_session(session_id)
            if session:
                session.data[key] = data
                session.update_access_time()
                self._save_session_to_disk(session)
            else:
                logger.warning(f"세션을 찾을 수 없습니다: {session_id}")
                
        except Exception as e:
            logger.error(f"세션 데이터 저장 실패: {session_id}, 키: {key}, 오류: {e}")
    
    def get_data(self, session_id: str, key: str) -> Any:
        """
        세션에서 데이터 조회
        
        Args:
            session_id: 세션 ID
            key: 데이터 키
            
        Returns:
            저장된 데이터 또는 None
        """
        try:
            session = self.get_session(session_id)
            if session:
                return session.data.get(key)
            return None
            
        except Exception as e:
            logger.error(f"세션 데이터 조회 실패: {session_id}, 키: {key}, 오류: {e}")
            return None
    
    def store_analysis_result(self, session_id: str, analysis_type: str, 
                            result: Dict[str, Any], file_path: str, 
                            success: bool = True, error_message: Optional[str] = None):
        """
        분석 결과를 세션에 저장
        
        Args:
            session_id: 세션 ID
            analysis_type: 분석 유형
            result: 분석 결과
            file_path: 분석된 파일 경로
            success: 분석 성공 여부
            error_message: 오류 메시지
        """
        try:
            session = self.get_session(session_id)
            if session:
                session.add_analysis_result(analysis_type, result, file_path, success, error_message)
                self._save_session_to_disk(session)
            else:
                logger.warning(f"세션을 찾을 수 없습니다: {session_id}")
                
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {session_id}, 분석 유형: {analysis_type}, 오류: {e}")
    
    def get_analysis_result(self, session_id: str, analysis_type: str) -> Optional[SessionAnalysisResult]:
        """
        세션에서 분석 결과 조회
        
        Args:
            session_id: 세션 ID
            analysis_type: 분석 유형
            
        Returns:
            분석 결과 또는 None
        """
        try:
            session = self.get_session(session_id)
            if session:
                return session.get_analysis_result(analysis_type)
            return None
            
        except Exception as e:
            logger.error(f"분석 결과 조회 실패: {session_id}, 분석 유형: {analysis_type}, 오류: {e}")
            return None
    
    def update_user_responses(self, session_id: str, step: int, response: Any):
        """
        사용자 응답 업데이트
        
        Args:
            session_id: 세션 ID
            step: 질의 단계
            response: 사용자 응답
        """
        try:
            session = self.get_session(session_id)
            if session:
                session.user_responses[f"step_{step}"] = response
                session.current_step = step
                session.update_access_time()
                self._save_session_to_disk(session)
            else:
                logger.warning(f"세션을 찾을 수 없습니다: {session_id}")
                
        except Exception as e:
            logger.error(f"사용자 응답 업데이트 실패: {session_id}, 단계: {step}, 오류: {e}")
    
    def get_user_responses(self, session_id: str) -> Dict[str, Any]:
        """
        사용자 응답 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            사용자 응답 딕셔너리
        """
        try:
            session = self.get_session(session_id)
            if session:
                return session.user_responses
            return {}
            
        except Exception as e:
            logger.error(f"사용자 응답 조회 실패: {session_id}, 오류: {e}")
            return {}
    
    def increment_api_calls(self, session_id: str, count: int = 1):
        """API 호출 횟수 증가"""
        try:
            session = self.get_session(session_id)
            if session:
                session.increment_api_calls(count)
                self._save_session_to_disk(session)
        except Exception as e:
            logger.error(f"API 호출 횟수 증가 실패: {session_id}, 오류: {e}")
    
    def increment_cache_hits(self, session_id: str, count: int = 1):
        """캐시 히트 횟수 증가"""
        try:
            session = self.get_session(session_id)
            if session:
                session.increment_cache_hits(count)
                self._save_session_to_disk(session)
        except Exception as e:
            logger.error(f"캐시 히트 횟수 증가 실패: {session_id}, 오류: {e}")
    
    def _save_session_to_disk(self, session: SessionData):
        """세션 데이터를 디스크에 저장"""
        try:
            session_file = self.session_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.dict(), f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"세션 디스크 저장 실패: {session.session_id}, 오류: {e}")
    
    def _load_session_from_disk(self, session_id: str) -> Optional[SessionData]:
        """디스크에서 세션 데이터 로드"""
        try:
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    return SessionData(**session_data)
            return None
        except Exception as e:
            logger.error(f"세션 디스크 로드 실패: {session_id}, 오류: {e}")
            return None
    
    def _remove_session(self, session_id: str):
        """세션 제거 (메모리 및 디스크)"""
        try:
            # 메모리에서 제거
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # 디스크에서 제거
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                
        except Exception as e:
            logger.error(f"세션 제거 실패: {session_id}, 오류: {e}")
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            # 메모리의 만료된 세션 찾기
            for session_id, session in self.sessions.items():
                if current_time - session.last_accessed > self.session_ttl:
                    expired_sessions.append(session_id)
            
            # 만료된 세션 제거
            for session_id in expired_sessions:
                self._remove_session(session_id)
            
            if expired_sessions:
                logger.info(f"만료된 세션 {len(expired_sessions)}개 정리 완료")
                
        except Exception as e:
            logger.error(f"만료된 세션 정리 실패: {e}")
    
    def auto_cleanup(self):
        """자동 정리 실행"""
        if not self.auto_cleanup_enabled:
            return
        
        now = datetime.now()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        logger.info("세션 자동 정리 시작")
        
        try:
            # 만료된 세션 정리
            self.cleanup_expired_sessions()
            
            # 세션 수 제한
            if len(self.sessions) > self.max_sessions:
                # 가장 오래된 세션들 제거
                sorted_sessions = sorted(
                    self.sessions.items(),
                    key=lambda x: x[1].last_accessed
                )
                
                sessions_to_remove = len(self.sessions) - self.max_sessions
                for session_id, _ in sorted_sessions[:sessions_to_remove]:
                    self._remove_session(session_id)
                
                logger.info(f"세션 수 제한으로 {sessions_to_remove}개 세션 제거")
            
            self.last_cleanup = now
            logger.info("세션 자동 정리 완료")
            
        except Exception as e:
            logger.error(f"세션 자동 정리 실패: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보 반환"""
        try:
            active_sessions = len(self.sessions)
            total_api_calls = sum(s.api_call_count for s in self.sessions.values())
            total_cache_hits = sum(s.cache_hit_count for s in self.sessions.values())
            
            # 평균 캐시 효율성 계산
            cache_efficiencies = [s.get_cache_efficiency() for s in self.sessions.values()]
            avg_cache_efficiency = sum(cache_efficiencies) / len(cache_efficiencies) if cache_efficiencies else 0
            
            return {
                'active_sessions': active_sessions,
                'max_sessions': self.max_sessions,
                'session_ttl_hours': self.session_ttl.total_seconds() / 3600,
                'total_api_calls': total_api_calls,
                'total_cache_hits': total_cache_hits,
                'average_cache_efficiency': round(avg_cache_efficiency, 2),
                'session_dir': str(self.session_dir),
                'auto_cleanup_enabled': self.auto_cleanup_enabled,
                'last_cleanup': self.last_cleanup.isoformat()
            }
            
        except Exception as e:
            logger.error(f"세션 통계 조회 실패: {e}")
            return {}


# 전역 세션 매니저 인스턴스
session_manager = SessionManager()