"""
분석 결과 캐시 시스템

분석 결과를 캐싱하여 중복 분석을 방지하고 API 호출을 최적화합니다.
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalysisCache:
    """분석 결과 캐싱을 위한 클래스"""
    
    def __init__(self, cache_dir: str = "data/cache/analysis"):
        """
        분석 캐시 초기화
        
        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=12)  # 12시간 TTL
        self.memory_cache = {}  # 메모리 캐시
        self.max_memory_cache_size = 50  # 메모리 캐시 최대 크기
        
        logger.info(f"AnalysisCache 초기화 완료: {self.cache_dir}")
    
    def get_cache_key(self, file_path: str, analysis_type: str, params: Dict[str, Any]) -> str:
        """
        분석 파라미터를 기반으로 캐시 키 생성
        
        Args:
            file_path: 파일 경로
            analysis_type: 분석 유형
            params: 분석 파라미터
            
        Returns:
            캐시 키 (MD5 해시)
        """
        try:
            # 파라미터 정규화 (정렬하여 일관성 보장)
            normalized_params = self._normalize_params(params)
            
            key_data = {
                'file_path': str(file_path),
                'analysis_type': analysis_type,
                'params': normalized_params
            }
            
            key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(key_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"캐시 키 생성 실패: {e}")
            # 대체 키 생성
            fallback_key = f"{file_path}_{analysis_type}_{hash(str(params))}"
            return hashlib.md5(fallback_key.encode()).hexdigest()
    
    def _normalize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """파라미터 정규화 (타입 변환 및 정렬)"""
        normalized = {}
        for key, value in sorted(params.items()):
            if isinstance(value, (list, tuple)):
                normalized[key] = sorted(list(value))
            elif isinstance(value, dict):
                normalized[key] = self._normalize_params(value)
            else:
                normalized[key] = value
        return normalized
    
    def get_cached_analysis(self, file_path: str, analysis_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        캐시된 분석 결과를 반환
        
        Args:
            file_path: 파일 경로
            analysis_type: 분석 유형
            params: 분석 파라미터
            
        Returns:
            캐시된 분석 결과 또는 None
        """
        try:
            cache_key = self.get_cache_key(file_path, analysis_type, params)
            
            # 메모리 캐시 확인
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    logger.info(f"메모리 캐시에서 분석 결과 로드: {analysis_type}")
                    return cache_entry['result']
                else:
                    # 만료된 캐시 제거
                    del self.memory_cache[cache_key]
            
            # 디스크 캐시 확인
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)
                    cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                    if datetime.now() - cache_time < self.cache_ttl:
                        # 메모리 캐시에 로드
                        self._add_to_memory_cache(cache_key, cache_entry)
                        logger.info(f"디스크 캐시에서 분석 결과 로드: {analysis_type}")
                        return cache_entry['result']
                    else:
                        # 만료된 캐시 파일 삭제
                        cache_file.unlink()
            
            return None
            
        except Exception as e:
            logger.error(f"캐시된 분석 결과 조회 실패: {analysis_type}, 오류: {e}")
            return None
    
    def cache_analysis(self, file_path: str, analysis_type: str, params: Dict[str, Any], result: Dict[str, Any]):
        """
        분석 결과를 캐시에 저장
        
        Args:
            file_path: 파일 경로
            analysis_type: 분석 유형
            params: 분석 파라미터
            result: 분석 결과
        """
        try:
            cache_key = self.get_cache_key(file_path, analysis_type, params)
            cache_entry = {
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'file_path': str(file_path),
                'analysis_type': analysis_type,
                'params': params,
                'result_size': len(str(result))
            }
            
            # 메모리 캐시에 저장
            self._add_to_memory_cache(cache_key, cache_entry)
            
            # 디스크 캐시에 저장
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            logger.info(f"분석 결과 캐시 저장 완료: {analysis_type}")
            
        except Exception as e:
            logger.error(f"분석 결과 캐시 저장 실패: {analysis_type}, 오류: {e}")
    
    def _add_to_memory_cache(self, cache_key: str, cache_entry: Dict[str, Any]):
        """메모리 캐시에 항목 추가 (크기 제한 적용)"""
        # 메모리 캐시 크기 제한
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # 가장 오래된 항목 제거
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['timestamp'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = cache_entry
    
    def clear_cache(self, analysis_type: Optional[str] = None, file_path: Optional[str] = None):
        """
        캐시 정리
        
        Args:
            analysis_type: 특정 분석 유형의 캐시만 정리
            file_path: 특정 파일의 캐시만 정리
        """
        try:
            if analysis_type or file_path:
                # 특정 조건에 맞는 캐시만 정리
                removed_count = 0
                
                # 메모리 캐시 정리
                keys_to_remove = []
                for key, entry in self.memory_cache.items():
                    if analysis_type and entry.get('analysis_type') == analysis_type:
                        keys_to_remove.append(key)
                    elif file_path and entry.get('file_path') == file_path:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    removed_count += 1
                
                # 디스크 캐시 정리
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            entry = json.load(f)
                            
                        should_remove = False
                        if analysis_type and entry.get('analysis_type') == analysis_type:
                            should_remove = True
                        elif file_path and entry.get('file_path') == file_path:
                            should_remove = True
                        
                        if should_remove:
                            cache_file.unlink()
                            removed_count += 1
                            
                    except Exception as e:
                        logger.warning(f"캐시 파일 읽기 실패: {cache_file}, 오류: {e}")
                
                logger.info(f"선택적 캐시 정리 완료: {removed_count}개 항목 제거")
            else:
                # 전체 캐시 정리
                self.memory_cache.clear()
                
                # 디스크 캐시 파일들 삭제
                removed_count = 0
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                    removed_count += 1
                
                logger.info(f"전체 캐시 정리 완료: {removed_count}개 항목 제거")
                
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        try:
            memory_count = len(self.memory_cache)
            disk_count = len(list(self.cache_dir.glob("*.json")))
            
            # 디스크 캐시 크기 계산
            disk_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            
            # 분석 유형별 통계
            analysis_types = {}
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                        analysis_type = entry.get('analysis_type', 'unknown')
                        analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
                except Exception:
                    continue
            
            return {
                'memory_cache_count': memory_count,
                'disk_cache_count': disk_count,
                'disk_cache_size_mb': round(disk_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir),
                'ttl_hours': self.cache_ttl.total_seconds() / 3600,
                'analysis_types': analysis_types
            }
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}


# 전역 분석 캐시 인스턴스
analysis_cache = AnalysisCache()