import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração de Estilo
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

# Funções de Dados Estabilizadas
@st.cache_data(ttl=600)
def get_data(ticker):
    try:
        # Busca 6 meses de dados para ter histórico suficiente para o RSI
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty: return None
        return df
    except: return None

@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
        eur = yf.download("EURUSD=X", period="1d", progress=False)['Close'].iloc[-1]
        return float(usd), float(eur)
    except: return 5.15, 1.08

# 2. Sidebar com Listas Completas
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        if st.checkbox("Aceito os Termos de Responsabilidade"):
            st.session_state.auth = True
            st.rerun()
        st.stop()

    mercado = st.selectbox("Mercado:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"])
    
    # Listas reconstruídas para garantir que nada suma
    if mercado == "Bolsa Brasileira (B3)":
        ativos = {
            "Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", 
            "Itaú (ITUB4)": "ITUB4.SA", "Ambev (ABEV3)": "ABEV3.SA",
            "XP Malls (XPML11)": "XPML11.SA", "Kinea RI (KNCR11)": "KNCR11.SA",
            "HGLG11": "HGLG11.SA", "MXRF11": "MXRF11.SA"
        }
    elif mercado == "Commodities":
        ativos = {
            "Soja": "ZS=F", "Milho": "ZC=F", "Petróleo Brent": "BZ=F", 
            "Ouro": "GC=F", "Prata": "SI=F", "Café": "KC=F", "Algodão": "CT=F"
        }
    else:
        ativos = {
            "Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", 
            "Solana (USD)": "SOL-USD", "Dólar para Real": "USDBRL=X", 
            "Euro para Dólar": "EURUSD=X", "S&P 500": "^GSPC"
        }
    
    nome_ativo = st.selectbox("Ativo:", list(ativos.keys()))
    ticker = ativos[nome_ativo]
    
    st.markdown("---")
    moeda_v = st.radio("Moeda:", ["USD", "BRL", "EUR"], horizontal=True)
    banca = st.select_slider("Sua Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Lógica de Processamento
usd_brl, eur_usd = get_cambio()
dados = get_data(ticker)

if dados is not None and len(dados) > 20:
    # Garantir que as colunas sejam tratadas como Séries simples
    fechamentos = dados['Close'].squeeze()
    
    # Cálculo RSI
    delta = fechamentos.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi_series = 100 - (100 / (1 + (gain / loss)))
    
    rsi_atual = float(rsi_series.iloc[-1])
    p_raw = float(fechamentos.iloc[-1])
    
    # Lógica de Preço Unitário
    is_cents = ("Soja" in nome_ativo or "Milho" in nome_ativo)
    p_unit_usd = p_raw / 100 if is_cents else p_raw
    
    # Conversão de Moeda
    m_origem = "BRL" if ticker.endswith(".SA") or "BRL" in ticker else "USD"
    if m_origem == "USD":
        p_final = p_unit_usd * usd_brl if moeda_v == "BRL" else p_unit_usd / eur_usd if moeda_v == "EUR" else p_unit_usd
    else:
        p_final = p_unit_usd / usd_brl if moeda_v == "USD" else (p_unit_usd / usd_brl) / eur_usd if moeda_v == "EUR" else p_unit_usd

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
        # Gráfico de Candlestick forçando os eixos
        fig = go.Figure(data=[go.Candlestick(
            x=dados.index,
            open=dados['Open'],
            high=dados['High'],
            low=dados['Low'],
            close=dados['Close'],
            name='Preço'
        )])
        fig.update_layout(template="plotly_dark", height=480, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        st.line_chart(rsi_series)
else:
    st.error("Conectando com a Bolsa... Se o erro persistir, altere o Ativo ou Mercado na lateral.")

st.markdown('<div style="text-align:center; color:#4b5563; font-size:12px; margin-top:30px;">VULKAN SYSTEM | Monitoramento Inteligente</div>', unsafe_allow_html=True)
