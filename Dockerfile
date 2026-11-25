FROM python:3.12-slim
WORKDIR /app
COPY app.py extra.py ./
ENV YJN_DB=/data/yjn.db YJN_UPLOADS=/data/uploads PORT=8000
VOLUME /data
EXPOSE 8000
CMD ["python", "app.py"]
