# import the necessary packages
import time

import keyboard as keyboard
import numpy as np
import cv2
import DobotDllType as dType
import math
from PIL import Image
import pickle
import random
import yaml

with open('config.yaml', 'r') as f:
    config_file = yaml.safe_load(f)


class Ball:
    def __init__(self, virtual_x, virtual_y, calibration_variables, image):
        self.virtual_x = virtual_x
        self.virtual_y = virtual_y
        self.image = image
        self.calibration_variables = calibration_variables
        self.real_x, self.real_y = self.get_real_coord()
        self.color_rgb = (1,1,1) #self.get_color_rgb()

    def get_real_coord(self):
        ratio = self.calibration_variables['distance_real'] / self.calibration_variables['distance_virtual']
        zero_pos_real = self.calibration_variables['zero_pos_real']
        zero_pos_virtual = self.calibration_variables['zero_pos_virtual']

        virtual_delta_x = self.virtual_x - zero_pos_virtual['x']
        virtual_delta_y = self.virtual_y - zero_pos_virtual['y']

        real_x = zero_pos_real['x'] + (ratio * virtual_delta_y)
        real_y = zero_pos_real['y'] + (ratio * virtual_delta_x)

        return real_x, real_y

    def get_color_rgb(self):
        image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        r, g, b = image[self.virtual_y][self.virtual_x]
        return r, g, b


class Camera:
    def __init__(self):
        pass

    camera = None

    def start(self, source=0, width=0, height=0):
        try:
            self.camera = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            # self.camera.set(cv2.CAP_PROP_EXPOSURE, -4)
            # width = 1024
            # height = 768
            if width != 0:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height != 0:
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        except:
            raise Exception("Failed to start camera")

    def get_frame(self):
        if self.camera is not None:
            ret, frame = self.camera.read()
            return frame
        else:
            raise Exception("First start camera with start() method")

    def save_frame(self, file_name):
        try:
            cv2.imwrite(f'{file_name}', self.get_frame())
        except:
            raise Exception("Frame not available")

    def start_stream(self, end_key):
        while not keyboard.is_pressed(f'{end_key}'):
            try:
                cv2.imshow('stream', self.get_frame())
                cv2.waitKey(1)
            except:
                raise Exception("Frame not available")


class Dobot:
    def __init__(self):
        pass

    api = dType.load()

    def connect(self, port, baudrate=115200):
        try:
            dType.ConnectDobot(self.api, f'{port}', baudrate)
        except:
            raise Exception("Failed to connect to Dobot Magician")

    def set_home_params(self, x, y, z, r, is_queued):
        dType.SetHOMEParams(self.api, x, y, z, r, isQueued=is_queued)

    def set_home_cmd(self, is_queued):
        dType.SetHOMECmd(self.api, temp=0, isQueued=is_queued)

    def set_end_effector_type(self, end_effector, is_queued):
        dType.SetEndEffectorType(self.api, endType=end_effector, isQueued=is_queued)

    def set_end_effector_suction_cup(self, enable_control, state, is_queued):
        dType.SetEndEffectorSuctionCup(self.api, enable_control, state, isQueued=is_queued)

    def set_ptp_cmd(self, ptp_mode, x, y, z, r, is_queued):
        dType.SetPTPCmd(self.api, ptp_mode, x, y, z, r, isQueued=is_queued)


# ----- SETUP -----

state = 0

color_tolerance = config_file['calibration']['color_tolerance']

# create object for camera
camera = Camera()
# create object for robot arm
dobot = Dobot()


# ----- END SETUP -----


def find_circles(image, calibration_variables, color_variables):
    found_circles_list = []
    output = image.copy()
    gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 15, param1=50, param2=30, minRadius=55, maxRadius=0)

    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            cv2.circle(output, (x, y), r, (0, 255, 0), 2)
            cv2.circle(output, (x, y), 2, (222, 255, 56), 2)

            # dynamically istantiate objects
            found_circles_list.append(Ball(x, y, calibration_variables, image))

    if state == -1:
        cv2.circle(output, (150, 100), 5, (0, 255, 0), 2)
        cv2.circle(output, (674, 100), 5, (0, 255, 0), 2)

        cv2.imshow("output", output)
        cv2.waitKey(1)
    print(found_circles_list)
    return found_circles_list


def rgb_to_name(rgb_color, color_variables):
    global color_tolerance
    for predefined_color in list(color_variables.values()):
        if abs(predefined_color["r"] - rgb_color[0]) <= color_tolerance and \
                abs(predefined_color["g"] - rgb_color[1]) <= color_tolerance and \
                abs(predefined_color["b"] - rgb_color[2]) <= color_tolerance:
            return predefined_color['tag']

    raise Exception("Color not found in color list")


def pick_place_circle(circles, coordinates, color_variables):
    global state
    print(circles)
    chosen_circle = random.choice(circles)
    # color_name = rgb_to_name(chosen_circle.color_rgb, color_variables)
    dobot.set_ptp_cmd(0, chosen_circle.real_x, chosen_circle.real_y, coordinates['hover']['z'], 0, 1)
    dobot.set_ptp_cmd(0, chosen_circle.real_x, chosen_circle.real_y, coordinates['pick']['z'], 0, 1)
    state = 2


def acquire_image(camera, crop=True):
    img = camera.get_frame()
    if crop:
        img = img[250:450, 200:1024]
    return img


def save_image(img, file_name):
    cv2.imwrite(f'{file_name}', img)


def main():
    global state

    # initialize camera
    camera.start(
        config_file['camera']['source'],
        config_file['camera']['width'],
        config_file['camera']['height']
    )

    # connect to robot arm
    dobot.connect(
        config_file['dobot']['port'],
        config_file['dobot']['baudrate']
    )

    # set home parameters
    dobot.set_home_params(
        x=config_file['coordinates']['base_pos']['x'],
        y=config_file['coordinates']['base_pos']['y'],
        z=config_file['coordinates']['base_pos']['z'],
        r=0,
        is_queued=0
    )

    # go home
    # dobot.set_home_cmd(is_queued=1)

    # set end effector type (suction cup)
    dobot.set_end_effector_type(
        config_file['dobot']['end_effector_type'],
        is_queued=0
    )

    dobot.set_home_cmd(1)
    dobot.set_ptp_cmd(1, config_file['coordinates']['base_pos']['x'], config_file['coordinates']['base_pos']['y'], config_file['coordinates']['base_pos']['z'], 0, 1)
    while True:
        if state == 0:

            img = acquire_image(camera, crop=True)
            save_image(img, 'raw_capture.jpeg')
            img = cv2.imread('raw_capture.jpeg')
            state = 1

        elif state == 1:
            try:
                circles = find_circles(img, config_file['calibration'], config_file['colors'])
                pick_place_circle(circles, config_file['coordinates'], config_file['colors'])

            except:
                state = 0


    # while not keyboard.is_pressed("q"):
    #     frame = camera.get_frame()
    #     frame = frame[250:450, 200:1024]
    #     find_circles(frame, config_file['calibration'], config_file['colors'])
    #     cv2.waitKey(1)
    # cv2.destroyAllWindows()

    # if state == -1:
    #     while not keyboard.is_pressed("q"):
    #         frame = camera.get_frame()
    #         frame = frame[250:450, 200:1024]
    #         find_circles(frame, config_file['calibration'], config_file['colors'])
    #         cv2.waitKey(1)
    #     cv2.destroyAllWindows()
    #
    #
    # elif state == 0:
    #     while not keyboard.is_pressed("s"):
    #         frame = camera.get_frame()
    #         frame = frame[250:450, 200:1024]
    #         cv2.imwrite('raw_capture.jpeg', frame)
    #         cv2.waitKey(1)
    #
    #     state = 1
    #
    #
    # elif state == 1:
    #     image = cv2.imread('raw_capture.jpeg')
    #     circles = find_circles(image, config_file['calibration'], config_file['colors'])
    #     for circle in circles:
    #         print(vars(circles[circles.index(circle)]))
    #         print(circle.color_rgb)
    #
    #     state = 2
    #
    #
    # elif state == 2:
    #     try:
    #         chosen_circle = random.choice(circles)
    #         print(chosen_circle.real_x)
    #         print(chosen_circle.real_y)
    #         pick_place_circle(chosen_circle, config_file['coordinates']['hoppers'], config_file['colors'])
    #         state = 4
    #     except:
    #         state = 1
    #     state = 0


if __name__ == '__main__':
    main()
