import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="9인제 배구 기록", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  { font-size: 1.1rem; }
    div.stButton > button:first-child { height: 4em; font-weight: bold; border-radius: 8px; }
    div.stButton > button[data-baseweb="button"]:focus { background-color: #2e7d32; color: white; border-color: #1b5e20; }
    .status-box { padding: 15px; border-radius: 10px; background-color: #eceff1; margin-bottom: 20px; border-left: 5px solid #263238; }
    </style>
    """, unsafe_allow_html=True)

# 1. 초기 데이터 설정
if 'log_data' not in st.session_state:
    st.session_state.log_data = []
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

# 팀 전체 명단 (이곳에 팀원 이름을 쭉 적어두면 됩니다)
if 'team_roster' not in st.session_state:
    st.session_state.team_roster = ["김철수", "이영희", "박지민", "최동훈", "정수진", "강민호", "윤서연", "조현우", "임지영", "후보1", "후보2", "후보3", "후보4"]

# 현재 코트 위 9명 포지션 매칭
if 'lineup' not in st.session_state:
    st.session_state.lineup = {
        "전위 좌": st.session_state.team_roster[0], "전위 중": st.session_state.team_roster[1], "전위 우": st.session_state.team_roster[2],
        "중위 좌": st.session_state.team_roster[3], "중위 중": st.session_state.team_roster[4], "중위 우": st.session_state.team_roster[5],
        "후위 좌": st.session_state.team_roster[6], "후위 중": st.session_state.team_roster[7], "후위 우": st.session_state.team_roster[8]
    }

# 2. 사이드바: 라인업 및 교체 관리
with st.sidebar:
    st.header("📋 현재 코트 라인업 (교체)")
    st.write("세트 시작 전이나 교체 시 선수를 변경하세요.")
    
    # 9개 포지션에 대해 드롭다운(선택창) 생성
    positions = ["전위 좌", "전위 중", "전위 우", "중위 좌", "중위 중", "중위 우", "후위 좌", "후위 중", "후위 우"]
    for pos in positions:
        st.session_state.lineup[pos] = st.selectbox(
            f"{pos}", 
            options=st.session_state.team_roster, 
            index=st.session_state.team_roster.index(st.session_state.lineup[pos]),
            key=f"select_{pos}"
        )
    
    st.divider()
    st.write("💡 여기서 선수를 변경하면 우측 코트 버튼 이름이 즉시 바뀝니다.")

# 3. 로직 함수
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

# --- 메인 화면 시작 ---
st.title("🏐 9인제 배구 실시간 대시보드 (v4.0)")

target_col, control_col = st.columns([3, 1])
with target_col:
    player_display = st.session_state.selected_player if st.session_state.selected_player else "선택 안 됨 (선수를 터치하세요)"
    st.markdown(f"""
        <div class="status-box">👉 <b>현재 기록 대상:</b> <span style="color:#1565c0; font-size:1.4em;">[{player_display}]</span></div>
        """, unsafe_allow_html=True)
with control_col:
    st.button("⏪ 직전 기록 취소", on_click=undo_last, use_container_width=True)

main_col1, main_col2 = st.columns([2, 3])

# 4. 선수 선택 영역 (사이드바에서 설정한 라인업 이름으로 버튼 생성)
with main_col1:
    st.subheader("👥 9인제 코트")
    
    row1 = st.columns(3)
    for i, pos in enumerate(["전위 좌", "전위 중", "전위 우"]):
        with row1[i]:
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): 
                st.session_state.selected_player = st.session_state.lineup[pos]

    row2 = st.columns(3)
    for i, pos in enumerate(["중위 좌", "중위 중", "중위 우"]):
        with row2[i]:
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): 
                st.session_state.selected_player = st.session_state.lineup[pos]

    row3 = st.columns(3)
    for i, pos in enumerate(["후위 좌", "후위 중", "후위 우"]):
        with row3[i]:
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): 
                st.session_state.selected_player = st.session_state.lineup[pos]

# 5. 액션 및 결과 영역 (이전과 동일)
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

st.divider()

# 6. 통계 요약 및 엑셀 다운로드
if st.session_state.log_data:
    df_log = pd.DataFrame(st.session_state.log_data)
    
    st.subheader("📈 현재 경기 기록 요약")
    attack_data = df_log[df_log['액션'] == '공격']
    total_attacks = len(attack_data)
    attack_points = len(attack_data[attack_data['결과'] == '득점'])
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("총 공격 시도", f"{total_attacks}회")
    col_b.metric("공격 득점", f"{attack_points}점")
    if total_attacks > 0:
        success_rate = round((attack_points / total_attacks) * 100, 1)
        col_c.metric("팀 공격 성공률", f"{success_rate}%")
    
    st.write("---")
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_log.to_excel(writer, index=False, sheet_name='경기기록')
    
    st.download_button(
        label="📥 엑셀 파일로 경기 기록 다운로드",
        data=buffer.getvalue(),
        file_name=f"배구경기기록_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
