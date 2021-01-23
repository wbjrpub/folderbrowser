"""
TODO document
"""
import html
import logging
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

# -------------------------------------------------------------------------------
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from io import StringIO, BytesIO
from typing import Callable, Dict


class RequestHandler(SimpleHTTPRequestHandler):
    """
    TODO document
    """

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

    def __init__(self, *args, **kwargs):
        self.routes = [
            (re.compile(rx), method)
            for rx, method in (
                ("^/browse(?P<path>.*)", self.__browse),
                # ('^/(?P<session_id>\d+)/browse(?P<path>.*)', self.__browse),
            )
        ]
        self.path: str = ""
        self.display_path: str = ""
        self.translated_path: str = ""
        super().__init__(*args, **kwargs)

    @staticmethod
    def sizeof_fmt(num, suffix="B"):
        """

        :param num:
        :param suffix:
        :return:
        """
        if num < 1024:
            return str(num) + "B"
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if num < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} Yi{suffix}"

    def do_GET(self):
        """

        :return:
        """
        func: Callable[[Dict], None]
        for regex, func in self.routes:
            match = regex.match(self.path)
            if match:
                group_dict = match.groupdict()
                # if int(group_dict['session_id']) != self.session_id:
                #     self.send_error(400, 'Not found')
                #     return
                return func(group_dict)
        return self.__default_route()

    def __browse(self, group_dict):
        self.path = group_dict["path"]
        if self.path == "" or os.path.isdir(self.path):
            if not self.path.endswith("/"):
                self.path += "/"
        action = reverse = None
        if "?" in self.path:
            self.path, query_params = self.path.split("?", 1)
            query_params = urllib.parse.parse_qs(query_params)
            if "tail" in query_params:
                action = "tail"
                reverse = "head"
            elif "head" in query_params:
                action = "head"
                reverse = "tail"
            else:
                self.send_error(404, "No such action")
                return
        self.display_path = (
            "Toplevel"
            if self.path == "/"
            else html.escape(urllib.parse.unquote(self.path.strip("/")))
        )
        if action:
            self.translated_path = self.translate_path(self.path)
            if os.path.isfile(self.translated_path):
                try:
                    num_lines = int(query_params[action][0])
                except Exception:  # pylint: disable=broad-except
                    num_lines = 40
                self._filepart(action, reverse, num_lines)
                return

        super().do_GET()

    # pylint: disable=too-many-locals
    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            entries = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list folder")
            return None
        entries.sort(key=lambda a: a.lower())
        buf = StringIO()
        buf.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        buf.write(
            "<html>\n<head>\n<title>Folder Listing for %s</title>\n" % self.display_path
        )
        buf.write(self.CSS)
        buf.write(
            "</head><body>\n<div id='header'><h2>Folder Listing for %s</h2>\n"
            % self.display_path
        )

        buf.write("</div><hr>\n<table id='dirlisting'>\n")
        if self.path != "/":
            buf.write(
                '<tr><td>&nbsp;</td><td colspan=3><a href="..">[Parent Folder]</a></td></tr>\n'
            )
        dirs = []
        files = []
        for name in entries:
            full_name = os.path.join(path, name)
            display_name = name
            link_name = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(full_name):
                display_name = name + "/"
                link_name = name + "/"
            if os.path.islink(full_name):
                display_name = name + "@"
                # Note: a link to a folder displays with @ and links with /
            linkname_quoted = urllib.parse.quote(link_name)
            if os.path.isfile(full_name):
                statinfo = os.stat(full_name)
                size = self.sizeof_fmt(statinfo.st_size)
                num_lines = 40
                files.append(
                    """<tr>
  <td align=right>%s</td>
  <td><a href="%s">%s</a></td>
  <td><a href="%s?head=%d" title="First %d lines">[head]</a></td>
  <td><a href="%s?tail=%d" title="Last %d lines">[tail]</a></td>
</tr>\n"""
                    % (
                        size,
                        linkname_quoted,
                        html.escape(display_name),
                        linkname_quoted,
                        num_lines,
                        num_lines,
                        linkname_quoted,
                        num_lines,
                        num_lines,
                    )
                )
            else:
                dirs.append(
                    """<tr>
  <td align=right>Folder</td>
  <td colspan='3'><a href="%s">%s</a></td>
</tr>\n"""
                    % (
                        linkname_quoted,
                        html.escape(display_name),
                    )
                )
        for item in dirs:
            buf.write(item)
        for item in files:
            buf.write(item)
        buf.write("</table>\n</body>\n</html>\n")
        length = buf.tell()
        buf.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return BytesIO(buf.read().encode())

    def _filepart(self, action, reverse, num_lines=40):
        linkname = urllib.parse.quote(os.path.basename(self.path.strip("/")))
        buf = StringIO()
        more_n = max(2, int(num_lines * 2))
        less_n = max(1, int(num_lines / 2))
        buf.write(
            f"""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>{html.escape(self.translated_path)}</title>
{self.CSS}
</head>
<body>
<div id='header'>
<p style='font-size: 14; font-family: monospace; font-weight: bold'>
<h2>File {self.display_path}</h2>
<a href="{linkname}?{action}={less_n}">[Less: {action} -n {less_n}]</a>
<a href="{linkname}?{action}={num_lines}">[Redo: {action} -n {num_lines}]</a>
<a href="{linkname}?{action}={more_n}">[More: {action} -n {more_n}]</a>
<a href="{linkname}?{reverse}={num_lines}">[Opposite: {reverse} -n {num_lines}]</a>
<a href="{linkname}">[Whole File]</a>
<a href=".">[Folder]</a></p>
</div>
<hr/><pre>
"""
        )
        try:
            txt = subprocess.check_output(
                [action, "-n", str(num_lines), self.translated_path], encoding="utf-8"
            )
            buf.write(html.escape(txt))
        # pylint: disable=broad-except
        except Exception as ex:
            buf.write(str(ex))
        buf.write("""</pre></body></html>""")
        length = buf.tell()
        buf.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", f"text/html; charset={encoding}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(buf.read().encode())

    def __default_route(self):
        resp = ""
        resp += f"URL was: {self.path}</br>"
        resp += '<a href="/browse/">browse</a> '
        # resp += f'<a href="/{self.session_id}/browse/">browse</a> '
        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(str.encode(resp))


# pylint: disable=too-few-public-methods
class Server:
    """
    TODO document
    """

    def __init__(
        self, log: logging.Logger, bind_address: str = "127.0.0.1", port: int = 8080
    ):
        """
        :param log: for logging
        :param bind_address: use "0.0.0.0" to listen on all addresses.
        Defaults to localhost only.
        :param port: port to listen on.
        """
        self.log = log
        self.port = port
        self.webserver = HTTPServer(("", self.port), RequestHandler)
        # self.webserver = HTTPServer(('', self.webserver_port), partial(RequestHandler, self))
        self.webserver.allow_reuse_address = True
        self.bind_address = bind_address
        self.url = f"http://{self.bind_address}:{self.port}/"
        self.thread = threading.Thread(
            name="webserver", target=self.webserver.serve_forever
        )
        self.thread.setDaemon(False)
        self.thread.start()
        log.info(f"Server URL: {self.url}")
        log.info(f"Browse URL: {self.url}browse/")

    def stop(self):
        """
        Stop processing. Returns
        :return: list of Exceptions encountered.
        """
        result = []
        try:
            self.webserver.shutdown()
        except Exception as ex:  # pylint: disable=broad-except
            result.append(ex)
            self.log(f"shutdown: {ex}")
        try:
            self.thread.join(1.0)
        except Exception as ex:  # pylint: disable=broad-except
            result.append(ex)
            self.log(f"thread.join: {ex}")
        return result
