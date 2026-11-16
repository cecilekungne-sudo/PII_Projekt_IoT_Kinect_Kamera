
import time
from concurrent import futures

import cv2
import grpc
import numpy as np
from google.protobuf.empty_pb2 import Empty

import image_interface_pb2
import image_interface_pb2_grpc


PORT = 4321


class ImageReceiver(image_interface_pb2_grpc.ImageRecieverServicer):
    def SayHello(self, request, context):
        print(f"Verbindungstest von: {request.name}")
        return image_interface_pb2.HelloReply(
            message=f"Hello, {request.name}!"
        )

    def SendImage(self, request, context):
        try:
            # RGB-Bild aus den empfangenen Bytes rekonstruieren
            rgb = np.frombuffer(request.rgb_img, dtype=np.uint8)
            rgb = rgb.reshape(
                (request.rgb_height, request.rgb_width, 3)
            )
            video = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            # Tiefenbild aus den empfangenen Bytes rekonstruieren
            depth = np.frombuffer(
                request.depth_img, dtype=np.uint16
            )
            depth = depth.reshape(
                (request.depth_height, request.depth_width)
            )

            # Tiefe für die Anzeige auf 8 Bit skalieren
            depth_display = np.clip(depth / 8, 0, 255).astype(np.uint8)

            cv2.imshow("Kinect RGB - Windows", video)
            cv2.imshow("Kinect Depth - Windows", depth_display)
            cv2.waitKey(1)

            print(
                f"Bild empfangen: RGB {rgb.shape}, "
                f"Depth {depth.shape}, Zeitstempel: {request.ts}"
            )

            return Empty()

        except Exception as error:
            print("Fehler beim Verarbeiten des Bildes:", error)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(error))
            return Empty()


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    image_interface_pb2_grpc.add_ImageRecieverServicer_to_server(
        ImageReceiver(), server
    )

    # Auf allen Netzwerkschnittstellen von Windows lauschen
    server.add_insecure_port(f"0.0.0.0:{PORT}")
    server.start()

    print(f"Windows-Empfänger läuft auf Port {PORT}.")
    print("Beenden mit Strg+C.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Empfänger wird beendet.")
    finally:
        server.stop(grace=1)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
