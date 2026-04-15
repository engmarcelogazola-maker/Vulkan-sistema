import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO DE ALTO NÍVEL
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #05070a !important; }
    .stMetric { background-color: #11151c; border: 1px solid #1e2530; border-radius: 10px; padding: 15px; }
    .status-card { padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    # Tickers otimizados
    opcoes = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Dólar (USD/BRL)": "BRL=X",
        "S&P 500": "^GSPC"
    }
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes.keys()))
    ticker = opcoes[escolha]
    st.markdown("---")
    banca = st.number_input("Sua Banca ($)", value=1000.0)

# 3. FUNÇÃO DE DADOS COM CACHE (PARA NÃO TRAVAR)
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos para evitar bloqueio
def load_data(symbol):
    # Força o download sem usar threads para evitar erro no servidor
    d = yf.download(symbol, period="1mo", interval="1d", threads=False, progress=False)
    return d

# 4. EXECUÇÃO
try:
    df = load_data(ticker)
    
    if df is not None and not df.empty and len(df) > 1:
        # Cálculo de RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi_series = 100 - (100 / (1 + (gain / loss)))
        
        # Pegar os valores mais recentes de forma segura
        ultimo_preco = float(df['Close'].iloc[-1])
        ultimo_rsi = float(rsi_series.iloc[-1])

        # Veredito VULKAN
        if ultimo_rsi < 35: sinal, cor, msg = "COMPRA FORTE", "#10b981", "Ativo subvalorizado. Oportunidade de entrada."
        elif ultimo_rsi > 65: sinal, cor, msg = "VENDA / RISCO", "#ef4444", "Ativo sobrecomprado. Grande chance de correção."
        else: sinal, cor, msg = "NEUTRO / AGUARDAR", "#f59e0b", "Mercado em equilíbrio. Aguarde os extremos."

        # INTERFACE
        st.markdown(f'''
            <div class="status-card" style="background-color: {cor}22; border-left: 5px solid {cor};">
                <h1 style="color: white; margin:0;">{sinal}</h1>
                <p style="margin:5px 0 0 0; opacity:0.8;">{msg}</p>
            </div>
        ''', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Preço Atual", f"$ {ultimo_preco:,.2f}")
        c2.metric("RSI (14)", f"{ultimo_rsi:.2f}")
        c3.metric("Risco (2%)", f"$ {banca * 0.02:.2f}")

        # Gráfico
        fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color=cor, width=2))])
        fig.update_layout(template="plotly_dark", height=350, margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("⚠️ Erro de Sincronização. Por favor, selecione outro ativo na barra lateral para destravar.")

except Exception as e:
    st.info("🔄 Conectando aos servidores globais... Troque o ativo na lateral se demorar.")
