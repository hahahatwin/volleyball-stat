import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="9인제 배구 기록", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 0.95rem; }
    
    /* 기본 버튼 (오른쪽 플레이 내용 영역 등) */
    div.stButton > button:first-child { 
        height: 3.2em; font-weight: bold; font-size: 0.95rem;
        border-radius: 6px; padding: 2px 5px;
    }
    div.stButton > button[data-baseweb="button"]:focus { 
        background-color: #2e7d32; color: white; border-color: #1b5e20; 
    }
    
    /* 상단 상태 표시줄 */
    .status-box { 
        padding: 8px 15px; border-radius: 8px; background-color: #eceff1; 
        border-left: 5px solid #263238; font-size: 1.05rem;
    }
    
    /* =========================================================
       🔥 선수 명단 영역을 리얼한 배구 코트로 바꾸는 마법의 CSS 🔥
       ========================================================= */
    /* 1. 코트 바닥 배경 및 흰색 테두리 */
    div[data-testid="column"]:has(#court-start) {
        background-color: #E27D5F !important; /* 리얼한 오렌지색 코트 바닥 */
        border: 4px solid white !important;
        border-radius: 10px !important;
        padding: 15px 15px 30px 15px !important;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.15), 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* 2. 코트 안의 선수 버튼을 사진처럼 노란색 동그라미로 변경 */
    div[data-testid="column"]:has(#court-start) div.stButton > button {
        background-color: #FFC107 !important; /* 쨍한 노란색 */
        color: #111 !important; /* 검은색 글씨 */
        border-radius: 50px !important; /* 완벽한 동그라미 */
        border: 2px solid white !important; /* 흰색 테두리 */
        height: 4.5em !important; 
        font-weight: 900 !important;
        font-size: 1.05rem !important;
        box-shadow: 2px 4px 6px rgba(0,0,0,0.4) !important; /* 입체감 그림자 */
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="column"]:has(#court-start) div.stButton > button:focus {
        background-color: #E65100 !important; /* 선택 시 진한 주황/빨강으로 변경 */
        color: white !important;
        transform: scale(0.95);
    }
    
    /* 3. 코트 안 포지션 글씨 (흰색으로 눈에 띄게) */
    div[data-testid="column"]:has(#court-start) .pos-label {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        text-align: center;
        margin-bottom: 5px;
        font-size: 0.9em;
        font-weight: 900;
    }

    /* 4. 리얼한 네트 모양 */
    .volleyball-net {
        width: 100%; height: 30px; background-color: #263238;
        background-image: linear-gradient(rgba(255,255,255,0.5) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.5) 2px, transparent 2px);
        background-size: 10px 10px; border-top: 5px solid #ffffff; border-bottom: 5px solid #ffffff;
        box-shadow: 0 5px 5px rgba(0,0,0,0.3);
        margin-top: 5px; margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'log_data' not in st.session_state:
    st.session_state.log_data = []
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

if 'team_roster' not in st.session_state:
    st.session_state.team_roster = [
        "유석현", "홍순석", "이준호", "조형민", "백충석", "문기영", "이광호", "김수홍", "홍성준", "김기상",
        "이민구", "문준기", "김수현", "이웅용", "이우형", "이준익", "문원기", "박준형", "문승민", "문상록",
        "김홍무", "손효준", "이대윤", "김백현", "김준영", "명 수", "양재훈", "방기성", "김두헌", "최병주",
        "길운상", "최민규", "강대서", "김용신", "유무영", "김태영", "신정환", "이규승"
    ]

if 'lineup' not in st.session_state:
    st.session_state.lineup = {
        "레프트": st.session_state.team_roster[0], "세터": st.session_state.team_roster[1], "라이트": st.session_state.team_roster[2],
        "앞차": st.session_state.team_roster[3], "센터": st.session_state.team_roster[4], "백차": st.session_state.team_roster[5],
        "레프트백": st.session_state.team_roster[6], "센터백": st.session_state.team_roster[7], "라이트백": st.session_state.team_roster[8]
    }

with st.sidebar:
    st.header("📋 라인업 설정 (교체)")
    positions = ["레프트", "세터", "라이트", "앞차", "센터", "백차", "레프트백", "센터백", "라이트백"]
    for pos in positions:
        st.session_state.lineup[pos] = st.selectbox(
            f"{pos}", options=st.session_state.team_roster, 
            index=st.session_state.team_roster.index(st.session_state.lineup[pos]), key=f"select_{pos}"
        )

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
        st.error("⚠️ 코트에서 선수를 먼저 선택하세요!")

def undo_last():
    if st.session_state.log_data:
        st.session_state.log_data.pop()

st.title("🏐 9인제 배구 실시간 대시보드 (v8.0)")

target_col, control_col = st.columns([3, 1])
with target_col:
    player_display = st.session_state.selected_player if st.session_state.selected_player else "선택 안 됨 (코트에서 선수를 터치하세요)"
    st.markdown(f"""
        <div class="status-box">👉 <b>현재 기록 대상:</b> <span style="color:#1565c0; font-size:1.3em;">[{player_display}]</span></div>
        """, unsafe_allow_html=True)
with control_col:
    st.button("⏪ 직전 기록 취소", on_click=undo_last, use_container_width=True)

st.write("")

if st.session_state.log_data:
    df_log = pd.DataFrame(st.session_state.log_data)
    stats = []
    for p in df_log['선수'].unique():
        p_data = df_log[df_log['선수'] == p]
        atk_pts = len(p_data[(p_data['액션'] == '공격') & (p_data['결과'] == '득점')])
        blk_pts = len(p_data[(p_data['액션'] == '블로킹') & (p_data['결과'] == '득점')])
        srv_pts = len(p_data[(p_data['액션'] == '서브') & (p_data['결과'] == '득점')])
        rec_perf = len(p_data[(p_data['액션'] == '리시브') & (p_data['결과'] == '정확')])
        dig_suc = len(p_data[(p_data['액션'] == '수비') & (p_data['결과'] == '성공')])
        err_list = ['범실', '실패', '네트터치', '오버넷', '캐치볼', '더블컨택']
        tot_err = len(p_data[p_data['결과'].isin(err_list)])
        
        stats.append({
            "선수명": p, "총 득점": atk_pts + blk_pts + srv_pts, "공격 득점": atk_pts,
            "블로킹": blk_pts, "서브 득점": srv_pts, "리시브 정확": rec_perf,
            "수비 성공": dig_suc, "총 범실": tot_err
        })
    stats_df = pd.DataFrame(stats).sort_values(by="총 득점", ascending=False).reset_index(drop=True)
    
    st.subheader("🏆 선수별 실시간 스탯 현황판")
    st.dataframe(stats_df, use_container_width=True, height=180)
else:
    st.info("💡 기록을 시작하면 이곳에 실시간 선수별 스탯 현황판이 즉시 나타납니다.")

st.divider()

main_col1, main_col2 = st.columns([2, 3])

# ==========================================
# 👥 리얼 코트 명단 영역 (CSS 타겟팅용 마커 포함)
# ==========================================
with main_col1:
    # 이 span 태그가 있어야 CSS가 이 기둥(column)을 코트 모양으로 바꿉니다!
    st.markdown('<span id="court-start"></span>', unsafe_allow_html=True)
    
    # 튼튼한 네트 그림
    st.markdown('<div class="volleyball-net"></div>', unsafe_allow_html=True)
    
    row1 = st.columns(3)
    for i, pos in enumerate(["레프트", "세터", "라이트"]):
        with row1[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): st.session_state.selected_player = st.session_state.lineup[pos]
    
    st.write("") # 줄 간격
    row2 = st.columns(3)
    for i, pos in enumerate(["앞차", "센터", "백차"]):
        with row2[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): st.session_state.selected_player = st.session_state.lineup[pos]
            
    st.write("")
    row3 = st.columns(3)
    for i, pos in enumerate(["레프트백", "센터백", "라이트백"]):
        with row3[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True): st.session_state.selected_player = st.session_state.lineup[pos]

# ==========================================
# ⚡ 플레이 내용 영역
# ==========================================
with main_col2:
    st.subheader("⚡ 플레이 내용 (터치 저장)")
    curr_p = st.session_state.selected_player
    
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.write("**[서브]**")
        if st.button("🔴 서브 득점", use_container_width=True): record_action(curr_p, "서브", "득점")
        if st.button("⚪ 서브 성공", use_container_width=True): record_action(curr_p, "서브", "성공")
        if st.button("❌ 서브 범실", use_container_width=True): record_action(curr_p, "서브", "범실")
    with r1_c2:
        st.write("**[리시브]**")
        if st.button("🎯 리시브 정확", use_container_width=True): record_action(curr_p, "리시브", "정확")
        if st.button("OK 리시브 보통", use_container_width=True): record_action(curr_p, "리시브", "성공")
        if st.button("💔 리시브 실패", use_container_width=True): record_action(curr_p, "리시브", "실패")
    with r1_c3:
        st.write("**[공격]**")
        if st.button("🔥 공격 득점", use_container_width=True): record_action(curr_p, "공격", "득점")
        if st.button("❌ 공격 범실", use_container_width=True): record_action(curr_p, "공격", "범실")

    st.write("---")

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.write("**[수비 / 세트]**")
        if st.button("👐 수비 성공", use_container_width=True): record_action(curr_p, "수비", "성공")
        if st.button("⬆️ 세트 정확", use_container_width=True): record_action(curr_p, "세트", "정확")
    with r2_c2:
        st.write("**[블로킹]**")
        if st.button("🧱 블로킹 득점", use_container_width=True): record_action(curr_p, "블로킹", "득점")
        if st.button("❌ 블로킹 범실", use_container_width=True): record_action(curr_p, "블로킹", "범실")
    with r2_c3:
        st.write("**[기타 범실]**")
        err1, err2 = st.columns(2)
        with err1:
            if st.button("⚠️ 네트터치", use_container_width=True): record_action(curr_p, "범실", "네트터치")
            if st.button("⚠️ 오버넷", use_container_width=True): record_action(curr_p, "범실", "오버넷")
        with err2:
            if st.button("⚠️ 캐치볼", use_container_width=True): record_action(curr_p, "범실", "캐치볼")
            if st.button("⚠️ 더블컨택", use_container_width=True): record_action(curr_p, "범실", "더블컨택")

st.divider()

if st.session_state.log_data:
    df_log = pd.DataFrame(st.session_state.log_data)
    with st.expander("📝 시간대별 전체 기록 로그 (펼치기)"):
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_log.to_excel(writer, index=False, sheet_name='경기기록로그')
        stats_df.to_excel(writer, index=False, sheet_name='선수별요약스탯')
    
    st.download_button(
        label="📥 엑셀 파일로 경기 기록 다운로드",
        data=buffer.getvalue(),
        file_name=f"배구경기기록_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
