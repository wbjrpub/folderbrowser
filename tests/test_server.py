"""
Test Server class
"""

import logging
import os
from time import sleep
import requests

from folderbrowser import Server


def setup_module(module):
    log = logging.getLogger("test")
    module.server = Server(log=log, port=12345)
    module.orig_cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    sleep(0.2)


def teardown_module(module):
    os.chdir(module.orig_cwd)
    if module.server:
        module.server.stop()
        module.server = None


def test_server_toplevel():
    resp = requests.get("http://127.0.0.1:12345/")
    print(resp)
    print(resp.text)
    assert resp.status_code == 200
    print(resp)
    print(resp.text)
    assert resp.status_code == 200
    assert "<title>Folder Listing for Toplevel</title>" in resp.text
    assert """Parent Folder""" not in resp.text
    assert """<td colspan='3'><a href="fixtures/">fixtures/</a></td>""" in resp.text


def test_server_file1000():
    resp = requests.get("http://127.0.0.1:12345/fixtures/file1000.txt")
    print(resp)
    print(resp.text)
    assert resp.status_code == 200
    assert "line0001" in resp.text
    assert "line1000" in resp.text
    assert "line1001" not in resp.text


def test_server_file1000_parts():
    for action, count, in (
        ("head", 10),
        ("head", 20),
        ("tail", 10),
        ("tail", 20),
        ("head", 10000),
        ("tail", 10000),
    ):
        resp = requests.get(
            f"http://127.0.0.1:12345/fixtures/file1000.txt?{action}={count}"
        )
        print(resp)
        print(resp.text)
        assert resp.status_code == 200
        num_lines = min(1000, count)
        if action == "head":
            opposite = "tail"
            assert f"line0001" in resp.text
            assert f"line{num_lines:04d}" in resp.text
            assert f"line{num_lines+1:04d}" not in resp.text
        else:
            opposite = "head"
            assert f"line1000" in resp.text
            assert f"line{1001 - num_lines:04d}" in resp.text
            assert f"line{1000-num_lines:04d}" not in resp.text
        assert f"""<h2>File fixtures/file1000.txt</h2>""" in resp.text
        assert (
            f"""<a href="file1000.txt?{action}={count//2}">[Less: {action} -n {count//2}]</a>"""
            in resp.text
        )
        assert (
            f"""<a href="file1000.txt?{action}={count}">[Redo: {action} -n {count}]</a>"""
            in resp.text
        )
        assert (
            f"""<a href="file1000.txt?{action}={count*2}">[More: {action} -n {count*2}]</a>"""
            in resp.text
        )
        assert (
            f"""<a href="file1000.txt?{opposite}={count}">[Opposite: {opposite} -n {count}]</a>"""
            in resp.text
        )
        assert f"""<a href="file1000.txt">[Whole File]</a>""" in resp.text
        assert f"""<a href=".">[Folder]</a></p>""" in resp.text


def test_server_fixtures_folder():
    resp = requests.get("http://127.0.0.1:12345/fixtures")
    _check_fixtures_folder_response(resp)


def test_server_fixtures_folder_ending_with_slash():
    resp = requests.get("http://127.0.0.1:12345/fixtures/")
    _check_fixtures_folder_response(resp)


def _check_fixtures_folder_response(resp):
    print(resp)
    print(resp.text)
    assert resp.status_code == 200
    assert "<title>Folder Listing for fixtures</title>" in resp.text
    assert (
        """<tr><td>&nbsp;</td><td colspan=3><a href="..">[Parent Folder]</a></td></tr>"""
        in resp.text
    )
    assert """<td><a href="file1000.txt">file1000.txt</a></td>""" in resp.text
    assert (
        """<td><a href="file1000.txt?head=40" title="First 40 lines">[head]</a></td>"""
        in resp.text
    )
    assert (
        """<td><a href="file1000.txt?tail=40" title="Last 40 lines">[tail]</a></td>"""
        in resp.text
    )


def test_server_dot_dot():
    for prefix in (
        "",
        "./",
        "fixtures/",
        "fixtures/dummy/",
    ):
        for path in (
            "..",
            "/..",
            "../",
            "/../",
        ):
            for suffix1 in (
                "",
                "?",
                "#",
            ):
                for suffix2 in (
                    "..",
                    "/..",
                    "../",
                    "/../",
                ):
                    sub_path = f"{prefix}{path}{suffix1}{suffix2}"
                    if sub_path != "" and "...." not in sub_path:
                        resp = requests.get(f"http://127.0.0.1:12345/{sub_path}")
                        _check_bad_path_response(resp)


def _check_bad_path_response(resp):
    print(resp)
    print(resp.text)
    assert resp.status_code == 400
    assert "Bad path: .. not allowed" in resp.text


def test_server_non_existing_file():
    resp = requests.get("http://127.0.0.1:12345/fixtures/non_existing_file.txt")
    print(resp)
    print(resp.text)
    assert resp.status_code == 404
    assert "File not found" in resp.reason
    assert "File not found" in resp.text
    assert "Nothing matches the given URI" in resp.text
