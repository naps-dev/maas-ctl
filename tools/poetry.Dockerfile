FROM python:3.11-buster

ARG POETRY_VERSION=1.4.1
ARG PYTEST_VERSION=7.2.1

RUN pip install --upgrade pip && pip install poetry==${POETRY_VERSION} && pip install pytest==${PYTEST_VERSION}

CMD ["/bin/sh", "-c"]
