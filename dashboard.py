import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Setup de Página
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); }
    .clean-disclaimer { font-size: 12px; color: #4b5563; text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# Função para pegar cotação de moedas para conversão
@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd_brl = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
        eur_usd = yf.download("EURUSD=X", period="1d", progress=False)['Close'].iloc[-1]
        return float(usd_brl), float(eur_usd)
    except:
        return 5.0, 1.08 # Valores reserva caso a API falhe

usd_brl, eur_usd = get_cambio()

# 2. Barra Lateral
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    st.markdown("---")
    
    if 'aceitou_termo' not in st.session_state:
        st.session_state.aceitou_termo = False

    if not st.session_state.aceitou_termo:
        st.subheader("📋 Termo de Uso")
        if st.checkbox("Aceito que esta é uma ferramenta de apoio e sou responsável por minhas operações."):
            st.session_state.aceitou_termo = True
            st.rerun()
        st.stop()

    st.subheader("🌐 Mercado")
    mercado = st.selectbox("Escolha a categoria:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"], label_visibility="collapsed")

    st.subheader("📈 Ativo")
    if mercado == "Bolsa Brasileira (B3)":
        lista_ativos = {"Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "XP Malls (XPML11)": "XPML11.SA", "HGLG11": "HGLG11.SA"}
    elif mercado == "Commodities":
        lista_ativos = {"Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Soja": "ZS=F", "Milho": "ZC=F", "Café": "KC=F"}
    else:
        lista_ativos = {"Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Dólar/Real": "USDBRL=X"}
    
    escolha_nome = st.selectbox("Selecione o ativo:", list(lista_ativos.keys()), label_visibility="collapsed")
    ticker = lista_ativos[escolha_nome]

    st.markdown("---")
    st.subheader("💰 Gestão de Banca")
    moeda_banca = st.radio("Exibir valores em:", ["USD", "BRL", "EUR"], horizontal=True)
    valor_banca = st.select_slider("Valor da Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Processamento de Dados
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # Valor Bruto (conforme vem da fonte)
    preco_raw = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # LÓGICA DE CONVERSÃO DE MOEDA
    # Identifica se a fonte original é BRL (ativos .SA) ou USD (resto)
    moeda_origem = "BRL" if ticker.endswith(".SA") or ticker == "USDBRL=X" else "USD"
    
    preco_convertido = preco_raw
    if moeda_origem == "USD":
        if moeda_banca == "BRL": preco_convertido = preco_raw * usd_brl
        elif moeda_banca == "EUR": preco_convertido = preco_raw / eur_usd
    elif moeda_origem == "BRL":
        if moeda_banca == "USD": preco_convertido = preco_raw / usd_brl
        elif moeda_banca == "EUR": preco_convertido = (preco_raw / usd_brl) / eur_usd

    # Unidades de Commodities
    unid = ""
    if mercado == "Commodities":
        if "Soja" in escolha_nome or "Milho" in escolha_nome: unid = " /bu"
        elif "Petróleo" in escolha_nome: unid = " /barril"
        elif "Ouro" in escolha_nome: unid = " /oz t"
        elif "Café" in escolha_nome: unid = " /lb"

    # Interface
    cor = "#108542" if rsi_val < 35 else "#a50e0e" if rsi_val > 65 else "#d97706"
    sinal = "COMPRA FORTE" if rsi_val < 35 else "VENDA / RISCO" if rsi_val > 65 else "NEUTRO / AGUARDAR"
    
    st.markdown(f'<div class="status-banner" style="background-color:{cor};"><h1>VEREDITO VULKAN: {sinal}</h1></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"{moeda_banca} {preco_convertido:,.2f}{unid}")
    c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
    c3.metric("Risco Sugerido (2%)", f"{moeda_banca} {(valor_banca * 0.02):,.2f}")

    tab1, tab2 = st.tabs(["📈 Gráfico", "📉 Filtro RSI"])
    with tab1:
        # O gráfico permanece na moeda original para evitar distorção visual histórica
        fig = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(), high=dados['High'].values.ravel(), low=dados['Low'].values.ravel(), close=dados['Close'].values.ravel())])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, title=f"Histórico em Moeda de Origem ({moeda_origem})")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig_r = go.Figure(data=[go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), line=dict(color='#9b51e0'))])
        fig_r.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown('<div class="clean-disclaimer">VULKAN SYSTEM | Inteligência com conversão de câmbio em tempo real.</div>', unsafe_allow_html=True)
