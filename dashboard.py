import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configuração da Página e Estilo Premium
st.set_page_config(page_title="VULKAN - Inteligência Financeira", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
    [data-testid="stMetricValue"] { font-size: 26px !important; }
    .status-banner {
        padding: 30px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 30px;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .status-banner p { color: white !important; font-size: 16px; margin-top: 12px; opacity: 0.95; }
    .status-banner b { color: #f0f0f0 !important; font-weight: bold; }
    .disclaimer-box {
        background-color: #1a1c23;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #f59e0b;
        font-size: 14px;
        color: #94a3b8;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Barra Lateral: "A" VULKAN e Termo de Aceite
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1162/1162501.png", width=70) # Ícone ilustrativo
    st.title("🛡️ A VULKAN SYSTEM")
    st.markdown("---")
    
    st.subheader("📋 Termo de Responsabilidade")
    termo = st.checkbox("Estou ciente que esta plataforma é uma ferramenta de apoio e que toda decisão financeira é de minha inteira responsabilidade.")
    
    if not termo:
        st.warning("⚠️ Você precisa aceitar os termos para liberar o acesso à análise.")
        st.stop()

    st.success("✅ Acesso Liberado")
    st.markdown("---")

    # Lista de ativos estável
    opcoes_ativos = {
        "Bitcoin (USD)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Dólar para Real": "USDBRL=X",
        "FII XP Malls (XPML11)": "XPML11.SA",
        "FII HGLG11": "HGLG11.SA",
        "Ação Petrobras (PETR4)": "PETR4.SA",
        "S&P 500 Index": "^GSPC"
    }
    escolha = st.selectbox("Selecione o Ativo:", list(opcoes_ativos.keys()))
    ticker = opcoes_ativos[escolha]

    # Campo manual otimizado
    ticker_manual = st.text_input("Ou digite o código manualmente (ex: SOL-USD):", "")
    if ticker_manual:
        ticker = ticker_manual.upper()

    # Gestão de Banca (Retornando o saldo)
    st.markdown("---")
    st.subheader("💰 Gestão de Banca")
    banca = st.number_input("Sua Banca ($ ou R$)", value=1000.0)

# 3. Busca de Dados (Lógica que funcionou perfeitamente)
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty and len(dados) > 50:
    # Seus cálculos originais mantidos
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # Extração de valores (Usando ravel)
    preco_atual = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])
    sma20_val = float(dados['SMA20'].values.ravel()[-1])

    # Lógica do Veredito Educativo (Lapidado)
    if rsi_val < 35:
        sinal, cor, desc = "COMPRA FORTE", "#108542", "A região indica exaustão vendedora. É uma oportunidade estatística, não uma garantia."
    elif rsi_val > 65:
        sinal, cor, desc = "VENDA / RISCO", "#a50e0e", "O preço está esticado acima da média. Momento de cautela e proteção de capital."
    else:
        sinal, cor, desc = "NEUTRO / AGUARDAR", "#d97706", "Sem vantagem estatística clara no momento. Preserve sua banca e aguarde."

    # 4. Banner de Veredito com Dados Otimizados (Retornando as informações)
    st.markdown(f"""
        <div class="status-banner" style="background-color:{cor};">
            <h1 style="color:white; margin:0; font-size: 32px; font-weight: bold;">VEREDITO DA VULKAN: {sinal}</h1>
            <p>
                <b>Ativo:</b> {ticker} | <b>Preço:</b> ${preco_atual:,.2f} | <b>RSI (14d):</b> {rsi_val:.2f} | <b>Média (20d):</b> ${sma20_val:,.2f}
            </p>
            <small style="color:white; opacity:0.85; margin-top:10px;">{desc}</small>
        </div>
        """, unsafe_allow_html=True)

    # 5. Métricas e Calculadora de Posição (Retornando a banca)
    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
    c2.metric("Termómetro RSI", f"{rsi_val:.2f}")
    
    # Sugestão de lote baseada em 2% de risco
    risco_sugerido = banca * 0.02
    c3.metric("Risco Sugerido (2%)", f"$ {risco_sugerido:,.2f}")

    # 6. Gráficos Profissionais (Candlestick e RSI em colunas)
    tab1, tab2 = st.tabs(["📈 Gráfico de Preço", "📊 Força Relativa (RSI)"])

    with tab1:
        fig_preco = go.Figure()
        fig_preco.add_trace(go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(),
                    high=dados['High'].values.ravel(), low=dados['Low'].values.ravel(),
                    close=dados['Close'].values.ravel(), name='Preço'))
        fig_preco.add_trace(go.Scatter(x=dados.index, y=dados['SMA20'].values.ravel(), name='Média 20', line=dict(color='#00d4ff', width=1.8)))
        fig_preco.update_layout(template="plotly_dark", height=480, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10))
        st.plotly_chart(fig_preco, use_container_width=True)

    with tab2:
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.add_trace(go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), name='RSI', line=dict(color='#9b51e0', width=2)))
        fig_rsi.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]), margin=dict(l=10,r=10))
        st.plotly_chart(fig_rsi, use_container_width=True)

    # 7. Cláusula de Responsabilidade Fixa no Rodapé
    st.markdown(f"""
        <div class="disclaimer-box">
            <strong>⚠️ AVISO LEGAL IMPORTANTE:</strong> A VULKAN SYSTEM é uma plataforma de análise de dados e estatísticas históricas. 
            O mercado financeiro envolve riscos significativos. Toda e qualquer decisão de investimento é de sua inteira responsabilidade. 
            Este site não fornece recomendações diretas. Retornos passados não garantem lucros futuros. 
            Não invista capital que você não pode perder.
        </div>
    """, unsafe_allow_html=True)

else:
    st.error("⚠️ Sincronizando com a Bolsa de Valores... Selecione outro ativo na lateral para destravar.")
