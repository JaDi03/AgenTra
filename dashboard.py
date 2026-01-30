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
                symbol = pos['symbol']
                pos_type = pos['type']
                entry_price = float(pos['entry_price'])
                current_price_val = float(pos['current_price'])
                quantity = float(pos['quantity'])
                
                # Calculate Unrealized PnL
                if pos_type == "LONG":
                    unrealized_pnl = (current_price_val - entry_price) * quantity
                else: # SHORT
                    unrealized_pnl = (entry_price - current_price_val) * quantity
                
                pnl_pct = (unrealized_pnl / (entry_price * quantity)) * 100 if (entry_price * quantity) > 0 else 0
                
                # Emoji for PnL
                emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
                
                # Position Card
                with st.container():
                    # Calculate metric values before expander
                    current_sl = float(pos.get('stop_loss', 0))
                    initial_sl = float(pos.get('initial_stop_loss', current_sl))
                    tp_price = float(pos.get('take_profit', 0))
                    sl_moved = abs(current_sl - initial_sl) > 0.01
                    
                    # Main Label for Expander
                    label = f"{emoji} {symbol} {pos_type} | PnL: ${unrealized_pnl:.2f} ({pnl_pct:.2f}%)"
                    
                    with st.expander(label, expanded=True):
                        # Metrics Row (compact)
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown(f"<p style='font-size:12px; margin:0;'>Entry</p><p style='font-size:16px; font-weight:bold; margin:0;'>${entry_price:.2f}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:12px; margin:0;'>Size</p><p style='font-size:16px; font-weight:bold; margin:0;'>{quantity:.4f}</p>", unsafe_allow_html=True)
                        with col_b:
                            # Current SL
                            if sl_moved:
                                sl_delta_val = current_sl - initial_sl
                                delta_color = "green" if (pos_type == "SHORT" and sl_delta_val < 0) or (pos_type == "LONG" and sl_delta_val > 0) else "red"
                                st.markdown(f"<p style='font-size:12px; margin:0;'>Current SL</p><p style='font-size:16px; font-weight:bold; margin:0; color:{delta_color};'>${current_sl:.2f} ({sl_delta_val:+.2f})</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='font-size:10px; color:gray; margin:0;'>Original: ${initial_sl:.2f}</p>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<p style='font-size:12px; margin:0;'>Stop Loss</p><p style='font-size:16px; font-weight:bold; margin:0;'>${current_sl:.2f}</p>", unsafe_allow_html=True)
                        with col_c:
                            st.markdown(f"<p style='font-size:12px; margin:0;'>Take Profit</p><p style='font-size:16px; font-weight:bold; margin:0;'>${tp_price:.2f}</p>", unsafe_allow_html=True)
                        
                        st.divider()
                        
                        # Chart with Entry/SL/TP markers
                        try:
                            import plotly.graph_objects as go
                            
                            # Create price levels for visualization
                            levels = [entry_price, current_sl, tp_price]
                            if sl_moved:
                                levels.append(initial_sl)
                            
                            min_price = min(levels) * 0.995
                            max_price = max(levels) * 1.005
                            
                            fig = go.Figure()
                            
                            # Current Price line (dynamic)
                            fig.add_trace(go.Scatter(
                                x=[0, 1],
                                y=[current_price_val, current_price_val],
                                mode='lines',
                                name='Current Price',
                                line=dict(color='white', width=2, dash='dot')
                            ))
                            
                            # Entry Price
                            fig.add_trace(go.Scatter(
                                x=[0, 1],
                                y=[entry_price, entry_price],
                                mode='lines+text',
                                name='Entry',
                                line=dict(color='blue', width=2),
                                text=['', f'Entry: ${entry_price:.2f}'],
                                textposition='middle right'
                            ))
                            
                            # Stop Loss levels
                            if sl_moved:
                                # Original SL (faded)
                                fig.add_trace(go.Scatter(
                                    x=[0, 1],
                                    y=[initial_sl, initial_sl],
                                    mode='lines+text',
                                    name='SL Original',
                                    line=dict(color='red', width=1, dash='dash'),
                                    text=['', f'SL1: ${initial_sl:.2f}'],
                                    textposition='middle right'
                                ))
                            
                            # Current SL
                            fig.add_trace(go.Scatter(
                                x=[0, 1],
                                y=[current_sl, current_sl],
                                mode='lines+text',
                                name='SL Current',
                                line=dict(color='red', width=2),
                                text=['', f'SL: ${current_sl:.2f}'],
                                textposition='middle right'
                            ))
                            
                            # Take Profit
                            fig.add_trace(go.Scatter(
                                x=[0, 1],
                                y=[tp_price, tp_price],
                                mode='lines+text',
                                name='Take Profit',
                                line=dict(color='green', width=2),
                                text=['', f'TP: ${tp_price:.2f}'],
                                textposition='middle right'
                            ))
                            
                            fig.update_layout(
                                height=250,
                                margin=dict(l=0, r=100, t=20, b=0),
                                xaxis=dict(visible=False),
                                yaxis=dict(range=[min_price, max_price], title='Price'),
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        except ImportError:
                            st.warning("Install plotly for chart visualization: `pip install plotly`")
                        
                        st.divider()
                        st.markdown(f"<p style='font-size:12px;'><b>Entry Time (UTC-6):</b> {pos.get('entry_time', 'N/A')}</p>", unsafe_allow_html=True)
                        st.markdown("**Reason:**")
                        st.info(pos.get('reason', 'No specific reason logged.'))
                        
                        st.divider()
                        # --- MANUAL CLOSE BUTTON (INSIDE EXPANDER) ---
                        safe_symbol = symbol.replace('/', '_')
                        req_path = os.path.join(r"C:\Users\USER\AgenTra", f"CLOSE_{safe_symbol}.req")
                        
                        if st.button(f"⛔ CLOSE {symbol}", key=f"btn_close_{i}", type="primary", use_container_width=True):
                            with open(req_path, "w") as f:
                                f.write("FORCE_CLOSE")
                            st.warning(f"Sending CLOSE signal for {symbol}...")
                            time.sleep(1)
                            st.rerun()
                st.divider()

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
