import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Setup e Estilo
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { 
        padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px; 
        font-weight: bold; font-size: 24px; letter-spacing: 1px;
    }
    .info-box { 
        background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #ef4444; 
        margin-bottom: 20px; font-size: 15px; color: #f8fafc; line-height: 1.6;
    }
    .highlight-cents { color: #f87171; font-weight: 900; text-decoration: underline; font-size: 17px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd_brl = yf.download("USDBRL=X", period="1d", progress=False)['Close']
        eur_usd = yf.download("EURUSD=X", period="1d", progress=False)['Close']
        return float(usd_brl.iloc[-1]), float(eur_usd.iloc[-1])
    except: return 5.15, 1.08

usd_brl_rate, eur_usd_rate = get_cambio()

# 2. Barra Lateral
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    if 'aceitou' not in st.session_state: st.session_state.aceitou = False
    if not st.session_state.aceitou:
        if st.checkbox("Aceito os termos de responsabilidade"):
            st.session_state.aceitou = True
            st.rerun()
        st.stop()
    
    mercado = st.selectbox("Mercado:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"])
    
    if mercado == "Bolsa Brasileira (B3)":
        lista = {"Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "Itaú (ITUB4)": "ITUB4.SA", "Ambev (ABEV3)": "ABEV3.SA", "XP Malls (XPML11)": "XPML11.SA", "MXRF11": "MXRF11.SA", "HGLG11": "HGLG11.SA", "KNCR11": "KNCR11.SA"}
    elif mercado == "Commodities":
        lista = {"Soja": "ZS=F", "Milho": "ZC=F", "Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Prata": "SI=F", "Café": "KC=F", "Algodão": "CT=F"}
    else:
        lista = {"Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (USD)": "SOL-USD", "Dólar para Real": "USDBRL=X", "S&P 500 Index": "^GSPC"}
    
    nome_ativo = st.selectbox("Ativo:", list(lista.keys()))
    ticker = lista[nome_ativo]
    
    st.markdown("---")
    moeda_b = st.radio("Exibir em:", ["USD", "BRL", "EUR"], horizontal=True)
    banca = st.select_slider("Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Busca de Dados com Tratamento de Erro
try:
    dados = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if not dados.empty:
        # Cálculo RSI
        delta = dados['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        dados['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        p_raw = float(dados['Close'].iloc[-1])
        r_val = float(dados['RSI'].iloc[-1])

        # Lógica de Preço
        is_cents = ("Soja" in nome_ativo or "Milho" in nome_ativo)
        p_base = p_raw / 100 if is_cents else p_raw
        m_origem = "BRL" if ticker.endswith(".SA") or ticker == "USDBRL=X" else "USD"
        
        if m_origem == "USD":
            p_final = p_base * usd_brl_rate if moeda_b == "BRL" else p_base / eur_usd_rate if moeda_b == "EUR" else p_base
        else:
            p_final = p_base / usd_brl_rate if moeda_b == "USD" else (p_base / usd_brl_rate) / eur_usd_rate if moeda_b == "EUR" else p_base

        # 4. Banner
        if r_val < 35: acao, cor = "COMPRAR", "#108542"
        elif r_val > 65: acao, cor = "VENDER", "#a50e0e"
        else: acao, cor = "AGUARDAR", "#d97706"

        st.markdown(f'<div class="status-banner" style="background-color:{cor}; color: white;">{acao} {nome_ativo.upper()}</div>', unsafe_allow_html=True)

        if is_cents:
            st.markdown(f"""
                <div class="info-box">
                    ⚠️ <b>LEITURA TÉCNICA:</b> O valor de <b>{p_raw:,.2f}</b> representa <span class="highlight-cents">CENTAVOS DE DÓLAR</span>. <br>
                    💵 Valor Unitário: <b>USD {p_base:,.4f}</b> por bushel. <br>
                    📌 <b>Saca (60kg) estimada:</b> {moeda_b} {(p_final * 2.3622):,.2f}
                </div>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Preço Atual", f"{moeda_b} {p_final:,.2f}")
        c2.metric("Força (RSI)", f"{r_val:.2f}")
        c3.metric("Risco (2%)", f"{moeda_b} {(banca * 0.02):,.2f}")

        tab1, tab2 = st.tabs(["📈 Gráfico de Preço", "📉 Indicador de Força"])
        with tab1:
            fig = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'], high=dados['High'], low=dados['Low'], close=dados['Close'], name='Candles')])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            fig_rsi = go.Figure(data=[go.Scatter(x=dados.index, y=dados['RSI'], line=dict(color='#9b51e0', width=2))])
            fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
            fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
            fig_rsi.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]), margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_rsi, use_container_width=True)
    else:
        st.warning("Aguardando dados do mercado...")

except Exception as e:
    st.error(f"Erro na conexão com a Bolsa. Tente trocar o ativo ou Mercado.")

st.markdown('<div style="text-align:center; color:#4b5563; font-size:12px; margin-top:30px;">VULKAN SYSTEM | Inteligência Multicamadas</div>', unsafe_allow_html=True)
