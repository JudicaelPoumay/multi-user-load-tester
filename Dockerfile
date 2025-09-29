ARG ACR_URL

FROM ${ACR_URL}/shared/belfius/mle/images/python as build-stage

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

# mount azure artifacts secret url and force pip to use it as the default repository
COPY requirements.txt requirements.txt
RUN --mount=type=secret,id=PIP_INDEX_URL python -m pip install -r requirements.txt  --index-url $(cat /run/secrets/PIP_INDEX_URL)

# TODO: this should point to a slim version
FROM ${ACR_URL}/shared/belfius/mle/images/python as final

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python
RUN mkdir /usr/app && chown -R python:python /usr/app
WORKDIR /usr/app

COPY --chown=python:python --from=build-stage /usr/app/venv /usr/app/venv
COPY --chown=python:python src/src/ .

USER 999

ENV PATH="/usr/app/venv/bin:$PATH"
CMD ["uvicorn","main:socket_app","--host", "0.0.0.0","--port","8080"]