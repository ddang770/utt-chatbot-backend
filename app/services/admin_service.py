# from app.config.database import get_db
from typing import List
from fastapi import  Request, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from app.config.database import SessionLocal
import app.models as models
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain_unstructured import UnstructuredLoader
from sqlalchemy.exc import IntegrityError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.vectorstore import VectorStore
import numpy as np

load_dotenv()

# Get user message and save to database for admin monitor
async def message_service(request: Request, db: Session):
    #Nhận message từ user, lưu DB
    user_id = request.cookies.get("user_id") or str(uuid.uuid4())
    data = await request.json()
    msg = data.get("message", "")

    new_msg = models.Message(user_id=user_id, message=msg)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    return {"reply": f"Bot received: {msg}"}

# Thống kê cho admin
def stats_service():
    db = SessionLocal()
    try:
        total_users = db.query(models.Message.user_id).distinct().count()

        todays_users = (
            db.query(models.Message.user_id)
            .filter(func.date(models.Message.created_at) == func.current_date())
            .distinct()
            .count()
        )

        num_messages = db.query(models.Message).count()
        num_documents = db.query(models.Document).count()

        return {
            "EM": "Get stats data success!",
            "EC": 0,
            "DT": {
                "total_users": total_users,
                "todays_users": todays_users,
                "num_messages": num_messages,
                "num_documents": num_documents
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in admin service...",
            "DT": {}
        }
    finally:
        db.close()

def format_size(size_bytes):
    """Chuyển byte → KB/MB/GB"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"

async def add_documents(files: list[UploadFile], db: Session):
    try:
        results = []
        UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            try:
                # Try saving metadata vào Postgres
                doc = models.Document(
                    name=file.filename,
                    size=f"{format_size(os.path.getsize(file_path))}",
                    upload_date=datetime.now(timezone.utc),
                    status="processed",
                    type=file.filename.split(".")[-1].upper(),
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            except IntegrityError:
                db.rollback()  # rollback để tiếp tục xử lý
                # Nếu đã tồn tại file thì update lại metadata
                existing_doc = db.query(models.Document).filter_by(name=file.filename).first()
                if existing_doc:
                    return {
                        "EC": 2,
                        "EM": f"Đã tồn tại file {file.filename}...",
                        "DT": []
                    }

            # Chunk file
            loader = UnstructuredLoader(file_path, mode="elements")
            documents = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=150,
                separators=["\n\n", "\n", ".", "!", "?", "…", ";"]
            )
            chunks = splitter.split_documents(documents)
            texts = [c.page_content for c in chunks if c.page_content.strip()]

            if not texts:
                results.append({
                    "name": file.filename,
                    "doc_id": doc.id,
                    "status": "empty"
                })
                continue

            # Add vào FAISS (global instance)
            faiss_index = VectorStore.get_instance()
            faiss_index.add_texts(
                texts,
                metadatas=[{"doc_id": doc.id, "source": file.filename} for _ in texts]
            )
            VectorStore.save()

            results.append({
                "name": file.filename,
                "doc_id": doc.id,
                "status": "processed"
            })

        return {
            "EM": "All files processed",
            "EC": 0,
            "DT": results
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "EC": 1,
            "EM": "Something wrong in admin service...",
            "DT": []
        }

def delete_document(doc_id: int, db: Session):
    try:
        faiss_index = VectorStore.get_instance()
        faiss_index.index.remove_ids(np.array([doc_id]))
        VectorStore.save()

        db.query(models.Document).filter(models.Document.id == doc_id).delete()
        db.commit()
        # return {"message": f"Document {doc_id} deleted"}
        return {
            "EM": f"Document {doc_id} deleted",
            "EC": 0,
            "DT": []
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in admin service...",
            "DT": []
        }