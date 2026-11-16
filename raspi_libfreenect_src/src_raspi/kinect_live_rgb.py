import time
from pathlib import Path

import freenect
from PIL import Image

# Bilder werden auf dem Raspberry Pi gespeichert.
data_dir = Path.home() / "pii_iot" / "data" / "live_rgb"
data_dir.mkdir(parents=True, exist_ok=True)

duration_seconds = 10
interval_seconds = 0.5
start_time = time.monotonic()
next_save = start_time
frame_number = 0

print("Live-RGB-Aufnahme startet ...", flush=True)

try:
    while time.monotonic() - start_time < duration_seconds:
        result = freenect.sync_get_video()

        if result is None:
            print("Kein RGB-Bild empfangen.", flush=True)
            continue

        rgb, timestamp = result
        now = time.monotonic()

        if now >= next_save:
            frame_number += 1
            filename = data_dir / f"frame_{frame_number:03d}.png"
            Image.fromarray(rgb.copy()).save(filename)

            print(
                f"Bild {frame_number} gespeichert: {filename.name}",
                flush=True
            )
            next_save = now + interval_seconds

finally:
    freenect.sync_stop()
    print(f"Aufnahme beendet. Gespeicherte Bilder: {frame_number}", flush=True)
