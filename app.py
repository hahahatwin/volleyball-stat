import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="9인제 배구 기록", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  { font-size: 1.1rem; }
    div.stButton > button:first-child { height: 4em; font-weight: bold; border-radius: 8px; }
    div.stButton > button[data-baseweb="button"]:focus { background-color: #2e7d32; color: white; border-color: #1b5e20; }
    .status-box { padding: 15px; border-radius: 10px; background-color: #eceff1; margin-bottom: 20px; border-left: 5px solid #263238; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏐 9인제 배구 실시간 대시보드")

# 2. 데이터 초기화
if 'log_data' not in st.session_state:
    st.session_state.log_data = []
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

# 기록 저장 함수
def record_action(player, action_name, result_name):
    if player:
        new_log = {
            "시간": datetime.now().strftime("%H:%M:%S"),
            "선수": player,
            "액션": action_name,
            "결과": result_name
        }
        st.session_state.log_data.append(new_log)
        st.session_state.selected_player = None 
    else:
        st.error("⚠️ 왼쪽에 선수를 먼저 터치해주세요!")

def undo_last():
    if st.session_state.log_data:
        st.session_state.log_data.pop()

# 상단 상태 표시줄
target_col, control_col = st.columns([3, 1])
with target_col:
    player_display = st.session_state.selected_player if st.session_state.selected_player else "선택 안 됨 (선수를 터치하세요)"
    st.markdown(f"""
        <div class="status-box">👉 <b>현재 기록 대상:</b> <span style="color:#1565c0; font-size:1.4em;">[{player_display}]</span></div>
        """, unsafe_allow_html=True)
with control_col:
    st.button("⏪ 직전 기록 취소", on_click=undo_last, use_container_width=True)

# 메인 대시보드
main_col1, main_col2 = st.columns([2, 3])

# 3. 선수 선택 영역 (9인제 3x3 코트 배치)
with main_col1:
    st.subheader("👥 9인제 코트 (선수 선택)")
    
    # 3줄로 나누어 실제 코트처럼 배치합니다. (이름은 나중에 수정 가능합니다)
    row1 = st.columns(3)
    with row1[0]: 
        if st.button("전위 좌", use_container_width=True): st.session_state.selected_player = "전위 좌"
    with row1[1]: 
        if st.button("전위 중", use_container_width=True): st.session_state.selected_player = "전위 중"
    with row1[2]: 
        if st.button("전위 우", use_container_width=True): st.session_state.selected_player = "전위 우"

    row2 = st.columns(3)
    with row2[0]: 
        if st.button("중위 좌", use_container_width=True): st.session_state.selected_player = "중위 좌"
    with row2[1]: 
        if st.button("중위 중", use_container_width=True): st.session_state.selected_player = "중위 중"
    with row2[2]: 
        if st.button("중위 우", use_container_width=True): st.session_state.selected_player = "중위 우"

    row3 = st.columns(3)
    with row3[0]: 
        if st.button("후위 좌", use_container_width=True): st.session_state.selected_player = "후위 좌"
    with row3[1]: 
        if st.button("후위 중", use_container_width=True): st.session_state.selected_player = "후위 중"
    with row3[2]: 
        if st.button("후위 우", use_container_width=True): st.session_state.selected_player = "후위 우"

# 4. 액션 및 결과 영역
with main_col2:
    st.subheader("⚡ 액션 터치 (즉시 저장)")
    curr_p = st.session_state.selected_player

    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        st.write("**[서브]**")
        if st.button("🔴 서브 득점", use_container_width=True): record_action(curr_p, "서브", "득점")
        if st.button("⚪ 서브 성공", use_container_width=True): record_action(curr_p, "서브", "성공")
        if st.button("❌ 서브 범실", use_container_width=True): record_action(curr_p, "서브", "범실")
    with r1_col2:
        st.write("**[리시브]**")
        if st.button("🎯 리시브 정확", use_container_width=True): record_action(curr_p, "리시브", "정확")
        if st.button("OK 리시브 보통", use_container_width=True): record_action(curr_p, "리시브", "성공")
        if st.button("💔 리시브 실패", use_container_width=True): record_action(curr_p, "리시브", "실패")

    st.write("---")
    
    r2_col1, r2_col2 = st.columns(2)
    with r2_col1:
        st.write("**[공격]**")
        if st.button("🔥 공격 득점", use_container_width=True): record_action(curr_p, "공격", "득점")
        if st.button("❌ 공격 범실", use_container_width=True): record_action(curr_p, "공격", "범실")
    with r2_col2:
        st.write("**[수비 / 토스]**")
        if st.button("👐 수비 성공", use_container_width=True): record_action(curr_p, "수비", "성공")
        if st.button("⬆️ 세트 정확", use_container_width=True): record_action(curr_p, "세트", "정확")

# 5. 실시간 로그
st.divider()
if st.session_state.log_data:
    st.write("📊 **실시간 경기 로그 (최신순)**")
    df_log = pd.DataFrame(st.session_state.log_data)
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
