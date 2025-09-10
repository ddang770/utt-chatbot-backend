# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (change if your app uses a different port)
EXPOSE 8000

# Run migrations on container start (optional, comment if not needed)
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
#CMD ["alembic", "upgrade", "head", "&&", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]