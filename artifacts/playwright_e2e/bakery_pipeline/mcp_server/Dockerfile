FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv pip install --system -e .
RUN playwright install chromium --with-deps

EXPOSE 8000
CMD ["python", "server.py"]
