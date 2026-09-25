FROM python:3.12-slim
RUN useradd --create-home --uid 10002 broker
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Docker socket access is controlled by deployment permissions; root is required by many daemon socket setups.
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
