FROM python:3.11-slim

RUN apt update && apt install -y build-essential jq less git

COPY ./dist/*.whl ./
RUN pip install *.whl && rm -rf *.whl

ENTRYPOINT ["mctl"]
