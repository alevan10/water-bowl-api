FROM python:3.9.12
ARG PYPI_USER
ARG PYPI_PASSWORD
WORKDIR /opt/waterbowl
COPY src/ api/
ENV PYTHONPATH "/opt/waterbowl:/opt/waterbowl/api:/opt/waterbowl/api/waterbowl-api"
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN pip install --upgrade pip;\
    pip install poetry==1.1.15;\
    poetry config http-basic.home $PYPI_USER $PYPI_PASSWORD;\
    poetry config virtualenvs.create false && poetry install -v
CMD ["uvicorn", "api.waterbowl-api.app:app", "--host", "0.0.0.0", "--port", "80"]
