# Always-on Jarvis runner: Telegram long-polling assistant wired to the Vault
# (finance-chief Supabase project) and the OrigineX database. Deploy on any
# always-on host (Railway, Fly.io, Render, or a small VM). Credentials come
# from host environment variables; see docs/JARVIS.md.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "jarvis"]
