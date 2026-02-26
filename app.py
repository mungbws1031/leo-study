# -*- coding: utf-8 -*-
import os
import tempfile

# Windows 한글 인코딩 오류 방지
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
import anthropic
import pathlib
import requests
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv(encoding="utf-8")

api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('\ufeff')

st.set_page_config(
    page_title="🎮 레오 학습 파트너",
    page_icon="🎮",
    layout="wide"
)

client = anthropic.Anthropic(api_key=api_key)

CHILD_NAME = os.getenv("CHILD_NAME", "아이").strip()
CHILD_GRADE = os.getenv("CHILD_GRADE", "3").strip()

SAVE_DIR = pathlib.Path("과제기록")
SAVE_DIR.mkdir(exist_ok=True)

DAY_THEMES = {
    0: "🗺️ 탐험가의 날",
    1: "🏗️ 건축가의 날",
    2: "🎨 크리에이터의 날",
    3: "⚔️ 전사의 날",
    4: "🎉 보상의 날",
    5: "🌿 자유의 날",
    6: "😴 휴식의 날"
}


def get_korean_font():
    font_path = os.path.join(tempfile.gettempdir(), "NanumGothic.ttf")
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        r = requests.get(url, timeout=15)
        with open(font_path, "wb") as f:
            f.write(r.content)
    return font_path


def generate_pdf(mission_text, date_str):
    font_path = get_korean_font()

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Nanum", fname=font_path)
    pdf.add_font("NanumB", fname=font_path)

    # 헤더
    pdf.set_fill_color(99, 179, 237)
    pdf.rect(0, 0, 210, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Nanum", size=16)
    pdf.set_y(7)
    pdf.cell(0, 10, f"  레오 학습 파트너  |  {date_str}", align="L")

    pdf.set_text_color(30, 30, 30)
    pdf.set_y(32)

    lines = mission_text.split('\n')
    for line in lines:
        clean = line.replace('**', '').replace('*', '').strip()
        if line.startswith('# '):
            pdf.set_font("Nanum", size=15)
            pdf.set_fill_color(235, 245, 255)
            pdf.multi_cell(0, 9, clean[2:] if clean.startswith('#') else clean, fill=True)
            pdf.ln(1)
        elif line.startswith('## '):
            pdf.set_font("Nanum", size=13)
            pdf.set_fill_color(255, 250, 230)
            pdf.multi_cell(0, 8, clean[3:] if clean.startswith('#') else clean, fill=True)
            pdf.ln(1)
        elif line.startswith('### '):
            pdf.set_font("Nanum", size=12)
            pdf.set_fill_color(240, 255, 240)
            pdf.multi_cell(0, 7, clean[4:] if clean.startswith('#') else clean, fill=True)
        elif clean == '':
            pdf.ln(3)
        elif clean.startswith('---'):
            pdf.set_draw_color(180, 180, 180)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        else:
            pdf.set_font("Nanum", size=11)
            pdf.set_fill_color(255, 255, 255)
            pdf.multi_cell(0, 6, clean)

    return bytes(pdf.output())


def generate_mission(level="보통", game_theme="랜덤"):
    today = datetime.now()
    theme = DAY_THEMES[today.weekday()]
    date_str = today.strftime("%m월 %d일")

    if today.weekday() == 6:
        return f"# 😴 오늘은 쉬는 날!\n\n{CHILD_NAME}아, 오늘은 푹 쉬어! 🎮"

    level_guide = {
        "쉬움": "아주 쉽게, 문제 1개씩만",
        "보통": "적당하게, 문제 2개씩",
        "어려움": "조금 도전적으로, 심화 문제 포함"
    }

    game_guide = {
        "랜덤": "마인크래프트 또는 로블록스 중 하나를 골라서",
        "마인크래프트": "마인크래프트 소재만 사용해서",
        "로블록스": "로블록스 소재만 사용해서"
    }

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        system=(
            f"당신은 '레오'입니다.\n"
            f"초등학교 {CHILD_GRADE}학년 ADHD 아이 '{CHILD_NAME}'의 AI 학습 친구예요.\n\n"
            f"[과제 만들기 규칙]\n"
            f"- 총 30분 이내 끝낼 수 있는 양 ({level_guide[level]})\n"
            f"- {game_guide[game_theme]} 모든 문제를 포장하기\n"
            f"- 구성: 영어 -> 수학 -> 국어 -> 보너스 순서\n"
            f"- 영어: 게임 관련 단어 3개 + 짧은 미션\n"
            f"- 수학: 게임 스토리 속 계산 문제\n"
            f"- 국어: 딱 3줄 글쓰기 (부담 없게)\n"
            f"- 보너스: 게임하면서 할 수 있는 미션\n\n"
            f"[게임 소재 예시]\n"
            f"- 마인크래프트: 크리퍼, 다이아몬드 광산, 엔더드래곤, 레드스톤, 마을 주민, 네더, 스켈레톤, 좀비\n"
            f"- 로블록스: Adopt Me(애완동물/달걀/로벅스), Blox Fruits(악마의열매/해적/검사), "
            f"Brookhaven(집꾸미기/자동차), Jailbreak(탈옥/경찰), 오비(장애물), 게임패스, 아바타, 트레이드\n\n"
            f"[말투 규칙]\n"
            f"- 친구처럼 반말\n"
            f"- 이모지 풍부하게 사용\n"
            f"- 틀려도 괜찮다는 말 꼭 포함\n"
            f"- 마지막에 짧은 응원 메시지"
        ),
        messages=[{
            "role": "user",
            "content": f"오늘은 {date_str} {theme}이야! {CHILD_NAME}이를 위한 오늘의 과제 만들어줘!"
        }]
    )
    return response.content[0].text


def save_mission(mission_text):
    today = datetime.now().strftime("%Y%m%d")
    filepath = SAVE_DIR / f"과제_{today}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"날짜: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        f.write("="*40 + "\n\n")
        f.write(mission_text)
    return filepath


def generate_parent_report():
    records = []
    for file in sorted(SAVE_DIR.glob("과제_*.txt"))[-7:]:
        with open(file, "r", encoding="utf-8") as f:
            records.append(f.read())

    if not records:
        return "아직 저장된 과제 기록이 없어요. 먼저 과제를 생성하고 저장해 주세요!"

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1000,
        system=(
            "당신은 교육 전문가입니다.\n"
            "ADHD 아이의 학습 기록을 분석해서 부모님께\n"
            "따뜻하고 격려가 되는 주간 리포트를 작성해주세요.\n"
            "포함 내용: 이번 주 학습 요약, 잘한 점, 다음 주 추천 방향, 부모님 팁 1가지\n"
            "말투: 따뜻하고 전문적으로"
        ),
        messages=[{
            "role": "user",
            "content": f"아이 이름: {CHILD_NAME}\n\n최근 학습 기록:\n\n" + "\n\n---\n\n".join(records)
        }]
    )
    return response.content[0].text


# ── UI ──
st.title("🎮 레오 학습 파트너")
today = datetime.now()
weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
st.caption(
    f"오늘은 {today.strftime('%Y년 %m월 %d일')} "
    f"{weekday_names[today.weekday()]}요일 | "
    f"{DAY_THEMES[today.weekday()]}"
)

with st.sidebar:
    st.header("⚙️ 설정")
    child_name_input = st.text_input("아이 이름", value=CHILD_NAME)
    st.selectbox("학년", ["1학년","2학년","3학년","4학년","5학년","6학년"], index=2)
    st.divider()
    level = st.radio("오늘의 난이도", ["쉬움", "보통", "어려움"], index=1, horizontal=True)
    game_theme = st.radio("게임 소재", ["랜덤", "마인크래프트", "로블록스"], index=0, horizontal=True)
    st.divider()
    st.header("📅 이번 주 완료")
    for i, day in enumerate(["월","화","수","목","금","토","일"]):
        st.checkbox(f"{day}요일", key=f"day_{i}")

tab1, tab2, tab3 = st.tabs(["📬 오늘의 과제", "📊 부모님 리포트", "📁 과제 기록"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🎮 오늘 과제 만들기!", type="primary", use_container_width=True):
            with st.spinner("레오가 과제를 만들고 있어요... 🤔✨"):
                mission = generate_mission(level, game_theme)
                st.session_state.mission = mission

    with col2:
        if st.button("🔄 다시 만들기", use_container_width=True):
            if "mission" in st.session_state:
                del st.session_state.mission

    if "mission" in st.session_state:
        st.divider()
        st.markdown(st.session_state.mission)
        st.divider()

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            if st.button("💾 저장하기", use_container_width=True):
                save_mission(st.session_state.mission)
                st.success("✅ 저장 완료!")
        with col_b:
            st.download_button(
                "📥 TXT 다운로드",
                data=st.session_state.mission,
                file_name=f"과제_{today.strftime('%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_c:
            try:
                pdf_data = generate_pdf(
                    st.session_state.mission,
                    today.strftime("%Y년 %m월 %d일")
                )
                st.download_button(
                    "📄 PDF 다운로드",
                    data=pdf_data,
                    file_name=f"과제_{today.strftime('%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.button("📄 PDF (준비중)", disabled=True, use_container_width=True)
        with col_d:
            pass

        st.divider()
        st.subheader("📋 카카오톡 복사용")
        st.code(st.session_state.mission, language=None)
    else:
        st.info("👆 버튼을 누르면 오늘의 과제가 만들어져요! 🎮")

with tab2:
    st.header("📊 이번 주 학습 리포트")
    if st.button("📊 리포트 생성", type="primary"):
        with st.spinner("분석 중... 📊"):
            report = generate_parent_report()
            st.session_state.report = report
    if "report" in st.session_state:
        st.divider()
        st.markdown(st.session_state.report)
        st.download_button(
            "📥 리포트 저장",
            data=st.session_state.report,
            file_name=f"리포트_{today.strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

with tab3:
    st.header("📁 저장된 과제 기록")
    saved_files = sorted(SAVE_DIR.glob("과제_*.txt"), reverse=True)
    if not saved_files:
        st.info("아직 저장된 과제가 없어요!")
    else:
        for file in saved_files:
            date_str = file.stem.replace("과제_", "")
            try:
                label = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일"
            except Exception:
                label = date_str
            with st.expander(f"📄 {label}"):
                with open(file, "r", encoding="utf-8") as f:
                    st.text(f.read())
