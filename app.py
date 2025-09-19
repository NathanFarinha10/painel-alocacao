import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from PyPDF2 import PdfReader
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Painel de Visões de Mercado",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÕES ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv('dados_mercado.csv')
        df['data_referencia'] = pd.to_datetime(df['data_referencia'])
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            'data_referencia', 'gestora', 'classe_ativo', 
            'sub_classe_ativo', 'visao', 'resumo_tese', 'frase_justificativa'
        ])
    return df

# (As funções de extração de PDF e IA permanecem as mesmas)
def extrair_texto_pdf(arquivo_pdf):
    # ... código inalterado ...
    leitor_pdf = PdfReader(arquivo_pdf)
    texto = ""
    for pagina in leitor_pdf.pages:
        texto += pagina.extract_text()
    return texto

def extrair_visoes_com_ia(texto_relatorio, nome_gestora):
    # ... código inalterado ...
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception:
        st.error("Chave de API do Google não configurada.")
        return None
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    prompt = f"""
    Você é um assistente de análise financeira altamente preciso...
    ...
    - "frase_justificativa": A citação EXATA (copiada e colada) do texto que justifica a visão atribuída.

    **Exemplo de Saída Esperada (deve ser um JSON válido):**
    [
        {{
            "data_referencia": "{data_hoje}",
            "gestora": "BlackRock",
            ...
            "frase_justificativa": "Mantemos nossa preferência por ações dos EUA devido à força de sua economia..."
        }}
    ]
    ...
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# --- CARREGAMENTO INICIAL DOS DADOS ---
df = carregar_dados()

# --- BARRA DE NAVEGAÇÃO LATERAL (SIDEBAR) ---
st.sidebar.title("Painel de Alocação")
pagina_selecionada = st.sidebar.radio(
    "Navegue pelas seções:",
    ["Visão Macro (Hub)", "Análise por Ativo", "Processar Relatórios"]
)
st.sidebar.markdown("---")
st.sidebar.info(f"Dados atualizados até: **{df['data_referencia'].max().strftime('%d/%m/%Y') if not df.empty else 'N/A'}**")


# --- ESTRUTURA DAS PÁGINAS ---

# --- PÁGINA 1: VISÃO MACRO (HUB) ---
if pagina_selecionada == "Visão Macro (Hub)":
    st.title("🌎 Visão Macro (Hub)")
    st.markdown("Dashboard consolidado com a visão das principais gestoras para diversas classes de ativos.")

    if not df.empty:
        gestoras_selecionadas = st.multiselect(
            "Filtre por Gestora(s):",
            options=sorted(df['gestora'].unique()),
            default=df['gestora'].unique()
        )
        df_filtrado = df[df['gestora'].isin(gestoras_selecionadas)]

        st.subheader("Heatmap de Visões de Mercado (Posições Mais Recentes)")
        if not df_filtrado.empty:
            df_heatmap = df_filtrado.sort_values('data_referencia').drop_duplicates(['gestora', 'sub_classe_ativo'], keep='last')
            heatmap_data = df_heatmap.pivot_table(index='sub_classe_ativo', columns='gestora', values='visao', aggfunc='first').fillna('N/A')
            mapa_cores_valores = {'Overweight': 3, 'Neutral': 2, 'Underweight': 1, 'N/A': 0}
            heatmap_data_numerica = heatmap_data.applymap(lambda x: mapa_cores_valores.get(x, 0))
            fig = px.imshow(heatmap_data_numerica, text_auto=False, aspect="auto",
                            labels=dict(x="Gestora", y="Sub-Classe de Ativo"),
                            color_continuous_scale=[(0, "#E0E0E0"), (0.33, "#D9534F"), (0.66, "#FFC107"), (1, "#5CB85C")])
            fig.update_traces(hovertemplate="<b>Gestora:</b> %{x}<br><b>Ativo:</b> %{y}<br><b>Visão:</b> %{customdata}<extra></extra>", customdata=heatmap_data)
            fig.update_layout(height=600, xaxis_title="", yaxis_title="", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Consenso de Mercado")
        consenso = df_filtrado.groupby('sub_classe_ativo')['visao'].agg(lambda x: x.mode()[0] if not x.mode().empty else 'N/A').reset_index()
        consenso.columns = ['Sub-Classe de Ativo', 'Visão de Consenso']
        st.dataframe(consenso, use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum dado carregado. Adicione dados através da página 'Processar Relatórios'.")


# --- PÁGINA 2: ANÁLISE POR ATIVO ---
elif pagina_selecionada == "Análise por Ativo":
    st.title("🔬 Análise por Ativo")
    st.markdown("Mergulhe em uma subclasse de ativo específica para ver a evolução histórica e as teses atuais.")

    if not df.empty:
        sub_classe_selecionada = st.selectbox(
            "Selecione a Sub-Classe de Ativo:",
            options=sorted(df['sub_classe_ativo'].unique())
        )

        if sub_classe_selecionada:
            df_historico = df[df['sub_classe_ativo'] == sub_classe_selecionada].copy()

            st.subheader(f"Evolução Histórica para: {sub_classe_selecionada}")
            mapa_valores_visao = {'Overweight': 3, 'Neutral': 2, 'Underweight': 1}
            df_historico['valor_visao'] = df_historico['visao'].map(mapa_valores_visao)
            fig_historico = px.line(df_historico, x='data_referencia', y='valor_visao', color='gestora', markers=True,
                                    labels={"data_referencia": "Data", "valor_visao": "Visão", "gestora": "Gestora"})
            fig_historico.update_layout(yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Underweight', 'Neutral', 'Overweight'], range=[0.5, 3.5]))
            df_historico = df_historico.sort_values(by=['gestora', 'data_referencia'])
            fig_historico.update_traces(customdata=df_historico['visao'], hovertemplate="<b>Data:</b> %{x|%d-%b-%Y}<br><b>Visão:</b> %{customdata}<extra></extra>")
            st.plotly_chart(fig_historico, use_container_width=True)

            st.subheader(f"Teses Atuais para: {sub_classe_selecionada}")
            df_teses = df_historico.sort_values('data_referencia').drop_duplicates(['gestora'], keep='last')
            st.dataframe(df_teses[['gestora', 'visao', 'resumo_tese', 'frase_justificativa', 'data_referencia']], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado carregado. Adicione dados através da página 'Processar Relatórios'.")

# --- PÁGINA 3: PROCESSAR RELATÓRIOS ---
elif pagina_selecionada == "Processar Relatórios":
    st.title("🤖 Processar Relatórios com IA")
    st.markdown("Faça o upload de um relatório em PDF para que a IA extraia as principais visões de alocação.")
    
    nome_gestora_input = st.text_input("Nome da Gestora (ex: BlackRock, PIMCO, Verde Asset):")
    arquivo_pdf = st.file_uploader("Selecione o arquivo PDF:", type="pdf")

    if st.button("Analisar Relatório") and arquivo_pdf and nome_gestora_input:
        with st.spinner("Lendo o PDF e consultando a IA... Isso pode levar um minuto."):
            # (O código de processamento e exibição do resultado da IA permanece o mesmo)
            texto_do_pdf = extrair_texto_pdf(arquivo_pdf)
            if texto_do_pdf:
                resultado_ia = extrair_visoes_com_ia(texto_do_pdf, nome_gestora_input)
                if resultado_ia:
                    st.subheader("Resultados da Extração (para sua revisão):")
                    try:
                        json_limpo = resultado_ia.strip().replace("```json", "").replace("```", "")
                        dados_extraidos = json.loads(json_limpo)
                        df_extraido = pd.DataFrame(dados_extraidos)
                        st.dataframe(df_extraido, use_container_width=True)
                        
                        st.subheader("Pronto para Copiar para o CSV")
                        csv_output = df_extraido.to_csv(index=False, header=False, lineterminator='\n')
                        st.text_area("Copie o texto abaixo e cole no final do seu arquivo `dados_mercado.csv`", value=csv_output, height=200)
                        st.info(f"Lembre-se de salvar (fazer o 'commit') da alteração no arquivo [dados_mercado.csv](https://github.com/SEU_USUARIO/painel-alocacao/edit/main/dados_mercado.csv) no GitHub.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar o resultado da IA: {e}")
                        st.text_area("Resposta Bruta da IA:", value=resultado_ia, height=200)
