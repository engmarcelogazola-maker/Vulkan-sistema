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
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .disclaimer-box {
        background-color: #1a1c23;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
        font-size: 13px;
        color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Barra Lateral e Termo de Aceite
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    st.markdown("---")
    
    st.subheader("📋 Termo de Responsabilidade")
    termo_aceite = st.checkbox("Estou ciente que este app é uma ferramenta de apoio e que toda decisão financeira é de minha inteira responsabilidade.")
    
    if not termo_aceite:
        st.warning("⚠️ Você precisa aceitar os termos na lateral para visualizar a análise.")
        st.stop() # Interrompe o código aqui se não "tikar"

    st.success("✅ Acesso Liberado")
    st.markdown("---")
    
    st.header("⚙️ Configurações")
    opcoes_ativos = {
        "Bitcoin (USD)": "BTC-USD",
        "Dólar para Real": "USDBRL=X",
        "FII XP Malls (XPML11)": "XPML11.SA",
        "FII Kinea RI (KNCR11)": "KNCR11.SA",
        "Ação Petrobras (PETR4)": "PETR4.SA",
        "S&P 500 Index": "^GSPC"
    }
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes_ativos.keys()))
    ticker = opcoes_ativos[escolha]

# 3. Busca de Dados (Sua lógica estável)
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    # Cálculos originais
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    preco_atual = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # Lógica do Veredito Educativo
    if rsi_val < 35:
        sinal, cor = "COMPRA FORTE", "#108542"
        contexto = "O mercado indica exaustão vendedora. É uma região de oportunidade estatística, não uma garantia de lucro."
    elif rsi_val > 65:
        sinal, cor = "VENDA / ALTO RISCO", "#a50e0e"
        contexto = "O preço está esticado acima da média histórica. Momento de cautela e proteção de capital."
    else:
        sinal, cor = "AGUARDAR / NEUTRO", "#d97706"
        contexto = "Sem vantagem clara no momento. O segredo do investidor é saber esperar a oportunidade certa."

    # 4. Interface Principal
    st.title("📊 Painel de Análise de Dados")
    
    st.markdown(f"""
        <div class="status-banner" style="background-color:{cor};">
            <h1 style="color:white; margin:0; font-size: 28px;">VEREDITO: {sinal}</h1>
            <p style="color:white; opacity:0.9; margin-top:5px;">{contexto}</p>
        </div>
        """, unsafe_allow_html=True)

    # 5. Gráficos em Abas
    tab1, tab2 = st.tabs(["📈 Gráfico", "📉 Filtro RSI"])
    with tab1:
        fig_preco = go.Figure()
        fig_preco.add_trace(go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(),
                    high=dados['High'].values.ravel(), low=dados['Low'].values.ravel(),
                    close=dados['Close'].values.ravel(), name='Preço'))
        fig_preco.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_preco, use_container_width=True)
    
    with tab2:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), line=dict(color='#9b51e0')))
        fig_rsi.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_rsi, use_container_width=True)

    # 6. Rodapé de Aviso Fixo (Obrigatório para LTA)
    st.markdown("""
        <div class="disclaimer-box">
            <strong>⚠️ AVISO LEGAL:</strong> Esta plataforma não é uma recomendação direta de investimento. 
            O mercado financeiro envolve riscos. O VULKAN fornece dados estatísticos para auxiliar sua decisão, 
            mas o resultado final depende exclusivamente da sua gestão de risco. Não use dinheiro que você não pode perder.
        </div>
    """, unsafe_allow_html=True)

else:
    st.error("Erro ao carregar dados.")
