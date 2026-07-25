import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
import os
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="9인제 배구 기록", layout="wide")

# ==========================================
# ☁️ 구글 시트 연결 셋업
# ==========================================
@st.cache_resource
def init_gsheets():
    try:
        key_dict = json.loads(st.secrets["google_credentials"])
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

# ==========================================
# 🎨 UI 디자인 스타일 적용 (선택된 선수 강조 포함)
# ==========================================
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 0.95rem; }
    
    section[data-testid="stSidebar"] { width: 220px !important; min-width: 220px !important; }
    
    /* 오른쪽 플레이 액션 버튼 (회색) */
    div.stButton > button[kind="secondary"] { 
        height: 3.2em; font-weight: bold; font-size: 0.95rem;
        border-radius: 6px; padding: 2px 2px;
        background-color: #f8f9fa; border: 1px solid #cfd8dc; color: #263238;
    }
    div.stButton > button[kind="secondary"]:focus { 
        background-color: #e0f2f1; color: #004d40; border-color: #00695c; 
    }
    
    /* 🔥 1. 기본 코트 선수 버튼 (노란색) */
    div.stButton > button[kind="primary"] {
        background-color: #FFC107 !important; 
        color: #111111 !important; 
        border-radius: 60px !important; 
        border: 2px solid #eeeeee !important; 
        height: 85px !important; 
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"] p {
        font-size: 2.8rem !important; /* 이름 2/3 꽉 차게 원상복구! */
        font-weight: 900 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 🔥 2. 선택된 코트 선수 버튼 (다홍색/빨간색으로 변신!) */
    div.stButton > button[kind="tertiary"] {
        background-color: #FF5722 !important; /* 튀는 다홍색 */
        color: #ffffff !important; /* 하얀색 글씨 */
        border-radius: 60px !important; 
        border: 4px solid #ffffff !important; 
        height: 85px !important; 
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0px 0px 15px rgba(255, 87, 34, 0.6) !important; /* 빛나는 그림자 */
        transform: scale(1.03); /* 선택 시 살짝 커지는 효과 */
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="tertiary"] p {
        font-size: 2.8rem !important; 
        font-weight: 900 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .status-box { 
        padding: 8px 15px; border-radius: 8px; background-color: #eceff1; 
        border-left: 5px solid #263238; font-size: 1.05rem;
    }
    .pos-label { 
        font-size: 0.95em; color: #37474f; margin-bottom: -3px; 
        font-weight: 900; text-align: center;
    }

    /* 네트 아트 */
    .net-container {
        position: relative; width: 100%; height: 60px;
        margin-top: 10px; margin-bottom: 30px;
    }
    .net-pole-left, .net-pole-right {
        position: absolute; top: 0; width: 6px; height: 80px;
        background-color: #90a4ae; border-radius: 2px;
    }
    .net-pole-left { left: 0; }
    .net-pole-right { right: 0; }
    
    .net-mesh {
        position: absolute; top: 10px; left: 6px; right: 6px; height: 40px;
        background-color: transparent;
        background-image: linear-gradient(#455a64 1px, transparent 1px), linear-gradient(90deg, #455a64 1px, transparent 1px);
        background-size: 12px 12px;
        border-top: 6px solid #ffffff; border-bottom: 2px solid #ffffff;
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 📊 상태 관리 및 명단 설정 (명단 자동 저장 기능 추가)
# ==========================================
LINEUP_FILE = "saved_lineup.json"

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

# 처음 접속 시 저장된 명단 파일이 있으면 불러오기
if 'lineup' not in st.session_state:
    default_lineup = {
        "레프트": st.session_state.team_roster[0], "세터": st.session_state.team_roster[1], "라이트": st.session_state.team_roster[2],
        "앞차": st.session_state.team_roster[3], "센터": st.session_state.team_roster[4], "백차": st.session_state.team_roster[5],
        "레프트백": st.session_state.team_roster[6], "센터백": st.session_state.team_roster[7], "라이트백": st.session_state.team_roster[8]
    }
    
    if os.path.exists(LINEUP_FILE):
        try:
            with open(LINEUP_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 저장된 명단 중 로스터에 있는 이름만 적용
            for k in default_lineup.keys():
                if k in saved and saved[k] in st.session_state.team_roster:
                    default_lineup[k] = saved[k]
        except Exception:
            pass
            
    st.session_state.lineup = default_lineup

# 라인업이 바뀔 때마다 파일에 자동 저장하는 함수
def update_lineup_file():
    with open(LINEUP_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.lineup, f, ensure_ascii=False)

with st.sidebar:
    st.header("📋 라인업(교체)")
    positions = ["레프트", "세터", "라이트", "앞차", "센터", "백차", "레프트백", "센터백", "라이트백"]
    for pos in positions:
        # 셀렉트박스를 변경할 때마다 update_lineup_file 함수가 실행되어 영구 저장됨
        st.session_state.lineup[pos] = st.selectbox(
            f"{pos}", options=st.session_state.team_roster, 
            index=st.session_state.team_roster.index(st.session_state.lineup[pos]), 
            key=f"select_{pos}", on_change=update_lineup_file
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

st.title("🏐 9인제 배구 실시간 대시보드")

target_col, control_col = st.columns([4, 1])
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
    
    st.subheader("🏆 실시간 스탯")
    st.dataframe(stats_df, use_container_width=True, height=150)
else:
    stats_df = pd.DataFrame()
    st.info("💡 기록을 시작하면 이곳에 실시간 스탯 현황판이 나타납니다.")

st.divider()

main_col1, main_col2 = st.columns([35, 65])

# ==========================================
# 👥 코트 명단 영역 (비율 35%)
# ==========================================
with main_col1:
    st.subheader("👥 코트 명단")
    
    st.markdown("""
        <div class="net-container">
            <div class="net-pole-left"></div>
            <div class="net-mesh"></div>
            <div class="net-pole-right"></div>
        </div>
    """, unsafe_allow_html=True)
    
    row1 = st.columns(3)
    for i, pos in enumerate(["레프트", "세터", "라이트"]):
        with row1[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            # 선택된 선수면 다홍색(tertiary) 버튼으로, 아니면 기본 노란색(primary) 버튼으로 렌더링
            btn_type = "tertiary" if st.session_state.selected_player == st.session_state.lineup[pos] else "primary"
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True, type=btn_type): 
                st.session_state.selected_player = st.session_state.lineup[pos]
                st.rerun() # 터치 시 즉시 색상 반영을 위해 리런
    
    st.write("")
    row2 = st.columns(3)
    for i, pos in enumerate(["앞차", "센터", "백차"]):
        with row2[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            btn_type = "tertiary" if st.session_state.selected_player == st.session_state.lineup[pos] else "primary"
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True, type=btn_type): 
                st.session_state.selected_player = st.session_state.lineup[pos]
                st.rerun()
            
    st.write("")
    row3 = st.columns(3)
    for i, pos in enumerate(["레프트백", "센터백", "라이트백"]):
        with row3[i]:
            st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
            btn_type = "tertiary" if st.session_state.selected_player == st.session_state.lineup[pos] else "primary"
            if st.button(st.session_state.lineup[pos], key=f"btn_{pos}", use_container_width=True, type=btn_type): 
                st.session_state.selected_player = st.session_state.lineup[pos]
                st.rerun()

# ==========================================
# ⚡ 플레이 내용 영역 (비율 65%)
# ==========================================
with main_col2:
    st.subheader("⚡ 플레이 내용")
    curr_p = st.session_state.selected_player
    
    act_c1, act_c2, act_c3, act_c4, act_c5 = st.columns(5)
    
    with act_c1:
        st.write("**[서브]**")
        if st.button("🔴 서브 득점", use_container_width=True): record_action(curr_p, "서브", "득점")
        if st.button("⚪ 서브 성공", use_container_width=True): record_action(curr_p, "서브", "성공")
        if st.button("❌ 서브 범실", use_container_width=True): record_action(curr_p, "서브", "범실")
        
    with act_c2:
        st.write("**[리시브]**")
        if st.button("🎯 리시브 정확", use_container_width=True): record_action(curr_p, "리시브", "정확")
        if st.button("OK 리시브 보통", use_container_width=True): record_action(curr_p, "리시브", "성공")
        if st.button("💔 리시브 실패", use_container_width=True): record_action(curr_p, "리시브", "실패")
        
    with act_c3:
        st.write("**[공격]**")
        if st.button("🔥 공격 득점", use_container_width=True): record_action(curr_p, "공격", "득점")
        if st.button("❌ 공격 범실", use_container_width=True): record_action(curr_p, "공격", "범실")
        st.write("**[블로킹]**")
        if st.button("🧱 블로킹 득점", use_container_width=True): record_action(curr_p, "블로킹", "득점")
        if st.button("❌ 블로킹 범실", use_container_width=True): record_action(curr_p, "블로킹", "범실")

    with act_c4:
        st.write("**[수비/세트]**")
        if st.button("👐 수비 성공", use_container_width=True): record_action(curr_p, "수비", "성공")
        if st.button("⬆️ 세트 정확", use_container_width=True): record_action(curr_p, "세트", "정확")

    with act_c5:
        st.write("**[기타 범실]**")
        if st.button("⚠️ 네트터치", use_container_width=True): record_action(curr_p, "범실", "네트터치")
        if st.button("⚠️ 오버넷", use_container_width=True): record_action(curr_p, "범실", "오버넷")
        if st.button("⚠️ 캐치볼", use_container_width=True): record_action(curr_p, "범실", "캐치볼")
        if st.button("⚠️ 더블컨택", use_container_width=True): record_action(curr_p, "범실", "더블컨택")

st.divider()

# ==========================================
# ☁️ 구글 시트 백업 및 엑셀 다운로드 영역
# ==========================================
st.subheader("💾 데이터 저장")
st.write("경기가 끝나거나 중간 백업이 필요할 때 아래 버튼을 누르면 구글 시트에 기록이 안전하게 저장됩니다.")

col_save1, col_save2 = st.columns(2)

with col_save1:
    if st.button("☁️ 구글 시트로 현재까지의 기록 백업하기", use_container_width=True, type="primary"):
        if st.session_state.log_data:
            with st.spinner("구글 시트에 데이터를 저장하는 중입니다..."):
                client = init_gsheets()
                if client:
                    try:
                        sheet_name = "배구경기기록"
                        sheet = client.open(sheet_name).sheet1
                        sheet.clear()
                        sheet.update([df_log.columns.values.tolist()] + df_log.values.tolist())
                        st.success(f"✅ 구글 시트('{sheet_name}')에 기록이 완벽하게 백업되었습니다!")
                    except Exception as e:
                        st.error(f"❌ 구글 시트 저장 실패: 스프레드시트 이름이 '{sheet_name}'이(가) 맞는지, 봇 계정에 편집자 권한을 주셨는지 확인하세요. (상세에러: {e})")
                else:
                    st.error("❌ 구글 시트 연결을 위한 열쇠(Secrets) 설정에 문제가 있습니다.")
        else:
            st.warning("⚠️ 아직 기록된 데이터가 없습니다.")

with col_save2:
    if st.session_state.log_data:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_log.to_excel(writer, index=False, sheet_name='경기기록로그')
            stats_df.to_excel(writer, index=False, sheet_name='선수별요약스탯')
        
        st.download_button(
            label="📥 엑셀 파일로 바로 다운로드",
            data=buffer.getvalue(),
            file_name=f"배구경기기록_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button("📥 엑셀 파일로 바로 다운로드", disabled=True, use_container_width=True)

if st.session_state.log_data:
    with st.expander("📝 시간대별 전체 기록 로그 (펼치기)"):
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
