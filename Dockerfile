FROM python:3.6-alpine3.8
LABEL Maintainer="264768502@qq.com"
RUN apk --no-cache add unzip p7zip gzip bzip2 unrar libarchive=3.3.3-r2
ARG APP=/usr/src/app
WORKDIR $APP
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . ./
WORKDIR $APP/logview
EXPOSE 5051
VOLUME /tmp
ENV LIBARCHIVE=/usr/lib/libarchive.so.13
ENV GUNICORN_WORKERS=5
ENV GUNICORN_BIND=0.0.0.0:5051
ENTRYPOINT ["gunicorn", "--config", "../gunicorn.conf", "--log-config", "../logging.conf", "app:app"]
