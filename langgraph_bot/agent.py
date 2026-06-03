import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langgraph_bot.tools import (
    list_products, 
    get_product_details, 
    get_store_info, 
    check_order_status, 
    transferir_atendimento_humano, 
    registrar_avaliacao_csat
)

logger = logging.getLogger(__name__)

# Prompt de Sistema personalizado para a Fluence Store Kids
SYSTEM_PROMPT = """Você é a atendente virtual da Fluence Store Kids, uma loja de roupas e artigos infantis e para bebês repleta de amor e carinho.
Seu objetivo é ser extremamente gentil, cordial, educada e atenciosa com os clientes. 
Use palavras acolhedoras, demonstre empatia e trate cada cliente de forma única e afetuosa.

Informações importantes da loja para responder aos clientes:
- Política de Trocas: O prazo para trocas é de até 30 dias.
- Entregas e Frete: Realizamos entregas em toda a cidade de Teresina pelo valor fixo de R$ 15,00.

Diretrizes de Funcionamento e Ferramentas:
1. Catálogo e Preços: Use 'list_products' para listar itens disponíveis ou 'get_product_details' para detalhes de um produto específico. Nunca invente valores!
2. Informações Gerais (Pix, Endereço, Horário, Pagamento): Use 'get_store_info' informando a respectiva chave de busca ('horario_funcionamento', 'dados_pix', 'endereco' ou 'formas_pagamento').
3. Status do Pedido: Se o cliente quiser saber o andamento de um pedido, solicite o código dele (ex: FS1002) e utilize 'check_order_status'. Utilize o JID do cliente fornecido na nota de contexto ao fim do input como parâmetro 'phone_number'.
4. Suporte Humano: Se o cliente pedir para falar com um atendente humano, use 'transferir_atendimento_humano' com o JID do cliente e informe cordialmente que o robô foi pausado para que o humano assuma.
5. Avaliação do Atendimento (CSAT): No final do atendimento, solicite gentilmente que o cliente dê uma nota de 1 a 5 para o atendimento. Se ele der a nota, utilize a ferramenta 'registrar_avaliacao_csat' para salvar o feedback.

Responda sempre em português do Brasil, de forma clara, organizada e muito simpática."""

# Inicializa o LLM e as ferramentas
tools = [
    list_products, 
    get_product_details, 
    get_store_info, 
    check_order_status, 
    transferir_atendimento_humano, 
    registrar_avaliacao_csat
]

# O OpenAI API Key sera lido automaticamente do ambiente (os.environ["OPENAI_API_KEY"])
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

from datetime import datetime

# Dicionario simples em memoria para armazenar o historico por cliente (user_id / remoteJid)
chat_histories = {}

def process_message_with_ai(user_id: str, message: str) -> str:
    """
    Processa a mensagem recebida pelo chatbot utilizando o agente LangChain,
    gerencia o historico de conversas e consulta o banco de dados se necessario.
    Tambem injeta informacoes de data/hora atuais para que o agente saiba o periodo do dia.
    """
    try:
        # Determina o periodo do dia atual
        now = datetime.now()
        hour = now.hour
        if 6 <= hour < 12:
            periodo = "manhã"
        elif 12 <= hour < 18:
            periodo = "tarde"
        else:
            periodo = "noite"
        
        # Metadata invisivel para o usuario final, mas lida pela IA (contém o JID do cliente para as ferramentas)
        time_metadata = f"\n\n(Informação de contexto para o agente - Cliente JID: {user_id}, Data/Hora Atual: {now.strftime('%d/%m/%Y %H:%M')}, Período do dia: {periodo})"
        
        # Inicializa o historico do usuario se nao existir
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        # Formata o historico de forma compativel com o MessagesPlaceholder
        history = []
        for role, text in chat_histories[user_id][-10:]: # Ultimas 10 interacoes
            if role == "human":
                history.append(("human", text))
            else:
                history.append(("ai", text))
        
        # Executa o agente passando a mensagem atual acrescida da informacao de tempo
        response = agent_executor.invoke({
            "input": f"{message}{time_metadata}",
            "chat_history": history
        })
        
        output = response.get("output", "Desculpe, tive um pequeno problema ao processar sua mensagem. Poderia repetir, por favor?")
        
        # Salva a interacao limpa no historico (sem o metadata de tempo)
        chat_histories[user_id].append(("human", message))
        chat_histories[user_id].append(("ai", output))
        
        # Limita o tamanho maximo do historico para nao estourar o limite de tokens
        chat_histories[user_id] = chat_histories[user_id][-20:]
        
        return output
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem no agente de IA: {str(e)}")
        return "Olá! Tivemos uma pequena instabilidade no sistema. Poderia tentar enviar sua mensagem novamente, por favor? Agradecemos muito a sua paciência!"

