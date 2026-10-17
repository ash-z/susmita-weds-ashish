"""Minimal web UI: upload a manga PDF, get narrated clips back.

Run: python -m mangaclip.web.app   then open http://localhost:5000
"""

from __future__ import annotations

import os
import threading
import traceback
import uuid

from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from ..pipeline import Options, make_clips

DATA_DIR = os.environ.get("MANGACLIP_DATA", os.path.abspath("mangaclip-jobs"))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024
jobs: dict[str, dict] = {}


def _run(job_id: str, pdf: str, out_dir: str, opts: Options) -> None:
    job = jobs[job_id]

    def progress(msg: str) -> None:
        job["log"].append(msg)

    try:
        outs = make_clips(pdf, out_dir, opts, progress)
        job["clips"] = [os.path.basename(o) for o in outs]
        job["status"] = "done"
    except Exception as e:  # surface any failure to the UI
        traceback.print_exc()
        job["status"] = "error"
        job["error"] = str(e)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/jobs")
def create_job():
    f = request.files.get("pdf")
    if not f or not f.filename.lower().endswith(".pdf"):
        return jsonify(error="Please upload a .pdf file"), 400
    job_id = uuid.uuid4().hex[:12]
    out_dir = os.path.join(DATA_DIR, job_id)
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, secure_filename(f.filename) or "input.pdf")
    f.save(pdf)
    form = request.form
    opts = Options(
        num_clips=max(1, min(10, int(form.get("clips", 1)))),
        pages_per_clip=max(1, min(8, int(form.get("pages", 2)))),
        clip_seconds=max(15, min(180, int(form.get("seconds", 45)))),
        engine=form.get("engine", "auto"),
        language=form.get("language", "English")[:40],
        right_to_left=form.get("direction", "rtl") == "rtl",
        tts=form.get("tts", "edge"),
        voice=form.get("voice") or None,
        format=form.get("format", "vertical"),
        captions=form.get("captions") == "on",
        music=form.get("music") == "on",
    )
    jobs[job_id] = {"status": "running", "log": [], "clips": [], "error": None}
    threading.Thread(target=_run, args=(job_id, pdf, out_dir, opts), daemon=True).start()
    return jsonify(id=job_id)


@app.get("/jobs/<job_id>")
def job_status(job_id: str):
    job = jobs.get(job_id) or abort(404)
    return jsonify(job)


@app.get("/jobs/<job_id>/files/<path:name>")
def job_file(job_id: str, name: str):
    if job_id not in jobs:
        abort(404)
    return send_from_directory(os.path.join(DATA_DIR, job_id), name)


def main() -> None:
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))


if __name__ == "__main__":
    main()
