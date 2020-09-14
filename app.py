from flask import Flask, render_template, redirect, url_for, send_file, make_response

from file import get_file_entries, retrieve_file
from logger import apply_log_config, log_exception
from path import PathInfo

apply_log_config()
app = Flask(__name__)


@app.route("/")
def home():
    return redirect(url_for("get_file_list"))


@app.route("/error")
def error():
    raise Exception("For testing purpose")


@app.route("/list", defaults={"file_path": "/"})
@app.route("/list/<path:file_path>")
def get_file_list(file_path: str):
    try:
        file_entries = get_file_entries(file_path)
        return render_template("file_list.html", current_path=PathInfo(file_path), file_entries=file_entries)
    except FileNotFoundError:
        log_exception()
        return "Directory not found.", 404
    except NotADirectoryError:
        log_exception()
        return "Path is not a directory.", 406
    except Exception as ex:
        log_exception(repr(ex))
        return f"Error occurred when viewing the directory. ({ex})", 500


@app.route("/download/<path:file_path>")
def download(file_path: str):
    try:
        file_stream = retrieve_file(PathInfo(file_path))
    except FileNotFoundError:
        log_exception()
        return "Path not found.", 404
    except IsADirectoryError:
        log_exception()
        return "Path to download the file is a directory.", 406

    resp = make_response(send_file(file_stream.stream, as_attachment=True, attachment_filename=file_stream.file_name))
    resp.headers["Content-Length"] = file_stream.file_size

    return resp


if __name__ == "__main__":
    app.run(port=8787)
