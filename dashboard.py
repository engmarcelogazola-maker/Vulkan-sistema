import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DE ALTA PERFORMANCE
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

# Cache para o site carregar instantaneamente para o cliente
@st.cache_data(ttl=3600)  # Guarda os dados por 1 hora para evitar bloqueios
def buscar_dados(ticker):
    try:
        # Busca direta e simplificada
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        return df
    except:
        return pd.DataFrame()

# Estilo Visual
st.markdown("""
    <style>
    .main { background-color: #05070a !important; }
    .status-card { padding: 20px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.1); color: white !important; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. INTERFACE LATERAL
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    # Tickers simplificados (mais fáceis de o Yahoo encontrar)
    opcoes = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Dólar": "USDBRL=X",
        "S&P 500": "^GSPC"
    }
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes.keys()))
    ticker = opcoes[escolha]
    banca = st.number_input("Sua Banca ($)", value=1000.0)

# 3. EXECUÇÃO PRINCIPAL
df = buscar_dados(ticker)

if not df.empty and len(df) > 14:
    # Cálculo do RSI (Otimizado)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    rsi_val = float(rsi.iloc[-1])
    preco = float(df['Close'].iloc[-1])

    # Lógica de Cores e Sinais
    if rsi_val < 35: sinal, cor = "COMPRA FORTE", "#10b981"
    elif rsi_val > 65: sinal, cor = "VENDA / ALTO RISCO", "#ef4444"
    else: sinal, cor = "AGUARDAR / NEUTRO", "#f59e0b"

    # Display Premium
    st.markdown(f'''
        <div class="status-card" style="background-color: {cor}22; border-left: 5px solid {cor};">
            <h2 style="margin:0; color:{cor};">{sinal}</h2>
            <p style="margin:5px 0 0 0;">Análise baseada em exaustão de preço (RSI: {rsi_val:.2f})</p>
        </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Preço Atual", f"$ {preco:,.2f}")
    col2.metric("Termómetro", f"{rsi_val:.2f}")
    col3.metric("Risco Sugerido", f"$ {banca * 0.02:.2f}")

    # Gráfico de Linha (Muito mais rápido que Candlestick no servidor)
    fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color=cor, width=2))])
    fig.update_layout(template="plotly_dark", height=350, margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⚠️ O sistema está a recalibrar os dados do Yahoo Finance. Por favor, selecione outro ativo na lateral para forçar a atualização.")
