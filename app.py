# -*- coding: utf-8 -*-
import os
import json
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
    page_title="🏠 우리집 학습 파트너",
    page_icon="🏠",
    layout="wide"
)

client = anthropic.Anthropic(api_key=api_key)

# ── 아이 프로필 로드 ──
CHILDREN_FILE = pathlib.Path("children.json")

def load_children():
    if CHILDREN_FILE.exists():
        with open(CHILDREN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)["children"]
    return [
        {"id": "1", "name": "영인", "grade": "3", "type": "elementary", "adhd": True, "themes": ["마인크래프트", "로블록스"]},
        {"id": "2", "name": "영서", "grade": "유치원", "type": "preschool", "adhd": False, "themes": ["공룡"]}
    ]

CHILDREN = load_children()

SAVE_DIR = pathlib.Path("과제기록")
SAVE_DIR.mkdir(exist_ok=True)

for child in CHILDREN:
    (SAVE_DIR / child["name"]).mkdir(exist_ok=True)

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


def generate_pdf(mission_text, date_str, child_name):
    font_path = get_korean_font()
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Nanum", fname=font_path)

    pdf.set_fill_color(99, 179, 237)
    pdf.rect(0, 0, 210, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Nanum", size=16)
    pdf.set_y(7)
    pdf.cell(0, 10, f"  {child_name}의 학습 파트너  |  {date_str}", align="L")

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


# ── 파닉스 스케줄 (주차별 순환) ──
PHONICS_SCHEDULE = [
    {"pattern": "단모음 a (short a)", "words": ["cat", "map", "bag", "hat", "fan"], "hint": "가운데 a 소리가 '애'"},
    {"pattern": "단모음 i (short i)", "words": ["pig", "big", "hit", "sit", "win"], "hint": "가운데 i 소리가 '이'"},
    {"pattern": "장모음 a_e (magic e)", "words": ["cake", "game", "name", "make", "late"], "hint": "끝에 e가 붙으면 가운데 a가 '에이'"},
    {"pattern": "이중자음 bl, cl, fl", "words": ["black", "block", "clap", "clock", "flag"], "hint": "두 자음이 합쳐진 소리"},
    {"pattern": "이중자음 sh, ch, th", "words": ["shop", "chip", "that", "ship", "chat"], "hint": "두 글자가 하나의 소리"},
    {"pattern": "이중모음 oo", "words": ["moon", "food", "cool", "pool", "boost"], "hint": "oo = '우' 긴 소리"},
]


def generate_mission_elementary(child, level="보통", game_theme="랜덤"):
    """초등학생용 과제 생성 (파닉스 포함)"""
    today = datetime.now()
    theme = DAY_THEMES[today.weekday()]
    date_str = today.strftime("%m월 %d일")

    if today.weekday() == 6:
        return f"# 😴 오늘은 쉬는 날!\n\n{child['name']}아, 오늘은 푹 쉬어! 🎮"

    level_guide = {
        "쉬움": "아주 쉽게, 문제 1개씩만",
        "보통": "적당하게, 문제 2개씩",
        "어려움": "조금 도전적으로, 심화 문제 포함"
    }

    themes = child.get("themes", ["마인크래프트", "로블록스"])
    if game_theme == "랜덤":
        game_desc = f"{' 또는 '.join(themes)} 중 하나를 골라서"
    else:
        game_desc = f"{game_theme} 소재만 사용해서"

    adhd_note = "ADHD 아이라서 집중 시간이 짧아요. 문제마다 게임 보상 언급 필수." if child.get("adhd") else ""

    # 주차별로 파닉스 패턴 순환
    week_num = today.isocalendar()[1]
    phonics = PHONICS_SCHEDULE[week_num % len(PHONICS_SCHEDULE)]
    phonics_words = ", ".join(phonics["words"])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1800,
        system=(
            f"당신은 '레오'입니다.\n"
            f"초등학교 {child['grade']}학년 아이 '{child['name']}'의 AI 학습 친구예요.\n"
            f"{adhd_note}\n\n"
            f"[과제 만들기 규칙]\n"
            f"- 총 35분 이내 끝낼 수 있는 양 ({level_guide[level]})\n"
            f"- {game_desc} 모든 문제를 포장하기\n"
            f"- 구성: 🔤 파닉스 -> 🎮 영어 -> ➕ 수학 -> ✏️ 국어 -> 🎁 보너스 순서\n\n"
            f"[🔤 파닉스 섹션 규칙]\n"
            f"- 오늘의 파닉스 패턴: {phonics['pattern']}\n"
            f"- 연습 단어: {phonics_words}\n"
            f"- 힌트: {phonics['hint']}\n"
            f"- 활동 1: 단어 읽기 + 한국어 뜻 맞추기 (3개)\n"
            f"- 활동 2: 빈칸 채우기 문제 1개 (예: c__t = cat)\n"
            f"- 활동 3: 게임 소재로 그 패턴 단어 만들기 1개\n\n"
            f"[🎮 영어 섹션 규칙]\n"
            f"- 게임 관련 단어 2개 + 짧은 문장 만들기\n\n"
            f"[➕ 수학 섹션 규칙]\n"
            f"- 게임 스토리 속 계산 문제\n\n"
            f"[✏️ 국어 섹션 규칙]\n"
            f"- 딱 3줄 글쓰기 (부담 없게)\n\n"
            f"[🎁 보너스]\n"
            f"- 게임하면서 할 수 있는 미션\n\n"
            f"[게임 소재]\n"
            f"- 마인크래프트: 크리퍼, 다이아몬드, 엔더드래곤, 레드스톤\n"
            f"- 로블록스: Adopt Me, Blox Fruits, Brookhaven, Jailbreak, 로벅스\n\n"
            f"[말투 규칙]\n"
            f"- 친구처럼 반말, 이모지 풍부하게\n"
            f"- 틀려도 괜찮다는 말 꼭 포함\n"
            f"- 마지막에 짧은 응원 메시지"
        ),
        messages=[{
            "role": "user",
            "content": f"오늘은 {date_str} {theme}이야! {child['name']}이를 위한 오늘의 과제 만들어줘!"
        }]
    )
    return response.content[0].text


def generate_mission_preschool(child, level="보통"):
    """유치원생용 과제 생성"""
    today = datetime.now()
    date_str = today.strftime("%m월 %d일")

    if today.weekday() == 6:
        return f"# 😴 오늘은 쉬는 날!\n\n{child['name']}아, 오늘은 신나게 놀아! 🦕"

    level_guide = {
        "쉬움": "아주 간단하게, 놀이 1개씩",
        "보통": "적당하게, 활동 2개씩",
        "어려움": "조금 더 도전적으로"
    }

    themes = child.get("themes", ["공룡"])
    theme_str = ", ".join(themes)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1200,
        system=(
            f"당신은 유치원생 '{child['name']}'의 다정한 AI 놀이 친구예요.\n"
            f"{child['name']}이는 {theme_str}을(를) 정말 좋아해요.\n\n"
            f"[활동 만들기 규칙]\n"
            f"- 총 15분 이내 끝낼 수 있는 양 ({level_guide[level]})\n"
            f"- {theme_str} 테마로 모든 활동 포장\n"
            f"- 구성: 한글 놀이 -> 수 놀이 -> 만들기/그리기 -> 보너스\n"
            f"- 한글 놀이: 자음/모음 1~2개, 그림과 함께 (예: ㄱ - 기린)\n"
            f"- 수 놀이: 1~10 숫자 세기, 모양 찾기, 색깔 맞추기\n"
            f"- 만들기/그리기: 손으로 할 수 있는 쉬운 미션\n"
            f"- 보너스: 엄마/아빠와 함께하는 미션 1개\n\n"
            f"[말투 규칙]\n"
            f"- 아주 쉽고 짧은 문장 (유치원생 눈높이)\n"
            f"- 이모지 많이 사용 🦕🌟\n"
            f"- 칭찬과 응원 가득\n"
            f"- '할 수 있어!' '잘했어!' 자주 사용"
        ),
        messages=[{
            "role": "user",
            "content": f"오늘은 {date_str}이야! {child['name']}이를 위한 오늘의 놀이 활동 만들어줘!"
        }]
    )
    return response.content[0].text


def generate_mission(child, level="보통", game_theme="랜덤"):
    if child["type"] == "preschool":
        return generate_mission_preschool(child, level)
    else:
        return generate_mission_elementary(child, level, game_theme)


def save_mission(mission_text, child_name):
    today = datetime.now().strftime("%Y%m%d")
    filepath = SAVE_DIR / child_name / f"과제_{today}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"날짜: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        f.write("="*40 + "\n\n")
        f.write(mission_text)
    return filepath


def generate_parent_report(child_name):
    child_dir = SAVE_DIR / child_name
    records = []
    for file in sorted(child_dir.glob("과제_*.txt"))[-7:]:
        with open(file, "r", encoding="utf-8") as f:
            records.append(f.read())

    if not records:
        return f"아직 {child_name}의 저장된 과제 기록이 없어요. 먼저 과제를 생성하고 저장해 주세요!"

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1000,
        system=(
            "당신은 교육 전문가입니다.\n"
            "아이의 학습 기록을 분석해서 부모님께\n"
            "따뜻하고 격려가 되는 주간 리포트를 작성해주세요.\n"
            "포함 내용: 이번 주 학습 요약, 잘한 점, 다음 주 추천 방향, 부모님 팁 1가지\n"
            "말투: 따뜻하고 전문적으로"
        ),
        messages=[{
            "role": "user",
            "content": f"아이 이름: {child_name}\n\n최근 학습 기록:\n\n" + "\n\n---\n\n".join(records)
        }]
    )
    return response.content[0].text


# ── UI ──
today = datetime.now()
weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

st.title("🏠 우리집 학습 파트너")
st.caption(
    f"오늘은 {today.strftime('%Y년 %m월 %d일')} "
    f"{weekday_names[today.weekday()]}요일 | "
    f"{DAY_THEMES[today.weekday()]}"
)

child_tabs = st.tabs([f"{'🎮' if c['type']=='elementary' else '🦕'} {c['name']}" for c in CHILDREN])

for idx, (child_tab, child) in enumerate(zip(child_tabs, CHILDREN)):
    with child_tab:
        is_preschool = child["type"] == "preschool"

        col_main, col_side = st.columns([4, 1])

        with col_side:
            st.markdown("**⚙️ 설정**")
            level = st.radio(
                "난이도",
                ["쉬움", "보통", "어려움"],
                index=1,
                key=f"level_{idx}",
                horizontal=False
            )
            if not is_preschool:
                theme_options = ["랜덤"] + child.get("themes", [])
                game_theme = st.radio(
                    "게임 소재",
                    theme_options,
                    index=0,
                    key=f"theme_{idx}"
                )
            else:
                game_theme = "랜덤"

            st.divider()
            st.markdown("**📅 이번 주 완료**")
            for i, day in enumerate(["월","화","수","목","금","토","일"]):
                st.checkbox(f"{day}", key=f"day_{idx}_{i}")

        with col_main:
            col1, col2 = st.columns([3, 1])
            with col1:
                btn_label = "🦕 오늘 활동 만들기!" if is_preschool else "🎮 오늘 과제 만들기!"
                if st.button(btn_label, type="primary", use_container_width=True, key=f"gen_{idx}"):
                    with st.spinner("만들고 있어요... 🤔✨"):
                        mission = generate_mission(child, level, game_theme)
                        st.session_state[f"mission_{idx}"] = mission

            with col2:
                if st.button("🔄 다시 만들기", use_container_width=True, key=f"regen_{idx}"):
                    if f"mission_{idx}" in st.session_state:
                        del st.session_state[f"mission_{idx}"]

            mission_key = f"mission_{idx}"
            if mission_key in st.session_state:
                st.divider()
                st.markdown(st.session_state[mission_key])
                st.divider()

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("💾 저장하기", use_container_width=True, key=f"save_{idx}"):
                        save_mission(st.session_state[mission_key], child["name"])
                        st.success("✅ 저장 완료!")
                with col_b:
                    st.download_button(
                        "📥 TXT",
                        data=st.session_state[mission_key],
                        file_name=f"{child['name']}_과제_{today.strftime('%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"dl_txt_{idx}"
                    )
                with col_c:
                    try:
                        pdf_data = generate_pdf(
                            st.session_state[mission_key],
                            today.strftime("%Y년 %m월 %d일"),
                            child["name"]
                        )
                        st.download_button(
                            "📄 PDF",
                            data=pdf_data,
                            file_name=f"{child['name']}_과제_{today.strftime('%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"dl_pdf_{idx}"
                        )
                    except Exception as e:
                        st.error(f"PDF 오류: {e}")

                st.divider()
                st.subheader("📋 카카오톡 복사용")
                st.code(st.session_state[mission_key], language=None)
            else:
                emoji = "🦕" if is_preschool else "🎮"
                st.info(f"👆 버튼을 누르면 {child['name']}이의 오늘 {'활동' if is_preschool else '과제'}이 만들어져요! {emoji}")

        st.divider()
        rep_col, rec_col = st.columns(2)

        with rep_col:
            st.subheader("📊 주간 리포트")
            if st.button("리포트 생성", key=f"report_btn_{idx}", type="primary"):
                with st.spinner("분석 중..."):
                    report = generate_parent_report(child["name"])
                    st.session_state[f"report_{idx}"] = report
            if f"report_{idx}" in st.session_state:
                st.markdown(st.session_state[f"report_{idx}"])
                st.download_button(
                    "📥 저장",
                    data=st.session_state[f"report_{idx}"],
                    file_name=f"{child['name']}_리포트_{today.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    key=f"dl_report_{idx}"
                )

        with rec_col:
            st.subheader("📁 과제 기록")
            child_dir = SAVE_DIR / child["name"]
            saved_files = sorted(child_dir.glob("과제_*.txt"), reverse=True)
            if not saved_files:
                st.info("아직 저장된 기록이 없어요!")
            else:
                for file in saved_files[:5]:
                    date_str = file.stem.replace("과제_", "")
                    try:
                        label = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일"
                    except Exception:
                        label = date_str
                    with st.expander(f"📄 {label}"):
                        with open(file, "r", encoding="utf-8") as f:
                            st.text(f.read())
