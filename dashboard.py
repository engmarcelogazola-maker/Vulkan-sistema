import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO VISUAL PREMIUM
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
    st.subheader("Configurações")
    # Tickers corrigidos para maior estabilidade
    opcoes = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Dólar (USD/BRL)": "USDBRL=X",
        "S&P 500": "^GSPC"
    }
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes.keys()))
    ticker = opcoes[escolha]
    
    st.markdown("---")
    banca = st.number_input("Sua Banca ($)", min_value=0.0, value=1000.0)
    risco_perc = st.slider("Risco por Operação (%)", 1, 5, 2)

# 3. PROCESSAMENTO DE DADOS (COM TRAVA DE SEGURANÇA)
try:
    # Busca dados do último mês
    df = yf.download(ticker, period="1mo", interval="1d")
    
    if df.empty:
        st.error("⚠️ Erro: Não foi possível obter dados do mercado agora. Tente novamente em instantes.")
    else:
        # Cálculo do RSI (Indicador de Decisão)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        preco_atual = float(df['Close'].iloc[-1])
        rsi_atual = float(df['RSI'].iloc[-1])

        # Lógica do Veredito VULKAN
        if rsi_atual < 35:
            sinal, cor = "COMPRA FORTE", "#10b981" # Verde
            desc = "Ativo em zona de desconto extrema. Alta probabilidade de subida."
        elif rsi_atual > 65:
            sinal, cor = "VENDA / ALTO RISCO", "#ef4444" # Vermelho
            desc = "Ativo sobrecomprado. Grande risco de correção negativa."
        else:
            sinal, cor = "AGUARDAR / NEUTRO", "#f59e0b" # Laranja
            desc = "Mercado sem tendência clara. Proteja o seu capital."

        # 4. INTERFACE DO PRODUTO
        st.markdown(f'''
            <div class="status-card" style="background-color: {cor}22; border-left: 5px solid {cor};">
                <h3 style="color: {cor}; margin: 0;">VEREDITO DO SISTEMA</h3>
                <h1 style="color: white; margin: 10px 0;">{sinal}</h1>
                <p style="color: white; opacity: 0.8;">{desc}</p>
            </div>
            ''', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        c2.metric("Termómetro RSI", f"{rsi_atual:.2f}")
        c3.metric("Risco Sugerido", f"$ {banca * (risco_perc / 100):.2f}")

        # Gráfico Profissional
        fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], name="Preço", line=dict(color=cor, width=3))])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.info("🔄 O sistema está a sincronizar com a Bolsa de Valores... Aguarde 5 segundos.")
