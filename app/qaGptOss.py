from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from os import getenv
from dotenv import load_dotenv
from app.vectorstore import VectorStore

load_dotenv()

# Cau hinh
vector_db_path = "../vectorstores/db_faiss"

# Load LLM
def load_llm():
    llm = ChatOpenAI(
        api_key=getenv("OPENROUTER_API_KEY"),
        base_url=getenv("OPENROUTER_BASE_URL"),
        model="openai/gpt-oss-20b:free",
        temperature=0.01
    )
    print("Loaded LLM")
    return llm

# Tao prompt template
def creat_prompt(template):
    prompt = PromptTemplate(template = template, input_variables=["context", "question"])
    print("Created prompt")
    return prompt


# Tao simple chain
def create_qa_chain(prompt, llm, db):
    llm_chain = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type= "stuff",
        retriever = db.as_retriever(search_type="similarity", search_kwargs = {"k":4}),
        return_source_documents = False,
        chain_type_kwargs= {'prompt': prompt}

    )
    print("Created QA chain")
    return llm_chain

# Read tu VectorDB
def read_vectors_db():
    # Lấy instance đã load sẵn hoặc tạo mới
    db = VectorStore.get_instance()
    print("Read vectors from db done")
    return db


#Tao Prompt Nhiệm vụ: trả lời CHỈ dựa trên NGỮ CẢNH được cung cấp.
template = """
Bạn là trợ lý tư vấn tuyển sinh của Trường Đại học Công nghệ Giao thông vận tải.

Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy nói không biết, đừng cố tạo ra câu trả lời.

{context}

CÂU HỎI: {question}
"""
# template = """<|im_start|>system\n
# Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy nói không biết, đừng cố tạo ra câu trả lời\n
# {context}<|im_end|>\n
# <|im_start|>user\n
# {question}<|im_end|>\n
# <|im_start|>assistant"""
# template = """
# Answer the question based only on the following context:

# {context}

# ---

# Answer the question based on the above context: {question}
# """

# Bat dau thu nghiem
def process_query (user_query: str):
    try: 
        prompt = creat_prompt(template)
        llm = load_llm()
        db = read_vectors_db()
        llm_chain  = create_qa_chain(prompt, llm, db)

        # Chay chain
        response = llm_chain.invoke({"query": user_query})
        print(response)
        # response sẽ trả về 1 dict gồm 2 key là: query và result
        if 'result' not in response:
            return {
                "EM": "Something wrong with query proccess ...",
                "EC": 1,
                "DT": ""
            }
            
        return {
            "EM": "Success",
            "EC": 0,
            "DT": response['result']
        }

    except Exception as e:
        print(f"Process query error: {str(e)}")  # In ra lỗi để debug
        raise e