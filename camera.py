import cv2
import keyboard


class Camera:
    def __init__(self, source=0, width=0, height=0):
        try:
            self.camera = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            if width != 0:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height != 0:
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        except:
            raise Exception("Failed to initialize camera")

    # retrieve current frame from camera
    def get_frame(self, crop=True):
        try:
            ret, frame = self.camera.read()
            if crop:
                frame = frame[290:330, 620:660]
            return frame
        except:
            raise Exception("Failed to retrieve frame from camera")

    # save current frame from camera
    def save_frame(self, file_name):
        try:
            cv2.imwrite(file_name, self.get_frame())
        except:
            raise Exception("Frame not available")

    # start live stream of camera in new window
    def start_stream(self, end_key):
        while not keyboard.is_pressed(end_key):
            try:
                cv2.imshow('stream', self.get_frame())
                cv2.waitKey(1)
            except:
                raise Exception("Failed to start camera stream")
