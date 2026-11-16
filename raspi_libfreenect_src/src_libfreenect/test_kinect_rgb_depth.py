import freenect
import frame_convert2
import cv2
import os

# Ordner für die Testbilder
os.makedirs("kinect_test", exist_ok=True)

rgb_received = False
depth_received = False

# RGB-Kamera
def display_rgb(dev, data, timestamp):
    global rgb_received

    image = frame_convert2.video_cv(data)

    if not rgb_received:
        print("RGB empfangen!")
        print("RGB Bildgröße:", image.shape)

        cv2.imwrite("kinect_test/rgb_test.jpg", image)
        print("RGB-Bild gespeichert.")

        rgb_received = True


# Depth-Kamera
def display_depth(dev, data, timestamp):
    global depth_received

    image = frame_convert2.pretty_depth_cv(data)

    if not depth_received:
        print("DEPTH empfangen!")
        print("Depth Bildgröße:", image.shape)

        cv2.imwrite("kinect_test/depth_test.jpg", image)
        print("Depth-Bild gespeichert.")

        depth_received = True


# Beide Datenströme starten
print("================================")
print("KINECT RGB + DEPTH TEST")
print("================================")

try:
    freenect.runloop(
        video=display_rgb,
        depth=display_depth
    )

except KeyboardInterrupt:
    print("\nTest manuell beendet.")

except Exception as e:
    print("Fehler:", e)

finally:
    print("RGB empfangen:", rgb_received)
    print("Depth empfangen:", depth_received)
    print("Test beendet.")
