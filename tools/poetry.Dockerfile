FROM python:3.11-buster

ARG POETRY_VERSION
ARG PYTEST_VERSION

RUN pip install --upgrade pip && pip install poetry==${POETRY_VERSION} && pip install pytest==${PYTEST_VERSION}

CMD ["/bin/sh", "-c"]
