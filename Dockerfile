ARG ACAPY_VERSION=1.0.0-rc0
ARG ACAPY_TAG=py36-1.16-1_${ACAPY_VERSION}

FROM python:3.6-slim AS base

WORKDIR /usr/src/app
# Install and configure poetry

ENV POETRY_VERSION=1.1.11
ENV POETRY_HOME=/opt/poetry

RUN apt-get update && apt-get install --yes curl && apt-get clean \
        && curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN ls /opt/poetry/bin
RUN poetry config virtualenvs.in-project true

# Setup project
COPY mediator_admin/ mediator_admin/
COPY pyproject.toml poetry.lock README.md ./
RUN poetry build

FROM bcgovimages/aries-cloudagent:${ACAPY_TAG}
COPY --from=base --chown=indy:indy /usr/src/app/dist/* /tmp/
RUN pip install /tmp/mediator_admin*-py3-none-any.whl && \
        rm /tmp/mediator_admin*
