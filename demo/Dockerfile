FROM python:3.10
WORKDIR /usr/src/app/

ENV POETRY_VERSION=1.1.11
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Setup project
RUN touch mediator_admin_demo.py
COPY pyproject.toml poetry.lock ./
ARG install_flags=--no-dev
RUN poetry install ${install_flags}

COPY mediator_admin_demo.py mediator_admin_demo.py

ENTRYPOINT ["poetry", "run"]
