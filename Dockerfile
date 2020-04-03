# Build stage
FROM debian:10.0 AS build-env
RUN apt-get update -y && \
    apt-get install -y wget build-essential unzip

WORKDIR /tmp

# entr
RUN wget https://bitbucket.org/eradman/entr/get/33816756113b.zip && \
    unzip 33816756113b.zip && \
    cd eradman-entr-33816756113b && \
    wget http://entrproject.org/patches/entr-3.9-wsl && \
    patch -p1 < entr-3.9-wsl && \
    ./configure && \
    make

# ffmpeg
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz.md5 && \
    md5sum -c ffmpeg-release-amd64-static.tar.xz.md5 && \
    tar xvf ffmpeg-release-amd64-static.tar.xz

# Dev stage
FROM debian:10.0 AS dev-env

RUN apt-get update -y && \
    apt-get install -y python3-dev python3-pip postgresql-client libpq-dev ack && \
    update-alternatives --install /usr/local/bin/python python /usr/bin/python3.7 1 && \
    update-alternatives --install /usr/local/bin/pip pip /usr/bin/pip3 1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd -m human && chown -R human /app
USER human

ENV PATH="/home/human/.local/bin:${PATH}"

COPY --from=build-env /tmp/eradman-entr-33816756113b/entr /usr/local/bin/
COPY --from=build-env /tmp/ffmpeg-4.*-amd64-static/* /usr/local/bin/
COPY ./Pipfile* /app/

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV FLASK_APP /app/api/app.py:create_app()
ENV FLASK_SKIP_DOTENV 1
ENV GOOGLE_APPLICATION_CREDENTIALS /app/secrets/google_credentials.json

RUN pip install pipenv && pipenv install --dev

COPY . /app

# Prod stage
FROM debian:10.0 AS prod-env

RUN apt-get update -y && \
    apt-get install -y python3-dev python3-pip postgresql-client libpq-dev && \
    update-alternatives --install /usr/local/bin/python python /usr/bin/python3.7 1 && \
    update-alternatives --install /usr/local/bin/pip pip /usr/bin/pip3 1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd -m human && chown -R human /app
USER human

ENV PATH="/home/human/.local/bin:${PATH}"

COPY --from=build-env /tmp/ffmpeg-4.*-amd64-static/* /usr/local/bin/
COPY ./Pipfile* /app/

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV FLASK_APP /app/api/app.py:create_app()
ENV FLASK_SKIP_DOTENV 1
ENV GOOGLE_APPLICATION_CREDENTIALS /app/secrets/google-credentials.json
ENV HOST 0.0.0.0
ENV PORT 9000

RUN pip install pipenv && pipenv install

COPY . /app

CMD ["pipenv", "run", "gunicorn", "-w", "4", "-b", "${HOST}:${PORT}", "api.app:create_app()"]
