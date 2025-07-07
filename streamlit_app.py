import json
import logging

import streamlit as st

from azure_services import search
from openai_services import ai_flow
from services.gerar_pdf import pdf_button

# Configuração do log
logging.basicConfig(level=logging.INFO)

# Show title and description.
st.title("📄 Análise de Vulnerabilidade em Arquitetura de Software")
st.write(
    "Faça o upload da sua arquitetura de software em jpeg, png ou pdf e receba o relatório de vulnerabilidades que ela possa ter."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = ""

# Campo para a chave, salva na sessão
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = ""

# Campo de entrada para a chave
if not st.session_state["openai_api_key"]:
    api_key = st.text_input("OpenAI API Key", type="password")
    st.info("Insira sua OpenAI API key para continuar", icon="🗝️")
    st.info("Importante que a sua chave tenha acesso ao modelo `o4-mini-2025-04-16`", icon="ℹ️")

    # Atualiza a sessão quando o usuário digita
    if api_key:
        logging.info("OpenAI API Key recebida.")
        st.session_state["openai_api_key"] = api_key
        st.rerun()
else:
    # Cria o cliente
    chat = ai_flow.Chat(st.session_state["openai_api_key"], model="o4-mini-2025-04-16")

    # Upload da arquitetura
    arquitetura = st.file_uploader(
        "Faça o upload da sua arquitetura (.pdf/.jpeg/.png)", type=("pdf", "jpeg", "png")
    )
    if arquitetura:
        logging.info("Arquivo de arquitetura recebido.")
        with st.spinner('Analisando arquitetura... Por favor, aguarde.'):
            response = chat.read_architecture(arquitetura)
            try:
                response = response.replace('```', '')
                response = response.replace('json', '')
                resultado = json.loads(response)
            except json.JSONDecodeError as e:
                logging.error(f"Erro ao decodificar JSON: {str(e)} response: {response}")
                st.error("Erro ao converter resposta para JSON.")
                raise e

        st.subheader("📦 Componentes Identificados")
        resultados_itens = resultado.get("componentes_identificados", [])
        st.write(resultados_itens)

        st.subheader("🧠 Descrição dos Componentes")
        for componente, descricao in resultado.get("descricao_componentes", {}).items():
            st.markdown(f"**{componente}**: {descricao}")

        st.subheader("🔁 Fluxo da Aplicação")
        resultados_fluxo = resultado.get("fluxo_aplicacao", [])
        st.write(resultados_fluxo)
        st.success("Análise da arquitetura concluída com sucesso!", icon="✅")

        with st.spinner('Analisando vulnerabilidade na arquitetura... Por favor, aguarde.'):

            search_rag = search.Search()
            response = search_rag.search_topic("Threat")

            docs_para_analise = []
            for item in response:
                docs_para_analise.append({
                    "id": item["id"],
                    "conteudo": item["conteudo"]
                })

            resultado_items = chat.check_vulnerability_per_item("items", docs_para_analise, resultados_itens)
            resultado_flow = chat.check_vulnerability_per_item("data-flow", docs_para_analise, resultados_fluxo)

            st.subheader("Resultado:")
            with st.expander("🔍 Análise de vulnerabilidade item a item"):
                st.write(resultado_items)

            with st.expander("🔍 Análise de vulnerabilidade do fluxo de dados"):
                st.write(resultado_flow)

        st.success("Análise de vulnerabilidades concluída com sucesso!", icon="✅")


        logging.info(resultado_flow)
        logging.info(resultado_items)
        logging.info(resultados_itens)
        logging.info(resultados_fluxo)
        logging.info(resultado.get("fluxo_aplicacao", []))
        logging.info(resultado.get("descricao_componentes", {}))
        # Gerar o PDF
        pdf_button(resultados_itens=resultados_itens,
                   resultado_items=resultado_items,
                   resultado_flow=resultado_flow,
                   resultados_fluxo=resultado.get("fluxo_aplicacao", []),
                   descricao_componentes=resultado.get("descricao_componentes", {}))
