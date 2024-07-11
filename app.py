
from flask import Flask, render_template, Response
import numpy as np
import cv2
import pickle
import PIL as Image
import threading
import time
import queue
import sys
import requests
from waitress import serve

# from werkzeug.middleware.profiler import ProfilerMiddleware


app = Flask(__name__)
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir="./profile")


class VideoCapture:

    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        print("fps:" + str(self.cap.get(cv2.CAP_PROP_FPS)))
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()  # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()


def gen_framesDetail(camera_id):
    cam = "rtsp://" + camera_id
    cap = VideoCapture(cam)

    while True:
        time.sleep(0.1)  # simulate time between events
        frame = cap.read()
        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )  # concat frame one by one and show result


@app.route("/")
def home():
    return "Hello, This is the Flask App in IIS Server."


@app.route("/video_feed_detail/<string:iddetail>/", methods=["GET"])
def video_feed_detail(iddetail):
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen_framesDetail(iddetail), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    # context = ("dgss_vn_cert.pem", "dgss.pem")  # certificate and key files
    # app.run(debug=True, ssl_context=context, port=3006)
    app.run(threaded=True)
    sys.exit()
