from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
import os
import faiss
from dotenv import load_dotenv
from typing import List

load_dotenv()

class VectorStore:
    _instance = None
    _db_path = "app/vectorstores/db_faiss"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=os.getenv("OPENAI_KEY")
            )

            if os.path.exists(os.path.join(cls._db_path, "index.faiss")):
                print("🔄 Loading FAISS index...")
                cls._instance = FAISS.load_local(
                    cls._db_path,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ FAISS index loaded successfully")
            else:
                print("⚡ No FAISS index found, creating a new empty one...")
                dimension = 1536  # text-embedding-3-small output size
                index = faiss.IndexFlatL2(dimension)
                docstore = InMemoryDocstore({})
                index_to_docstore_id = {}

                cls._instance = FAISS(
                    embedding_function=embeddings,
                    index=index,
                    docstore=docstore,
                    index_to_docstore_id=index_to_docstore_id
                )
                print("✅ Empty FAISS index created")

        return cls._instance

    @classmethod
    def save(cls):
        if cls._instance:
            cls._instance.save_local(cls._db_path)
            print("💾 FAISS index saved")

    @classmethod
    def add_texts(cls, texts: List[str], metadatas: List[dict] = None):
        faiss_index = cls.get_instance()
        faiss_index.add_texts(texts, metadatas=metadatas)
        cls.save()

    @classmethod
    def delete(cls, doc_ids: List[str]):
        faiss_index = cls.get_instance()
        # FAISS LangChain delete expects document IDs (string keys from docstore)
        # => cần convert doc_ids sang string để match metadata["doc_id"]
        keys_to_delete = [
            k for k, v in faiss_index.docstore._dict.items()
            if v.metadata.get("doc_id") in doc_ids
        ]
        if keys_to_delete:
            faiss_index.delete(keys_to_delete)
            cls.save()
            print(f"🗑️ Deleted {len(keys_to_delete)} docs from FAISS")
        else:
            print("⚠️ No matching doc_ids found in FAISS")