import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
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

# Suporte dinâmico a múltiplos provedores de IA (Groq, Hugging Face, OpenAI, Gemini)
groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
hf_api_key = os.getenv("HF_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

provider = os.getenv("IA_PROVIDER", "").lower()

# Autodetecta o provedor com base nas chaves fornecidas
if not provider:
    if groq_api_key:
        provider = "groq"
    elif hf_api_key:
        provider = "huggingface"
    elif google_api_key and google_api_key.startswith("AIzaSy"):
        provider = "gemini"
    elif openai_api_key and openai_api_key.startswith("sk-"):
        provider = "openai"
    else:
        # Se a chave do Gemini foi colocada em OPENAI_API_KEY
        if openai_api_key and openai_api_key.startswith("AIzaSy"):
            provider = "gemini"
            google_api_key = openai_api_key
        else:
            provider = "gemini"

if provider == "groq":
    from langchain_openai import ChatOpenAI
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.3,
        api_key=groq_api_key or openai_api_key,
        base_url="https://api.groq.com/openai/v1"
    )
elif provider == "huggingface":
    from langchain_openai import ChatOpenAI
    model_name = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.3,
        api_key=hf_api_key or openai_api_key,
        base_url="https://api-inference.huggingface.co/v1"
    )
elif provider == "openai":
    from langchain_openai import ChatOpenAI
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.3,
        api_key=openai_api_key
    )
else:  # gemini
    model_name = os.getenv("GEMINI_MODEL")
    if not model_name or not model_name.strip():
        model_name = "gemini-1.5-flash-latest"
    llm = ChatGoogleGenerativeAI(
        model=model_name.strip(),
        temperature=0.3,
        google_api_key=google_api_key or openai_api_key
    )

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
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

