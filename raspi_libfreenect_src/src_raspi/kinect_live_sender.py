
import time
from datetime import datetime

import cv2
import freenect
import grpc
import numpy as np
from google.protobuf.timestamp_pb2 import Timestamp

import image_interface_pb2
import image_interface_pb2_grpc

# Windows-Empfänger
SERVER = "141.19.176.39"
PORT = 4321


def main():
    # Verbindung zum Windows-PC herstellen
    with grpc.insecure_channel(f"{SERVER}:{PORT}") as channel:
        stub = image_interface_pb2_grpc.ImageRecieverStub(channel)

        # Verbindung testen
        response = stub.SayHello(
            image_interface_pb2.HelloRequest(name="Kinect Raspberry Pi")
        )
        print("Windows-Empfänger:", response.message)

        print("Live-Kinect-Übertragung gestartet. Abbruch mit Strg+C.")

        try:
            while True:
                # Live-Tiefenbild und RGB-Bild von der Kinect lesen
                depth, _ = freenect.sync_get_depth()
                rgb, _ = freenect.sync_get_video()

                # Prüfen, ob beide Bilder vorhanden sind
                if depth is None or rgb is None:
                    print("Kein Kinect-Bild erhalten.")
                    time.sleep(0.1)
                    continue

                # Zeitstempel erstellen
                ts = Timestamp()
                ts.FromDatetime(datetime.now())

                # Bilder und Bildgrößen in die gRPC-Nachricht packen
                message = image_interface_pb2.KinectImage(
                    ts=ts,
                    rgb_img=rgb.tobytes(),
                    rgb_height=rgb.shape[0],
                    rgb_width=rgb.shape[1],
                    depth_img=depth.astype(np.uint16).tobytes(),
                    depth_height=depth.shape[0],
                    depth_width=depth.shape[1],
                )

                # Live-Bilder an Windows senden
                stub.SendImage(message)
                print("RGB und Tiefenbild gesendet")

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nÜbertragung beendet.")
        finally:
            # Kinect-Verbindung sauber schließen
            freenect.sync_stop()


if __name__ == "__main__":
    main()
