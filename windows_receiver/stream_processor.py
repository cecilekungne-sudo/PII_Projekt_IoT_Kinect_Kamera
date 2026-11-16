import numpy as np
import time
import cv2
from concurrent import futures
import queue
import threading

import grpc
from google.protobuf.empty_pb2 import Empty

from communication import image_interface_pb2
from communication import image_interface_pb2_grpc

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




# Camera information based on the Kinect v1 hardware
CameraParams = {
    "cx": 322.515987,
    "cy": 259.055966,
    "fx": 521.179233,
    "fy": 493.033034,
    "k1": 0.05858325,
    "k2": 0.03856792,
    "k3": 0.0,
    "p1": 0.0,
    "p2": 0.0,
}


def depthToPointCloudPos(x_d, y_d, z, scale=1000):
    # This runs in Python slowly as it is required to be called from within a loop, but it is a more intuitive example than it's vertorized alternative (Purly for example)
    # calculate the real-world xyz vertex coordinate from the raw depth data (one vertex at a time).
    x = (x_d - CameraParams['cx']) * z / CameraParams['fx']
    y = (y_d - CameraParams['cy']) * z / CameraParams['fy']

    return x / scale, y / scale, z / scale

CameraPosition = {
    "x": 0, # actual position in meters of kinect sensor relative to the viewport's center.
    "y": 0, # actual position in meters of kinect sensor relative to the viewport's center.
    "z": 1.7, # height in meters of actual kinect sensor from the floor.
    "roll": 0, # angle in degrees of sensor's roll (used for INU input - trig function for this is commented out by default).
    "azimuth": 0, # sensor's yaw angle in degrees.
    "elevation": -5, # sensor's pitch angle in degrees.
}

def applyCameraOrientation(pt):
    # Kinect Sensor Orientation Compensation
    # This runs slowly in Python as it is required to be called within a loop, but it is a more intuitive example than it's vertorized alternative (Purly for example)
    # use trig to rotate a vertex around a gimbal.
    def rotatePoints(ax1, ax2, deg):
        # math to rotate vertexes around a center point on a plane.
        hyp = np.sqrt(pt[ax1] ** 2 + pt[ax2] ** 2) # Get the length of the hypotenuse of the real-world coordinate from center of rotation, this is the radius!
        d_tan = np.arctan2(pt[ax2], pt[ax1]) # Calculate the vertexes current angle (returns radians that go from -180 to 180)

        cur_angle = np.degrees(d_tan) % 360 # Convert radians to degrees and use modulo to adjust range from 0 to 360.
        new_angle = np.radians((cur_angle + deg) % 360) # The new angle (in radians) of the vertexes after being rotated by the value of deg.

        pt[ax1] = hyp * np.cos(new_angle) # Calculate the rotated coordinate for this axis.
        pt[ax2] = hyp * np.sin(new_angle) # Calculate the rotated coordinate for this axis.

    #rotatePoints(0, 2, CameraPosition['roll']) #rotate on the Y&Z plane # Disabled because most tripods don't roll. If an Inertial Nav Unit is available this could be used)
    rotatePoints(1, 2, CameraPosition['elevation']) #rotate on the X&Z plane
    rotatePoints(0, 1, CameraPosition['azimuth']) #rotate on the X&Y plane

    # Apply offsets for height and linear position of the sensor (from viewport's center)
    pt[:] += np.float_([CameraPosition['x'], CameraPosition['y'], CameraPosition['z']])

    return pt
