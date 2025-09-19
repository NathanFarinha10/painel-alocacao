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
    df = pd.read_csv('dados_mercado.csv')
    # Importante: converte a coluna de data para o formato datetime para ordenação correta nos gráficos
    df['data_referencia'] = pd.to_datetime(df['data_referencia'])
    return df

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
    Você é um assistente de análise financeira especializado em ler relatórios de gestoras de ativos.
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
    - "visao": A visão qualitativa. Use estritamente uma das seguintes opções: "Overweight", "Neutral", "Underweight". Se a visão não for clara, use "Neutral".
    - "resumo_tese": Um resumo muito curto (uma frase) da justificativa para a visão.

    **Exemplo de Saída Esperada (deve ser um JSON válido):**
    [
        {{
            "data_referencia": "{data_hoje}",
            "gestora": "BlackRock",
            "classe_ativo": "Ações",
            "sub_classe_ativo": "EUA",
            "visao": "Overweight",
            "resumo_tese": "Crescimento resiliente e liderança em tecnologia, apesar dos riscos com juros."
        }}
    ]

    Se você não encontrar nenhuma visão clara no texto, retorne uma lista vazia [].
    Sua resposta deve conter APENAS o JSON, sem nenhum texto adicional antes ou depois.
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text


# --- INTERFACE PRINCIPAL ---
st.title("📊 Painel Consolidado de Visões de Mercado")

df = carregar_dados()
# Adicionamos uma terceira aba
tab1, tab2, tab3 = st.tabs([
    "**Dashboard Consolidado**", 
    "**🤖 Extração com IA**", 
    "**📈 Análise Histórica**"
])

# --- ABA 1: DASHBOARD ---
with tab1:
    st.sidebar.header("Filtros do Dashboard")
    gestoras_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Gestora(s):",
        options=sorted(df['gestora'].unique()),
        default=df['gestora'].unique()
    )
    df_filtrado = df[df['gestora'].isin(gestoras_selecionadas)]

    st.subheader("Principais Consensos e Divergências")
    consenso = df_filtrado.groupby('sub_classe_ativo')['visao'].agg(lambda x: x.mode()[0] if not x.mode().empty else 'N/A').reset_index()
    consenso.columns = ['Sub-Classe de Ativo', 'Visão de Consenso']
    st.dataframe(consenso, use_container_width=True, hide_index=True)

    st.subheader("Heatmap de Visões de Mercado")
    if not df_filtrado.empty:
        # Pega a visão mais recente para cada combinação de gestora/ativo para o heatmap
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
    else:
        st.warning("Nenhuma gestora selecionada.")
    
    with st.expander("Ver tabela de dados completa (visões mais recentes)"):
        st.dataframe(df_filtrado.sort_values('data_referencia').drop_duplicates(['gestora', 'sub_classe_ativo'], keep='last'))

# --- ABA 2: EXTRAÇÃO COM IA ---
with tab2:
    st.header("Extraia Visões de Relatórios em PDF")
    # ... (O CÓDIGO DESTA ABA PERMANECE IGUAL) ...
    st.markdown("Faça o upload de um relatório mensal ou trimestral de uma gestora para que a IA extraia as principais visões de alocação.")
    
    nome_gestora_input = st.text_input("Nome da Gestora (ex: BlackRock, PIMCO, Verde Asset):")
    arquivo_pdf = st.uploader("Selecione o arquivo PDF:", type="pdf")

    if st.button("Analisar Relatório") and arquivo_pdf and nome_gestora_input:
        with st.spinner("Lendo o PDF e consultando a IA... Isso pode levar um minuto."):
            texto_do_pdf = extrair_texto_pdf(arquivo_pdf)
            
            if texto_do_pdf:
                st.success("Texto do PDF extraído com sucesso!")
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
                        st.text_area(
                            label="Copie o texto abaixo e cole no final do seu arquivo `dados_mercado.csv`",
                            value=csv_output,
                            height=200
                        )
                        st.info(
                            "Lembre-se de salvar (fazer o 'commit') da alteração no arquivo "
                            "[dados_mercado.csv](https://github.com/SEU_USUARIO/painel-alocacao/edit/main/dados_mercado.csv) "
                            "no GitHub para que o dashboard seja atualizado."
                        )

                    except json.JSONDecodeError:
                        st.error("A IA retornou um formato que não é um JSON válido. Tente novamente ou ajuste o prompt.")
                        st.text_area("Resposta Bruta da IA:", value=resultado_ia, height=200)
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar o resultado: {e}")
                        st.text_area("Resposta Bruta da IA:", value=resultado_ia, height=200)
                else:
                    st.error("Não foi possível obter uma resposta da IA.")
            else:
                st.error("Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem.")


# --- ABA 3: ANÁLISE HISTÓRICA (NOVA SEÇÃO) ---
with tab3:
    st.header("Evolução das Visões ao Longo do Tempo")
    st.markdown("Selecione uma sub-classe de ativo para ver como as opiniões das gestoras mudaram.")

    # Filtro para selecionar a sub-classe de ativo
    sub_classe_selecionada = st.selectbox(
        "Selecione a Sub-Classe de Ativo:",
        options=sorted(df['sub_classe_ativo'].unique())
    )

    if sub_classe_selecionada:
        df_historico = df[df['sub_classe_ativo'] == sub_classe_selecionada].copy()

        if not df_historico.empty:
            # Mapeia visões para valores numéricos para plotagem
            mapa_valores_visao = {'Overweight': 3, 'Neutral': 2, 'Underweight': 1}
            df_historico['valor_visao'] = df_historico['visao'].map(mapa_valores_visao)

            # Cria o gráfico de linha
            fig_historico = px.line(
                df_historico,
                x='data_referencia',
                y='valor_visao',
                color='gestora',
                markers=True, # Adiciona marcadores para cada ponto de dado
                labels={
                    "data_referencia": "Data de Referência",
                    "valor_visao": "Visão",
                    "gestora": "Gestora"
                },
                title=f"Histórico de Visões para: {sub_classe_selecionada}"
            )

            # Customiza o eixo Y para mostrar os rótulos de texto em vez de números
            fig_historico.update_layout(
                yaxis=dict(
                    tickmode='array',
                    tickvals=[1, 2, 3],
                    ticktext=['Underweight', 'Neutral', 'Overweight'],
                    range=[0.5, 3.5] # Ajusta o range para dar um espaçamento melhor
                )
            )
            
            # Melhora o hover text para mostrar a visão real, não o número
            # É preciso reordenar o dataframe para garantir que o customdata corresponda aos pontos
            df_historico = df_historico.sort_values(by=['gestora', 'data_referencia'])
            fig_historico.update_traces(
                customdata=df_historico['visao']
            )
            fig_historico.update_traces(
                 hovertemplate="<b>Data:</b> %{x|%d-%b-%Y}<br><b>Visão:</b> %{customdata}<extra></extra>"
            )

            st.plotly_chart(fig_historico, use_container_width=True)
        else:
            st.warning("Nenhum dado histórico encontrado para a seleção.")
