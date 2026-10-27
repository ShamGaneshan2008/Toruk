FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
WORKDIR /app
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m -u 1000 app
COPY --chown=app:app src /app/src
COPY --chown=app:app download_chat_backbone.py /app/download_chat_backbone.py
COPY --chown=app:app selector.pt /app/selector.pt
ENV PYTHONPATH=/app/src
RUN echo '479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d  /app/selector.pt' | sha256sum -c -
RUN mkdir /app/backbone && chown app:app /app/backbone
USER app
RUN python /app/download_chat_backbone.py --output /app/backbone
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=150s CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:7860/healthz',timeout=3))['ready']"
CMD ["python", "-m", "toruk_lm.inference_server", "--backbone-dir", "/app/backbone", "--selector-checkpoint", "/app/selector.pt", "--host", "0.0.0.0", "--port", "7860"]
