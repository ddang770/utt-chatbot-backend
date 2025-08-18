from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Tạo ứng dụng FastAPI
app = FastAPI()

# List of allowed origins (frontend URLs)
origins = [
    "http://localhost:3000"     # for local React dev
]

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],          # or ["GET", "POST"]
    allow_headers=["*"],          # or specific headers
)