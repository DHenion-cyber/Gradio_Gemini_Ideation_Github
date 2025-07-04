FROM python:3.9-slim

WORKDIR /app

RUN mkdir -p /data && chmod 777 /data
RUN mkdir -p /.streamlit && chmod 777 /.streamlit

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY src/ ./src/

RUN pip install --no-cache-dir -r requirements.txt

# ENV STREAMLIT_HOME=/data/.streamlit # Setting this via Hugging Face Space Variables

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
