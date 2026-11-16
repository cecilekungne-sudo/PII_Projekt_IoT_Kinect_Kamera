import freenect
import cv2
import time
import sys
import os
import numpy as np


def main():
    if len(sys.argv) != 2:
        print("Usage: record.py [FOLDER]")
        return

    rec_folder = sys.argv[1]

    if not os.path.isdir(rec_folder):
        print("No valid Folder given")
        return

    frames = []

    i = 0

    print("Recording...")
    while 1:
        try:
            depth_frame = freenect.sync_get_depth()[0]
            video_frame = freenect.sync_get_video()[0]

            frames.append((depth_frame.copy(), video_frame.copy()))

            print(f"\rRecording Frame {i}", end="")

            i += 1
        except KeyboardInterrupt:
            break

    print("\n\nSave Stream...")
    for i, f in enumerate(frames):
        np.save(f"{rec_folder}/f{i}_depth.npy", f[0])
        np.save(f"{rec_folder}/f{i}_rgb.npy", f[1])

        print(f"\rSave Frame {i}", end="")


if __name__ == "__main__":
    main()
