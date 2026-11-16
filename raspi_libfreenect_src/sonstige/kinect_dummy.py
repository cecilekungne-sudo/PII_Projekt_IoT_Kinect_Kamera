import sys
import time
import numpy as np
import cv2
import os
from datetime import datetime

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from .show_record import load_frames_from_folder

from communication import image_interface_pb2
from communication import image_interface_pb2_grpc

PORT = 4321
SERVER = "127.0.0.1"

def kinect_img_from_frame(frame):
    depth_im = frame[0]
    rgb_im = frame[1]

    color_data = rgb_im.tobytes()
    h_color = rgb_im.shape[0]
    w_color = rgb_im.shape[1]

    depth_data = depth_im.tobytes()
    h_depth = depth_im.shape[0]
    w_depth = depth_im.shape[1]

    ts = Timestamp()
    ts.FromDatetime(datetime.now())

    k_im = image_interface_pb2.KinectImage(
        ts=ts,
        rgb_img=color_data,
        rgb_height=h_color,
        rgb_width=w_color,
        depth_img=depth_data,
        depth_height=h_depth,
        depth_width=w_depth,
    )

    return k_im

def kinect_dummy(rec_folder, server_address, server_port, fps=20):
    if type(server_port) is str:
        server_port = int(server_port)

    if type(fps) is str:
        fps = int(fps)

    frames = load_frames_from_folder(rec_folder)

    with grpc.insecure_channel(f"{server_address}:{server_port}") as channel:
        stub = image_interface_pb2_grpc.ImageRecieverStub(channel)

        response = stub.SayHello(image_interface_pb2.HelloRequest(name="you"))
        print("Greeter client received: " + response.message)

        for f in frames:
            k_im = kinect_img_from_frame(f)
            _ = stub.SendImage(k_im)

            time.sleep(1 / fps)
