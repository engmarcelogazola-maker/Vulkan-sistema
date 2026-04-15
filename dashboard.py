import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configuração de Estilo e Página
st.set_page_config(page_title="VULKAN - Inteligência de Dados", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    .status-banner {
        padding: 25px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 30px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Título e Menu Lateral
st.title("🛡️ VULKAN: Inteligência Financeira")

with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Lista expandida com FIIs e Ações
    opcoes_ativos = {
        "Bitcoin (USD)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Dólar para Real": "USDBRL=X",
        "FII XP Malls (XPML11)": "XPML11.SA",
        "FII Kinea RI (KNCR11)": "KNCR11.SA",
        "FII HGLG11": "HGLG11.SA",
        "Ação Petrobras (PETR4)": "PETR4.SA",
        "S&P 500 Index": "^GSPC"
    }
    
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes_ativos.keys()))
    ticker = opcoes_ativos[escolha]

    ticker_manual = st.text_input("Ou digite o código (ex: MXRF11.SA):", "")
    if ticker_manual:
        ticker = ticker_manual.upper()

    st.markdown("---")
    st.subheader("💰 Gestão de Risco")
    banca = st.number_input("Sua Banca ($ ou R$)", value=1000.0)

# 3. Busca de Dados (Sua lógica estável)
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    # Seus cálculos originais mantidos integralmente
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # Extração segura
    preco_atual = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])
    sma20_val = float(dados['SMA20'].values.ravel()[-1])

    # Lógica do Veredito
    if rsi_val < 35:
        sinal, cor = "COMPRA FORTE", "#108542" # Verde
    elif rsi_val > 65:
        sinal, cor = "VENDA / ALTO RISCO", "#a50e0e" # Vermelho
    else:
        sinal, cor = "AGUARDAR / NEUTRO", "#d97706" # Laranja

    # 4. Banner de Veredito
    st.markdown(f"""
        <div class="status-banner" style="background-color:{cor};">
            <h1 style="color:white; margin:0; font-size: 30px;">VEREDITO: {sinal}</h1>
            <p style="color:white; opacity:0.9; margin-top:5px;">Análise baseada em Força Relativa e Tendência</p>
        </div>
        """, unsafe_allow_html=True)

    # 5. Métricas e Calculadora de Posição
    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"{preco_atual:,.2f}")
    c2.metric("Termómetro RSI", f"{rsi_val:.2f}")
    
    # Sugestão de lote baseada em 2% de risco (Útil para o seu cliente LTA)
    risco_sugerido = banca * 0.02
    c3.metric("Risco Sugerido (2%)", f"{risco_sugerido:,.2f}")

    # 6. Gráficos em Abas
    tab1, tab2 = st.tabs(["📈 Gráfico de Preço", "📊 Força do Ativo"])

    with tab1:
        fig_preco = go.Figure()
        fig_preco.add_trace(go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(),
                    high=dados['High'].values.ravel(), low=dados['Low'].values.ravel(),
                    close=dados['Close'].values.ravel(), name='Preço'))
        fig_preco.add_trace(go.Scatter(x=dados.index, y=dados['SMA20'].values.ravel(), name='Média 20', line=dict(color='#00d4ff', width=1.5)))
        fig_preco.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_preco, use_container_width=True)

    with tab2:
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.add_trace(go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), name='RSI', line=dict(color='#9b51e0', width=2)))
        fig_rsi.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_rsi, use_container_width=True)

else:
    st.error("⚠️ Sincronizando com a Bolsa de Valores... Selecione outro ativo para destravar.")
