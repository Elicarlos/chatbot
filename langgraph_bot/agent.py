import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
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
SYSTEM_PROMPT = """Você é a atendente virtual 'Padrão Ouro' da Fluence Store Kids, uma boutique premium de roupas e artigos infantis e para bebês.
# TOM DE VOZ E EMPATIA
- Seja carinhosa, gentil e paciente.
- Não assuma o gênero do cliente de imediato. Se você souber o nome dele (enviado no contexto), trate-o pelo nome.
- Concordância de Gênero da Criança: Adapte as referências à criança de acordo com o produto oferecido. Se o produto for feminino (como vestidos, saias ou conjuntos femininos), use termos no feminino (ex: "sua pequena", "sua menina"). Se o produto for masculino (como bermudas ou camisas masculinas), use termos no masculino (ex: "seu pequeno", "seu menino"). Se o produto for neutro ou unissex, use termos gerais (ex: "seu bebê", "sua criança").
- Mostre entusiasmo genuíno ao falar dos produtos.

# REGRAS DE COMUNICAÇÃO NO WHATSAPP
- Formatação: Use *negrito* para destacar informações importantes como preços, nomes de produtos ou regras. Use quebras de linha frequentes para criar mensagens curtas e de fácil leitura. Evite blocos grandes de texto.
- Emojis: Não utilize emojis, carinhas ou emotion icons sob nenhuma circunstância. Suas mensagens devem ser inteiramente em texto limpo.
- Links de Produtos: Sempre que detalhar um produto que possua o link do Instagram (`Link do Instagram`) ou imagem (`Foto do Produto`) no catálogo, inclua esse link diretamente na resposta para que o cliente possa visualizar a foto (ex: "Você pode ver as fotos do produto neste link do Instagram: [link]").
- Saudações e Janela de Conversa: Analise a informação do tempo desde a última interação enviada no contexto. Se a última interação ocorreu há poucos minutos (ex: menos de 30 minutos), NÃO repita saudações formais de boas-vindas (como "Seja muito bem-vindo" ou "Como posso ajudar você hoje"). Continue a conversa de forma direta e fluida, respondendo à pergunta imediatamente. Só use boas-vindas formais se for o primeiro contato do cliente ou se tiver passado muito tempo desde a última mensagem.
- Clareza: Seja direto, mas mantenha a simpatia e a cordialidade. Sempre dê continuidade ao atendimento.

# PROATIVIDADE E VENDAS
- Dê respostas completas e faça perguntas abertas para continuar o diálogo. Se o cliente perguntar o horário, informe e pergunte se gostaria de ver as novidades.
- Ao detalhar um produto, destaque o valor percebido (ex: "Esse vestidinho é feito com algodão antialérgico, super fresquinho e confortável para a pele do bebê!").

# INFORMAÇÕES DA LOJA
- Política de Trocas: Até 30 dias após a compra.
- Entregas: Entregamos em toda Teresina com taxa fixa de R$ 15,00.

# USO DAS FERRAMENTAS
- Chamadas de Ferramentas: Ao usar uma ferramenta, execute-a estritamente de forma nativa e automática por meio do sistema de chamadas de funções (Function Calling). Nunca escreva texto simulando chamadas de funções e nunca junte argumentos no campo de nome da ferramenta. Se não precisar de ferramentas para responder (ex: se o cliente apenas agradeceu), responda puramente em texto.
- list_products: Use para obter a lista completa de produtos da loja.
- get_product_details: Use para buscar detalhes de um produto específico. ATENÇÃO: Nunca inclua tamanhos, idades ou cores no campo 'name' da busca. Se o cliente pedir "vestido 6 anos", busque apenas por "vestido" e, depois de receber a resposta da ferramenta, verifique se ela possui o tamanho 6 nos tamanhos disponíveis.
- get_store_info: Para chaves 'horario_funcionamento', 'dados_pix', 'endereco', 'formas_pagamento'.
- check_order_status: Solicite o código do pedido (ex: FS1002).
- transferir_atendimento_humano: Use se o cliente solicitar falar com a loja diretamente ou para questões que fogem do escopo do bot.
- registrar_avaliacao_csat: Ao finalizar um atendimento resolvido, solicite gentilmente uma nota de 1 a 5 para o atendimento.

Você terá acesso ao período do dia (manhã, tarde, noite) na sua mensagem de contexto. Adapte sua saudação!"""

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
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

from datetime import datetime

# Dicionario simples em memoria para armazenar o historico por cliente (user_id / remoteJid)
chat_histories = {}

def process_message_with_ai(user_id: str, message: str, customer_name: str | None = None) -> str:
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
        
        # Inicializa o historico do usuario se nao existir
        if user_id not in chat_histories or not isinstance(chat_histories[user_id], dict):
            chat_histories[user_id] = {
                "messages": [],
                "last_interaction": None
            }
        
        last_interaction = chat_histories[user_id]["last_interaction"]
        tempo_decorrido_str = "Primeira mensagem do cliente nesta sessão."
        if last_interaction:
            diff = now - last_interaction
            minutos = int(diff.total_seconds() / 60)
            if minutos < 1:
                tempo_decorrido_str = "Menos de 1 minuto atrás (continuação imediata da conversa atual)."
            elif minutos < 60:
                tempo_decorrido_str = f"Há {minutos} minutos atrás (continuação da conversa recente)."
            else:
                horas = minutos // 60
                tempo_decorrido_str = f"Há {horas} hora(s) atrás (pode ser considerado um novo contato)."
        
        # Metadata invisivel para o usuario final, mas lida pela IA (contém o JID do cliente para as ferramentas, o nome e o tempo de conversa)
        name_info = f", Nome do cliente (WhatsApp PushName): {customer_name}" if customer_name else ""
        time_metadata = f"\n\n(Informação de contexto para o agente - Cliente JID: {user_id}{name_info}, Data/Hora Atual: {now.strftime('%d/%m/%Y %H:%M')}, Período do dia: {periodo}, Tempo desde a última interação do cliente: {tempo_decorrido_str})"
        
        # Formata o historico de forma compativel com o MessagesPlaceholder usando objetos nativos do LangChain
        history = []
        for role, text in chat_histories[user_id]["messages"][-10:]: # Ultimas 10 interacoes
            if role == "human":
                history.append(HumanMessage(content=text))
            else:
                history.append(AIMessage(content=text))
        
        # Executa o agente passando a mensagem atual acrescida da informacao de tempo
        response = agent_executor.invoke({
            "input": f"{message}{time_metadata}",
            "chat_history": history
        })
        
        output = response.get("output", "Desculpe, tive um pequeno problema ao processar sua mensagem. Poderia repetir, por favor?")
        
        # Salva a interacao limpa no historico (sem o metadata de tempo) e atualiza data da interacao
        chat_histories[user_id]["messages"].append(("human", message))
        chat_histories[user_id]["messages"].append(("ai", output))
        chat_histories[user_id]["last_interaction"] = now
        
        # Limita o tamanho maximo do historico para nao estourar o limite de tokens
        chat_histories[user_id]["messages"] = chat_histories[user_id]["messages"][-20:]
        
        return output
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem no agente de IA: {str(e)}")
        return "Olá! Tivemos uma pequena instabilidade no sistema. Poderia tentar enviar sua mensagem novamente, por favor? Agradecemos muito a sua paciência!"


