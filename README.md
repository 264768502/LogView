# Introduce
This a online log view tool, normally you need define a online compressed log path.
app will download/extract it, and show file list with hyperlink.
Then once you choose one of them, you can start view log online with colorfulled by ansi if it contained.

# Requriment
* Flask/Jinja2: python webapp framework
* gunicorn: webapp deploy tool
* libarchive-c: extract file
* requests: download file
* supervisor: Need install before deploy this app (backgroup deamon)!!

# Compressed Support List
All compressed file which support by [libarchive](http://libarchive.org/)

# API
## /logview/log/&lt;logurl&gt;
Use to download and return file list (/logview/view/&lt;logpath&gt;)
If download/extract fail, will return http code 400/500
Normally log/extract will be put to system tempdir with append `logview`

## /logview/view/&lt;logpath&gt;
Use to view log content, click will guide to view log

# Deploy by Shell
Clone this project to your local, and run `install.sh`
Some operation request sudo permission
Default deploy port at 5051, can be change at supervisor.conf

# Deplog by Docker
```sh
# Build normal
docker build -t logview:1.5.2 .
# Build in China Network
docker build -t logview:1.5.2 -f Dockerfile4CN .
# Deploy
docker run --name logview --mount type=bind,source=/tmp,target=/tmp -p 5051:5051 -d --restart always logview:1.5.2
```

# Changelog
## 1.5.2
* Add support online view stream with high size (500M) support
## 1.5.1
* Add support mjpeg playback online
## 1.5.0
* Add support video playback online
