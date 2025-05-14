import streamlit as st
import pandas as pd
import os

# 상태 초기화
if "trigger" not in st.session_state:
    st.session_state.trigger = False

@st.cache_data
def load_data():
    return pd.read_csv("restaurants_with_region.csv")

df = load_data()

def trigger_prediction():
    st.session_state.trigger = True

def save_feedback(menu, 식당명, 만족도, 의견):
    feedback_df = pd.DataFrame([{
        "메뉴": menu,
        "식당명": 식당명,
        "만족도": 만족도,
        "의견": 의견
    }])
    file = "feedback_log.csv"
    if os.path.exists(file):
        feedback_df.to_csv(file, mode="a", header=False, index=False)
    else:
        feedback_df.to_csv(file, index=False)

st.title("🍱 메뉴 추천 MVP")

# --- 조건 기반 자동 추천 UI ---
auto_mode = st.radio("추천 방식 선택", ["수동 입력", "조건 기반 추천"])

menu = ""
if auto_mode == "조건 기반 추천":
    taste = st.selectbox("맛 유형", ["매콤", "담백", "시원"])
    style = st.selectbox("식사 형태", ["국물", "밥", "면"])

    # 조건에 따라 메뉴 자동 선택
    if taste == "매콤" and style == "밥":
        menu = "제육볶음"
    elif taste == "매콤" and style == "국물":
        menu = "부대찌개"
    elif taste == "담백" and style == "면":
        menu = "물냉면"
    elif taste == "시원" and style == "국물":
        menu = "된장찌개"
    else:
        menu = "비빔밥"

    st.info(f"자동 추천된 메뉴: {menu}")

else:
    category_mode = st.radio("카테고리로 추천받을까요?", ["선택 안 함", "사용"])
    category_to_menu = {
        "따뜻한 국물": ["김치찌개", "순두부찌개", "부대찌개"],
        "매콤한 맛": ["제육볶음", "쭈꾸미볶음", "마라탕"],
        "가벼운 식사": ["비빔밥", "물냉면"],
        "고기 푸짐한": ["제육볶음", "갈비탕"]
    }

    if category_mode == "사용":
        category = st.radio("카테고리를 골라주세요", list(category_to_menu.keys()))
        recommended = category_to_menu[category]
        menu = st.selectbox("추천 메뉴 중에서 선택하세요", recommended)
    else:
        menu = st.text_input("먹고 싶은 메뉴를 직접 입력하세요", placeholder="예: 제육볶음")

region = st.selectbox("지역을 선택하세요", df["지역"].unique())
priority = st.radio("어떤 기준을 가장 중요하게 생각하세요?", ("가성비", "맛", "양"))

if st.button("추천 받기"):
    st.session_state.trigger = True

# 추천 실행
if st.session_state.trigger and menu:
    st.session_state.trigger = False

    filtered = df[(df["메뉴"] == menu) & (df["지역"] == region)]

    if not filtered.empty:
        keywords = {
            "양 많": 0.3, "불향": 0.2, "밑반찬": 0.1,
            "고기 부드러움": 0.2, "건더기 많음": 0.2,
            "국물 진함": 0.2, "햄 푸짐": 0.2
        }

        def calc_bonus(review):
            return sum(b for k, b in keywords.items() if k in review)

        filtered["가산점"] = filtered["요약"].apply(calc_bonus)

        if priority == "가성비":
            filtered["최종점수"] = (filtered["평점"] + filtered["가산점"]) / filtered["가격"] * 1000
        elif priority == "맛":
            filtered["최종점수"] = filtered["평점"]
        elif priority == "양":
            filtered["최종점수"] = filtered["가산점"]

        filtered = filtered.sort_values("최종점수", ascending=False)

        st.subheader(f"'{region}' 지역 '{menu}' 추천 결과 ({priority} 기준) 🍽️")

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for i, (_, row) in enumerate(filtered.iterrows(), 1):
            with st.container():
                if i == 1:
                    image_path = f"images/{row['메뉴']}.jpg"
                    if os.path.exists(image_path):
                        st.image(image_path, width=200, caption=f"{row['메뉴']} 대표 이미지")
                medal = medals.get(i, f"{i}위")
                st.markdown(f"""
                ### {medal} {i}위. {row['식당명']}
                - 메뉴: **{row['메뉴']}**
                - 지역: **{row['지역']}**
                - 가격: **{int(row['가격'])}원**
                - 평점: ⭐ {row['평점']}
                - 가산점: ➕ {row['가산점']}
                - 최종점수: {round(row['최종점수'], 2)}
                - 요약: _"{row['요약']}"_
                ---
                """)

                with st.form(key=f"feedback_form_{i}"):
                    st.markdown("**이 추천이 어땠나요?**")
                    rating = st.radio("만족도", ["좋아요", "별로예요"], key=f"rate_{i}")
                    comment = st.text_input("한 줄 의견 (선택)", key=f"comment_{i}")
                    submitted = st.form_submit_button("제출")

                    if submitted:
                        save_feedback(row["메뉴"], row["식당명"], rating, comment)
                        st.success("피드백 감사합니다!")
    else:
        st.warning("해당 지역에 해당 메뉴 식당이 없습니다.")
elif st.session_state.trigger and not menu:
    st.warning("메뉴를 입력하거나 선택해주세요.")
    st.session_state.trigger = False
