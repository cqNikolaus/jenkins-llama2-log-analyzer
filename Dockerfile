FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY analyze_log.py .
CMD ["python", "analyze_log.py"]
