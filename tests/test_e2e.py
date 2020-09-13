from flask import url_for


def test_root_redirection(client):
    resp = client.head("/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://localhost" + url_for("get_file_list")

    resp = client.head("/", follow_redirects=True)
    assert resp.status_code == 200


def test_view_root(client):
    resp = client.head(url_for("get_file_list"))
    assert resp.status_code == 200


def test_view_file(client):
    resp = client.head(url_for("get_file_list", file_path="C.mkv"))
    assert resp.status_code == 406


def test_view_file_in_directory(client):
    resp = client.head(url_for("get_file_list", file_path="A/B.mp4"))
    assert resp.status_code == 406


def test_view_directory(client):
    resp = client.head(url_for("get_file_list", file_path="A"))
    assert resp.status_code == 200


def test_view_not_existed_directory(client):
    resp = client.head(url_for("get_file_list", file_path="TestTestTestTestTestTestTestTestTest"))
    assert resp.status_code == 404


def test_download_file(client):
    resp = client.head(url_for("download", file_path="C.mkv"))
    assert resp.status_code == 200


def test_download_not_existed_file(client):
    resp = client.head(url_for("download", file_path="TestTestTestTestTestTest.mkv"))
    assert resp.status_code == 404


def test_download_file_in_directory(client):
    resp = client.head(url_for("download", file_path="A/B.mp4"))
    assert resp.status_code == 200


def test_download_directory(client):
    resp = client.head(url_for("download", file_path="A"))
    assert resp.status_code == 406
