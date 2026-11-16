import freenect
import frame_convert2

def display_rgb(dev, data, timestamp):
    image = frame_convert2.video_cv(data)

    print(
        "RGB empfangen:",
        image.shape,
        "Zeitstempel:",
        timestamp
    )

print("Starte Kinect RGB-Test...")

try:
    freenect.runloop(video=display_rgb)

except KeyboardInterrupt:
    print("RGB-Test beendet.")
