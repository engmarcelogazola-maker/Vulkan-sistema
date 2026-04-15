import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configuração de Estilo e Página
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .info-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 20px; font-size: 14px; color: #e2e8f0; }
    .clean-disclaimer { font-size: 12px; color: #4b5563; text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# Função para conversão de moedas em tempo real
@st.cache_data(ttl=3600)
def get_cambio():
    try:
        usd_brl = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
        eur_usd = yf.download("EURUSD=X", period="1d", progress=False)['Close'].iloc[-1]
        return float(usd_brl), float(eur_usd)
    except:
        return 5.15, 1.08 

usd_brl_rate, eur_usd_rate = get_cambio()

# 2. Barra Lateral
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    st.markdown("---")
    
    if 'aceitou_termo' not in st.session_state:
        st.session_state.aceitou_termo = False

    if not st.session_state.aceitou_termo:
        st.subheader("📋 Termo de Responsabilidade")
        if st.checkbox("Aceito que esta é uma ferramenta de apoio e sou responsável por minhas operações."):
            st.session_state.aceitou_termo = True
            st.rerun()
        st.stop()

    # Janela 01: Mercado
    st.subheader("🌐 Mercado")
    mercado = st.selectbox("Escolha a categoria:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"], label_visibility="collapsed")

    # Janela 02: Ativo (Listas Completas e Fixas)
    st.subheader("📈 Ativo")
    if mercado == "Bolsa Brasileira (B3)":
        lista_ativos = {
            "Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "Itaú (ITUB4)": "ITUB4.SA",
            "Ambev (ABEV3)": "ABEV3.SA", "XP Malls (XPML11)": "XPML11.SA", "KNCR11": "KNCR11.SA",
            "HGLG11": "HGLG11.SA", "MXRF11": "MXRF11.SA"
        }
    elif mercado == "Commodities":
        lista_ativos = {
            "Soja": "ZS=F", "Milho": "ZC=F", "Petróleo Brent": "BZ=F", 
            "Ouro": "GC=F", "Prata": "SI=F", "Café": "KC=F", "Algodão": "CT=F"
        }
    else:
        lista_ativos = {
            "Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (USD)": "SOL-USD",
            "Dólar para Real": "USDBRL=X", "Euro para Dólar": "EURUSD=X", "S&P 500 Index": "^GSPC"
        }
    
    escolha_nome = st.selectbox("Selecione o ativo:", list(lista_ativos.keys()), label_visibility="collapsed")
    ticker = lista_ativos[escolha_nome]

    st.markdown("---")
    st.subheader("💰 Gestão de Banca")
    moeda_banca = st.radio("Moeda de Exibição:", ["USD", "BRL", "EUR"], horizontal=True)
    valor_banca = st.select_slider("Valor total da Banca:", options=[100, 1000, 5000, 10000, 50000, 100000, 1000000], value=1000)

# 3. Processamento de Dados
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    preco_cru = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # Lógica de Conversão Profissional
    is_centavos = ("Soja" in escolha_nome or "Milho" in escolha_nome)
    moeda_origem = "BRL" if ticker.endswith(".SA") or ticker == "USDBRL=X" else "USD"
    
    preco_unidade_base = preco_cru / 100 if is_centavos else preco_cru
    
    if moeda_origem == "USD":
        if moeda_banca == "BRL": preco_exibicao = preco_unidade_base * usd_brl_rate
        elif moeda_banca == "EUR": preco_exibicao = preco_unidade_base / eur_usd_rate
        else: preco_exibicao = preco_unidade_base
    else:
        if moeda_banca == "USD": preco_exibicao = preco_unidade_base / usd_brl_rate
        elif moeda_banca == "EUR": preco_exibicao = (preco_unidade_base / usd_brl_rate) / eur_usd_rate
        else: preco_exibicao = preco_unidade_base

    # 4. Interface
    cor = "#108542" if rsi_val < 35 else "#a50e0e" if rsi_val > 65 else "#d97706"
    sinal = "COMPRA" if rsi_val < 35 else "VENDA / RISCO" if rsi_val > 65 else "NEUTRO"
    
    st.markdown(f'<div class="status-banner" style="background-color:{cor};"><h1>VEREDITO VULKAN: {sinal} em {escolha_nome.upper()}</h1></div>', unsafe_allow_html=True)

    if is_centavos:
        saca_60kg = preco_exibicao * 2.3622
        st.markdown(f"""
            <div class="info-box">
                <b>Nota Técnica:</b> Em Chicago, o {escolha_nome} é cotado em centavos. 
                O valor de <b>{preco_cru:.2f} USD</b> equivale a <b>USD {(preco_cru/100):.4f}</b> por bushel. <br>
                📌 <b>Contrato Padrão:</b> 5.000 bushels | <b>Conversão estimada:</b> {moeda_banca} {saca_60kg:.2f} por saca (60kg).
            </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço por Unidade", f"{moeda_banca} {preco_exibicao:,.4f}")
    c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
    c3.metric("Risco Sugerido (2%)", f"{moeda_banca} {(valor_banca * 0.02):,.2f}")

    tab1, tab2 = st.tabs(["📈 Gráfico de Preço", "📉 Filtro RSI"])
    with tab1:
        fig_p = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'], high=dados['High'], low=dados['Low'], close=dados['Close'], name='Preço')])
        fig_p.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)
    with tab2:
        fig_r = go.Figure(data=[go.Scatter(x=dados.index, y=dados['RSI'], line=dict(color='#9b51e0', width=2))])
        fig_r.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown('<div class="clean-disclaimer">VULKAN SYSTEM | Inteligência Aplicada ao Mercado Multicamadas.</div>', unsafe_allow_html=True)
else:
    st.error("⚠️ Dados não disponíveis para este ativo no momento.")
