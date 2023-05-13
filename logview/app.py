# -*- coding: utf-8 -*-
import os
import shutil
import time
import re
import tempfile
import xml.dom.minidom
import mimetypes
import subprocess
import csv
try:
    from urllib.parse import unquote, quote
except ImportError:
    from urllib import unquote, quote

import markdown
import libarchive
import requests
from flask import Flask, request, abort, redirect, send_file, Response
from werkzeug.exceptions import HTTPException
from jinja2 import Environment, PackageLoader
try:
    from ansi2html import Ansi2HTMLConverter
    ANSI2HTML_FLAG = True
except ImportError:
    ANSI2HTML_FLAG = False
try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import XmlLexer, IniLexer
    PYGMENTS_FLAG = True
except ImportError:
    PYGMENTS_FLAG = False

from keywordlist import ERROR_KEYWORDS

app = Flask(__name__)

DOWNLOAD_PATH = os.path.join(tempfile.gettempdir(), u'logview', u'download')
EXTRACT_PATH = os.path.join(tempfile.gettempdir(), u'logview', u'extract')
MAX_LOG_SIZE = 100 * 1024 * 1024 # 100M for max log size which can be view online
MAX_STREAM_SIZE = 500 * 1024 * 1024 # 500M for stream, such as mkv/avi/mp4/webm/ts/wav/mp3/aac
DOWNLOAD_TIMEOUT = 5 * 60
JIRA_INT_ID = u'jenkinsvc'
JIRA_INT_PW = u'Jan@12345678'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>{}</title>
    </head>
    <body>{}</body>
</html>'''

@app.route('/')
def index1():
    '''root path'''
    return redirect('/logview/')

@app.route('/logview')
def index2():
    '''root path'''
    return redirect('/logview/')

@app.route('/logview/')
def index():
    '''root path'''
    return app.send_static_file('index.html')

@app.errorhandler(Exception)
def handle_exception(err):
    if isinstance(err, HTTPException):
        return err
    app.logger.error("Exception: %s(%s)", err, type(err))
    app.logger.exception("Exception Stack")
    return "Found Unknown Exception, please contact Syna MM SQA\n" + str(err), 500

@app.route('/logview/log')
def api_logextract():
    '''download and extract log'''
    def download_log(log_url, local_path):
        '''download log'''
        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)
        if not os.path.exists(local_path):
            with open(local_path, 'wb') as logfile:
                try:
                    app.logger.info("Try download log file")
                    req = requests.get(log_url, timeout=DOWNLOAD_TIMEOUT)
                except requests.exceptions.RequestException as err:
                    app.logger.error("Download Log Fail: %s", err)
                    return False, err
                app.logger.info("Put content to file")
                logfile.write(req.content)
                app.logger.info("Download Log Success")
                return True, ''
        else:
            app.logger.info("Logs File already exist")
            return True, ''
    def extract_log(src_file, dst_path):
        '''extract log'''
        def extract(cmds):
            try:
                subprocess.check_output(cmds)
                return None
            except subprocess.CalledProcessError as err:
                app.logger.error("Extract File Fail(cmd): %s", err.output)
                return err.output
        app.logger.info("Extract Path: %s", src_file)
        app.logger.info("Extract File: %s", dst_path)
        org = os.getcwd()
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        app.logger.info("Change cwd to %s", dst_path)
        os.chdir(dst_path)
        try:
            app.logger.info("Create lock file: %s", os.path.join(dst_path, '.lock'))
            open(os.path.join(dst_path, '.lock'), 'a').close()
            app.logger.info("Extract File: %s", src_file)
            libarchive.extract_file(src_file)
            app.logger.info("Extract File Pass")
            return True, ''
        except libarchive.ArchiveError as err:
            app.logger.error("Extract File Fail(libarchive): %s", err)
            file2cmd = {
                u'.7z': [u'7z', u'x', u'-y', src_file],
                u'.zip': [u'unzip', u'-o', u'-q', src_file],
                u'.tar': [u'tar', u'xvf', src_file],
                u'.tar.gz': [u'tar', u'zxvf', src_file],
                u'.tgz': [u'tar', u'zxvf', src_file],
                u'.tar.bz2': [u'tar', u'jxvf', src_file],
                u'.tar.bz': [u'tar', u'jxvf', src_file],
                u'.tar.Z': [u'tar', u'Zxvf', src_file],
                u'.rar': [u'rar', u'x', src_file],
            }
            for file_ext, cmd in file2cmd.items():
                if src_file.endswith(file_ext):
                    res = extract(cmd)
                    if res is None:
                        return True, ''
                    else:
                        return False, res
                    break
            shutil.rmtree(dst_path, ignore_errors=True)
            shutil.rmtree(src_file, ignore_errors=True)
            return False, err
        finally:
            if os.path.exists(os.path.join(dst_path, '.lock')):
                os.remove(os.path.join(dst_path, '.lock'))
            os.chdir(org)
            app.logger.info("Remove extracted file")
            os.remove(src_file)
    def transurl_to_dirname(url):
        file_name = quote(url, safe='')
        return file_name
    app.logger.info("API Log Download:")
    logurl = request.args.get(u'url')
    if not logurl:
        abort(400, "No url Parameter")
    url_decoded = unquote(logurl)
    app.logger.info("Request URL: %s", url_decoded)
    filename = transurl_to_dirname(url_decoded)
    app.logger.info("Logs File Name: %s", filename)

    if os.path.exists(os.path.join(EXTRACT_PATH, filename)):
        app.logger.info("Logs Folder already exist")
        for _ in range(30):
            if os.path.exists(os.path.join(EXTRACT_PATH, filename, '.lock')):
                time.sleep(1)
                continue
            else:
                break
        else:
            abort(500, "Others are also view this log, but extract hang!")
        return redirect('/logview/view/' + filename)

    res, err = download_log(url_decoded, os.path.join(DOWNLOAD_PATH, filename))
    if not res:
        abort(400, "Download Log Fail {}".format(err))

    res, err = extract_log(os.path.join(DOWNLOAD_PATH, filename),
                           os.path.join(EXTRACT_PATH, filename))
    if not res:
        abort(400, "Extract Log Fail {}".format(err))

    return redirect('/logview/view/' + filename)

@app.route("/logview/view/<path:logurl>")
def log_view(logurl):
    '''View extract log or log list'''
    def human_size(num, suffix='B'):
        '''change btye num to human readable string'''
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Yi', suffix)
    def get_props(logpath):
        '''get log path/size'''
        logsprop = []
        for dirpath, _, filenames in os.walk(logpath):
            for logfile in filenames:
                url = os.path.join(dirpath, logfile).replace(logpath, '')
                size = human_size(os.path.getsize(os.path.join(dirpath, logfile)))
                logsprop.append({'url': url, 'size': size})
        logsprop.sort(key=lambda url: url.get('url'))
        return logsprop
    def create_index_data(http_path, logsprop):
        '''create view for log list'''
        env = Environment(
            loader=PackageLoader(app.name, 'templates'),
        )
        context = {
            'path': http_path,
            'logsprop': logsprop,
        }
        html = env.get_template('download.html').render(context)
        return html
    def prefix2color(content):
        '''add color for prefix in log'''
        return content.replace(u'[WARNING]', u'\x1b[38;5;166m[WARNING]\x1b[0m')\
                      .replace(u'[ERROR]', u'\x1b[38;5;196m[ERROR]\x1b[0m')\
                      .replace(u'[CRITICAL]', u'\x1b[38;5;196m[ERROR]\x1b[0m')\
                      .replace(u' DEBUG ', u' \x1b[38;5;75m[DEBUG]\x1b[0m ')\
                      .replace(u' INFO ', u' \x1b[38;5;40m[INFO]\x1b[0m ')\
                      .replace(u' WARNING ', u' \x1b[38;5;166m[WARNING]\x1b[0m ')\
                      .replace(u' ERROR ', u' \x1b[38;5;196m[ERROR]\x1b[0m ')\
                      .replace(u' CRITICAL ', u' \x1b[38;5;196m[CRITICAL]\x1b[0m ')\
                      .replace(u' Fail ', u'\x1b[38;5;196m Fail \x1b[0m')\
                      .replace(u' W/IPTV', u' \x1b[38;5;166mW/IPTV\x1b[0m')\
                      .replace(u' E/IPTV', u' \x1b[38;5;196mE/IPTV\x1b[0m')\
                      .replace(u' F/IPTV', u' \x1b[38;5;196mF/IPTV\x1b[0m')
    def keyword2color(content):
        '''add color for special known error keyword'''
        replacements = {keyword: u'\x1b[38;5;196m{}\x1b[0m'.format(keyword)
                        for keyword in ERROR_KEYWORDS}
        substrs = sorted(replacements, key=len, reverse=True)
        regexp = re.compile('|'.join(map(re.escape, substrs)))
        return regexp.sub(lambda match: replacements[match.group(0)], content)
    def newline4html(content):
        '''change newline to <br>'''
        log_s = content.find(u'pre class="ansi2html-content">') + \
                len(u'pre class="ansi2html-content">')
        log_e = content.rfind(u'</pre>')
        log = content[log_s:log_e]
        new_log = log.replace('\r', '').replace(u'\n', u'<br>')
        return content.replace(log, new_log)
    def transurl_to_dirname(url):
        file_list = url.split('//')
        url_len = len(file_list)
        dir_name = file_list[0] + '//' + file_list[1]
        if url_len == 3:
            log_name = '/' + file_list[2]
            file_name = quote(dir_name, safe='') + log_name
        else:
            file_name = quote(dir_name, safe='')
        return file_name
    app.logger.info("View Log: %s", logurl)
    _logurl = transurl_to_dirname(logurl)
    if os.path.isdir(os.path.join(EXTRACT_PATH, _logurl)):
        logsprop = get_props(os.path.join(EXTRACT_PATH, _logurl))
        if not logsprop:
            if u'/' in _logurl:
                return redirect(u'/logview/view/' + _logurl[:_logurl.rfind('/')])
            else:
                abort(400, "Fail to find folder {}".format(_logurl))
        http_path = u'/logview/view/' + _logurl
        return create_index_data(http_path, logsprop)
    if not os.path.isfile(os.path.join(EXTRACT_PATH, _logurl)):
        abort(400, "Fail to find file {}".format(_logurl))
    if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) == 0:
        return u"{} is blank file".format(_logurl)
    if _logurl.split(u'.')[-1] in (u'log', u'txt'):
        app.logger.info("User Click log/txt")
        if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) > MAX_LOG_SIZE:
            abort(400, "Log size too big(over {} bytes)".format(MAX_LOG_SIZE))
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            log_content = logf.read().decode('UTF-8', 'ignore')
            if ANSI2HTML_FLAG:
                content = prefix2color(log_content)
                content = keyword2color(content)
                content = Ansi2HTMLConverter().convert(content)
            content = newline4html(content)
            app.logger.info("Return Log Content")
            return content
        abort(400, "Log Content open Fail, maybe non-text file? or non-UTF8 text")
    elif _logurl.split(u'.')[-1] in (u'xml', ):
        app.logger.info("User Click xml file")
        if PYGMENTS_FLAG:
            with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
                xml_content = logf.read().decode('UTF-8', 'ignore')
            app.logger.info("Convert it with highlight")
            content = highlight(xml_content, XmlLexer(), HtmlFormatter(full=True))
            return content
        else:
            xml_content = xml.dom.minidom.parse(os.path.join(EXTRACT_PATH, _logurl))
            app.logger.info("Pretty xml first")
            content = xml_content.toprettyxml()
            app.logger.info("Return RAW XML Content")
            return Response(content, mimetype='text/xml')
    elif _logurl.split(u'.')[-1] in (u'jpg', u'png', u'gif'):
        mimetype, _ = mimetypes.guess_type(_logurl)
        app.logger.info("Return Image Content")
        return send_file(os.path.join(EXTRACT_PATH, _logurl), mimetype=mimetype)
    elif _logurl.split(u'.')[-1] in (u'ini', u'cfg', u'inf'):
        app.logger.info("User Click config file")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            cfg_content = logf.read().decode('UTF-8', 'ignore')
            if PYGMENTS_FLAG:
                app.logger.info("Convert it with highlight")
                content = highlight(cfg_content, IniLexer(), HtmlFormatter(full=True))
                return content
            else:
                app.logger.info("Send to user without highlight")
                return Response(cfg_content, mimetype='text/xml')
        abort(400, "Cfg Content open Fail, maybe non-text file? or non-UTF8 text")
    elif _logurl.split(u'.')[-1] in (u'md', u'markdown'):
        app.logger.info("User Click markdown file")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as mdf:
            md_content = mdf.read().decode('UTF-8', 'ignore')
            html_content = markdown.markdown(md_content)
            return HTML_TEMPLATE.format(_logurl, html_content)
    elif _logurl.split(u'.')[-1] in (u'csv',):
        app.logger.info("User Click csv file")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'r') as csvf:
            reader = csv.reader(csvf)
            table = ['<table border="1">']
            for row in reader:
                table.append("<tr><td>"+"</td><td>".join(row)+"</td></tr>")
            table.append('</table>')
            return HTML_TEMPLATE.format(_logurl, ''.join(table))
    elif _logurl.split(u'.')[-1].split(u'?')[0] in (u'wav', u'mp3'):
        if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) > MAX_STREAM_SIZE:
            abort(400, "File size too big(over {} bytes)".format(MAX_STREAM_SIZE))
        if u'file' in request.args:
            return send_file(os.path.join(EXTRACT_PATH, _logurl))
        file_url = '/logview/view/' + _logurl.replace('/log/', '//log/')+'?file=1' # TODO: fix path workaround
        env = Environment(loader=PackageLoader(app.name, 'templates'))
        context = {'audiofile': file_url}
        html = env.get_template('audioPlayBack.html').render(context)
        return html
    elif _logurl.split(u'.')[-1].split(u'?')[0] in (u'mjpeg', u'mjpg'):
        if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) > MAX_STREAM_SIZE:
            abort(400, "File size too big(over {} bytes)".format(MAX_STREAM_SIZE))
        ext = _logurl.split(u'.')[-1].split(u'?')[0]
        if u'file' in request.args:
            return send_file(os.path.join(EXTRACT_PATH, _logurl))
        file_url = '/logview/view/' + _logurl.replace('/log/', '//log/')+'?file=1' # TODO: fix path workaround
        env = Environment(loader=PackageLoader(app.name, 'templates'))
        context = {'videofile': file_url}
        html = env.get_template('mjpegPlayer.html').render(context)
        return html
    elif _logurl.split(u'.')[-1].split(u'?')[0] in (u'avi', u'mkv', u'mp4', u'ts', u'webm'):
        if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) > MAX_STREAM_SIZE:
            abort(400, "File size too big(over {} bytes)".format(MAX_STREAM_SIZE))
        ext = _logurl.split(u'.')[-1].split(u'?')[0]
        if u'file' in request.args:
            return send_file(os.path.join(EXTRACT_PATH, _logurl))
        file_url = '/logview/view/' + _logurl.replace('/log/', '//log/')+'?file=1' # TODO: fix path workaround
        env = Environment(loader=PackageLoader(app.name, 'templates'))
        context = {'videofile': file_url, 'videomime': 'video/{}'.format(ext)}
        html = env.get_template('videoPlayBack.html').render(context)
        return html
    elif u'tombstone_' in _logurl:
        app.logger.info("User Click tombstone")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            content = logf.read().decode('UTF-8', 'ignore')
            app.logger.info("Return Log Content")
            return HTML_TEMPLATE.format(_logurl, "<pre>{}</pre>".format(content))
        abort(400, "Log Content open Fail, maybe non-text file? or non-UTF8 text")
    elif u'anr_' in _logurl:
        app.logger.info("User Click ANR")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            content = logf.read().decode('UTF-8', 'ignore')
            app.logger.info("Return Log Content")
            return HTML_TEMPLATE.format(_logurl, "<pre>{}</pre>".format(content))
        abort(400, "Log Content open Fail, maybe non-text file? or non-UTF8 text")
    elif u'last_' in _logurl:
        app.logger.info("User Click Recovery Log")
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            content = logf.read().decode('UTF-8', 'ignore')
            app.logger.info("Return Log Content")
            return HTML_TEMPLATE.format(_logurl, "<pre>{}</pre>".format(content))
        abort(400, "Log Content open Fail, maybe non-text file? or non-UTF8 text")
    elif _logurl.endswith('log'):
        app.logger.info("User Click Log")
        if os.path.getsize(os.path.join(EXTRACT_PATH, _logurl)) > MAX_LOG_SIZE:
            abort(400, "Log size too big(over {} bytes)".format(MAX_LOG_SIZE))
        with open(os.path.join(EXTRACT_PATH, _logurl), 'rb') as logf:
            content = logf.read().decode('UTF-8', 'ignore')
            app.logger.info("Return Log Content")
            return HTML_TEMPLATE.format(_logurl, "<pre>{}</pre>".format(content))
        abort(400, "Log Content open Fail, maybe non-text file? or non-UTF8 text")
    else:
        app.logger.info("Return Unknown Content")
        return send_file(os.path.join(EXTRACT_PATH, _logurl))

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=True, debug=True)
