import numpy as np
import time
import cv2
from concurrent import futures
import queue
import threading

import grpc
from google.protobuf.empty_pb2 import Empty

import image_interface_pb2
import image_interface_pb2_grpc

PORT = 4321
SERVER = "127.0.0.1"
SERVER_ACCEPT = "0.0.0.0"


class ImageReciever(image_interface_pb2_grpc.ImageRecieverServicer):
    def __init__(self, display):
        image_interface_pb2_grpc.ImageRecieverServicer.__init__(self)

        self.display = display

    def SayHello(self, request, context):
        return image_interface_pb2.HelloReply(message=f"Hello, {request.name}!")

    def SendImage(self, request, context):
        rgb_im = np.frombuffer(request.rgb_img, np.uint8)
        rgb_im = rgb_im.reshape((request.rgb_height, request.rgb_width, 3))
        rgb_im = cv2.cvtColor(rgb_im, cv2.COLOR_RGB2BGR)

        depth_im = np.frombuffer(request.depth_img, np.uint16)
        depth_im = depth_im.reshape((request.depth_height, request.depth_width))

        self.display.show_frame((depth_im, rgb_im))

        print(f"Image Recieved at ts {request.ts}")
        return Empty()


class ImageDisplay(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.queue = queue.Queue()
        self.cond = threading.Condition()
        self.done = False

    def kill(self):
        self.done = True
        with self.cond:
            self.cond.notify()

    def show_frame(self, frame):
        self.queue.put(frame)
        with self.cond:
            self.cond.notify()

    def run(self):
        cv2.namedWindow("Depth")
        cv2.namedWindow("Video")

        while not self.done:
            while self.queue.empty():
                with self.cond:
                    self.cond.wait(timeout=100)

                if self.done:
                    return

            frame = self.queue.get()

            print(frame)

            depth_conv = (frame[0] // 8).astype(np.uint8)

            cv2.imshow("Depth", depth_conv)
            cv2.imshow("Video", frame[1])
            cv2.waitKey(1)

        cv2.destroyWindow("Depth")
        cv2.destroyWindow("Video")
        cv2.waitKey(1)


def main():
    tpe = futures.ThreadPoolExecutor(max_workers=10)
    server = grpc.server(tpe)

    display_thread = ImageDisplay()
    display_thread.start()

    image_interface_pb2_grpc.add_ImageRecieverServicer_to_server(
        ImageReciever(display_thread), server
    )

    server.add_insecure_port(SERVER_ACCEPT + ":" + str(PORT))
    server.start()

    print("Server startet")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass

    print("wait for Server...")
    server.stop(grace=1)
    display_thread.kill()
    print("wait for ImageDisplay...")
    display_thread.join()

    print("All closed")


if __name__ == "__main__":
    main()
