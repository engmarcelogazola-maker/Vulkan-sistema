import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Setup de Página e Identidade Visual
st.set_page_config(page_title="VULKAN SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 12px; padding: 18px; border: 1px solid #30363d; }
    .status-banner { 
        padding: 25px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 25px; 
        border: 1px solid rgba(255,255,255,0.1); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3); 
    }
    .clean-disclaimer { 
        font-size: 12px; 
        color: #4b5563; 
        text-align: center; 
        margin-top: 50px; 
        padding: 20px; 
        border-top: 1px solid #1f2937; 
    }
    </style>
    """, unsafe_allow_html=True)

# Função para conversão de moedas em tempo real
@st.cache_data(ttl=3600)
def get_cambio():
    try:
        # Busca cotação atual do Dólar e Euro
        usd_brl = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
        eur_usd = yf.download("EURUSD=X", period="1d", progress=False)['Close'].iloc[-1]
        return float(usd_brl), float(eur_usd)
    except:
        return 5.15, 1.08 # Fallback caso a API falhe

usd_brl_rate, eur_usd_rate = get_cambio()

# 2. Barra Lateral: Fluxo de Acesso e Filtros
with st.sidebar:
    st.title("🛡️ VULKAN SYSTEM")
    st.markdown("---")
    
    # Trava de Segurança: Termo de Responsabilidade
    if 'aceitou_termo' not in st.session_state:
        st.session_state.aceitou_termo = False

    if not st.session_state.aceitou_termo:
        st.subheader("📋 Termo de Uso")
        st.info("Para liberar o acesso, confirme sua ciência abaixo:")
        if st.checkbox("Aceito que esta é uma ferramenta de apoio estatístico e que toda decisão financeira é de minha inteira responsabilidade."):
            st.session_state.aceitou_termo = True
            st.rerun()
        st.stop()
    else:
        st.success("✅ Acesso Liberado")

    # Seleção de Mercado (Janela 01)
    st.subheader("🌐 Mercado")
    mercado = st.selectbox("Escolha a categoria:", ["Bolsa Brasileira (B3)", "Commodities", "Moedas & Cripto"], label_visibility="collapsed")

    # Seleção de Ativo (Janela 02)
    st.subheader("📈 Ativo")
    if mercado == "Bolsa Brasileira (B3)":
        lista_ativos = {
            "Petrobras (PETR4)": "PETR4.SA", "Vale (VALE3)": "VALE3.SA", "Itaú (ITUB4)": "ITUB4.SA",
            "Ambev (ABEV3)": "ABEV3.SA", "XP Malls (XPML11)": "XPML11.SA", "KNCR11": "KNCR11.SA",
            "HGLG11": "HGLG11.SA", "MXRF11": "MXRF11.SA"
        }
    elif mercado == "Commodities":
        lista_ativos = {
            "Petróleo Brent": "BZ=F", "Ouro": "GC=F", "Prata": "SI=F", "Soja": "ZS=F",
            "Milho": "ZC=F", "Café": "KC=F", "Algodão": "CT=F"
        }
    else:
        lista_ativos = {
            "Bitcoin (USD)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (USD)": "SOL-USD",
            "Dólar para Real": "USDBRL=X", "Euro para Dólar": "EURUSD=X", "S&P 500 Index": "^GSPC"
        }
    
    escolha_nome = st.selectbox("Selecione o ativo:", list(lista_ativos.keys()), label_visibility="collapsed")
    ticker = lista_ativos[escolha_nome]

    # Gestão de Banca com Barra Interativa
    st.markdown("---")
    st.subheader("💰 Gestão de Banca")
    moeda_banca = st.radio("Exibir valores em:", ["USD", "BRL", "EUR"], horizontal=True)
    valor_banca = st.select_slider(
        "Valor total da Banca:",
        options=[100, 1000, 5000, 10000, 50000, 100000, 1000000],
        value=1000
    )

# 3. Processamento de Dados (Lógica de Inteligência VULKAN)
dados = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not dados.empty:
    # Cálculos Técnicos (RSI e Médias)
    dados['SMA20'] = dados['Close'].rolling(window=20).mean()
    delta = dados['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    dados['RSI'] = 100 - (100 / (1 + (gain / loss)))

    preco_raw = float(dados['Close'].values.ravel()[-1])
    rsi_val = float(dados['RSI'].values.ravel()[-1])

    # Lógica de Conversão de Moedas Matemática
    moeda_origem = "BRL" if ticker.endswith(".SA") or ticker == "USDBRL=X" else "USD"
    preco_convertido = preco_raw

    if moeda_origem == "USD":
        if moeda_banca == "BRL": preco_convertido = preco_raw * usd_brl_rate
        elif moeda_banca == "EUR": preco_convertido = preco_raw / eur_usd_rate
    elif moeda_origem == "BRL":
        if moeda_banca == "USD": preco_convertido = preco_raw / usd_brl_rate
        elif moeda_banca == "EUR": preco_convertido = (preco_raw / usd_brl_rate) / eur_usd_rate

    # Unidades de Medida para Commodities
    unid = ""
    if mercado == "Commodities":
        if "Soja" in escolha_nome or "Milho" in escolha_nome: unid = " /bu"
        elif "Petróleo" in escolha_nome: unid = " /barril"
        elif "Ouro" in escolha_nome or "Prata" in escolha_nome: unid = " /oz t"
        elif "Café" in escolha_nome or "Algodão" in escolha_nome: unid = " /lb"

    # Lógica de Veredito Personalizado por Ativo
    if rsi_val < 35:
        sinal, cor = f"COMPRA: {escolha_nome.upper()}", "#108542"
        instrucao = f"A VULKAN detectou exaustão vendedora. Região de oportunidade para {escolha_nome}."
    elif rsi_val > 65:
        sinal, cor = f"VENDA / RISCO: {escolha_nome.upper()}", "#a50e0e"
        instrucao = f"Sobrecompra detectada. Sugerido reduzir exposição ou realizar lucros em {escolha_nome}."
    else:
        sinal, cor = f"NEUTRO: {escolha_nome.upper()}", "#d97706"
        instrucao = f"Sem vantagem clara no momento para {escolha_nome}. Preserve sua banca."

    # 4. Interface Principal
    st.markdown(f"""
        <div class="status-banner" style="background-color:{cor};">
            <h1 style="color:white; margin:0; font-size: 26px; font-weight: bold;">VEREDITO VULKAN: {sinal}</h1>
            <p style="color:white; opacity:0.9; margin-top:10px; font-size: 16px;">{instrucao}</p>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Atual", f"{moeda_banca} {preco_convertido:,.2f}{unid}")
    c2.metric("Termômetro RSI", f"{rsi_val:.2f}")
    c3.metric("Risco Sugerido (2%)", f"{moeda_banca} {(valor_banca * 0.02):,.2f}")

    tab1, tab2 = st.tabs(["📈 Gráfico de Preço", "📉 Filtro de Força (RSI)"])
    
    with tab1:
        fig_p = go.Figure(data=[go.Candlestick(x=dados.index, open=dados['Open'].values.ravel(), high=dados['High'].values.ravel(), 
                                               low=dados['Low'].values.ravel(), close=dados['Close'].values.ravel(), name='Preço')])
        fig_p.add_trace(go.Scatter(x=dados.index, y=dados['SMA20'].values.ravel(), name='Média 20', line=dict(color='#00d4ff', width=1.5)))
        fig_p.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)
    
    with tab2:
        fig_r = go.Figure()
        fig_r.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig_r.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
        fig_r.add_trace(go.Scatter(x=dados.index, y=dados['RSI'].values.ravel(), name='RSI', line=dict(color='#9b51e0', width=2)))
        fig_r.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 100]), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_r, use_container_width=True)

    # 5. Rodapé Profissional (Disclaimer Clean)
    st.markdown(f"""
        <div class="clean-disclaimer">
            VULKAN SYSTEM | A inteligência de dados aplicada ao mercado multicamadas. <br>
            Aviso: Toda decisão financeira é de responsabilidade exclusiva do investidor.
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("⚠️ Erro ao carregar dados. Verifique a conexão ou selecione outro ativo no menu lateral.")
