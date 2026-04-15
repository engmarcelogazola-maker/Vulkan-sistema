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
    .status-banner { padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); }
    .info-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 20px; font-size: 14px; color: #e2e8f0; }
    .clean-disclaimer { font-size: 12px; color: #4b5563; text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd_brl = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
        eur_usd = yf.download("EURUSD=X", period="1d", progress=False)['Close'].iloc[-1]
        return float(usd_brl), float(eur_usd)
    except: return 5.15, 1.08

usd_brl_rate, eur_usd_rate = get_cambio()

# 2. Barra Lateral
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    if 'aceitou_termo' not in st.session_state: st.session_state.aceitou_termo = False
    if not st.session_state.aceitou_termo:
        if st.checkbox("Aceito os termos de responsabilidade"):
            st.session_state.aceitou_termo = True
            st.rerun()
        st.stop()
    
    mercado = st.selectbox("Mercado:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"])
    
    if mercado == "Bolsa Brasileira (B3)":
        lista = {"Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "XP Malls (XPML11)": "XPML11.SA", "MXRF11": "MXRF11.SA"}
    elif mercado == "Commodities":
        lista = {"Milho": "ZC=F", "Soja": "ZS=F", "Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Café": "KC=F"}
    else:
        lista = {"Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Dólar/Real": "USDBRL=X"}
    
    escolha_nome = st.selectbox("Ativo:", list(lista.keys()))
    ticker = lista[escolha_nome]
    
    st.markdown("---")
    moeda_banca = st.radio("Moeda:", ["USD", "BRL", "EUR"], horizontal=True)
    valor_banca = st.select_slider("Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Processamento
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    preco_raw = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # Lógica de conversão para o banner
    moeda_origem = "BRL" if ticker.endswith(".SA") or ticker == "USDBRL=X" else "USD"
    preco_real_unidade = preco_raw
    
    # AJUSTE ESPECÍFICO PARA MILHO E SOJA (Centavos para Dólares)
    if "Milho" in escolha_nome or "Soja" in escolha_nome:
        preco_real_unidade = preco_raw / 100 # Transforma 451.50 em 4.51

    # Conversão de Câmbio
    preco_final = preco_real_unidade
    if moeda_origem == "USD":
        if moeda_banca == "BRL": preco_final = preco_real_unidade * usd_brl_rate
        elif moeda_banca == "EUR": preco_final = preco_real_unidade / eur_usd_rate

    # 4. Interface de Veredito
    cor = "#108542" if rsi_val < 35 else "#a50e0e" if rsi_val > 65 else "#d97706"
    sinal = "COMPRA" if rsi_val < 35 else "VENDA / RISCO" if rsi_val > 65 else "NEUTRO"
    
    st.markdown(f'<div class="status-banner" style="background-color:{cor};"><h1>VEREDITO VULKAN: {sinal} em {escolha_nome.upper()}</h1></div>', unsafe_allow_html=True)

    # Legenda Explicativa para Commodities
    if "Milho" in escolha_nome or "Soja" in escolha_nome:
        saca_60kg = preco_final * 2.362 # 1 saca de 60kg tem ~2.36 bushels
        st.markdown(f"""
            <div class="info-box">
                <b>💡 Nota Técnica:</b> Em Chicago, o {escolha_nome} é cotado em centavos. 
                O valor de <b>{preco_raw:.2f}</b> equivale a <b>{moeda_banca} {preco_real_unidade:.4f}</b> por bushel. <br>
                📌 <b>Contrato Padrão:</b> 5.000 bushels | <b>Conversão estimada:</b> {moeda_banca} {saca_60kg:.2f} por saca (60kg).
            </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço por Unidade", f"{moeda_banca} {preco_final:,.4f}")
    c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
    c3.metric("Risco Sugerido (2%)", f"{moeda_banca} {(valor_banca * 0.02):,.2f}")

    tab1, tab2 = st.tabs(["📈 Gráfico", "📉 Filtro RSI"])
    with tab1:
        fig = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(), high=dados['High'].values.ravel(), low=dados['Low'].values.ravel(), close=dados['Close'].values.ravel())])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig_r = go.Figure(data=[go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), line=dict(color='#9b51e0'))])
        fig_r.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown('<div class="clean-disclaimer">VULKAN SYSTEM | Inteligência Aplicada com Conversão Técnica.</div>', unsafe_allow_html=True)
