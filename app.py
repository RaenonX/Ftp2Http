from flask import Flask, render_template, redirect, url_for, send_file

from ftp import get_file_entries, retrieve_file
from path import PathInfo

app = Flask(__name__)


@app.route("/")
def home():
    return redirect(url_for("get_file_list"))


@app.route("/list", defaults={"ftp_path": "/"})
@app.route("/list/<path:ftp_path>")
def get_file_list(ftp_path: str):
    return render_template("file_list.html",
                           current_path=PathInfo(ftp_path), file_entries=get_file_entries(ftp_path))


@app.route("/download/<path:ftp_path>")
def download(ftp_path: str):
    file_stream = retrieve_file(ftp_path)

    if not file_stream:
        return "Error downloading the file. Check if the file exists. Also make sure that it is NOT a directory."

    file_name = ftp_path.split(ftp_path)[-1]
    return send_file(file_stream, as_attachment=True, attachment_filename=file_name)


if __name__ == "__main__":
    app.run()