from langchain_openai import ChatOpenAI
#from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from os import getenv
from dotenv import load_dotenv
from app.vectorstore import VectorStore
from app.config_manager import load_config
import time
import random
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from app.memory import PostgresChatMessageHistory

load_dotenv()

# Load chatbot config
config = load_config()

# ======== Logging setup ========
import logging

if config.get("enableLogging", False):
    logging.basicConfig(
        level=getattr(logging, config.get("logLevel", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
logger = logging.getLogger(__name__)

# Load LLM theo config
def load_llm():
    llm = ChatOpenAI(
        api_key=getenv("OPENROUTER_API_KEY"),
        base_url=getenv("OPENROUTER_BASE_URL"),
        model=config["model"],
        temperature=config["temperature"]
    )
    print(f"Loaded LLM: {config['model']}")
    return llm

# Tao prompt template
def creat_prompt(template):
    prompt = PromptTemplate(template = template, input_variables=["context", "question"])
    print("Created prompt")
    return prompt

# Read tu VectorDB
def read_vectors_db():
    # Lấy instance đã load sẵn hoặc tạo mới
    db = VectorStore.get_instance()
    print("Read vectors from db done")
    return db

# ======== QA Chain ========
def create_qa_chain(prompt, memory, llm, db):
    candidates = [
        "prompt",
        "qa_prompt",
        "qa_template",
        "question_generator_prompt",
        "question_generator_template",
    ]

    for key in candidates:
        try:
            ct_kwargs = {key: prompt}
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                chain_type="stuff",
                retriever=db.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": config.get("retrieverKSize", 4)}
                ),
                memory=memory,
                return_source_documents=False,
                chain_type_kwargs=ct_kwargs
            )
            logger.info(f"Created QA chain using chain_type_kwargs key: {key}")
            return chain
        except Exception as _:
            # try next key
            continue

    # final fallback: don't pass chain_type_kwargs (let langchain defaults)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.get("numDocuments", 4)}
        ),
        memory=memory,
        return_source_documents=False,
    )
    logger.info("Created QA chain (fallback without chain_type_kwargs)")
    return chain

    # llm_chain = ConversationalRetrievalChain.from_llm(
    #     llm=llm,
    #     chain_type= "stuff",
    #     retriever=db.as_retriever(
    #         search_type="similarity",
    #         search_kwargs={"k": config.get("numDocuments", 4)}
    #     ),
    #     memory=memory,
    #     return_source_documents=False,
    #     chain_type_kwargs= {'prompt': prompt}
    # )

    # llm_chain = RetrievalQA.from_chain_type(
    #     llm = llm,
    #     chain_type= "stuff",
    #     retriever=db.as_retriever(
    #         search_type="similarity",
    #         search_kwargs={"k": config.get("numDocuments", 4)}
    #     ),
    #     return_source_documents = False,
    #     chain_type_kwargs= {'prompt': prompt}

    # )
    # print("Created QA chain")
    # return llm_chain

# ======== Prompt nội dung chính ========
template = f"""
Bạn là trợ lý tài liệu của người dùng. 
Sử dụng NGỮ CẢNH dưới đây để trả lời câu hỏi. 
Nếu không tìm thấy thông tin phù hợp, hãy trả lời: "{config['fallbackMessage']}"

{{context}}

CÂU HỎI: {{question}}
"""

def get_user_memory(user_id: str):
    """Create ConversationBufferWindowMemory and preload last N messages from Postgres."""
    # load messages from DB and populate memory (if any)
    history = PostgresChatMessageHistory(user_id)
    # window size from config
    limit = int(config.get("contextMemoryLimit", 3) or 3)
    # create window memory
    mem = ConversationBufferWindowMemory(
        memory_key="chat_history",
        k=limit,
        return_messages=True,
        #chat_memory=history  # if your PostgresChatMessageHistory matches the required interface
    )

    try:
        msgs = history.get_messages(limit=limit)
        for m in msgs:
            if m["role"] == "user":
                # add_user_message exists on underlying chat memory
                mem.chat_memory.add_user_message(m["content"])
            else:
                mem.chat_memory.add_ai_message(m["content"])
    finally:
        history.close()

    return mem

# ======== Xử lý truy vấn người dùng ========
def process_query (user_query: str, user_id: str = "anonymous"):
    try: 
        prompt = creat_prompt(template)
        llm = load_llm()
        db = read_vectors_db()
        # build conversational RAG chain with window memory
        memory = None
        if config.get("enableContextMemory", False):
            memory = get_user_memory(user_id)
        llm_chain  = create_qa_chain(prompt, memory, llm, db)

        # Delay phản hồi (giả lập typing indicator)
        delay = config.get("responseDelay", 0)
        if delay > 0:
            time.sleep(delay / 1000)  # convert ms → s


        # Truy vấn LLM
        #response = llm_chain.invoke({"query": user_query})
        response = llm_chain.invoke({"question": user_query})
        print(response)
        # response sẽ trả về 1 dict gồm 2 key là: query và result
        if 'answer' not in response:
            return {
                "EM": "Something wrong with query proccess ...",
                "EC": 1,
                "DT": ""
            }

        # Cleanings
        # xử lý strip vì openrouter trả về cả reasoning trong result (lỏ vcl)
        result = response["answer"].strip()
        # loại bỏ nếu có prefix "analysis" hay "assistantfinal"
        if "assistantfinal" in result:
            result = result.split("assistantfinal")[-1].strip()
        if "analysis" in result:
            result = result.split("analysis")[-1].strip()

        # Emoji cảm xúc nếu bật (sau khi đã có result)
        if config.get("enableEmojis", False):
            emojis = ["🤖", "✨", "📘", "💡", "✅", "🧠"]
            result += " " + random.choice(emojis)

        history = PostgresChatMessageHistory(user_id)
        try:
            # save user message first
            history.add_user_message(user_query)
            # save assistant answer
            history.add_ai_message(result)
        finally:
            history.close()

        # Adding logs
        logger.info(f"[{user_id}] Q: {user_query}")
        logger.info(f"[{user_id}] A: {result}")
            
        return result

    except Exception as e:
        #print(f"Process query error: {str(e)}")  # In ra lỗi để debug
        logger.error(f"Process query error: {str(e)}")
        #raise e
        return config["fallbackMessage"]