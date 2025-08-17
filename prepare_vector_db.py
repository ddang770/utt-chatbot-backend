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

from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, UnstructuredPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
#from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Khai bao bien
pdf_data_path = "backup_data"
vector_db_path = "vectorstores/db_faiss"

# Ham 1. Tao ra vector DB tu 1 doan text
def create_db_from_text():
    raw_text = """Nhằm đáp ứng nhu cầu và thị hiếu của khách hàng về việc sở hữu số tài khoản đẹp, dễ nhớ, giúp tiết kiệm thời gian, mang đến sự thuận lợi trong giao dịch. Ngân hàng Sài Gòn – Hà Nội (SHB) tiếp tục cho ra mắt tài khoản số đẹp 9 số và 12 số với nhiều ưu đãi hấp dẫn.
    Cụ thể, đối với tài khoản số đẹp 9 số, SHB miễn phí mở tài khoản số đẹp trị giá 880.000đ; giảm tới 80% phí mở tài khoản số đẹp trị giá từ 1,1 triệu đồng; phí mở tài khoản số đẹp siêu VIP chỉ còn 5,5 triệu đồng.
    Đối với tài khoản số đẹp 12 số, SHB miễn 100% phí mở tài khoản số đẹp, khách hàng có thể lựa chọn tối đa toàn bộ dãy số của tài khoản. Đây là một trong những điểm ưu việt của tài khoản số đẹp SHB so với thị trường. Ngoài ra, khách hàng có thể lựa chọn số tài khoản trùng số điện thoại, ngày sinh, ngày đặc biệt, hoặc số phong thủy mang lại tài lộc cho khách hàng trong quá trình sử dụng.
    Hiện nay, SHB đang cung cấp đến khách hàng 3 loại tài khoản số đẹp: 9 số, 10 số và 12 số. Cùng với sự tiện lợi khi giao dịch online mọi lúc mọi nơi qua dịch vụ Ngân hàng số, hạn chế rủi ro khi sử dụng tiền mặt, khách hàng còn được miễn phí chuyển khoản qua mobile App SHB, miễn phí quản lý và số dư tối thiểu khi sử dụng tài khoản số đẹp của SHB.
    Ngoài kênh giao dịch tại quầy, khách hàng cũng dễ dàng mở tài khoản số đẹp trên ứng dụng SHB Mobile mà không cần hồ sơ thủ tục phức tạp.
    Hướng mục tiêu trở thành ngân hàng số 1 về hiệu quả tại Việt Nam, ngân hàng bán lẻ hiện đại nhất và là ngân hàng số được yêu thích nhất tại Việt Nam, SHB sẽ tiếp tục nghiên cứu và cho ra mắt nhiều sản phẩm dịch vụ số ưu việt cùngchương trình ưu đãi hấp dẫn, mang đến cho khách hàng lợi ích và trải nghiệm tuyệt vời nhất.
    Để biết thêm thông tin về chương trình, Quý khách vui lòng liên hệ các điểm giao dịch của SHB trên toàn quốc hoặc Hotline *6688"""

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=512,
        chunk_overlap=50,
        length_function=len,
    )

    chunks = text_splitter.split_text(raw_text)

    #Embedding
    #embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=getenv("OPENAI_KEY"))
    embedding_model = GPT4AllEmbeddings(model_file="models/all-MiniLM-L6-v2-f16.gguf")

    # Dua vao Faiss Vector DB
    db = FAISS.from_texts(texts=chunks, embedding=embedding_model)
    db.save_local(vector_db_path)
    return db

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

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100,  separators=["\n\n", "\n", ".", "!", "?", "…", ";"])
    chunks = text_splitter.split_documents(documents)
    ## Remove empty chunks (if any splitter produced zero-length pieces)
    chunks = [c for c in chunks if c.page_content.strip()]
    print("Documents splitted")
    print("Chunks 10th: ", chunks[10].page_content)

    # Embedding
    embedding_model = GPT4AllEmbeddings(model_file="models/all-MiniLM-L6-v2-f16.gguf")
    #embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=getenv("GOOGLE_API_KEY"))
    print("Embedding vector ....")
    db = FAISS.from_documents(chunks, embedding_model)
    print("Embeddings done")
    db.save_local(vector_db_path)
    print("Vectors saved")
    return db

create_db_from_files()