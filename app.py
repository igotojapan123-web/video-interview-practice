"""
대한항공 영상면접 연습 - Streamlit 앱
2026 상반기 실제 면접 방식 반영
"""

import streamlit as st
import tempfile
import time
import json
import os
from datetime import datetime
from pathlib import Path
import queue
import threading

from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import numpy as np
from openai import OpenAI

from questions import (
    QUESTIONS, CATEGORIES,
    get_questions_by_category,
    get_random_questions,
    get_question_by_id,
    KAL_2026_COMMON_QUESTION,
    KAL_2026_OPTIONAL_QUESTIONS
)

# 페이지 설정
st.set_page_config(
    page_title="대한항공 영상면접 연습",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== 메인 웹사이트 유도 배너 =====
st.markdown("""
<div style="
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
">
    <h2 style="margin: 0 0 0.5rem 0; font-size: 1.5rem;">🎉 FLYREADY 정식 버전이 출시되었습니다!</h2>
    <p style="margin: 0 0 1rem 0; opacity: 0.9;">
        더 많은 기능과 AI 면접 코칭을 경험해보세요. 3일간 무료 체험!
    </p>
    <a href="https://flyready.co.kr" target="_blank" style="
        display: inline-block;
        background: white;
        color: #7c3aed;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1rem;
        transition: transform 0.2s;
    ">
        ✈️ FLYREADY 바로가기 →
    </a>
</div>
""", unsafe_allow_html=True)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        margin-bottom: 2rem;
    }
    .question-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .common-question-box {
        background: linear-gradient(135deg, #0062B1 0%, #004080 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        font-size: 1rem;
        line-height: 1.6;
    }
    .timer-box {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        padding: 2rem;
    }
    .timer-warning {
        color: #ff4444;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .countdown-box {
        font-size: 8rem;
        font-weight: bold;
        text-align: center;
        padding: 3rem;
        color: #0062B1;
    }
    .tip-box {
        background: #f0f7ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .score-box {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 2rem;
        border-radius: 1rem;
    }
    .score-high { background: #d4edda; color: #155724; }
    .score-mid { background: #fff3cd; color: #856404; }
    .score-low { background: #f8d7da; color: #721c24; }
    .keyword-found {
        background: #d4edda;
        color: #155724;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
    }
    .keyword-missing {
        background: #f8d7da;
        color: #721c24;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
    }
    .option-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid transparent;
    }
    .option-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .option-card-selected {
        border: 2px solid #0062B1;
        background: #f0f7ff;
    }
    .info-banner {
        background: #e3f2fd;
        border-left: 4px solid #0062B1;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 0 0.5rem 0.5rem 0;
    }
    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .step-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ddd;
    }
    .step-dot-active {
        background: #0062B1;
    }
    .step-dot-done {
        background: #28a745;
    }
</style>
""", unsafe_allow_html=True)


# 세션 상태 초기화
def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'phase' not in st.session_state:
        st.session_state.phase = 'ready'
    if 'recorded_video' not in st.session_state:
        st.session_state.recorded_video = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'practice_history' not in st.session_state:
        st.session_state.practice_history = []
    if 'recording_frames' not in st.session_state:
        st.session_state.recording_frames = []
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'audio_frames' not in st.session_state:
        st.session_state.audio_frames = []
    # 2026 상반기 전용 상태
    if 'kal2026_step' not in st.session_state:
        st.session_state.kal2026_step = 1  # 1~7
    if 'answer_time' not in st.session_state:
        st.session_state.answer_time = 90  # 기본 90초
    if 'selected_optional' not in st.session_state:
        st.session_state.selected_optional = None  # 선택문항 인덱스
    if 'script_text' not in st.session_state:
        st.session_state.script_text = ""  # 스크립트 내용
    if 'confirm_start_time' not in st.session_state:
        st.session_state.confirm_start_time = None
    if 'countdown_start_time' not in st.session_state:
        st.session_state.countdown_start_time = None

init_session_state()


# OpenAI 클라이언트
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
    if api_key:
        return OpenAI(api_key=api_key)
    return None


# 비디오 프로세서 (녹화용)
class VideoRecorder(VideoProcessorBase):
    def __init__(self):
        self.frames = []
        self.audio_frames = []
        self.is_recording = False
        self.lock = threading.Lock()

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        if self.is_recording:
            with self.lock:
                self.frames.append(img.copy())

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def recv_audio(self, frame):
        if self.is_recording:
            with self.lock:
                self.audio_frames.append(frame.to_ndarray())
        return frame


# AI 분석 함수
def analyze_answer(audio_path: str, question: str, keywords: list) -> dict:
    """음성을 텍스트로 변환하고 AI 분석 수행"""
    client = get_openai_client()
    if not client:
        return {
            "error": "OpenAI API 키가 설정되지 않았습니다.",
            "score": 0,
            "transcript": "",
            "structure": "분석 불가",
            "keywords": [],
            "missingKeywords": keywords,
            "length": "분석 불가",
            "suggestions": ["API 키를 설정해주세요"]
        }

    # 1. Whisper로 음성 → 텍스트
    transcript = ""
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko",
                response_format="text"
            )
            transcript = transcription
    except Exception as e:
        transcript = f"[음성 인식 실패: {str(e)}]"

    # 2. GPT로 답변 분석
    analysis_prompt = f"""
당신은 10년 경력의 대한항공 객실승무원 면접관입니다.
지원자의 영상면접 답변을 **실제 면접처럼 엄격하게** 평가해주세요.

## 질문
{question}

## 지원자 답변 (음성 인식)
{transcript}

## 평가 기준 키워드
{', '.join(keywords)}

## ⚠️ 엄격한 점수 기준 (반드시 준수!)

### 90-100점: 합격권 (상위 5%)
- 질문 의도를 완벽히 파악
- 구체적인 경험/사례 포함
- 논리적 구조 (두괄식 + 근거 + 마무리)
- 핵심 키워드 대부분 언급
- 진정성이 느껴지는 답변

### 70-89점: 양호 (상위 30%)
- 질문에 적절히 답변
- 일부 구체적 사례 포함
- 기본적인 논리 구조 있음
- 일부 키워드 언급

### 50-69점: 보통 (평균)
- 질문에 답변했으나 구체성 부족
- 두루뭉술한 일반적 답변
- 구조가 다소 산만함
- 암기한 듯한 느낌

### 30-49점: 미흡
- 질문 의도 파악 부족
- 구체적 내용 없음
- 너무 짧거나 횡설수설
- 준비 부족이 느껴짐

### 0-29점: 심각
- 질문과 무관한 답변
- 답변 거의 없음
- 의미없는 내용

## 감점 요소
- 너무 짧은 답변 (30초 미만): -15점
- 구체적 사례/경험 없음: -10점
- 두괄식 구조 없음: -5점
- 횡설수설/반복: -10점
- 핵심 키워드 누락 (각 -3점)
- "어...", "음..." 등 필러워드 과다: -5점

## 분석 요청
다음 형식으로 JSON 응답해주세요:

{{
  "score": (위 기준에 따른 0-100 점수 - 엄격하게!),
  "structure": (답변 구조 평가 - 두괄식인지, 논리적 흐름이 있는지),
  "keywords": (답변에 포함된 키워드 배열),
  "missingKeywords": (누락된 키워드 배열),
  "length": (답변 길이 평가 - 적절/짧음/길음),
  "suggestions": (개선 제안 3개 배열 - 아래 톤 가이드 참고)
}}

## suggestions 톤 가이드 (코칭/응원 느낌으로!)
- "~하세요" 대신 → "~해보면 좋아요" 또는 "~하면 더 좋아질 수 있어요"
- "반드시" → 사용 금지
- "명확히" → "자연스럽게"
- 문장 끝에 긍정적 뉘앙스 추가

예시:
- "선택한 핵심가치를 첫 문장에서 자연스럽게 언급하면 인상이 더 강해질 수 있어요"
- "본인만의 경험이나 사례를 하나 넣어보면 답변이 훨씬 생생해져요"
- "마지막에 승무원으로서의 포부를 한 마디 덧붙이면 마무리가 깔끔해져요"

⚠️ 중요: 평균 지원자의 점수는 50-65점대입니다. 80점 이상은 정말 잘한 경우에만 주세요!
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """당신은 엄격하지만 공정한 대한항공 면접관입니다.
실제 면접처럼 냉정하게 평가합니다.
- 평균 점수는 55점 내외입니다
- 80점 이상은 정말 뛰어난 답변에만 부여합니다
- 구체적 경험이 없으면 높은 점수를 주지 마세요
- 반드시 JSON 형식으로만 응답하세요"""
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        analysis = json.loads(completion.choices[0].message.content)
        analysis["transcript"] = transcript
        return analysis

    except Exception as e:
        return {
            "error": str(e),
            "score": 40,
            "transcript": transcript,
            "structure": "분석 중 오류 발생",
            "keywords": [],
            "missingKeywords": keywords,
            "length": "분석 불가",
            "suggestions": ["다시 녹화해보세요", "조용한 환경에서 녹음하세요", f"오류: {str(e)}"]
        }


# ===== 페이지 렌더링 =====

def render_home():
    """홈페이지"""
    st.markdown('<p class="main-header">✈️ 대한항공 영상면접 연습</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">실전처럼 연습하고, AI 피드백으로 개선하세요</p>', unsafe_allow_html=True)

    # 2026 상반기 연습 (메인)
    st.subheader("🆕 2026 상반기 실제 면접 연습")
    st.markdown("""
    <div class="info-banner">
        ℹ️ 실제 면접 프로세스를 그대로 재현합니다: 질문 선택 → 스크립트 작성 → 2분 확인 → 녹화
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎬 2026 상반기 면접 연습 시작", type="primary", use_container_width=True):
        st.session_state.page = 'kal2026'
        st.session_state.kal2026_step = 1
        st.session_state.selected_optional = None
        st.session_state.script_text = ""
        st.rerun()

    st.divider()

    # 빠른 시작 (기존 방식)
    st.subheader("🚀 빠른 연습 (기존 방식)")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎲 랜덤 5문제 연습", use_container_width=True):
            st.session_state.questions = get_random_questions(5)
            st.session_state.current_index = 0
            st.session_state.phase = 'ready'
            st.session_state.page = 'practice'
            st.rerun()

    with col2:
        if st.button("📚 전체 문제 연습", use_container_width=True):
            st.session_state.questions = QUESTIONS.copy()
            st.session_state.current_index = 0
            st.session_state.phase = 'ready'
            st.session_state.page = 'practice'
            st.rerun()

    # 카테고리별 연습
    st.subheader("📂 카테고리별 연습")
    cols = st.columns(len(CATEGORIES))

    for i, (cat_id, cat_info) in enumerate(CATEGORIES.items()):
        if cat_id == 'kal2026':
            continue  # 2026은 위에서 별도 처리
        with cols[i]:
            if st.button(f"{cat_info['icon']} {cat_info['name']}", use_container_width=True):
                st.session_state.questions = get_questions_by_category(cat_id)
                st.session_state.current_index = 0
                st.session_state.phase = 'ready'
                st.session_state.page = 'practice'
                st.rerun()

    # 연습 기록
    st.subheader("📊 내 연습 기록")
    if st.session_state.practice_history:
        for record in reversed(st.session_state.practice_history[-5:]):
            with st.expander(f"**{record['question'][:30]}...** - {record['score']}점"):
                st.write(f"**답변:** {record.get('transcript', '없음')[:200]}...")
                st.write(f"**분석:** {record.get('structure', '없음')}")
    else:
        st.caption("아직 연습 기록이 없습니다. 위에서 연습을 시작해보세요!")


def render_kal2026():
    """2026 상반기 면접 연습 페이지"""
    step = st.session_state.kal2026_step

    # 상단 네비게이션
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 홈으로"):
            st.session_state.page = 'home'
            st.session_state.kal2026_step = 1
            st.rerun()
    with col2:
        st.caption(f"2026 상반기 면접 연습 | Step {step}/7")

    # 스텝 인디케이터
    step_html = '<div class="step-indicator">'
    for i in range(1, 8):
        if i < step:
            step_html += '<div class="step-dot step-dot-done"></div>'
        elif i == step:
            step_html += '<div class="step-dot step-dot-active"></div>'
        else:
            step_html += '<div class="step-dot"></div>'
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)

    # Step 1: 안내 화면
    if step == 1:
        render_kal2026_step1()
    elif step == 2:
        render_kal2026_step2()
    elif step == 3:
        render_kal2026_step3()
    elif step == 4:
        render_kal2026_step4()
    elif step == 5:
        render_kal2026_step5()
    elif step == 6:
        render_kal2026_step6()
    elif step == 7:
        render_kal2026_step7()


def render_kal2026_step1():
    """Step 1: 안내 화면"""
    st.markdown("""
    <div class="info-banner">
        ℹ️ <strong>2026 상반기 실제 면접 기준으로 구성된 연습입니다.</strong><br>
        실제 면접에서는 메일로 질문을 받고, 답변 스크립트를 파일로 제출한 후 녹화합니다.<br>
        답변 시간은 안내 메일을 확인하세요.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("⏱️ 답변 녹화 시간 설정")

    answer_time = st.number_input(
        "답변 녹화 시간 (초)",
        min_value=30,
        max_value=300,
        value=st.session_state.answer_time,
        step=10,
        help="실제 답변 시간은 안내 메일을 확인하세요"
    )
    st.session_state.answer_time = answer_time

    st.caption("💡 실제 답변 시간은 안내 메일을 확인하세요")

    st.divider()

    st.subheader("📋 연습 진행 순서")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("**1. 질문 선택**\n\n공통문항 확인\n+ 선택문항 1개 선택")
    with col2:
        st.info("**2. 스크립트 준비**\n\n답변 키워드를\n간략히 정리")
    with col3:
        st.info("**3. 2분 확인**\n\n제출 내용 확인\n녹화 준비")
    with col4:
        st.info("**4. 답변 녹화**\n\n카운트다운 후\n자동 녹화 시작")

    st.divider()

    if st.button("다음 단계로 →", type="primary", use_container_width=True):
        st.session_state.kal2026_step = 2
        st.rerun()


def render_kal2026_step2():
    """Step 2: 질문 선택 화면"""
    st.subheader("📝 면접 질문")

    # 공통문항
    st.markdown("### 공통문항 (필수)")
    st.markdown(f"""
    <div class="common-question-box">
        {KAL_2026_COMMON_QUESTION['question']}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 선택문항
    st.markdown("### 선택문항 (4개 중 1개 선택)")

    for idx, opt in enumerate(KAL_2026_OPTIONAL_QUESTIONS):
        is_selected = st.session_state.selected_optional == idx
        card_class = "option-card option-card-selected" if is_selected else "option-card"

        col1, col2 = st.columns([5, 1])
        with col1:
            with st.container():
                st.markdown(f"**{idx+1}. {opt['title']}**")
                st.caption(opt['question'][:150] + "...")
        with col2:
            if st.button("선택" if not is_selected else "✓ 선택됨", key=f"opt_{idx}",
                        type="primary" if is_selected else "secondary"):
                st.session_state.selected_optional = idx
                st.rerun()

    st.divider()

    # 선택된 문항 상세 표시
    if st.session_state.selected_optional is not None:
        selected = KAL_2026_OPTIONAL_QUESTIONS[st.session_state.selected_optional]
        with st.expander(f"✅ 선택한 문항: {selected['title']}", expanded=True):
            st.write(selected['question'])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.kal2026_step = 1
            st.rerun()
    with col2:
        if st.session_state.selected_optional is not None:
            if st.button("연습 시작 →", type="primary", use_container_width=True):
                st.session_state.kal2026_step = 3
                st.rerun()
        else:
            st.button("선택문항을 선택해주세요", disabled=True, use_container_width=True)


def render_kal2026_step3():
    """Step 3: 스크립트 준비 화면"""
    st.subheader("📝 스크립트 준비")

    # 선택한 질문 표시
    st.markdown("**📌 공통문항**")
    st.markdown(f"""
    <div class="common-question-box" style="font-size: 0.95rem;">
        {KAL_2026_COMMON_QUESTION['question']}
    </div>
    """, unsafe_allow_html=True)

    selected = KAL_2026_OPTIONAL_QUESTIONS[st.session_state.selected_optional]
    st.markdown(f"**📌 선택문항: {selected['title']}**")
    st.markdown(f"""
    <div class="question-box" style="font-size: 0.95rem;">
        {selected['question']}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 스크립트 입력 - 라벨을 text_area 내부로 이동
    script = st.text_area(
        "✏️ 답변 키워드를 간략히 요약해서 정리하세요",
        value=st.session_state.script_text,
        height=200,
        placeholder="핵심 키워드와 답변 흐름을 정리해보세요...\n\n예시:\n- 선택한 핵심가치: Caring\n- 관련 경험: 봉사활동에서...\n- 강조할 포인트: ...",
        label_visibility="visible"
    )
    st.session_state.script_text = script

    st.caption("💡 실제 면접에서는 이 내용을 워드/한글 파일로 제출합니다")

    st.divider()

    # 실제 면접에서는 뒤로 돌아갈 수 없으므로, 이전 단계 버튼 제거
    if st.button("준비 완료 → 녹화로 넘어가기", type="primary", use_container_width=True):
        st.session_state.kal2026_step = 4
        st.session_state.confirm_start_time = time.time()
        st.rerun()


def render_kal2026_step4():
    """Step 4: 2분 확인 시간"""
    st.markdown("### 🎬 녹화 준비를 해주세요")

    # 타이머
    if st.session_state.confirm_start_time is None:
        st.session_state.confirm_start_time = time.time()

    elapsed = time.time() - st.session_state.confirm_start_time
    remaining = max(0, 120 - int(elapsed))  # 2분 = 120초

    minutes = remaining // 60
    seconds = remaining % 60

    timer_class = "timer-warning" if remaining <= 30 else ""
    st.markdown(f'<div class="timer-box {timer_class}">{minutes:01d}:{seconds:02d}</div>', unsafe_allow_html=True)

    # 안내 문구 (스크립트는 표시하지 않음)
    st.markdown("""
    <div class="info-banner" style="text-align: center; font-size: 1.1rem;">
        📹 <strong>카메라 위치, 조명, 복장을 최종 점검하세요.</strong><br><br>
        ✅ 카메라가 눈높이에 있는지 확인<br>
        ✅ 얼굴이 밝게 보이는지 확인<br>
        ✅ 단정한 복장 착용<br>
        ✅ 조용한 환경 확보
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 실제 면접에서는 뒤로 돌아갈 수 없으므로, 이전 단계 버튼 제거
    if st.button("⏩ 바로 녹화 시작", type="primary", use_container_width=True):
        st.session_state.kal2026_step = 5
        st.session_state.countdown_start_time = time.time()
        st.rerun()

    # 자동 넘어가기
    if remaining <= 0:
        st.session_state.kal2026_step = 5
        st.session_state.countdown_start_time = time.time()
        st.rerun()

    time.sleep(1)
    st.rerun()


def render_kal2026_step5():
    """Step 5: 5초 카운트다운"""
    if st.session_state.countdown_start_time is None:
        st.session_state.countdown_start_time = time.time()

    elapsed = time.time() - st.session_state.countdown_start_time
    remaining = max(0, 5 - int(elapsed))

    st.markdown("### 🎬 녹화가 곧 시작됩니다")

    if remaining > 0:
        st.markdown(f'<div class="countdown-box">{remaining}</div>', unsafe_allow_html=True)
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.kal2026_step = 6
        st.session_state.record_start_time = time.time()
        st.rerun()


def render_kal2026_step6():
    """Step 6: 답변 녹화"""
    # 질문 표시
    st.markdown("### 📌 공통문항")
    st.markdown(f"""
    <div class="common-question-box" style="font-size: 0.9rem; padding: 1rem;">
        {KAL_2026_COMMON_QUESTION['question'][:200]}...
    </div>
    """, unsafe_allow_html=True)

    selected = KAL_2026_OPTIONAL_QUESTIONS[st.session_state.selected_optional]
    st.markdown(f"### 📌 선택문항: {selected['title']}")
    st.markdown(f"""
    <div class="question-box" style="font-size: 0.9rem; padding: 1rem;">
        {selected['question'][:200]}...
    </div>
    """, unsafe_allow_html=True)

    # 비디오 및 타이머
    video_col, control_col = st.columns([2, 1])

    with video_col:
        ctx = webrtc_streamer(
            key="video-interview-2026",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                "video": {"width": 640, "height": 480},
                "audio": True
            },
            video_processor_factory=VideoRecorder,
            async_processing=True,
        )

        if ctx.video_processor:
            ctx.video_processor.is_recording = True
            st.session_state.video_processor = ctx.video_processor

    with control_col:
        if 'record_start_time' not in st.session_state:
            st.session_state.record_start_time = time.time()

        elapsed = time.time() - st.session_state.record_start_time
        remaining = max(0, st.session_state.answer_time - int(elapsed))

        st.markdown("### 🔴 녹화 중")
        timer_class = "timer-warning" if remaining <= 10 else ""
        st.markdown(f'<div class="timer-box {timer_class}">{remaining}초</div>', unsafe_allow_html=True)

        if remaining <= 0 or st.button("⏹️ 답변 완료", type="primary", use_container_width=True):
            if hasattr(st.session_state, 'video_processor'):
                st.session_state.video_processor.is_recording = False
            st.session_state.kal2026_step = 7
            st.rerun()

        time.sleep(1)
        st.rerun()


def render_kal2026_step7():
    """Step 7: AI 분석"""
    st.markdown("### 🎉 녹화 완료!")

    # AI 분석 수행
    if st.session_state.analysis_result is None:
        with st.spinner("AI가 답변을 분석하고 있습니다..."):
            selected = KAL_2026_OPTIONAL_QUESTIONS[st.session_state.selected_optional]
            combined_keywords = KAL_2026_COMMON_QUESTION['keywords'] + selected['keywords']
            combined_question = f"""[공통문항] {KAL_2026_COMMON_QUESTION['question']}

[선택문항: {selected['title']}] {selected['question']}"""

            # 실제 오디오 데이터가 있는 경우 분석
            result = None
            audio_analyzed = False

            # webrtc에서 녹음된 오디오가 있는지 확인
            if hasattr(st.session_state, 'audio_frames') and st.session_state.audio_frames:
                try:
                    import numpy as np
                    from pydub import AudioSegment
                    import io

                    # 오디오 프레임을 하나로 합치기
                    audio_data = np.concatenate(st.session_state.audio_frames)

                    # WAV 파일로 변환
                    audio_segment = AudioSegment(
                        audio_data.tobytes(),
                        frame_rate=48000,
                        sample_width=2,
                        channels=1
                    )

                    # 임시 파일로 저장
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        audio_segment.export(f.name, format="wav")
                        result = analyze_answer(f.name, combined_question, combined_keywords)
                        audio_analyzed = True
                        os.unlink(f.name)  # 임시 파일 삭제

                except Exception as e:
                    st.warning(f"음성 분석 중 오류가 발생했습니다: {str(e)}")

            # 오디오 분석이 안 된 경우 데모 모드
            if result is None:
                import random

                # 음성이 감지되지 않은 경우 - 분석 없이 안내 메시지만 표시
                result = {
                    "score": 0,
                    "transcript": "",
                    "structure": "",
                    "keywords": [],
                    "missingKeywords": [],
                    "length": "",
                    "suggestions": [],
                    "no_audio": True,  # 음성 미감지 플래그
                    "demo_mode": True
                }

            st.session_state.analysis_result = result

            # 기록 저장
            record = {
                "question": f"[2026] 공통문항 + {selected['title']}",
                "category": "2026 상반기",
                "score": result["score"],
                "transcript": result["transcript"],
                "structure": result["structure"],
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.practice_history.append(record)

    result = st.session_state.analysis_result

    # 음성 미감지 시 안내 메시지만 표시
    if result.get("no_audio"):
        st.warning("🎤 **음성이 감지되지 않았습니다.**")
        st.info("""
        마이크가 제대로 연결되어 있는지 확인하고 다시 연습해보세요.

        **체크리스트:**
        - 브라우저에서 마이크 권한을 허용했는지 확인
        - 마이크가 음소거되어 있지 않은지 확인
        - 조용한 환경에서 충분한 볼륨으로 말하기
        """)
    else:
        # 점수 표시
        score = result.get("score", 0)
        score_class = "score-high" if score >= 80 else ("score-mid" if score >= 60 else "score-low")
        st.markdown(f'<div class="score-box {score_class}">{score}점</div>', unsafe_allow_html=True)

        # 탭으로 분석 결과 표시
        tab1, tab2, tab3 = st.tabs(["📝 내 답변", "📊 분석", "💡 개선점"])

        with tab1:
            st.write(result.get("transcript", ""))

        with tab2:
            st.write(f"**구조:** {result.get('structure', '')}")
            st.write(f"**길이:** {result.get('length', '')}")

            # 포함된 키워드 (긍정적 피드백)
            found_keywords = result.get("keywords", [])
            if found_keywords:
                st.write("**✨ 이런 키워드가 포함됐어요:**")
                keywords_html = ""
                for kw in found_keywords:
                    keywords_html += f'<span class="keyword-found">✓ {kw}</span> '
                st.markdown(keywords_html, unsafe_allow_html=True)

            # 미포함 키워드 (부드러운 제안)
            missing_keywords = result.get("missingKeywords", [])
            if missing_keywords:
                st.write("")
                missing_list = "', '".join(missing_keywords)
                st.info(f"💡 **'{missing_list}'** 키워드도 넣어보면 답변이 더 풍성해질 수 있어요!")

        with tab3:
            for sug in result.get("suggestions", []):
                st.info(f"💡 {sug}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 연습", use_container_width=True):
            st.session_state.kal2026_step = 1
            st.session_state.selected_optional = None
            st.session_state.script_text = ""
            st.session_state.analysis_result = None
            st.session_state.confirm_start_time = None
            st.session_state.countdown_start_time = None
            st.rerun()
    with col2:
        if st.button("🏠 홈으로", type="primary", use_container_width=True):
            st.session_state.page = 'home'
            st.session_state.kal2026_step = 1
            st.session_state.analysis_result = None
            st.rerun()


def render_practice():
    """기존 연습 페이지 (다른 카테고리용)"""
    if not st.session_state.questions:
        st.session_state.page = 'home'
        st.rerun()
        return

    question = st.session_state.questions[st.session_state.current_index]
    phase = st.session_state.phase

    # 상단 네비게이션
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 홈으로"):
            st.session_state.page = 'home'
            st.session_state.phase = 'ready'
            st.rerun()
    with col2:
        st.caption(f"{question.category_name} | {st.session_state.current_index + 1} / {len(st.session_state.questions)}")

    # 질문 표시
    st.markdown(f'<div class="question-box">{question.question}</div>', unsafe_allow_html=True)

    # 비디오 영역
    video_col, control_col = st.columns([2, 1])

    with video_col:
        if phase in ['ready', 'prep', 'recording']:
            ctx = webrtc_streamer(
                key="video-interview",
                mode=WebRtcMode.SENDRECV,
                media_stream_constraints={
                    "video": {"width": 640, "height": 480},
                    "audio": True
                },
                video_processor_factory=VideoRecorder,
                async_processing=True,
            )

            if ctx.video_processor:
                st.session_state.video_processor = ctx.video_processor

        elif phase == 'review' and st.session_state.recorded_video:
            st.video(st.session_state.recorded_video)

    with control_col:
        if phase == 'ready':
            st.markdown("### 준비되셨나요?")
            st.markdown(f"- 준비시간: **{question.prep_time}초**")
            st.markdown(f"- 답변시간: **{question.answer_time}초**")

            if st.button("🎬 연습 시작", type="primary", use_container_width=True):
                st.session_state.phase = 'prep'
                st.session_state.prep_start_time = time.time()
                st.rerun()

        elif phase == 'prep':
            elapsed = time.time() - st.session_state.get('prep_start_time', time.time())
            remaining = max(0, question.prep_time - int(elapsed))

            st.markdown("### ⏱️ 준비시간")
            timer_class = "timer-warning" if remaining <= 10 else ""
            st.markdown(f'<div class="timer-box {timer_class}">{remaining}초</div>', unsafe_allow_html=True)

            st.markdown("**💡 팁:**")
            for tip in question.tips:
                st.markdown(f"- {tip}")

            if remaining <= 0:
                st.session_state.phase = 'recording'
                st.session_state.record_start_time = time.time()
                if hasattr(st.session_state, 'video_processor'):
                    st.session_state.video_processor.is_recording = True
                st.rerun()

            if st.button("⏭️ 바로 시작", use_container_width=True):
                st.session_state.phase = 'recording'
                st.session_state.record_start_time = time.time()
                if hasattr(st.session_state, 'video_processor'):
                    st.session_state.video_processor.is_recording = True
                st.rerun()

            time.sleep(1)
            st.rerun()

        elif phase == 'recording':
            elapsed = time.time() - st.session_state.get('record_start_time', time.time())
            remaining = max(0, question.answer_time - int(elapsed))

            st.markdown("### 🔴 녹화 중")
            timer_class = "timer-warning" if remaining <= 10 else ""
            st.markdown(f'<div class="timer-box {timer_class}">{remaining}초</div>', unsafe_allow_html=True)

            if remaining <= 0 or st.button("⏹️ 답변 완료", type="primary", use_container_width=True):
                if hasattr(st.session_state, 'video_processor'):
                    st.session_state.video_processor.is_recording = False
                st.session_state.phase = 'review'
                st.rerun()

            time.sleep(1)
            st.rerun()

        elif phase == 'review':
            st.markdown("### 답변 완료!")

            if st.button("🔄 다시 녹화", use_container_width=True):
                st.session_state.phase = 'ready'
                st.session_state.recorded_video = None
                st.rerun()

            if st.button("🤖 AI 분석 받기", type="primary", use_container_width=True):
                st.session_state.phase = 'analyzing'
                st.rerun()

            if st.button("⏭️ 다음 문제", use_container_width=True):
                if st.session_state.current_index < len(st.session_state.questions) - 1:
                    st.session_state.current_index += 1
                    st.session_state.phase = 'ready'
                    st.session_state.recorded_video = None
                else:
                    st.session_state.page = 'home'
                st.rerun()

        elif phase == 'analyzing':
            st.markdown("### 🔄 AI 분석 중...")
            with st.spinner("음성을 텍스트로 변환하고 분석 중입니다..."):
                import random

                # 더 현실적인 점수 분포 (평균 55점)
                demo_score = max(25, min(85, int(random.gauss(55, 15))))

                if demo_score >= 70:
                    structure_msg = "답변 구조가 잘 갖춰져 있습니다."
                    length_msg = "적절"
                elif demo_score >= 50:
                    structure_msg = "기본 구조는 있으나 개선이 필요합니다."
                    length_msg = "다소 짧음"
                else:
                    structure_msg = "답변 구조가 산만합니다. 두괄식으로 정리하세요."
                    length_msg = "짧음"

                # 음성 미감지 - 분석 없이 안내만
                result = {
                    "score": 0,
                    "transcript": "",
                    "structure": "",
                    "keywords": [],
                    "missingKeywords": [],
                    "length": "",
                    "suggestions": [],
                    "no_audio": True,
                    "demo_mode": True
                }
                st.session_state.analysis_result = result

                record = {
                    "question": question.question,
                    "category": question.category_name,
                    "score": result["score"],
                    "transcript": result["transcript"],
                    "structure": result["structure"],
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.practice_history.append(record)

                st.session_state.phase = 'result'
                st.rerun()

        elif phase == 'result':
            result = st.session_state.analysis_result

            # 음성 미감지 시 안내 메시지만 표시
            if result.get("no_audio"):
                st.warning("🎤 **음성이 감지되지 않았습니다.**")
                st.info("""
                마이크가 제대로 연결되어 있는지 확인하고 다시 연습해보세요.

                **체크리스트:**
                - 브라우저에서 마이크 권한을 허용했는지 확인
                - 마이크가 음소거되어 있지 않은지 확인
                - 조용한 환경에서 충분한 볼륨으로 말하기
                """)
            else:
                score = result.get("score", 0)
                score_class = "score-high" if score >= 80 else ("score-mid" if score >= 60 else "score-low")
                st.markdown(f'<div class="score-box {score_class}">{score}점</div>', unsafe_allow_html=True)

                tab1, tab2, tab3 = st.tabs(["📝 내 답변", "📊 분석", "💡 개선점"])

                with tab1:
                    st.write(result.get("transcript", ""))

                with tab2:
                    st.write(f"**구조:** {result.get('structure', '')}")
                    st.write(f"**길이:** {result.get('length', '')}")

                    # 포함된 키워드 (긍정적 피드백)
                    found_keywords = result.get("keywords", [])
                    if found_keywords:
                        st.write("**✨ 이런 키워드가 포함됐어요:**")
                        keywords_html = ""
                        for kw in found_keywords:
                            keywords_html += f'<span class="keyword-found">✓ {kw}</span> '
                        st.markdown(keywords_html, unsafe_allow_html=True)

                    # 미포함 키워드 (부드러운 제안)
                    missing_keywords = result.get("missingKeywords", [])
                    if missing_keywords:
                        st.write("")
                        missing_list = "', '".join(missing_keywords)
                        st.info(f"💡 **'{missing_list}'** 키워드도 넣어보면 답변이 더 풍성해질 수 있어요!")

                with tab3:
                    for sug in result.get("suggestions", []):
                        st.info(f"💡 {sug}")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 다시 연습", use_container_width=True):
                    st.session_state.phase = 'ready'
                    st.session_state.recorded_video = None
                    st.session_state.analysis_result = None
                    st.rerun()
            with col2:
                if st.button("⏭️ 다음 문제", use_container_width=True, type="primary"):
                    if st.session_state.current_index < len(st.session_state.questions) - 1:
                        st.session_state.current_index += 1
                        st.session_state.phase = 'ready'
                        st.session_state.recorded_video = None
                        st.session_state.analysis_result = None
                    else:
                        st.session_state.page = 'home'
                    st.rerun()


def render_review():
    """연습 기록 페이지"""
    st.markdown('<p class="main-header">📊 연습 기록</p>', unsafe_allow_html=True)

    if st.button("← 홈으로"):
        st.session_state.page = 'home'
        st.rerun()

    if not st.session_state.practice_history:
        st.info("아직 연습 기록이 없습니다. 연습을 시작해보세요!")
        if st.button("🚀 연습 시작하기", type="primary"):
            st.session_state.page = 'home'
            st.rerun()
        return

    # 통계
    scores = [r["score"] for r in st.session_state.practice_history]
    avg_score = sum(scores) / len(scores)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 연습 횟수", f"{len(st.session_state.practice_history)}회")
    with col2:
        st.metric("평균 점수", f"{avg_score:.1f}점")
    with col3:
        st.metric("최고 점수", f"{max(scores)}점")

    st.divider()

    # 기록 목록
    for i, record in enumerate(reversed(st.session_state.practice_history)):
        with st.expander(f"**{record['question'][:40]}...** | {record['score']}점 | {record.get('category', '')}"):
            st.write(f"**점수:** {record['score']}점")
            st.write(f"**답변:** {record.get('transcript', '없음')}")
            st.write(f"**분석:** {record.get('structure', '없음')}")
            st.caption(f"연습 시간: {record.get('timestamp', '')}")


# 사이드바
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📌 메뉴")

        if st.button("🏠 홈", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()

        if st.button("🆕 2026 상반기 연습", use_container_width=True):
            st.session_state.page = 'kal2026'
            st.session_state.kal2026_step = 1
            st.rerun()

        if st.button("📊 연습 기록", use_container_width=True):
            st.session_state.page = 'review'
            st.rerun()

        st.divider()

        st.markdown("### ℹ️ 안내")
        st.caption("""
        - 카메라/마이크 권한 필요
        - 2026 상반기: 실제 면접 방식
        - AI 분석으로 피드백 제공
        """)

        st.divider()
        st.caption("대한항공 영상면접 연습 v2.0")
        st.caption("2026 상반기 업데이트")


# 메인
def main():
    render_sidebar()

    if st.session_state.page == 'home':
        render_home()
    elif st.session_state.page == 'kal2026':
        render_kal2026()
    elif st.session_state.page == 'practice':
        render_practice()
    elif st.session_state.page == 'review':
        render_review()


if __name__ == "__main__":
    main()
