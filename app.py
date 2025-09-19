import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel de Visões de Mercado",
    page_icon="📊",
    layout="wide"
)

# --- CARREGAMENTO DOS DADOS ---
# Função para carregar os dados do CSV. O @st.cache_data garante que os dados
# não sejam recarregados a cada interação do usuário, melhorando a performance.
@st.cache_data
def carregar_dados():
    df = pd.read_csv('dados_mercado.csv')
    # Converte a coluna de visão para um tipo categórico com ordem definida
    # Isso garante que o heatmap e os filtros apareçam na ordem correta.
    ordem_visoes = ['Strong Overweight', 'Overweight', 'Neutral', 'Underweight', 'Strong Underweight']
    df['visao_categorica'] = pd.Categorical(df['visao'], categories=ordem_visoes, ordered=True)
    return df

df = carregar_dados()

# --- TÍTULO DO PAINEL ---
st.title("📊 Painel Consolidado de Visões de Mercado")
st.markdown("Análise das principais visões de mercado das gestoras globais e locais.")

# --- EXIBIÇÃO DOS DADOS BRUTOS (temporário) ---
st.subheader("Dados Carregados")
st.dataframe(df)
