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
        df = pd.DataFrame()
    return df

@st.cache_data
def carregar_kpis():
    try:
        return pd.read_csv('kpis_macro.csv')
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def carregar_riscos_oportunidades():
    try:
        return pd.read_csv('riscos_oportunidades.csv')
    except FileNotFoundError:
        return pd.DataFrame()

# --- FUNÇÕES DE PROCESSAMENTO DE IA ---
def extrair_texto_pdf(arquivo_pdf):
    # (Código inalterado)
    leitor_pdf = PdfReader(arquivo_pdf)
    texto = ""
    for pagina in leitor_pdf.pages:
        texto += pagina.extract_text()
    return texto

def extrair_visoes_com_ia(texto_relatorio, nome_gestora):
    # (Código inalterado)
    # Omitido para encurtar
    return "[]" 

# --- CARREGAMENTO INICIAL DOS DADOS ---
df_visoes = carregar_dados_visoes()
df_kpis = carregar_kpis()
df_riscos = carregar_riscos_oportunidades()

# --- LÓGICA DE NAVEGAÇÃO E ESTADO ---
# Inicializa o estado da sessão se ainda não existir
if 'pagina_selecionada' not in st.session_state:
    st.session_state.pagina_selecionada = "Visão Macro (Hub)"
if 'gestora_foco' not in st.session_state:
    st.session_state.gestora_foco = None

# Função de callback para ser chamada quando um botão de relatório é clicado
def selecionar_gestora_e_navegar(nome_gestora):
    st.session_state.gestora_foco = nome_gestora
    st.session_state.pagina_selecionada = "Análise por Gestora"

# --- BARRA DE NAVEGAÇÃO LATERAL (SIDEBAR) ---
st.sidebar.title("Market Intelligence")

# O radio button agora lê e escreve no session_state
pagina_selecionada = st.sidebar.radio(
    "Navegue pelas seções:",
    ["Visão Macro (Hub)", "Assets View", "Análise por Gestora", "Processar Relatórios"],
    key='pagina_selecionada'
)

st.sidebar.markdown("---")
if not df_visoes.empty:
    st.sidebar.info(f"Dados de visões atualizados até: **{df_visoes['data_referencia'].max().strftime('%d/%m/%Y')}**")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .card {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px 20px;
        margin-bottom: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tag {
        background-color: #e9ecef;
        color: #495057;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.9em;
        font-weight: 500;
    }
    .tag-otimista { background-color: #d4edda; color: #155724; }
    .tag-neutro { background-color: #fff3cd; color: #856404; }
    .tag-pessimista { background-color: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)


# --- PÁGINAS DA APLICAÇÃO ---

# --- PÁGINA 1: VISÃO MACRO (HUB) ---
if st.session_state.pagina_selecionada == "Visão Macro (Hub)":
    st.title("🌐 Global Intelligence")
    st.markdown("Análise completa do cenário macroeconômico global e oportunidades de investimento")
    st.markdown("---")

    st.subheader("Global Scenery in a Nutshell")
    col1, col2, col3, col4 = st.columns(4)
    if not df_kpis.empty:
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
        if not df_riscos.empty:
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
                # Cada item agora é um botão que chama a função de callback
                st.button(
                    f"{row['gestora']} - Outlook {row['data_referencia'].strftime('%b %Y')}",
                    key=row['gestora'],
                    use_container_width=True,
                    on_click=selecionar_gestora_e_navegar,
                    args=(row['gestora'],) # Passa o nome da gestora para a função
                )
# --- PÁGINA 2: ANÁLISE POR ATIVO ---
elif st.session_state.pagina_selecionada == "Assets View":
    st.title("📊 Assets View")
    st.markdown("Análise detalhada das classes de ativos por região")

    if not df_visoes.empty:
        regioes = df_visoes['regiao'].unique()
        regiao_selecionada = st.radio("Seleção de Região", options=regioes, horizontal=True)
        df_regiao = df_visoes[df_visoes['regiao'] == regiao_selecionada]
        
        col_classes, col_detalhes = st.columns([1, 3])

        with col_classes:
            classes_ativos = df_regiao['classe_ativo_geral'].unique()
            classe_selecionada = st.radio("Classes de Ativos", options=classes_ativos, label_visibility="collapsed")

        with col_detalhes:
            st.header(f"{classe_selecionada} - {regiao_selecionada}")
            
            # --- NOVAS SEÇÕES USANDO O JSON ---
            lookup_key = f"{regiao_selecionada}_{classe_selecionada}"
            detalhes = detalhes_ativos.get(lookup_key, {})

            if detalhes:
                st.markdown(f"**Overview:** *{detalhes.get('overview', 'N/A')}*")
                st.markdown(f"**Consensus:** `{detalhes.get('consensus', 'N/A')}`")

                st.subheader("Visões das Gestoras")
                # (Código para exibir os cards das gestoras - inalterado)
                df_views = df_regiao[df_regiao['classe_ativo_geral'] == classe_selecionada]
                df_views_recentes = df_views.sort_values('data_referencia').drop_duplicates('gestora', keep='last')
                for _, row in df_views_recentes.iterrows():
                    # ... (código dos cards inalterado)
                    st.markdown(f"""
                        <div class="card">
                            <div><strong>{row['gestora']}</strong><br><small>{row['resumo_tese']}</small></div>
                            <div class="tag ...">{...}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.subheader("Principais Drivers")
                drivers = detalhes.get('drivers', [])
                st.write(" &nbsp; ".join([f"`{driver}`" for driver in drivers]))

                st.subheader("Investment Thesis")
                thesis = detalhes.get('investment_thesis', {})
                st.markdown(f"""
                    <div class="case-box bullish">
                        <strong>Bullish Case</strong><br>
                        {thesis.get('bullish', 'N/A')}
                    </div>
                    <div class="case-box bearish">
                        <strong>Bearish Case</strong><br>
                        {thesis.get('bearish', 'N/A')}
                    </div>
                    <div class="case-box base">
                        <strong>Base Case</strong><br>
                        {thesis.get('base', 'N/A')}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Dados detalhados para esta seleção de ativo ainda não foram cadastrados.")

# --- PÁGINA 3: ANÁLISE POR GESTORA (NOVA PÁGINA) ---
elif st.session_state.pagina_selecionada == "Análise por Gestora":
    st.title("🏢 Análise por Gestora")
    
    gestora_selecionada = st.selectbox(
        "Selecione a Gestora para analisar:",
        options=sorted(df_visoes['gestora'].unique()),
        # O selectbox inicia com a gestora que foi clicada no Hub
        index=sorted(df_visoes['gestora'].unique()).index(st.session_state.gestora_foco) if st.session_state.gestora_foco in sorted(df_visoes['gestora'].unique()) else 0
    )
    
    if gestora_selecionada:
        st.session_state.gestora_foco = gestora_selecionada # Atualiza o foco se o usuário mudar no selectbox
        df_gestora = df_visoes[df_visoes['gestora'] == gestora_selecionada]
        
        st.subheader(f"Visões Atuais de: {gestora_selecionada}")
        df_atual = df_gestora.sort_values('data_referencia').drop_duplicates('sub_classe_ativo', keep='last')
        st.dataframe(df_atual[['sub_classe_ativo', 'visao', 'resumo_tese', 'data_referencia']], use_container_width=True, hide_index=True)

        st.subheader("Evolução Histórica das Visões")
        ativo_para_historico = st.selectbox(
            "Selecione um ativo para ver o histórico desta gestora:",
            options=sorted(df_gestora['sub_classe_ativo'].unique())
        )
        if ativo_para_historico:
            df_historico_gestora = df_gestora[df_gestora['sub_classe_ativo'] == ativo_para_historico]
            mapa_valores_visao = {'Overweight': 3, 'Neutral': 2, 'Underweight': 1}
            df_historico_gestora['valor_visao'] = df_historico_gestora['visao'].map(mapa_valores_visao)
            fig = px.line(df_historico_gestora, x='data_referencia', y='valor_visao', markers=True, title=f"Histórico para {ativo_para_historico}")
            fig.update_layout(yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Underweight', 'Neutral', 'Overweight'], range=[0.5, 3.5]))
            st.plotly_chart(fig, use_container_width=True)

# --- PÁGINA 4: PROCESSAR RELATÓRIOS ---
elif st.session_state.pagina_selecionada == "Processar Relatórios":
    st.title("🤖 Processar Relatórios com IA")
    
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
