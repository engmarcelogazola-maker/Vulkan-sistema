import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. SETUP
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

# Interface Customizada
st.markdown("""
    <style>
    .main { background-color: #05070a !important; }
    .status-card { padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    # Tickers mais estáveis (completos)
    opcoes = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Dólar/Real": "USDBRL=X"
    }
    ticker = opcoes[st.selectbox("Ativo:", list(opcoes.keys()))]
    banca = st.number_input("Banca ($)", value=1000.0)

# 3. BUSCA DE DADOS (VERSÃO REFORÇADA)
try:
    # Usamos o proxy do yfinance para evitar bloqueios do Streamlit
    data = yf.Ticker(ticker)
    df = data.history(period="1mo", interval="1d")
    
    if df.empty or len(df) < 14:
        st.warning("🔄 O mercado está lento. Tente trocar o ativo na barra lateral para destravar.")
    else:
        # Cálculo do RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        rsi_atual = float(rsi.iloc[-1])
        preco_atual = float(df['Close'].iloc[-1])

        # Veredito
        if rsi_atual < 35: sinal, cor = "COMPRA FORTE", "#10b981"
        elif rsi_atual > 65: sinal, cor = "VENDA / ALTO RISCO", "#ef4444"
        else: sinal, cor = "AGUARDAR / NEUTRO", "#f59e0b"

        # Display
        st.markdown(f'<div class="status-card" style="background-color: {cor}22; border-left: 5px solid {cor};"><h1>{sinal}</h1><p>RSI: {rsi_atual:.2f}</p></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        c2.metric("Risco Sugerido (2%)", f"$ {banca * 0.02:.2f}")

        # Gráfico
        fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color=cor))])
        fig.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("⚠️ Conexão instável com a Bolsa. Por favor, atualize a página.")
