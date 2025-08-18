import subprocess

# --- Patch sysctl Rosetta check for Intel Macs ---
_orig_run = subprocess.run

def safe_run(*args, **kwargs):
    if args[0] == ["sysctl", "-n", "sysctl.proc_translated"]:
        # Fake "not running under Rosetta"
        class FakeResult:
            stdout = b"0\n"
        return FakeResult()
    return _orig_run(*args, **kwargs)

subprocess.run = safe_run
# -------------------------------------------------

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
#from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from os import getenv
from dotenv import load_dotenv

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
    # Embeding
    print("Reading vectors from db...")
    embedding_model = GPT4AllEmbeddings(model_file="../models/all-MiniLM-L6-v2-f16.gguf")
    #embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=getenv("GOOGLE_API_KEY"))
    db = FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)
    print("Read vectors from db done")
    return db


# Bat dau thu nghiem
db = read_vectors_db()
llm = load_llm()

#Tao Prompt
template = """
Bạn là trợ lý tư vấn tuyển sinh. Nhiệm vụ: trả lời CHỈ dựa trên NGỮ CẢNH được cung cấp.

Hãy sử dụng những thông tin ngữ cảnh sau để trả lời câu hỏi. Nếu thông tin không có trong ngữ cảnh, hãy nói "Xin lỗi, tôi không thể trả lời câu hỏi của bạn, hãy thử hỏi theo cách khác", đừng cố gắng bịa ra câu trả lời. Chỉ sử dụng những thông tin ngữ cảnh sau, đừng sử dụng kiến thức của riêng bạn. Hãy cố gắng bao quát đầy đủ thông tin trong ngữ cảnh để trả lời sao cho đầy đủ nhất có thể tránh tóm tắt ngắn gọn dẫn đến thiếu thông tin.

{context}

CÂU HỎI: {question}
"""
# template = """<|im_start|>system\nSử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy nói không biết, đừng cố tạo ra câu trả lời\n
# {context}<|im_end|>\n<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant"""
# template = """
# Answer the question based only on the following context:
#
# {context}
#
# ---
#
# Answer the question based on the above context: {question}
# """
prompt = creat_prompt(template)

llm_chain  = create_qa_chain(prompt, llm, db)

# Chay cai chain
question = "4 tháng cuối năm 2023, SHB đã làm gì?"
response = llm_chain.invoke({"query": question})
print(response)