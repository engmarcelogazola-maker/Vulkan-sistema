import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração e Estilo
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { 
        padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px; 
        font-weight: bold; font-size: 26px; text-transform: uppercase;
    }
    .info-box { 
        background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #ef4444; 
        margin-bottom: 20px; font-size: 15px; color: #f8fafc; line-height: 1.6;
    }
    .alert-text { color: #f87171; font-weight: 900; text-decoration: underline; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# Funções de Dados Blindadas
@st.cache_data(ttl=600)
def get_clean_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty: return None
        # Correção para o novo formato do Yahoo Finance (Multi-Index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd = yf.download("USDBRL=X", period="1d", progress=False)
        if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
        return float(usd['Close'].iloc[-1]), 5.15
    except: return 5.15, 1.08

# 2. Sidebar
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        if st.checkbox("Aceito os Termos de Responsabilidade"):
            st.session_state.auth = True
            st.rerun()
        st.stop()

    mercado = st.selectbox("Mercado:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"])
    
    if mercado == "Bolsa Brasileira (B3)":
        ativos = {"Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "Itaú (ITUB4)": "ITUB4.SA", "Ambev (ABEV3)": "ABEV3.SA", "XP Malls (XPML11)": "XPML11.SA", "Kinea RI (KNCR11)": "KNCR11.SA", "HGLG11": "HGLG11.SA", "MXRF11": "MXRF11.SA"}
    elif mercado == "Commodities":
        ativos = {"Soja": "ZS=F", "Milho": "ZC=F", "Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Prata": "SI=F", "Café": "KC=F", "Algodão": "CT=F"}
    else:
        ativos = {"Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (USD)": "SOL-USD", "Dólar para Real": "USDBRL=X", "S&P 500": "^GSPC"}
    
    nome_ativo = st.selectbox("Ativo:", list(ativos.keys()))
    ticker = ativos[nome_ativo]
    
    st.markdown("---")
    moeda_v = st.radio("Moeda:", ["USD", "BRL", "EUR"], horizontal=True)
    banca = st.select_slider("Sua Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Processamento
usd_brl, eur_usd = get_cambio()
df = get_clean_data(ticker)

if df is not None and len(df) > 20:
    # Cálculo RSI Profissional
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    rsi_atual = float(df['RSI'].iloc[-1])
    p_raw = float(df['Close'].iloc[-1])
    
    is_cents = ("Soja" in nome_ativo or "Milho" in nome_ativo)
    p_unit_usd = p_raw / 100 if is_cents else p_raw
    m_origem = "BRL" if ticker.endswith(".SA") or "BRL" in ticker else "USD"
    
    if m_origem == "USD":
        p_final = p_unit_usd * usd_brl if moeda_v == "BRL" else p_unit_usd / 1.08 if moeda_v == "EUR" else p_unit_usd
    else:
        p_final = p_unit_usd / usd_brl if moeda_v == "USD" else (p_unit_usd / usd_brl) / 1.08 if moeda_v == "EUR" else p_unit_usd

    # 4. Interface
    if rsi_atual < 35: acao, cor = "COMPRAR", "#108542"
    elif rsi_atual > 65: acao, cor = "VENDER", "#a50e0e"
    else: acao, cor = "AGUARDAR", "#d97706"

    st.markdown(f'<div class="status-banner" style="background-color:{cor}; color: white;">{acao} {nome_ativo}</div>', unsafe_allow_html=True)

    if is_cents:
        st.markdown(f"""
            <div class="info-box">
                🚨 <b>IMPORTANTE:</b> O valor de {p_raw:,.2f} na bolsa refere-se a <span class="alert-text">CENTAVOS DE DÓLAR</span>. <br>
                💵 Isso equivale a <b>USD {p_unit_usd:,.4f}</b> por bushel. <br>
                📌 <b>Saca (60kg) estimada:</b> {moeda_v} {(p_final * 2.3622):,.2f}
            </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"{moeda_v} {p_final:,.2f}")
    c2.metric("Força RSI", f"{rsi_atual:.2f}")
    c3.metric("Risco (2%)", f"{moeda_v} {(banca * 0.02):,.2f}")

    t1, t2 = st.tabs(["📊 Gráfico de Velas", "📈 Força Relativa (RSI)"])
    with t1:
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço')])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#9b51e0', width=2)))
        # Zonas de Cor no RSI
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.15, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.15, line_width=0)
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)
        fig_rsi.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_rsi, use_container_width=True)
else:
    st.error("Erro ao carregar dados. Tente alterar o ativo.")
