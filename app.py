import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from PyPDF2 import PdfReader
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Market Intelligence Platform",
    page_icon="🌐",
    layout="wide"
)

# --- FUNÇÕES DE CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados_visoes():
    try:
        df = pd.read_csv('dados_mercado.csv')
        df['data_referencia'] = pd.to_datetime(df['data_referencia'])
    except FileNotFoundError:
        df = pd.DataFrame() # Retorna DF vazio se não encontrar
    return df

@st.cache_data
def carregar_kpis():
    try:
        return pd.read_csv('kpis_macro.csv')
    except FileNotFoundError:
        return pd.DataFrame({'nome_metrica': [], 'valor': []})

@st.cache_data
def carregar_riscos_oportunidades():
    try:
        return pd.read_csv('riscos_oportunidades.csv')
    except FileNotFoundError:
        return pd.DataFrame({'tipo': [], 'topico': [], 'descricao': [], 'score': []})

# --- FUNÇÕES DE PROCESSAMENTO DE IA ---
def extrair_texto_pdf(arquivo_pdf):
    leitor_pdf = PdfReader(arquivo_pdf)
    texto = ""
    for pagina in leitor_pdf.pages:
        texto += pagina.extract_text()
    return texto

def extrair_visoes_com_ia(texto_relatorio, nome_gestora):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error("Chave de API do Google não configurada. Por favor, adicione-a nos Segredos (Secrets) do Streamlit.")
        return None
    
    data_hoje = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""
    Você é um assistente de análise financeira altamente preciso, especializado em ler relatórios de gestoras de ativos.
    Sua tarefa é extrair as visões de investimento (teses) do texto fornecido.

    Texto do Relatório:
    ---
    {texto_relatorio}
    ---

    Analise o texto acima e retorne uma lista de visões em formato JSON.
    Cada item na lista deve ser um objeto JSON com os seguintes campos:
    - "data_referencia": Use a data de hoje: "{data_hoje}".
    - "gestora": "{nome_gestora}"
    - "classe_ativo": A classe de ativo principal (ex: Ações, Renda Fixa, Juros, Moedas).
    - "sub_classe_ativo": A especificação do ativo (ex: EUA, Europa, Brasil, Global High Grade).
    - "visao": A visão qualitativa. Use estritamente uma das seguintes opções: "Overweight", "Neutral", "Underweight".
    - "resumo_tese": Um resumo muito curto (uma frase) da justificativa para a visão.
    - "frase_justificativa": A citação EXATA (copiada e colada) do texto que justifica a visão atribuída.

    **Exemplo de Saída Esperada (deve ser um JSON válido):**
    [
        {{
            "data_referencia": "{data_hoje}",
            "gestora": "BlackRock",
            "classe_ativo": "Ações",
            "sub_classe_ativo": "EUA",
            "visao": "Overweight",
            "resumo_tese": "Crescimento resiliente e liderança em tecnologia, apesar dos riscos com juros.",
            "frase_justificativa": "Mantemos nossa preferência por ações dos EUA devido à força de sua economia e ao domínio contínuo no setor de tecnologia."
        }}
    ]

    Se você não encontrar nenhuma visão clara no texto, retorne uma lista vazia [].
    Sua resposta deve conter APENAS o JSON, sem nenhum texto adicional antes ou depois.
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# --- CARREGAMENTO INICIAL DOS DADOS ---
df_visoes = carregar_dados_visoes()
df_kpis = carregar_kpis()
df_riscos = carregar_riscos_oportunidades()

# --- BARRA DE NAVEGAÇÃO LATERAL (SIDEBAR) ---
st.sidebar.title("Market Intelligence")
pagina_selecionada = st.sidebar.radio(
    "Navegue pelas seções:",
    ["Visão Macro (Hub)", "Análise por Ativo", "Processar Relatórios"]
)
st.sidebar.markdown("---")
if not df_visoes.empty:
    st.sidebar.info(f"Dados de visões atualizados até: **{df_visoes['data_referencia'].max().strftime('%d/%m/%Y')}**")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .stMetric {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-color: #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PÁGINA 1: VISÃO MACRO (HUB) ---
if pagina_selecionada == "Visão Macro (Hub)":
    st.title("🌐 Global Intelligence")
    st.markdown("Análise completa do cenário macroeconômico global e oportunidades de investimento")
    st.markdown("---")

    st.subheader("Global Scenery in a Nutshell")
    st.text("Termômetro do cenário macroeconômico global atual")
    
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, row in df_kpis.iterrows():
        if i < len(cols):
            with cols[i]:
                st.metric(label=row['nome_metrica'], value=row['valor'])

    st.subheader("Sentiment Geral do Mercado")
    if not df_riscos.empty:
        oportunidades = df_riscos[df_riscos['tipo'] == 'Oportunidade']
        sentimento = int(oportunidades['score'].mean()) if not oportunidades.empty else 50
        st.progress(sentimento)
        st.text(f"{sentimento}% Otimista - Cenário favorável para investimentos de risco moderado")
    
    st.markdown("---")
    
    col_risco, col_reports = st.columns(2)

    with col_risco:
        st.subheader("Risk/Opportunities Map")
        for _, row in df_riscos.iterrows():
            if row['tipo'] == 'Oportunidade':
                st.info(f"**Oportunidade: {row['topico']}** (Score: {row['score']}) \n*_{row['descricao']}_*")
            else:
                st.warning(f"**Risco: {row['topico']}** (Score: {row['score']}) \n*_{row['descricao']}_*")

    with col_reports:
        st.subheader("New Reports")
        if not df_visoes.empty:
            novos_relatorios = df_visoes.sort_values('data_referencia', ascending=False).drop_duplicates('gestora').head(5)
            for _, row in novos_relatorios.iterrows():
                st.markdown(f"**Outlook {row['data_referencia'].strftime('%b %Y')}** \n*{row['gestora']}* \n `{row['data_referencia'].strftime('%d %b')}`")
                st.markdown("<hr style='margin:5px 0px'>", unsafe_allow_html=True)

# --- PÁGINA 2: ANÁLISE POR ATIVO ---
elif pagina_selecionada == "Análise por Ativo":
    st.title("🔬 Análise por Ativo")
    st.markdown("Mergulhe em uma subclasse de ativo específica para ver a evolução histórica e as teses atuais.")

    if not df_visoes.empty:
        sub_classe_selecionada = st.selectbox(
            "Selecione a Sub-Classe de Ativo:",
            options=sorted(df_visoes['sub_classe_ativo'].unique())
        )

        if sub_classe_selecionada:
            df_historico = df_visoes[df_visoes['sub_classe_ativo'] == sub_classe_selecionada].copy()

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
        st.info("Nenhum dado de visões carregado. Adicione dados através da página 'Processar Relatórios'.")

# --- PÁGINA 3: PROCESSAR RELATÓRIOS ---
elif pagina_selecionada == "Processar Relatórios":
    st.title("🤖 Processar Relatórios com IA")
    st.markdown("Faça o upload de um relatório em PDF para que a IA extraia as principais visões de alocação.")
    
    nome_gestora_input = st.text_input("Nome da Gestora (ex: BlackRock, PIMCO, Verde Asset):")
    arquivo_pdf = st.file_uploader("Selecione o arquivo PDF:", type="pdf")

    if st.button("Analisar Relatório") and arquivo_pdf and nome_gestora_input:
        with st.spinner("Lendo o PDF e consultando a IA... Isso pode levar um minuto."):
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
