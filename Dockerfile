<<<<<<< HEAD
ARG ACR_URL
=======
FROM continuumio/miniconda3 AS build
>>>>>>> 9606a005f40eca14eb9b249e3dfc971b7a858289

FROM ${ACR_URL}/shared/belfius/mle/images/python as build-stage

<<<<<<< HEAD
WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"
=======
# Copy requirements and install dependencies
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy
>>>>>>> 9606a005f40eca14eb9b249e3dfc971b7a858289

# mount azure artifacts secret url and force pip to use it as the default repository
COPY requirements.txt requirements.txt
RUN --mount=type=secret,id=PIP_INDEX_URL python -m pip install -r requirements.txt  --index-url $(cat /run/secrets/PIP_INDEX_URL)

<<<<<<< HEAD
# TODO: this should point to a slim version
FROM ${ACR_URL}/shared/belfius/mle/images/python as final
=======
# Create non-root user for security
#RUN useradd --create-home --shell /bin/bash appuser && \
#    chown -R appuser:appuser /app
#USER appuser
>>>>>>> 9606a005f40eca14eb9b249e3dfc971b7a858289

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
RUN mkdir /usr/app && chown -R python:python /usr/app
WORKDIR /usr/app

<<<<<<< HEAD
COPY --chown=python:python --from=build-stage /usr/app/venv /usr/app/venv
COPY --chown=python:python src/src/ .
=======
# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH /opt/conda/envs/multi-user-load-tester/bin:$PATH
>>>>>>> 9606a005f40eca14eb9b249e3dfc971b7a858289

USER 999

<<<<<<< HEAD
ENV PATH="/usr/app/venv/bin:$PATH"
CMD ["uvicorn","main:asgi","--host", "0.0.0.0","--port","8080"]
=======
# Run the application
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> 9606a005f40eca14eb9b249e3dfc971b7a858289
