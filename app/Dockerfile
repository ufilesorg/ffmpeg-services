FROM python:3.12-slim AS fast-base

RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt 

RUN adduser --disabled-password --gecos '' user && mkdir /app/logs && chown -R user:user /app/logs

FROM fast-base AS fast-server

USER user
COPY --chown=user:user . .

CMD ["python", "-m" ,"debugpy", "--listen", "0.0.0.0:3000", "-m", "app"]
# CMD [ "python","app.py" ]