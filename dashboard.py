import streamlit as st
import pandas as pd
import json
import os
import time

# Page Config
st.set_page_config(
    page_title="AgenTra Dashboard",
    page_icon="💸",
    layout="wide"
)

# --- Constants ---
STATE_FILE = "state.json"
STRATEGY_FILE = "strategy.md"
LOG_FILE = "agent.log"
STOP_SIGNAL = "STOP_REQUEST"

# --- Helpers ---
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def load_strategy():
    if not os.path.exists(STRATEGY_FILE):
        return "Strategy not found."
    with open(STRATEGY_FILE, "r") as f:
        return f.read()

def tail_logs(lines=20):
    if not os.path.exists(LOG_FILE):
        return ["Log file not found."]
    try:
        with open(LOG_FILE, "r") as f:
            content = f.readlines()
            return content[-lines:]
    except:
        return ["Error reading logs."]

# --- Header ---
st.title("🤖 Autonomous Trading Agent Dashboard")

# --- Auto Refresh ---
if st.button("🔄 Refresh Data"):
    st.rerun()

state = load_state()

if state:
    # --- Top Metrics Row ---
    # --- Top Metrics Row ---
    balance = state.get("account_balance", 0.0)
    
    # Recalculate PnL from history to ensure accuracy (fix potential sync issues)
    history = state.get("trade_history", [])
    if history:
        pnl = sum([t.get('realized_pnl', 0.0) for t in history])
        wins = len([t for t in history if t.get('realized_pnl', 0.0) > 0])
        losses = len([t for t in history if t.get('realized_pnl', 0.0) <= 0])
    else:
        pnl = 0.0
        wins = 0
        losses = 0
    
    # Latest Analysis Data
    analysis = state.get("latest_analysis", {})
    last_symbol = analysis.get("symbol", "N/A")
    price = analysis.get("price", 0.0)
    rsi = analysis.get("rsi", 0.0)
    adx = analysis.get("adx", 0.0)

    # Metrics Columns
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 Balance", f"${balance:,.2f}", delta=f"${pnl:,.2f}")
    m2.metric("Win/Loss", f"{wins}W / {losses}L")
    m3.metric(f"Last Scanned: {last_symbol}", f"${price:,.2f}")
    m4.metric("📉 RSI (15m)", f"{rsi:.1f}")
    m5.metric("📊 ADX (15m)", f"{adx:.1f}")
    
    st.divider()

    # --- MAIN CONTENT LAYOUT ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # 1. ACTIVE POSITIONS
        st.subheader("🟢 Active Positions")
        positions = state.get("current_positions", [])
        
        if positions:
            for i, pos in enumerate(positions):
                symbol = pos.get('symbol')
                p_type = pos.get('type')
                entry_p = float(pos.get('entry_price', 0))
                qty = float(pos.get('quantity', 0))
                sl = float(pos.get('stop_loss', 0))
                init_sl = float(pos.get('initial_stop_loss', sl)) # Get Original SL
                curr_p = float(pos.get('current_price', entry_p)) 
                
                # SL Delta Logic (Show trailing progress)
                sl_delta = sl - init_sl
                # For Long: Up (+delta) is Good (Green). Normal.
                # For Short: Down (-delta) is Good (Green). Inverse.
                d_color = "normal" if p_type == "LONG" else "inverse"
                if abs(sl_delta) < 0.0000001: sl_delta = None # Hide if no change

                # Calc Unrealized PnL
                if p_type == "LONG":
                     u_pnl_usd = (curr_p - entry_p) * qty
                     u_pnl_pct = ((curr_p - entry_p) / entry_p) * 100
                else:
                     u_pnl_usd = (entry_p - curr_p) * qty
                     u_pnl_pct = ((entry_p - curr_p) / entry_p) * 100
                
                # Color logic
                pnl_color = "🟢" if u_pnl_usd >= 0 else "🔴"
                
                # Time formatting (Shorten it)
                e_time = pos.get('entry_time', '')
                try:
                    short_time = e_time.split(' ')[1][:5] if ' ' in e_time else e_time
                except:
                    short_time = e_time

                # Card Header
                label = f"{pnl_color} {short_time} | {symbol} {p_type} | PnL: ${u_pnl_usd:.2f} ({u_pnl_pct:.2f}%)"
                
                with st.expander(label, expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Entry Price", f"${entry_p:.5f}")
                    c2.metric("Size", f"{qty:.4f}")
                    # Format delta to string to avoid float errors
                    delta_str = f"{sl_delta:.5f}" if sl_delta is not None else None
                    c3.metric("Stop Loss", f"${sl:.5f}", delta=delta_str, delta_color=d_color)
                    c4.metric("Take Profit", f"${float(pos.get('take_profit',0) or 0):.5f}")
                
                    st.divider()
                    st.caption(f"**Full Entry Time:** {e_time}")
                    st.markdown(f"**Reason:** \n > {pos.get('reason', 'No specific reason logged.')}")
                    
                    st.divider()
                    # --- MANUAL CLOSE BUTTON (INSIDE CARD) ---
                    safe_symbol = symbol.replace('/', '_')
                    # USE ABSOLUTE PATH to ensure Main.py sees it
                    req_path = os.path.join(r"C:\Users\USER\AgenTra", f"CLOSE_{safe_symbol}.req")
                    
                    if st.button(f"⛔ CLOSE {symbol}", key=f"btn_close_{i}", type="primary"):
                        with open(req_path, "w") as f:
                            f.write("FORCE_CLOSE")
                        st.warning(f"Sending CLOSE signal for {symbol}...")
                        time.sleep(1) # Visual feedback
                        st.rerun()

        else:
            st.info("No active positions. Waiting for setup...")

        st.divider()

        # 2. TRADE HISTORY
        st.subheader("📜 Trade History")
        history = state.get("trade_history", [])
        
        if history:
            df_hist = pd.DataFrame(history)
            # Reverse to show newest first
            df_hist = df_hist.iloc[::-1]
            
            # Formatting PnL coloring
            def color_pnl(val):
                color = 'green' if val > 0 else 'red'
                return f'color: {color}'

            if not df_hist.empty:
                cols_hist = ["symbol", "type", "entry_price", "exit_price", "realized_pnl", "pnl_percent", "reason"]
                cols_final_hist = [c for c in cols_hist if c in df_hist.columns]
                
                # Apply style
                st.dataframe(
                    df_hist[cols_final_hist].style.map(color_pnl, subset=['realized_pnl', 'pnl_percent']),
                    width="stretch",
                    hide_index=True
                )
        else:
            st.text("No closed trades yet.")

    with col_right:
        # 3. CONTROL PANEL
        st.subheader("🛠️ Controls")
        if st.button("🚨 PANIC: CLOSE ALL & STOP", type="primary"):
            with open(STOP_SIGNAL, "w") as f:
                f.write("STOP")
            st.error("KILL SIGNAL SENT! Closing positions...")

        st.markdown("---")
        
        # 4. LIVE LOGS (Hidden by default to avoid flickering)
        with st.expander("📟 Live Logs", expanded=False):
            logs = tail_logs(20)
            st.code("".join(logs), language="text")
        
        st.markdown("---")
        
        # 5. STRATEGY (Folded)
        with st.expander("👀 View Active Strategy"):
            strategy_content = load_strategy()
            st.text_area("Strategy Rules", strategy_content, height=300, disabled=True)

else:
    st.warning("State file not found. Please run 'python main.py' first.")

# Auto-refresh logic
time.sleep(5)
st.rerun()
