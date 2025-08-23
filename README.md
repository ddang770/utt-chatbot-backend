# Chatbot for documents

Technologies used:
- LangChain
- RAG
- gpt-oss-20b model
- gemini embedding api

![Image](https://d2908q01vomqb2.cloudfront.net/887309d048beef83ad3eabf2a79a64a389ab1c9f/2023/07/13/DBBLOG-3334-image001.png)

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

alembic upgrade head

- Tạo Models trong models.py
- Tạo migration script, chạy:  
```alembic revision --autogenerate -m "create messages table"```  
-> Nó sẽ tạo file trong alembic/versions/xxxxxxxx_create_messages_table.py.
Bên trong sẽ có code SQLAlchemy để tạo bảng.
- Apply migration:  
```alembic upgrade head```  
Lúc này bảng sẽ được tạo trong Postgres.
- Nếu thay đổi schema trong models.py, chạy để render lại.