from openai import OpenAI
import base64
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)

class Chat:

    def __init__(self, openai_api_key, model):
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model

    def load_prompt(self, filename):
        try:
            with open('prompts/' + filename, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            return conteudo
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {filename}")
            return None
        except Exception as e:
            print(f"Erro ao ler o arquivo: {e}")
            return None
    
    def read_architecture(self, uploaded_file): 

        document = base64.b64encode(uploaded_file.read()).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Você é um agente especialista em arquitetura de sistemas e irá receber uma imagem de arquitetura para análise geral.
                            Seus objetivos são:
                            1. Interpretar a arquitetura e montar uma lista de componentes de cada elemento presente na imagem. Exemplo: AWS - S3, AWS - EC2, AWS - ECR, AWS - Lambda.
                            2. Explicar o que cada componente faz. Exemplo: AWS - S3: serviço de armazenamento em nuvem de arquivos.
                            3. Explicar o fluxo da aplicação apresentada com base na imagem.
                            
                            ⚠️ Responda exclusivamente no formato JSON, utilizando as seguintes chaves:

                            {{
                            "componentes_identificados": [ "AWS - S3", "AWS - EC2", ... ],
                            "descricao_componentes": {{
                                "AWS - S3": "Serviço de armazenamento de objetos em nuvem...",
                                "AWS - EC2": "Serviço de computação elástica para hospedar aplicações..."
                            }},
                            "fluxo_aplicacao": "Descreva aqui o fluxo de como os componentes interagem entre si com base nas setas e estrutura da imagem.
                            Descreva em itens enumerados, nomeando a interação entre eles como o exemplo a seguir:

                            1. Business users/back-office apps ↔ Customer On-Premises Gateway: Usuários e aplicações locais iniciam conexões via VPN Gateway ou ExpressRoute para o Azure.
                            2. Customer On-Premises Gateway ↔ Azure Virtual Network Gateway (Hub): O tráfego ingressa na rede hub do SWIFT Integration Layer pela Virtual Network Gateway.
                            3. Hub Virtual Network ↔ Alliance Connect Virtual Subscription (Peering): Através de Virtual Network Peering, o tráfego é roteado para a assinatura Alliance Connect Virtual.
                            4. Gateway Subnet ↔ vSRX Untrust NIC (VA ou VB): O Virtual Network Gateway entrega o tráfego à subnet de gateway; o vSRX recebe pela interface Untrust.
                            5. vSRX Untrust NIC → vSRX Interconnect NIC → vSRX Trust NIC: O appliance Juniper vSRX aplica políticas (NSG, UDR, Policy Set) e encaminha internamente dos lados Untrust para Trust.
                            
                            }}
                            """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{document}"
                        }
                    }
                ]
            }

        ]
        logging.info("Enviando mensagem para análise de arquitetura.")
        stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        
        response = stream.choices[0].message.content
        logging.info("Análise de arquitetura concluída.")
        return response
    
    def check_vulnerability_per_item(self, analysis_type, docs_content, arch_content):

        """
        Faz análise STRIDE baseada em conteúdo retornado da busca.
        
        Parâmetros:
            analysis_type (str): 'items' ou 'data-flow'
            content (list[dict]): Lista com chaves 'id' e 'conteudo'
            arch_content (str): Conteudo da arquitetura (itens ou dataflow)
        """
        # Construir string formatada para o prompt
        blocos_documento = []
        for doc in docs_content:
            bloco = f"### Documento: {doc['id']}\n{doc['conteudo']}\n"
            blocos_documento.append(bloco)

        content_doc_string = "\n---\n".join(blocos_documento)

        if analysis_type == 'items':
            with open('openai_services/sample_items.txt', encoding="utf-8") as f:
                sample = f.read()
        
        if analysis_type == 'data-flow':
            with open('openai_services/sample_dataflow.txt', encoding="utf-8") as f:
                sample = f.read()


        prompt = f"""
            Você está prestes a realizar uma análise de vulnerabilidade de arquitetura de sistemas em cloud com base na metodologia STRIDE.

            Abaixo estão os documentos relevantes que contêm diretrizes sobre ameaças e mitigações:

            {content_doc_string}
            
            Abaixo está o conteúdo da arquitetura que você deve analisar:
            {arch_content}

            Com base no conteúdo acima, realize a análise do tipo **{analysis_type}** e forneça:
            - As ameaças STRIDE relevantes
            - As justificativas técnicas detalhadas
            - Recomendações de mitigação detalhadas
            - E, se possível, uma organização em tópicos por componente ou interação.

            Evite o uso de markdowns, pois será exibido em um streamlit e siga o exemplo a seguir:
            {sample}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        logging.info(f"Enviando mensagem para análise de vulnerabilidade do tipo {analysis_type}.")
        stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        
        response = stream.choices[0].message.content
        logging.info(f"Análise de vulnerabilidade do tipo {analysis_type} concluída.")
        return response