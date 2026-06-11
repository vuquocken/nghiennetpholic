# Dockerfile cho Nghiện Netflix (dùng cho Hugging Face Spaces / Render / Fly.io)
FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Hugging Face Spaces mặc định dùng cổng 7860; Render sẽ tự đặt biến PORT khác.
ENV PORT=7860
EXPOSE 7860

CMD ["python", "server.py"]
