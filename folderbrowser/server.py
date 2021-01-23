"""
Provides classes to implement a folder browser.
"""
import html
import logging
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

# -------------------------------------------------------------------------------
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from io import StringIO


class FolderBrowserHandler:
    """
    Provides the main do_GET method for browsing a folder or viewing a file
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

    def __init__(self, request_handler: SimpleHTTPRequestHandler):
        self.request_handler = request_handler
        self.path: str = ""
        self.display_path: str = ""
        self.translated_path: str = ""

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

    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Generate a response for the given path.
        :return: None if this function has generated the response.
        False if no response was genereted, i.e. the path was not handled.
        """
        self.path = self.request_handler.path
        if "?" in self.path:
            self.path, query_params = self.path.split("?", 1)
        else:
            self.path, query_params = self.path, None

        local_path = "." + self.path
        if os.path.isdir(local_path):
            self._handle_directory(local_path)
            return None

        self.display_path = self._get_display_path()

        action = reverse = None
        if query_params is not None:
            query_params = urllib.parse.parse_qs(query_params)
            if "tail" in query_params:
                action = "tail"
                reverse = "head"
            elif "head" in query_params:
                action = "head"
                reverse = "tail"
            else:
                self.request_handler.send_error(404, "No such action")
                return None
        if action:
            self.translated_path = self.request_handler.translate_path(self.path)
            if os.path.isfile(self.translated_path):
                try:
                    num_lines = int(query_params[action][0])
                except Exception:  # pylint: disable=broad-except
                    num_lines = 40
                self._send_part_of_file(action, reverse, num_lines)
                return None
        # Not handled by us:
        return False

    def _handle_directory(self, local_path):
        if not self.path.endswith("/"):
            self.path += "/"
        self.display_path = self._get_display_path()
        self._list_directory(local_path)

    # pylint: disable=too-many-locals
    def _list_directory(self, local_path):
        """Helper to produce a directory listing."""
        try:
            entries = os.listdir(local_path)
        except os.error:
            self.request_handler.send_error(404, "No permission to list folder")
            return
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
            full_name = os.path.join(local_path, name)
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
        self.request_handler.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.request_handler.send_header(
            "Content-type", "text/html; charset=%s" % encoding
        )
        self.request_handler.send_header("Content-Length", str(length))
        self.request_handler.end_headers()
        self.request_handler.wfile.write(buf.read().encode())

    def _send_part_of_file(self, action, reverse, num_lines=40):
        link_name = urllib.parse.quote(os.path.basename(self.path.strip("/")))
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
<a href="{link_name}?{action}={less_n}">[Less: {action} -n {less_n}]</a>
<a href="{link_name}?{action}={num_lines}">[Redo: {action} -n {num_lines}]</a>
<a href="{link_name}?{action}={more_n}">[More: {action} -n {more_n}]</a>
<a href="{link_name}?{reverse}={num_lines}">[Opposite: {reverse} -n {num_lines}]</a>
<a href="{link_name}">[Whole File]</a>
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
        self.request_handler.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.request_handler.send_header(
            "Content-type", f"text/html; charset={encoding}"
        )
        self.request_handler.send_header("Content-Length", str(length))
        self.request_handler.end_headers()
        self.request_handler.wfile.write(buf.read().encode())

    def _get_display_path(self):
        if self.path == "/":
            return "Toplevel"
        return html.escape(urllib.parse.unquote(self.path.strip("/")))


class RequestHandler(SimpleHTTPRequestHandler):
    """
    Handles http GET requests for the Server class in this module.
    """

    def __init__(self, *args, **kwargs):
        self.folder_browser_handler = FolderBrowserHandler(self)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """
        :return:
        """
        result = self.folder_browser_handler.do_GET()
        if result is False:
            super().do_GET()


# pylint: disable=too-few-public-methods
class Server:
    """
    Creates and starts an http server, allowing access to the current folder
    and its contents (including subfolders).
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
            self.log.error(f"shutdown: {ex}")
        try:
            self.thread.join(1.0)
        except Exception as ex:  # pylint: disable=broad-except
            result.append(ex)
            self.log.error(f"thread.join: {ex}")
        return result
