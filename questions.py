"""대한항공 영상면접 질문 은행"""

from dataclasses import dataclass
from typing import List
import random

@dataclass
class Question:
    id: int
    category: str
    category_name: str
    question: str
    tips: List[str]
    keywords: List[str]
    prep_time: int = 30  # 준비시간 (초)
    answer_time: int = 60  # 답변시간 (초)

CATEGORIES = {
    'motivation': {'name': '지원동기', 'icon': '🎯'},
    'service': {'name': '서비스 상황', 'icon': '✈️'},
    'teamwork': {'name': '팀워크', 'icon': '🤝'},
    'company': {'name': '대한항공', 'icon': '🛫'},
    'personality': {'name': '인성/가치관', 'icon': '💫'},
}

QUESTIONS = [
    # 지원동기
    Question(
        id=1,
        category='motivation',
        category_name='지원동기',
        question='대한항공 객실승무원에 지원한 동기는 무엇인가요?',
        tips=[
            '대한항공만의 차별점을 언급하세요',
            '본인의 경험과 연결지어 이야기하세요',
            '진정성 있는 이유를 말하세요'
        ],
        keywords=['대한항공', '서비스', '글로벌', '성장']
    ),
    Question(
        id=2,
        category='motivation',
        category_name='지원동기',
        question='입사 후 5년, 10년 뒤 어떤 승무원이 되고 싶나요?',
        tips=[
            '구체적인 목표를 제시하세요',
            '대한항공 내 성장 경로를 언급하세요',
            '팀에 기여할 수 있는 부분을 말하세요'
        ],
        keywords=['성장', '리더십', '멘토', '전문성']
    ),
    Question(
        id=3,
        category='motivation',
        category_name='지원동기',
        question='승무원이라는 직업의 가장 큰 매력은 무엇이라고 생각하나요?',
        tips=[
            '단순히 여행이 아닌 서비스 관점에서 답변하세요',
            '본인의 가치관과 연결지으세요'
        ],
        keywords=['서비스', '만남', '성장', '도전']
    ),

    # 서비스 상황
    Question(
        id=4,
        category='service',
        category_name='서비스 상황',
        question='기내에서 승객이 큰 소리로 불만을 표출한다면 어떻게 대처하시겠습니까?',
        tips=[
            '먼저 경청하는 자세를 보여주세요',
            '공감 표현 후 해결책을 제시하세요',
            '다른 승객에 대한 배려도 언급하세요'
        ],
        keywords=['경청', '공감', '해결', '배려']
    ),
    Question(
        id=5,
        category='service',
        category_name='서비스 상황',
        question='특별 기내식을 요청했는데 누락된 승객이 있다면 어떻게 하시겠습니까?',
        tips=[
            '진심어린 사과를 먼저 하세요',
            '가능한 대안을 제시하세요',
            '재발 방지 의지를 보여주세요'
        ],
        keywords=['사과', '대안', '책임감', '서비스 회복']
    ),
    Question(
        id=6,
        category='service',
        category_name='서비스 상황',
        question='비행 중 의료 응급상황이 발생하면 어떻게 대처하시겠습니까?',
        tips=[
            '매뉴얼에 따른 절차를 언급하세요',
            '팀워크의 중요성을 강조하세요',
            '침착함을 유지하는 것이 중요합니다'
        ],
        keywords=['안전', '절차', '팀워크', '침착']
    ),

    # 팀워크
    Question(
        id=7,
        category='teamwork',
        category_name='팀워크',
        question='팀 내에서 갈등이 생겼을 때 어떻게 해결하셨나요?',
        tips=[
            '구체적인 경험을 이야기하세요',
            '본인의 역할을 명확히 하세요',
            '결과와 배운 점을 말하세요'
        ],
        keywords=['소통', '조율', '해결', '협력']
    ),
    Question(
        id=8,
        category='teamwork',
        category_name='팀워크',
        question='선배 승무원과 의견이 다를 때 어떻게 하시겠습니까?',
        tips=[
            '존중하는 태도를 보여주세요',
            '합리적인 의사소통 방법을 제시하세요',
            '팀의 목표를 우선시하세요'
        ],
        keywords=['존중', '소통', '유연성', '팀 목표']
    ),
    Question(
        id=9,
        category='teamwork',
        category_name='팀워크',
        question='본인이 팀에서 주로 어떤 역할을 하나요?',
        tips=[
            '구체적인 예시와 함께 설명하세요',
            '승무원 업무와 연결지어 말하세요'
        ],
        keywords=['역할', '기여', '협력', '리더십']
    ),

    # 대한항공 관련
    Question(
        id=10,
        category='company',
        category_name='대한항공',
        question='대한항공의 최근 뉴스 중 인상 깊었던 것은 무엇인가요?',
        tips=[
            '최근 1-2개월 내 뉴스를 언급하세요',
            '본인의 생각과 의견을 덧붙이세요',
            '회사에 대한 관심을 보여주세요'
        ],
        keywords=['관심', '분석', '의견', '업계 동향']
    ),
    Question(
        id=11,
        category='company',
        category_name='대한항공',
        question='대한항공과 아시아나 합병에 대해 어떻게 생각하시나요?',
        tips=[
            '객관적인 사실을 바탕으로 말하세요',
            '긍정적인 시각을 유지하세요',
            '본인이 기여할 수 있는 점을 언급하세요'
        ],
        keywords=['시너지', '변화', '기회', '적응']
    ),
    Question(
        id=12,
        category='company',
        category_name='대한항공',
        question='대한항공의 서비스 철학에 대해 알고 있는 것을 말해주세요.',
        tips=[
            '공식 홈페이지 내용을 참고하세요',
            '본인의 서비스 철학과 연결지으세요'
        ],
        keywords=['Excellence in Flight', '고객 중심', '안전']
    ),

    # 인성/가치관
    Question(
        id=13,
        category='personality',
        category_name='인성/가치관',
        question='본인의 장점과 단점은 무엇인가요?',
        tips=[
            '승무원 직무와 연관지어 말하세요',
            '단점은 개선 노력과 함께 말하세요',
            '진솔하게 답변하세요'
        ],
        keywords=['자기인식', '성장', '개선', '강점']
    ),
    Question(
        id=14,
        category='personality',
        category_name='인성/가치관',
        question='스트레스를 받을 때 어떻게 해소하시나요?',
        tips=[
            '건강한 해소 방법을 말하세요',
            '업무에 지장을 주지 않는 방법이어야 합니다'
        ],
        keywords=['자기관리', '회복력', '균형', '건강']
    ),
    Question(
        id=15,
        category='personality',
        category_name='인성/가치관',
        question='가장 힘들었던 경험과 그것을 극복한 방법을 말해주세요.',
        tips=[
            '구체적인 상황을 설명하세요',
            '극복 과정에서 배운 점을 강조하세요',
            '성장한 모습을 보여주세요'
        ],
        keywords=['극복', '성장', '회복력', '배움']
    ),
    Question(
        id=16,
        category='personality',
        category_name='인성/가치관',
        question='서비스란 무엇이라고 생각하시나요?',
        tips=[
            '본인만의 정의를 내려보세요',
            '경험을 바탕으로 이야기하세요',
            '승무원 서비스와 연결지으세요'
        ],
        keywords=['고객', '진심', '배려', '가치']
    ),
]


def get_questions_by_category(category: str) -> List[Question]:
    """카테고리별 질문 반환"""
    return [q for q in QUESTIONS if q.category == category]


def get_random_questions(count: int = 5) -> List[Question]:
    """랜덤 질문 반환"""
    return random.sample(QUESTIONS, min(count, len(QUESTIONS)))


def get_question_by_id(question_id: int) -> Question:
    """ID로 질문 찾기"""
    for q in QUESTIONS:
        if q.id == question_id:
            return q
    return None
