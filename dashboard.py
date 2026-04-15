import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configuração e Estilo
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); }
    .clean-disclaimer { font-size: 12px; color: #4b5563; text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# 2. Lógica de Aceite e Menu Lateral
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    st.markdown("---")
    
    # Sistema de Aceite que "some" após clicar
    if 'aceitou_termo' not in st.session_state:
        st.session_state.aceitou_termo = False

    if not st.session_state.aceitou_termo:
        st.subheader("📋 Termo de Responsabilidade")
        st.info("Para acessar a inteligência VULKAN, confirme sua ciência abaixo:")
        if st.checkbox("Compreendo que toda ação financeira é de minha inteira responsabilidade e que esta plataforma é apenas uma ferramenta de apoio estatístico."):
            st.session_state.aceitou_termo = True
            st.rerun()
        st.stop()
    else:
        st.success("✅ Acesso Autorizado")

    # JANELA 01: Seleção de Mercado
    st.subheader("🌐 Janela 01: Mercado")
    mercado = st.selectbox("Escolha a categoria:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"])

    # JANELA 02: Seleção de Ativo (Baseado na Janela 01)
    st.subheader("📈 Janela 02: Ativo")
    if mercado == "Bolsa Brasileira (B3)":
        lista_ativos = {
            "Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "Itaú (ITUB4)": "ITUB4.SA", 
            "Ambev (ABEV3)": "ABEV3.SA", "XP Malls (XPML11)": "XPML11.SA", "HGLG11": "HGLG11.SA", "KNCR11": "KNCR11.SA"
        }
    elif mercado == "Commodities":
        lista_ativos = {
            "Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Café": "KC=F", 
            "Soja": "ZS=F", "Milho": "ZC=F", "Algodão": "CT=F", "Prata": "SI=F"
        }
    else:
        lista_ativos = {
            "Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Dólar/Real": "USDBRL=X", "Euro/Dólar": "EURUSD=X"
        }
    
    ticker = lista_ativos[st.selectbox("Selecione o ativo específico:", list(lista_ativos.keys()))]

    # GESTÃO DE BANCA: Barra Deslizante e Moedas
    st.markdown("---")
    st.subheader("💰 Gestão de Banca")
    moeda_banca = st.radio("Moeda da conta:", ["USD", "BRL", "EUR"], horizontal=True)
    
    valor_banca = st.select_slider(
        f"Selecione o valor ({moeda_banca}):",
        options=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
        value=1000
    )
    # Campo para ajuste fino caso queiram digitar
    valor_ajuste = st.number_input("Ajuste fino do valor:", value=valor_banca)

# 3. Processamento de Dados
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    # Cálculos Estáveis
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    preco_atual = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # Lógica de Veredito (Mantendo o feminino nos textos)
    if rsi_val < 35: sinal, cor, desc = "COMPRA FORTE", "#108542", "A VULKAN detectou exaustão vendedora. Região estatística favorável."
    elif rsi_val > 65: sinal, cor, desc = "VENDA / RISCO", "#a50e0e", "A VULKAN detectou sobrecompra. Momento de proteção e cautela."
    else: sinal, cor, desc = "NEUTRO / AGUARDAR", "#d97706", "A VULKAN não identifica vantagem clara. Preserve sua banca."

    # 4. Interface Principal
    st.markdown(f"""
        <div class="status-banner" style="background-color:{cor};">
            <h1 style="color:white; margin:0; font-size: 26px;">VEREDITO VULKAN: {sinal}</h1>
            <p style="color:white; opacity:0.9; margin-top:5px;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"{moeda_banca} {preco_atual:,.2f}")
    c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
    c3.metric("Risco Sugerido (2%)", f"{moeda_banca} {(valor_ajuste * 0.02):,.2f}")

    tab1, tab2 = st.tabs(["📈 Gráfico", "📉 Filtro RSI"])
    with tab1:
        fig = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(), high=dados['High'].values.ravel(), 
                                               low=dados['Low'].values.ravel(), close=dados['Close'].values.ravel())])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig_r = go.Figure(data=[go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), line=dict(color='#9b51e0'))])
        fig_r.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_r, use_container_width=True)

    # 5. Rodapé Clean
    st.markdown(f"""
        <div class="clean-disclaimer">
            VULKAN SYSTEM | A inteligência de dados aplicada ao mercado. <br>
            Aviso: Esta ferramenta fornece dados estatísticos. Toda decisão financeira é de responsabilidade exclusiva do investidor.
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("Erro ao carregar dados. Tente selecionar outro ativo.")
