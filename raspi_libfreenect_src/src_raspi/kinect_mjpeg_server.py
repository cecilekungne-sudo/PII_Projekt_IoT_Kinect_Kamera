from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO

import freenect
from PIL import Image

class KinectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/video_feed"):
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=frame"
        )
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        print("Windows hat den Live-Stream geöffnet.", flush=True)

        try:
            while True:
                result = freenect.sync_get_video()
                if result is None:
                    continue

                rgb, _ = result
                buffer = BytesIO()
                Image.fromarray(rgb.copy()).save(buffer, format="JPEG")

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                self.wfile.write(buffer.getvalue())
                self.wfile.write(b"\r\n")
                self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError):
            print("Live-Stream beendet.", flush=True)
        finally:
            freenect.sync_stop()

    def log_message(self, format, *args):
        pass

print("Kinect-Live-Server startet auf Port 5000 ...", flush=True)
HTTPServer(("0.0.0.0", 5000), KinectHandler).serve_forever()
