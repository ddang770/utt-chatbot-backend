# from app.config.database import get_db
from typing import List
from fastapi import  Request, UploadFile, HTTPException
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
from fastapi.responses import FileResponse
import time
import jwt

load_dotenv()

base_dir = os.path.dirname(os.path.dirname(__file__))   # go up from services/ -> app/
data_dir = os.path.join(base_dir, "data")

# Thống kê cho admin
def stats_service(start_date: str = None, end_date: str = None):
    """
    Get statistics for messages, users and documents within a date range.
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    Usage examples:
    # Get all stats
    stats_service()

    # Get stats for specific date range
    stats_service("2024-01-01", "2024-01-31")

    # Get stats from start date to now
    stats_service("2024-01-01")

    # Get stats until end date
    stats_service(end_date="2024-01-31")
    """
    db = SessionLocal()
    try:
        # Build date filter condition
        date_filter = []
        if start_date:
            date_filter.append(func.date(models.Message.created_at) >= start_date)
        if end_date:
            date_filter.append(func.date(models.Message.created_at) <= end_date)

        # Daily user counts
        users_query = (
            db.query(
                func.date(models.Message.created_at).label('date'),
                func.count(func.distinct(models.Message.user_id)).label('count')
            )
            .group_by(func.date(models.Message.created_at))
            .order_by(func.date(models.Message.created_at))
        )
        if date_filter:
            users_query = users_query.filter(*date_filter)
        users_per_day = users_query.all()

        # Daily message counts
        messages_query = (
            db.query(
                func.date(models.Message.created_at).label('date'),
                func.count().label('count')
            )
            .group_by(func.date(models.Message.created_at))
            .order_by(func.date(models.Message.created_at))
        )
        if date_filter:
            messages_query = messages_query.filter(*date_filter)
        messages_per_day = messages_query.all()

        # Total documents count (just a number)
        documents_query = db.query(models.Document)
        total_documents = documents_query.count()

        # Recent user messages only
        recent_messages = (
            db.query(models.Message)
            .filter(models.Message.role == "user")  # only user messages
            .order_by(models.Message.created_at.desc())
            .limit(2)
            .all()
        )

        stats = {
            "users": [
                {"date": str(day.date), "count": day.count}
                for day in users_per_day
            ],
            "messages": [
                {"date": str(day.date), "count": day.count}
                for day in messages_per_day
            ],
            "documents": total_documents,  # just the number
            "dataMessagesWithDates": [
                {
                    "id": msg.id,
                    "user": str(msg.user_id),
                    "message": msg.message,
                    "timestamp": msg.created_at.isoformat(),
                }
                for msg in recent_messages
            ]
        }

        return {
            "EM": "Get stats data success!",
            "EC": 0,
            "DT": stats
        }

    except Exception as e:
        print(f"Error in stats_service: {str(e)}")
        return {
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
    
def get_all_documents(db: Session):
    try:
        docs = db.query(models.Document).all()
        return  {
            "EC": 0,
            "EM": "Get document metadata successful!",
            "DT": [
                {
                    "id": d.id,
                    "name": d.name,
                    "size": d.size,
                    "uploadDate": d.upload_date.strftime("%Y-%m-%d") if d.upload_date else None,
                    "status": d.status,
                    "type": d.type
                }
                for d in docs
            ]
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in chat service...",
            "DT": []
        }


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

            # Generate stable FAISS IDs
            faiss_ids = [str(uuid.uuid4()) for _ in texts]

            # Add vào FAISS (global instance)
            faiss_index = VectorStore.get_instance()
            faiss_index.add_texts(
                texts,
                metadatas=[{"doc_id": doc.id, "source": file.filename} for _ in texts],
                ids = faiss_ids
            )
            VectorStore.save()

            # Save FAISS IDs to Postgres
            doc.vector_ids = faiss_ids
            db.add(doc)
            db.commit()

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


async def delete_document(request: Request, db: Session):
    try:
        # get the doc_id from request and init vectordb instance
        faiss_index = VectorStore.get_instance()
        data = await request.json()
        doc_id = data.get("id")

        # 1.find document in DB
        document = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not document:
            return {"EC": 1, "EM": f"Document {doc_id} not found", "DT": []}

        # 2.remove vectors by FAISS IDs
        if document.vector_ids:
            faiss_index.delete(ids=document.vector_ids)
            VectorStore.save()

        # 3.delete physical file in app/data/ folder
        # base_dir = os.path.dirname(os.path.dirname(__file__))   # go up from services/ -> app/
        # data_dir = os.path.join(base_dir, "data")
        file_path = os.path.join(data_dir, document.name)

        if os.path.exists(file_path):
            os.remove(file_path)

        # 4.delete from postgresql
        db.delete(document)
        db.commit()

        return {
            "EM": f"Document '{document.name}' deleted",
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
    
# View document service
ALGORITHM = "HS256"
SECRET_KEY=os.getenv("JWT_SECRET_KEY")
def create_signed_url(doc_id: int, expires_in: int = 180): # Expires in 30 minutes
    payload = {"doc_id": doc_id, "exp": int(time.time()) + expires_in}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return f"/documents/{doc_id}/signed?token={token}"

def serve_signed_document(doc_id: int, token: str, db: Session):
    # validate signed token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        doc_id_from_token = payload.get("doc_id")
        if doc_id_from_token != doc_id:
            raise HTTPException(status_code=403, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

    #lookup document metadata
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # build path from metadata
    file_path = os.path.join(data_dir, doc.name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # detect MIME type based on extension or DB "type"
    mime_type = {
        "PDF": "application/pdf",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "TXT": "text/plain",
        "MD": "text/markdown",
    }.get(doc.type.upper(), "application/octet-stream")


    return FileResponse(
        file_path, 
        media_type=mime_type, 
        headers={"Content-Disposition": f'inline; filename="{doc.name}"'}
        )