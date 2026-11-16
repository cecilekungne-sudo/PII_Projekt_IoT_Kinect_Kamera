import time
from pathlib import Path

import freenect
from PIL import Image

# Speicherort auf dem Raspberry Pi
data_dir = Path.home() / "pii_iot" / "data" / "rgb_frames"
data_dir.mkdir(parents=True, exist_ok=True)

print("Kinect-RGB-Aufnahme startet ...")

try:
    for i in range(1, 11):
        result = freenect.sync_get_video()

        if result is None:
            print(f"Bild {i}: kein Bild empfangen")
            continue

        rgb, timestamp = result
        datei = data_dir / f"frame_{i:03d}.png"

        Image.fromarray(rgb.copy()).save(datei)

        print(f"Bild {i}/10 gespeichert: {datei.name}")
        print(f"  Auflösung: {rgb.shape[1]} x {rgb.shape[0]}")
        time.sleep(1)

finally:
    freenect.sync_stop()
    print("Aufnahme beendet.")
