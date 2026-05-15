from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, UnstructuredPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Khai bao bien
pdf_data_path = "data"
vector_db_path = "vectorstores/db_faiss"

# Ham 1. Tao ra vector DB tu 1 doan text
# def create_db_from_text():
#     raw_text = """Trường Đại học Công nghệ Giao thông Vận tải (tên tiếng Anh: University Of Transport Technology, tên viết tắt: UTT) là trường Đại học công lập được nâng cấp năm 2011 từ Trường Cao đẳng giao thông vận tải- trực thuộc Bộ Giao thông Vận tải. 
#     Tiền thân là trường Cao đẳng Công chính, được thành lập ngày 15/11/1945."""

#     text_splitter = CharacterTextSplitter(
#         separator="\n",
#         chunk_size=512,
#         chunk_overlap=50,
#         length_function=len,
#     )

#     chunks = text_splitter.split_text(raw_text)

#     #Embedding
#     embedding_model = OpenAIEmbeddings(
#         model="text-embedding-3-small",
#         api_key=getenv("OPENAI_KEY")
#     )

#     # Dua vao Faiss Vector DB
#     db = FAISS.from_texts(texts=chunks, embedding=embedding_model)
#     db.save_local(vector_db_path)
#     return db

def create_db_from_files():
    # Khai bao loader de quet toan bo thu muc data
    print("Loading documents...")
    #loader_cls = UnstructuredPDFLoader(mode="elements")
    #loader_cls=UnstructuredPDFLoader, loader_kwargs={"mode": "elements"}
    loader = DirectoryLoader(pdf_data_path, glob="*.pdf", show_progress=True, loader_cls=UnstructuredPDFLoader, loader_kwargs={"mode": "elements"})
    documents = loader.load()
    print("Documents loaded")
    ## Remove empty docs (whole page/element blank)
    documents = [doc for doc in documents if doc.page_content.strip()]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=150,  separators=["\n\n", "\n", ".", "!", "?", "…", ";"])
    chunks = text_splitter.split_documents(documents)
    ## Remove empty chunks (if any splitter produced zero-length pieces)
    chunks = [c for c in chunks if c.page_content.strip()]
    print("Documents splitted")
    print("Chunks 10th: ", chunks[10].page_content)

    # Embedding
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=getenv("OPENAI_KEY")
    )
    #embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=getenv("GOOGLE_API_KEY"))
    print("Embedding vector ....")
    db = FAISS.from_documents(chunks, embedding_model)
    print("Embeddings done")
    db.save_local(vector_db_path)
    print("Vectors saved")
    return db
