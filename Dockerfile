FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    YJN_DB=/data/yjn.db \
    YJN_UPLOADS=/data/uploads

WORKDIR /app
COPY app.py extra.py theme.py admin.py ./
RUN mkdir -p /data

# Render يحدد PORT تلقائياً، والتطبيق يقرأه من المتغير (الافتراضي 8000 محلياً)
EXPOSE 8000
CMD ["python", "app.py"]
