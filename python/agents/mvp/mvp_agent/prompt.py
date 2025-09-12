# 서브 에이전트 프롬프트들을 import
from .sub_agents.generation.prompt import REPORT_GENERATION_PROMPT
from .sub_agents.evaluation.prompt import REPORT_EVALUATION_PROMPT

# 체커 에이전트 프롬프트 생성 함수
def get_checker_prompt(quality_threshold: float, max_iterations: int) -> str:
    """
    환경변수 값을 사용하여 체커 프롬프트를 동적으로 생성합니다.
    
    Args:
        quality_threshold: 품질 임계값
        max_iterations: 최대 반복 횟수
    
    Returns:
        str: 동적으로 생성된 체커 프롬프트
    """
    return f"""
당신은 리포트 품질 체크 전문가입니다. 다음을 확인해야 합니다:

1. 현재 리포트의 품질 점수가 임계값({quality_threshold}점) 이상인지 확인
2. 최대 반복 횟수({max_iterations}회)에 도달했는지 확인

조건 확인 도구를 사용하여 다음을 판단하세요:
- 품질 점수가 {quality_threshold}점 이상이면 루프 종료
- 최대 반복 횟수에 도달하면 루프 종료
- 그렇지 않으면 리포트 재생성 진행

각 조건의 상태를 명확히 보고하세요.
"""

# 모든 프롬프트를 다시 export하여 기존 코드와의 호환성 유지
__all__ = ['REPORT_GENERATION_PROMPT', 'REPORT_EVALUATION_PROMPT', 'get_checker_prompt']