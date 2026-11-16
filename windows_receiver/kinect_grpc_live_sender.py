import time
import threading
from datetime import datetime, timezone

import numpy as np
import freenect
import grpc

import image_interface_pb2
import image_interface_pb2_grpc


# IP-Adresse deines Windows-Laptops
SERVER_ADDRESS = "141.19.179.147"
SERVER_PORT = 4321

FPS = 10

latest_rgb = None
latest_depth = None
frame_lock = threading.Lock()
stop_event = threading.Event()


def video_callback(dev, data, timestamp):
    global latest_rgb
    with frame_lock:
        latest_rgb = np.ascontiguousarray(data).copy()


def depth_callback(dev, data, timestamp):
    global latest_depth
    with frame_lock:
        latest_depth = np.ascontiguousarray(data).copy()


def send_images(stub):
    print("Warte auf RGB- und Depth-Bilder ...")

    while not stop_event.is_set():

        with frame_lock:
            rgb = None if latest_rgb is None else latest_rgb.copy()
            depth = None if latest_depth is None else latest_depth.copy()

        if rgb is not None and depth is not None:

            ts = image_interface_pb2.Timestamp() if hasattr(
                image_interface_pb2, "Timestamp"
            ) else None

            from google.protobuf.timestamp_pb2 import Timestamp
            ts = Timestamp()
            ts.FromDatetime(datetime.now(timezone.utc))

            message = image_interface_pb2.KinectImage(
                ts=ts,
                rgb_img=rgb.tobytes(),
                rgb_height=rgb.shape[0],
                rgb_width=rgb.shape[1],
                depth_img=depth.astype(np.uint16, copy=False).tobytes(),
                depth_height=depth.shape[0],
                depth_width=depth.shape[1],
            )

            try:
                stub.SendImage(message, timeout=5)
                print(
                    f"Gesendet: RGB {rgb.shape} | "
                    f"Depth {depth.shape}"
                )
            except grpc.RpcError as error:
                print("gRPC-Fehler:", error)
                time.sleep(2)

        time.sleep(1 / FPS)


def main():
    address = f"{SERVER_ADDRESS}:{SERVER_PORT}"
    print("Verbinde mit Windows-Empfänger:", address)

    with grpc.insecure_channel(address) as channel:
        grpc.channel_ready_future(channel).result(timeout=10)

        stub = image_interface_pb2_grpc.ImageRecieverStub(channel)

        response = stub.SayHello(
            image_interface_pb2.HelloRequest(name="Raspberry Pi 4")
        )
        print("Windows-Empfänger:", response.message)

        sender_thread = threading.Thread(
            target=send_images,
            args=(stub,),
            daemon=True
        )
        sender_thread.start()

        print("Kinect-Livestream gestartet. Abbruch mit STRG+C.")

        try:
            freenect.runloop(
                video=video_callback,
                depth=depth_callback
            )
        except KeyboardInterrupt:
            print("\nLivestream wird beendet.")
        finally:
            stop_event.set()
            sender_thread.join(timeout=3)


if __name__ == "__main__":
    main()
