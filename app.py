from flask import Flask, Response, request
import cv2
import numpy as np
import threading
from threading import Timer
from datetime import datetime, date
import time
import queue
import sys
import os
from time import sleep
from waitress import serve
app = Flask(__name__)

from threading import Timer


class Repeat(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class VideoCapture:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
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
                # self.cap.release()
                # print("không phản hồi")
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
    frame_rate = 30
    prev = 0
    cam = "rtsp://" + camera_id
    cap = VideoCapture(cam)
    while True:
        time_elapsed = time.time() - prev
        frame = cap.read()
        # time.sleep(0.05)  # simulate time between events xóa bộ nhớ đệm
        if time_elapsed > 1.0 / frame_rate:
            prev = time.time()
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )  # concat frame one by one and show result


def setInterval(func, time):
    e = threading.Event()
    while not e.wait(time):
        func()


# using


def capture_video_camera(linkPath, fileName, recordTime):
    now = datetime.today().strftime("%Y-%m-%d")
    nowtime = str(datetime.today().strftime("%H:%M:%S")).replace(":", ".")
    path = "./resources/" + fileName
    if not os.path.exists(path):
        os.makedirs("./resources/" + fileName)
        print("Folder %s created!" % path)
    else:
        print("Folder %s already exists" % path)

    pathdate = "./resources/" + fileName + "/" + now
    if not os.path.exists(pathdate):
        os.makedirs("./resources/" + fileName + "/" + now)
        print("Folder %s created!" % pathdate)
    else:
        print("Folder %s already exists" % pathdate)
    # Mở webcam
    fps = 20
    cap = cv2.VideoCapture("rtsp://" + linkPath)
    # Đặt thông số cho video đầu ra
    size = (
        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    # cấu trúc lưu file ./resources/cameraname/date/cameraname + hours + minute + second.avi
    out = cv2.VideoWriter(
        pathdate + "/" + fileName + nowtime + ".avi",
        cv2.VideoWriter_fourcc("D", "I", "V", "X"),
        fps,
        size,
    )
    start_time = time.time()
    # and (time.time() - start_time) < recordTime - 1
    while cap.isOpened() and (time.time() - start_time) < recordTime - 1:
        # lưu video 5p01s mỗi lần
        ret, frame = cap.read()
        if not ret:
            break
        # Ghi khung hình vào tệp tin video
        cv2.resize(frame, (960, 540))
        out.write(frame)
        # Hiển thị khung hình
        # cv2.imshow("Webcam", frame)
        # Nhấn 'q' để thoát nếu dùng application
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    Timer(recordTime - 1, capture_video_camera(linkPath, fileName, recordTime)).start()
    # Giải phóng tài nguyên
    cap.release()
    out.release()
    cv2.destroyAllWindows()


@app.route("/capture_video", methods=["POST"])
def capture_video():
    "Lưu màn hình cần đường dẫn và tên camera"
    request_data = request.get_json()
    if request_data["PathLink"] != "" and request_data["FileName"] != "":
        Timer(
            300,
            capture_video_camera(
                request_data["PathLink"], request_data["FileName"], 300
            ),
        ).start()

        return "<h1>Đã lưu !!!</h1>"
    else:
        return "Không có kết nối"


@app.route("/video_feed_detail/<string:iddetail>/", methods=["GET"])
def video_feed_detail(iddetail):
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen_framesDetail(iddetail), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    return "This is Media Server"


if __name__ == "__main__":
    # context = ("dgss_vn_cert.pem", "dgss.pem")  # certificate and key files
    # threading.Thread(target = app.run( ssl_context=context, port=3006,)).start()
    #app.run(debug=True, port=8003, use_reloader=False)
    serve(app)
    #server = wsgiserver.WSGIServer(app)
    #server.start()
    # sys.exit()
