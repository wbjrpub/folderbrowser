import os, re, subprocess, sys, threading, logging
import html, urllib.request, urllib.parse, urllib.error
import urllib.parse
from io import StringIO, BytesIO

#-------------------------------------------------------------------------------
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routes = [(re.compile(rx), method) for rx, method in (
            ('^/browse(?P<path>.*)', self.__browse),
            # ('^/(?P<session_id>\d+)/browse(?P<path>.*)', self.__browse),
        )]
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    CSS = """
<style>
#header {
  background-color: EEF;
}
table {
  border-collapse: collapse;
}
table, th, td {
    border: 1px solid black;
}
#dirlisting {
  font-family: monospace;
}

#dirlisting a {
  text-decoration: none;
}
</style>
"""

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        if num < 1024:
            return "%dB" % num
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def do_GET(self):
        for rx, func in self.routes:
            m = rx.match(self.path)
            if m:
                groupdict = m.groupdict()
                # if int(groupdict['session_id']) != self.session_id:
                #     self.send_error(400, 'Not found')
                #     return
                return func(groupdict)
        return self.__default_route()

    def __browse(self, groupdict):
        self.path = groupdict['path']
        if self.path == '' or os.path.isdir(self.path):
            if not self.path.endswith('/'):
                self.path += '/'
        action = reverse = None
        if '?' in self.path:
            self.path, query_params = self.path.split('?', 1)
            query_params = urllib.parse.parse_qs(query_params)
            if 'tail' in query_params:
                action = 'tail'
                reverse = 'head'
            elif 'head' in query_params:
                action = 'head'
                reverse = 'tail'
            else:
                self.send_error(404, "No such action")
                return
        self.displaypath = "Toplevel" if self.path=='/' else html.escape(urllib.parse.unquote(self.path.strip('/')))
        if action:
            self.translated_path = SimpleHTTPRequestHandler.translate_path(self, self.path)
            if os.path.isfile(self.translated_path):
                try:
                    n = int(query_params[action][0])
                except:
                    n = 40
                self.filepart(action, reverse, n)
                return

        return SimpleHTTPRequestHandler.do_GET(self)

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            entries = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        entries.sort(key=lambda a: a.lower())
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<head>\n<title>Directory Listing for %s</title>\n" % self.displaypath)
        f.write(self.CSS)
        f.write("</head><body>\n<div id='header'><h2>Directory Listing for %s</h2>\n" % self.displaypath)

        f.write("</div><hr>\n<table id='dirlisting'>\n")
        if self.path != '/':
            f.write('<tr><td>&nbsp;</td><td colspan=3><a href="..">[Parent Directory]</a></td></tr>\n')
        dirs = []
        files = []
        for name in entries:
            fullname = os.path.join(path, name)
            displayname = name
            linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            linkname_quoted = urllib.parse.quote(linkname)
            if os.path.isfile(fullname):
                statinfo = os.stat(fullname)
                size = self.sizeof_fmt(statinfo.st_size)
                n = 40
                files.append("""<tr>
  <td align=right>%s</td>
  <td><a href="%s">%s</a></td>
  <td><a href="%s?head=%d" title="First %d lines">[head]</a></td>
  <td><a href="%s?tail=%d" title="Last %d lines">[tail]</a></td>
</tr>\n"""
                    % (size,
                       linkname_quoted, html.escape(displayname),
                       linkname_quoted, n, n,
                       linkname_quoted, n, n,
                    ))
            else:
                dirs.append("""<tr>
  <td align=right>Directory</td>
  <td colspan='3'><a href="%s">%s</a></td>
</tr>\n"""
                    % (linkname_quoted, html.escape(displayname),
                    ))
        for s in dirs:
            f.write(s)
        for s in files:
            f.write(s)
        f.write("</table>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return BytesIO(f.read().encode())

    def filepart(self, action, reverse, n=40):
        linkname = urllib.parse.quote(os.path.basename(self.path.strip('/')))
        f = StringIO()
        f.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>%s</title>
%s
</head>
<body>
<div id='header'>
<p style='font-size: 14; font-family: monospace; font-weight: bold'>
<h2>File %s</h2>
<a href="%s?%s=%d">[Less: %s -n %s]</a>
<a href="%s?%s=%d">[Redo: %s -n %s]</a>
<a href="%s?%s=%d">[More: %s -n %s]</a>
<a href="%s?%s=%d">[Opposite: %s -n %s]</a>
<a href="%s">[Whole File]</a>
<a href="%s">[Directory]</a></p>
</div>
<hr/><pre>
""" % (html.escape(self.translated_path),
       self.CSS,
       self.displaypath, #html.escape(self.translated_path),
       linkname, action, max(1, int(n/2)), action, max(1, int(n/2)),
       linkname, action, n, action, n,
       linkname, action, max(2, int(n*2)), action, max(2, int(n*2)),
       linkname, reverse, n, reverse, n,
       linkname,
       '.' #'browse/%s' % urllib.quote(dirname),
    ))
        try:
            s = subprocess.check_output([action, '-n', str(n), self.translated_path], encoding='utf-8')
            f.write(html.escape(s))
        except Exception as ex:
            f.write(str(ex))
        f.write("""</pre></body></html>""")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(f.read().encode())

    def __default_route(self):
        resp = ''
        resp += 'URL was: %s</br>' % self.path
        resp += '<a href="/browse/">browse</a> '
        # resp += '<a href="/%d/browse/">browse</a> ' % self.session_id
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(str.encode(resp))



class Server:
    def __init__(self, log: logging.Logger):
        self.log = log
        self.webserver_port = 8081
        self.webserver = HTTPServer(('', self.webserver_port), RequestHandler)
        # self.webserver = HTTPServer(('', self.webserver_port), partial(RequestHandler, self))
        self.webserver.allow_reuse_address = True
        self.HOSTNAME = '127.0.0.1'
        self.url = 'http://%s:%d/' % (self.HOSTNAME, self.webserver_port)
        self.thread = threading.Thread(name='webserver', target=self.webserver.serve_forever)
        self.thread.setDaemon(False)
        self.thread.start()
        log.info("Server URL: %s", self.url)
