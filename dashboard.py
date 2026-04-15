import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. SETUP E ESTILO
st.set_page_config(page_title="VULKAN | Inteligência Financeira", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #05070a !important; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; }
    .status-card { 
        padding: 20px; border-radius: 10px; text-align: center; 
        margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); 
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    opcoes = {
        "Dólar/Real (USD-BRL)": "USDBRL=X",
        "Bitcoin (BTC-USD)": "BTC-USD", 
        "Ethereum (ETH-USD)": "ETH-USD",
        "Solana (SOL-USD)": "SOL-USD"
    }
    ticker = opcoes[st.selectbox("Ativo Principal:", list(opcoes.keys()), key="sb_ativo")]
    st.markdown("---")
    st.subheader("🛡️ Gestão de Risco")
    banca = st.number_input("Sua Banca ($)", min_value=0.0, value=1000.0, key="ni_banca")
    risco_perc = st.slider("Risco por Operação (%)", 1, 5, 2, key="sl_risco")

# 3. LÓGICA TÉCNICA
try:
    dados = yf.download(ticker, period="6mo", interval="1d")
    if not dados.empty:
        # Cálculos Técnicos (RSI)
        delta = dados['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        dados['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        preco_atual = float(dados['Close'].iloc[-1])
        rsi_val = float(dados['RSI'].iloc[-1])

        # DEFINIÇÃO DE ESTRATÉGIA AUTOMÁTICA
        if rsi_val < 35:
            sinal, cor = "COMPRA FORTE", "#10b981"
            explica = f"🔥 **POR QUE COMPRAR?** O RSI está em {rsi_val:.2f}, indicando que o ativo está 'sobrevendido'. A pressão de venda exauriu e o preço está em zona de desconto."
        elif rsi_val > 65:
            sinal, cor = "VENDA / ALTO RISCO", "#ef4444"
            explica = f"⚠️ **POR QUE VENDER?** O RSI está em {rsi_val:.2f}, indicando que o ativo está 'sobrecomprado'. O mercado está esticado e há risco de correção imediata."
        else:
            sinal, cor = "AGUARDAR / NEUTRO", "#f59e0b"
            explica = f"⚖️ **POR QUE AGUARDAR?** O RSI está em {rsi_val:.2f} (nível neutro). O investidor profissional aguarda as extremidades para ter maior vantagem estatística."

        # 4. EXIBIÇÃO
        st.markdown(f'''
            <div class="status-card" style="background-color: {cor}22; border-left: 5px solid {cor};">
                <h1 style="color: white; margin:0;">{sinal}</h1>
            </div>
            ''', unsafe_allow_html=True)
        
        st.info(explica)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
        c3.metric("Risco Sugerido", f"$ {banca * (risco_perc / 100):.2f}")

        # Gráfico
        st.subheader("📊 Gráfico de Tendência")
        fig = go.Figure(data=[go.Scatter(x=dados.index, y=dados['Close'], name="Preço", line=dict(color=cor))])
        fig.update_layout(template="plotly_dark", height=350, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Erro ao conectar com o mercado. Tente atualizar a página.")
