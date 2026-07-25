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
# 🎨 UI 디자인 스타일 적용
# ==========================================
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 0.95rem; }
    section[data-testid="stSidebar"] { width: 220px !important; min-width: 220px !important; }
    
    div.stButton > button[kind="secondary"] { 
        height: 3.2em; font-weight: bold; font-size: 0.95rem;
        border-radius: 6px; padding: 2px 2px;
        background-color: #f8f9fa; border: 1px solid #cfd8dc; color: #263238;
    }
    div.stButton > button[kind="secondary"]:focus { 
        background-color: #e0f2f1; color: #004d40; border-color: #00695c; 
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #FFC107 !important; color: #111111 !important; 
        border-radius: 60px !important; border: 2px solid #eeeeee !important; 
        height: 85px !important; width: 100% !important;
        display: flex !important; justify-content: center !important; align-items: center !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2) !important; transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"] p {
        font-size: 2.8rem !important; font-weight: 900 !important; line-height: 1 !important; margin: 0 !important; padding: 0 !important;
    }

    div.stButton > button[kind="tertiary"] {
        background-color: #FF5722 !important; color: #ffffff !important; 
        border-radius: 60px !important; border: 4px solid #ffffff !important; 
        height: 85px !important; width: 100% !important;
        display: flex !important; justify-content: center !important; align-items: center !important;
        box-shadow: 0px 0px 15px rgba(255, 87, 34, 0.6) !important; transform: scale(1.03); transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="tertiary"] p {
        font-size: 2.8rem !important; font-weight: 900 !important; line-height: 1 !important; margin: 0 !important; padding: 0 !important;
    }
    
    .pos-label { font-size: 0.95em; color: #37474f; margin-bottom: -3px; font-weight: 900; text-align: center; }
    .net-container { position: relative; width: 100%; height: 60px; margin-top: 10px; margin-bottom: 30px; }
    .net-pole-left, .net-pole-right { position: absolute; top: 0; width: 6px; height: 80px; background-color: #90a4ae; border-radius: 2px; }
    .net-pole-left { left: 0; } .net-pole-right { right: 0; }
    .net-mesh {
        position: absolute; top: 10px; left: 6px; right: 6px; height: 40px;
        background-color: transparent;
        background-image: linear-gradient(#455a64 1px, transparent 1px), linear-gradient(90deg, #455a64 1px, transparent 1px);
        background-size: 12px 12px; border-top: 6px solid #ffffff; border-bottom: 2px solid #ffffff; box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 📊 상태 관리 및 명단
# ==========================================
LINEUP_FILE = "saved_lineup.json"

if 'log_data' not in st.session_state: st.session_state.log_data = []
if 'selected_player' not in st.session_state: st.session_state.selected_player = None

if 'team_roster' not in st.session_state:
    st.session_state.team_roster = [
        "유석현", "홍순석", "이준호", "조형민", "백충석", "문기영", "이광호", "김수홍", "홍성준", "김기상",
        "이민구", "문준기", "김수현", "이웅용", "이우형", "이준익", "문원기", "박준형", "문승민", "문상록",
        "김홍무", "손효준", "이대윤", "김백현", "김준영", "명 수", "양재훈", "방기성", "김두헌", "최병주",
        "길운상", "최민규", "강대서", "김용신", "유무영", "김태영", "신정환", "이규승"
    ]

if 'lineup' not in st.session_state:
    default_lineup = { "레프트": st.session_state.team_roster[0], "세터": st.session_state.team_roster[1], "라이트": st.session_state.team_roster[2], "앞차": st.session_state.team_roster[3], "센터": st.session_state.team_roster[4], "백차": st.session_state.team_roster[5], "레프트백": st.session_state.team_roster[6], "센터백": st.session_state.team_roster[7], "라이트백": st.session_state.team_roster[8] }
    if os.path.exists(LINEUP_FILE):
        try:
            with open(LINEUP_FILE, "r", encoding="utf-8") as f: saved = json.load(f)
            for k in default_lineup.keys():
                if k in saved and saved[k] in st.session_state.team_roster: default_lineup[k] = saved[k]
        except Exception: pass
    st.session_state.lineup = default_lineup

def update_lineup_file():
    with open(LINEUP_FILE, "w", encoding="utf-8") as f: json.dump(st.session_state.lineup, f, ensure_ascii=False)

def select_player(p_name): st.session_state.selected_player = p_name

def record_action(player, action_name, result_name):
    if player:
        st.session_state.log_data.append({ "시간": datetime.now().strftime("%H:%M:%S"), "선수": player, "액션": action_name, "결과": result_name })
        st.session_state.selected_player = None 
    else:
        st.toast("⚠️ 코트에서 선수를 먼저 선택하세요!", icon="⚠️")

def undo_last():
    if st.session_state.log_data: st.session_state.log_data.pop()

def reset_data():
    st.session_state.log_data = []
    st.session_state.selected_player = None
    st.toast("🔄 기록이 전체 초기화되었습니다!", icon="♻️")

with st.sidebar:
    st.header("📋 경기 및 라인업 설정")
    match_name = st.text_input("📅 경기명 (입력 시 기록 리셋)", value=datetime.now().strftime("%Y-%m-%d 연습경기"), on_change=reset_data)
    st.button("🔄 현재 기록 전체 초기화", on_click=reset_data, use_container_width=True)
    st.divider()
    
    positions = ["레프트", "세터", "라이트", "앞차", "센터", "백차", "레프트백", "센터백", "라이트백"]
    for pos in positions:
        st.session_state.lineup[pos] = st.selectbox(f"{pos}", options=st.session_state.team_roster, index=st.session_state.team_roster.index(st.session_state.lineup[pos]), key=f"select_{pos}", on_change=update_lineup_file)

# ==========================================
# 🏐 대시보드 상단 영역
# ==========================================
col_title, col_undo = st.columns([4, 1])
with col_title: st.title(f"🏐 실시간 대시보드: {match_name}")
with col_undo: st.write(""); st.button("⏪ 직전 기록 취소", on_click=undo_last, use_container_width=True)

stats_df = pd.DataFrame()
if st.session_state.log_data:
    df_log = pd.DataFrame(st.session_state.log_data)
    stats = []
    for p in df_log['선수'].unique():
        p_data = df_log[df_log['선수'] == p]
        
        # 🎯 공격 성공률
        atk_pts = len(p_data[(p_data['액션'] == '공격') & (p_data['결과'] == '득점')])
        atk_err = len(p_data[(p_data['액션'] == '공격') & (p_data['결과'] == '범실')])
        atk_tot = atk_pts + atk_err
        atk_rate = round((atk_pts / atk_tot * 100), 1) if atk_tot > 0 else 0.0
        
        # 🎯 리시브 성공률
        rec_ex = len(p_data[(p_data['액션'] == '리시브') & (p_data['결과'] == '정확')])
        rec_ok = len(p_data[(p_data['액션'] == '리시브') & (p_data['결과'] == '성공')])
        rec_fail = len(p_data[(p_data['액션'] == '리시브') & (p_data['결과'] == '실패')])
        rec_tot = rec_ex + rec_ok + rec_fail
        rec_rate = round(((rec_ex + rec_ok) / rec_tot * 100), 1) if rec_tot > 0 else 0.0
        
        # 🎯 서브 성공률
        srv_pts = len(p_data[(p_data['액션'] == '서브') & (p_data['결과'] == '득점')])
        srv_ok = len(p_data[(p_data['액션'] == '서브') & (p_data['결과'] == '성공')])
        srv_err = len(p_data[(p_data['액션'] == '서브') & (p_data['결과'] == '범실')])
        srv_tot = srv_pts + srv_ok + srv_err
        srv_rate = round(((srv_pts + srv_ok) / srv_tot * 100), 1) if srv_tot > 0 else 0.0
        
        # 수비 및 세트, 블로킹, 범실
        dig_suc = len(p_data[(p_data['액션'] == '수비') & (p_data['결과'] == '성공')])
        set_ex = len(p_data[(p_data['액션'] == '세트') & (p_data['결과'] == '정확')])
        blk_pts = len(p_data[(p_data['액션'] == '블로킹') & (p_data['결과'] == '득점')])
        tot_err = len(p_data[p_data['결과'].isin(['범실', '실패', '네트터치', '오버넷', '캐치볼', '더블컨택'])])
        
        stats.append({
            "경기명": match_name, "선수명": p, 
            "총 득점": atk_pts + blk_pts + srv_pts,
            "공격 성공률(%)": atk_rate, "리시브 성공률(%)": rec_rate, "서브 성공률(%)": srv_rate,
            "수비 성공": dig_suc, "세트 정확": set_ex, "블로킹 득점": blk_pts, "총 범실": tot_err
        })
    stats_df = pd.DataFrame(stats).sort_values(by="총 득점", ascending=False).reset_index(drop=True)
    st.subheader("🏆 경기/선수별 성공률 및 심층 스탯")
    st.dataframe(stats_df, use_container_width=True, height=150)
else:
    st.info("💡 기록을 시작하면 성공률 및 효율 스탯이 실시간으로 자동 계산됩니다.")

st.divider()

main_col1, main_col2 = st.columns([35, 65])

# ==========================================
# 👥 코트 명단 영역 
# ==========================================
with main_col1:
    st.subheader("👥 코트 명단")
    st.markdown("""<div class="net-container"><div class="net-pole-left"></div><div class="net-mesh"></div><div class="net-pole-right"></div></div>""", unsafe_allow_html=True)
    for row_pos in [["레프트", "세터", "라이트"], ["앞차", "센터", "백차"], ["레프트백", "센터백", "라이트백"]]:
        cols = st.columns(3)
        for i, pos in enumerate(row_pos):
            with cols[i]:
                st.markdown(f'<div class="pos-label">{pos}</div>', unsafe_allow_html=True)
                p_name = st.session_state.lineup[pos]
                btn_type = "tertiary" if st.session_state.selected_player == p_name else "primary"
                st.button(p_name, key=f"btn_{pos}", use_container_width=True, type=btn_type, on_click=select_player, args=(p_name,))
        st.write("")

# ==========================================
# ⚡ 플레이 내용 영역
# ==========================================
with main_col2:
    st.subheader("⚡ 플레이 내용")
    curr_p = st.session_state.selected_player
    act_c1, act_c2, act_c3, act_c4, act_c5 = st.columns(5)
    
    with act_c1:
        st.write("**[서브]**")
        st.button("🔴 서브 득점", use_container_width=True, on_click=record_action, args=(curr_p, "서브", "득점"))
        st.button("⚪ 서브 성공", use_container_width=True, on_click=record_action, args=(curr_p, "서브", "성공"))
        st.button("❌ 서브 범실", use_container_width=True, on_click=record_action, args=(curr_p, "서브", "범실"))
        
    with act_c2:
        st.write("**[리시브]**")
        st.button("🎯 리시브 정확", use_container_width=True, on_click=record_action, args=(curr_p, "리시브", "정확"))
        st.button("OK 리시브 보통", use_container_width=True, on_click=record_action, args=(curr_p, "리시브", "성공"))
        st.button("💔 리시브 실패", use_container_width=True, on_click=record_action, args=(curr_p, "리시브", "실패"))
        
    with act_c3:
        st.write("**[공격]**")
        st.button("🔥 공격 득점", use_container_width=True, on_click=record_action, args=(curr_p, "공격", "득점"))
        st.button("❌ 공격 범실", use_container_width=True, on_click=record_action, args=(curr_p, "공격", "범실"))
        st.write("**[블로킹]**")
        st.button("🧱 블로킹 득점", use_container_width=True, on_click=record_action, args=(curr_p, "블로킹", "득점"))
        st.button("❌ 블로킹 범실", use_container_width=True, on_click=record_action, args=(curr_p, "블로킹", "범실"))

    with act_c4:
        st.write("**[수비/세트]**")
        st.button("👐 수비 성공", use_container_width=True, on_click=record_action, args=(curr_p, "수비", "성공"))
        st.button("⬆️ 세트 정확", use_container_width=True, on_click=record_action, args=(curr_p, "세트", "정확"))

    with act_c5:
        st.write("**[기타 범실]**")
        st.button("⚠️ 네트터치", use_container_width=True, on_click=record_action, args=(curr_p, "범실", "네트터치"))
        st.button("⚠️ 오버넷", use_container_width=True, on_click=record_action, args=(curr_p, "범실", "오버넷"))
        st.button("⚠️ 캐치볼", use_container_width=True, on_click=record_action, args=(curr_p, "범실", "캐치볼"))
        st.button("⚠️ 더블컨택", use_container_width=True, on_click=record_action, args=(curr_p, "범실", "더블컨택"))

st.divider()

# ==========================================
# ☁️ 구글 시트 백업 (경기별 탭 생성 및 머리글 완벽 지원)
# ==========================================
st.subheader("💾 분석 데이터 누적 저장")
st.write("버튼을 누르면 경기명으로 된 '새로운 탭(시트)'이 생성되며 머리글과 함께 깔끔하게 저장됩니다.")

col_save1, col_save2 = st.columns(2)

with col_save1:
    if st.button("☁️ 구글 시트에 현재 경기 스탯 저장하기", use_container_width=True):
        if not stats_df.empty:
            with st.spinner("구글 시트에 데이터를 저장하는 중입니다..."):
                client = init_gsheets()
                if client:
                    try:
                        sheet_name = "배구경기기록"
                        spreadsheet = client.open(sheet_name)
                        
                        # 📌 1. 현재 경기명과 똑같은 이름의 탭(시트)을 찾거나 새로 만듭니다.
                        try:
                            worksheet = spreadsheet.worksheet(match_name)
                            worksheet.clear() # 이미 해당 경기의 탭이 있다면, 기존 내용을 지우고 최신 기록으로 덮어씁니다.
                        except gspread.exceptions.WorksheetNotFound:
                            worksheet = spreadsheet.add_worksheet(title=match_name, rows="100", cols="20")
                        
                        # 📌 2. 머리글(항목 이름)과 데이터를 합쳐서 깔끔하게 저장합니다.
                        data_to_save = [stats_df.columns.values.tolist()] + stats_df.values.tolist()
                        worksheet.update(data_to_save)
                        
                        st.success(f"✅ 구글 시트에 '{match_name}' 전용 탭이 생성/업데이트 되었습니다!")
                    except Exception as e:
                        st.error(f"❌ 구글 시트 저장 실패: {e}")
                else:
                    st.error("❌ 구글 시트 연결 오류.")
        else:
            st.warning("⚠️ 아직 기록된 데이터가 없습니다.")

with col_save2:
    if not stats_df.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            stats_df.to_excel(writer, index=False, sheet_name=match_name[:30])
            df_log.to_excel(writer, index=False, sheet_name='상세시간로그')
        st.download_button(label="📥 엑셀 파일로 통계 다운로드", data=buffer.getvalue(), file_name=f"배구분석_{match_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.button("📥 엑셀 파일로 통계 다운로드", disabled=True, use_container_width=True)
