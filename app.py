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
@st.cache_data
def carregar_dados():
    df = pd.read_csv('dados_mercado.csv')
    ordem_visoes = ['Overweight', 'Neutral', 'Underweight'] # Simplificado para o exemplo
    # Usaremos a coluna 'visao' diretamente, o Plotly pode ordenar
    return df

df = carregar_dados()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")
gestoras_selecionadas = st.sidebar.multiselect(
    "Selecione a(s) Gestora(s):",
    options=df['gestora'].unique(),
    default=df['gestora'].unique()
)

# Filtra o dataframe principal com base na seleção
df_filtrado = df[df['gestora'].isin(gestoras_selecionadas)]

# --- TÍTULO DO PAINEL ---
st.title("📊 Painel Consolidado de Visões de Mercado")
st.markdown("Análise das principais visões de mercado das gestoras globais e locais.")

# --- RESUMOS DE TEXTO (CONSENSO E DIVERGÊNCIAS) ---
st.subheader("Principais Consensos e Divergências")

# Encontra a visão mais comum (consenso) para cada subclasse de ativo
consenso = df_filtrado.groupby('sub_classe_ativo')['visao'].agg(lambda x: x.mode()[0] if not x.mode().empty else 'N/A').reset_index()
consenso.columns = ['Sub-Classe de Ativo', 'Visão de Consenso']

col1, col2 = st.columns(2)

with col1:
    st.info("Visão de Consenso por Ativo")
    st.dataframe(consenso, use_container_width=True)

with col2:
    st.warning("Destaques")
    # Exemplo simples de destaque
    overweights = df_filtrado[df_filtrado['visao'] == 'Overweight']['sub_classe_ativo'].nunique()
    underweights = df_filtrado[df_filtrado['visao'] == 'Underweight']['sub_classe_ativo'].nunique()
    st.markdown(f"Atualmente, há **{overweights}** subclasses com pelo menos uma visão 'Overweight' e **{underweights}** com pelo menos uma visão 'Underweight' no filtro atual.")


# --- HEATMAP DE VISÕES ---
st.subheader("Heatmap de Visões de Mercado")

if not df_filtrado.empty:
    # Prepara a tabela para o heatmap (pivot)
    heatmap_data = df_filtrado.pivot_table(
        index='sub_classe_ativo',
        columns='gestora',
        values='visao',
        aggfunc=lambda x: ' '.join(x) # Simplesmente junta as visões se houver duplicatas
    ).fillna('N/A') # Preenche células vazias

    # Mapeia as visões para valores numéricos para o Plotly colorir
    mapa_cores_valores = {'Overweight': 3, 'Neutral': 2, 'Underweight': 1, 'N/A': 0}
    heatmap_data_numerica = heatmap_data.applymap(lambda x: mapa_cores_valores.get(x, 0))

    fig = px.imshow(
        heatmap_data_numerica,
        text_auto=False, # Para não mostrar os números nas células
        aspect="auto",
        labels=dict(x="Gestora", y="Sub-Classe de Ativo", color="Nível de Visão"),
        color_continuous_scale=[(0, "#E0E0E0"), (0.25, "#D9534F"), (0.5, "#FFC107"), (1, "#5CB85C")] # N/A, Under, Neutral, Over
    )

    # Adiciona o texto original de volta como anotação (hover text)
    fig.update_traces(
        hovertemplate="<b>Gestora:</b> %{x}<br><b>Ativo:</b> %{y}<br><b>Visão:</b> %{customdata}<extra></extra>",
        customdata=heatmap_data
    )

    fig.update_layout(
        height=600,
        xaxis_title="",
        yaxis_title="",
        coloraxis_showscale=False # Esconde a barra de cores contínua
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhuma gestora selecionada ou dados disponíveis para a seleção.")


# --- EXIBIÇÃO DOS DADOS COMPLETOS (opcional) ---
with st.expander("Ver tabela de dados completa"):
    st.dataframe(df_filtrado)
