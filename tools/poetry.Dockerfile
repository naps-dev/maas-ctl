FROM python:3.11-buster

RUN pip install --upgrade pip && pip install poetry && pip install pytest

CMD ["/bin/sh", "-c"]
