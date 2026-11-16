
import freenect
import frame_convert2
import cv2
import threading
import time

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# Aktuelle Bilder speichern
latest_frames = {
    "rgb": None,
    "depth": None
}

frame_lock = threading.Lock()


# RGB-Bild erfassen
def display_rgb(dev, data, timestamp):
    try:
        image = frame_convert2.video_cv(data)
        success, encoded = cv2.imencode(".jpg", image)

        if success:
            with frame_lock:
                latest_frames["rgb"] = encoded.tobytes()

    except Exception as e:
        print("RGB-Fehler:", e)


# Depth-Bild erfassen
def display_depth(dev, data, timestamp):
    try:
        image = frame_convert2.pretty_depth_cv(data)
        success, encoded = cv2.imencode(".jpg", image)

        if success:
            with frame_lock:
                latest_frames["depth"] = encoded.tobytes()

    except Exception as e:
        print("Depth-Fehler:", e)


# Browser-Seite
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kinect RGB + Depth Live</title>

    <style>
        body {
            background: #222;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
        }

        h1 {
            margin-bottom: 40px;
        }

        .container {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 25px;
            flex-wrap: wrap;
        }

        .camera {
            width: 48%;
            min-width: 300px;
        }

        img {
            width: 100%;
            border: 3px solid white;
        }

        h2 {
            margin-bottom: 15px;
        }
    </style>
</head>

<body>

    <h1>Kinect Live: RGB + Depth</h1>

    <div class="container">

        <div class="camera">
            <h2>RGB Kamera</h2>
            <img src="/rgb">
        </div>

        <div class="camera">
            <h2>Depth Kamera</h2>
            <img src="/depth">
        </div>

    </div>

</body>
</html>
"""


# HTTP-Server
class KinectHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
            return

        if self.path not in ["/rgb", "/depth"]:
            self.send_error(404)
            return

        frame_type = self.path[1:]

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=frame"
        )
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        try:
            while True:

                with frame_lock:
                    frame = latest_frames[frame_type]

                if frame is not None:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(
                        b"Content-Type: image/jpeg\r\n\r\n"
                    )
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()

                time.sleep(0.05)

        except (BrokenPipeError, ConnectionResetError):
            print(frame_type, "Browser-Verbindung beendet.")

    def log_message(self, format, *args):
        pass


# Server starten
server = ThreadingHTTPServer(
    ("0.0.0.0", 5000),
    KinectHandler
)

server.daemon_threads = True

threading.Thread(
    target=server.serve_forever,
    daemon=True
).start()


print("================================")
print("KINECT RGB + DEPTH LIVE SERVER")
print("================================")
print("RGB und Depth werden gestartet.")
print("Browser-Adresse: http://RASPBERRY_PI_IP:5000")


try:
    freenect.runloop(
        video=display_rgb,
        depth=display_depth
    )

except KeyboardInterrupt:
    print("\nLive-Test beendet.")

except Exception as e:
    print("Kinect-Fehler:", e)

finally:
    server.shutdown()
    server.server_close()
    freenect.sync_stop()
