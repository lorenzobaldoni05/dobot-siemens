import numpy as np
import cv2
import DobotDllType as dType
import keyboard
import yaml
import colorsys
from camera import Camera
from dobot import Dobot
from opcua_client import Opcua

# open yaml config file
with open('config.yaml', 'r') as f:
    config_file = yaml.safe_load(f)


# save image to file
def save_image(img, file_name):
    cv2.imwrite(f'{file_name}', img)


# get color name from image
def get_color(img, yaml_colors, color_space='hsv'):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # convert BGR image to RGB color space
    average_color = np.mean(img_rgb, axis=(0, 1))  # average color
    average_color = list(map(round, average_color))  # convert average color to list

    # if color space is RGB
    if color_space == 'rgb':
        max_color_value = max(average_color)
        if average_color.count(max_color_value) > 1:
            raise Exception("Equal values in color code")
        max_color_value_index = average_color.index(max_color_value)

        if max_color_value_index == 0:
            return 'red'
        elif max_color_value_index == 1:
            return 'green'
        else:
            return 'blue'

    # if color space is HSV
    elif color_space == 'hsv':
        r, g, b = (average_color[0] / 255, average_color[1] / 255, average_color[2] / 255)  # normalize RGB values
        h, s, v = colorsys.rgb_to_hsv(r, g, b)  # convert RGB values to HSV
        h, s, v = (int(h * 359), int(s * 255), int(v * 255))  # Expand HSV range

        print(f'h value: {h}')

        hsv_dict = yaml_colors.get('hsv')

        for hsv_color in hsv_dict:
            ranges_str = hsv_dict[hsv_color]['h']
            ranges_str_split = ranges_str.split(',')
            for h_range in ranges_str_split:
                boundaries = h_range.split('-')
                if int(boundaries[0]) < h < int(boundaries[1]):
                    return hsv_color

        raise Exception('H value not in range')


# pick and place ball in corresponding hopper
def pick_place_ball(hopper):
    dobot.set_ptp_cmd(1, config_file['coordinates']['ball_hover']['x'],
                      config_file['coordinates']['ball_hover']['y'],
                      config_file['coordinates']['ball_hover']['z'], 0, 1)

    dobot.set_end_effector_suction_cup(True, True, 1)

    dobot.set_ptp_cmd(1, config_file['coordinates']['ball_pick']['x'],
                      config_file['coordinates']['ball_pick']['y'],
                      config_file['coordinates']['ball_pick']['z'], 0, 1)

    dobot.set_ptp_cmd(1, config_file['coordinates']['ball_hover']['x'],
                      config_file['coordinates']['ball_hover']['y'],
                      config_file['coordinates']['ball_hover']['z'], 0, 1)

    dobot.set_ptp_cmd(1, config_file['coordinates']['home']['x'],
                      config_file['coordinates']['home']['y'],
                      config_file['coordinates']['home']['z'], 0, 1)

    dobot.set_ptp_cmd(1, config_file['coordinates']['hoppers'][f'{hopper}']['x'],
                      config_file['coordinates']['hoppers'][f'{hopper}']['y'],
                      config_file['coordinates']['hoppers'][f'{hopper}']['z'], 0, 1)

    dobot.set_end_effector_suction_cup(True, False, 1)

    dobot.set_ptp_cmd(1, config_file['coordinates']['home']['x'],
                      config_file['coordinates']['home']['y'],
                      config_file['coordinates']['home']['z'], 0, 1)


# update OPC UA variables
def update_opcua(hopper):
    cb_hopper_node_id = config_file['opcua']['node_ids'][f'cb_{hopper}']        # node id of corresponding hopper
    _, cb_hopper = opcua_connection.read_value(cb_hopper_node_id)       # read value of contained balls in hopper
    opcua_connection.write_value(cb_hopper_node_id, 'Byte', cb_hopper + 1)     # write updated value


dobot = Dobot(config_file['dobot']['port'])  # instantiate object of Dobot class
camera = Camera(config_file['camera']['source'],
                config_file['camera']['width'],
                config_file['camera']['height'])  # instantiate object of Camera class
opcua_connection = Opcua(config_file['opcua']['url'],
                         config_file['opcua']['user'],
                         config_file['opcua']['psw'],
                         config_file['opcua']['timeout_ms'])  # instantiate object of Opcua class

dobot.connect()  # connect to robot arm
opcua_connection.client_connect()  # connect OPC UA client

# set home parameters
dobot.set_home_params(
    config_file['coordinates']['home']['x'],
    config_file['coordinates']['home']['y'],
    config_file['coordinates']['home']['z'],
    0, 0
)

# set end effector type
dobot.set_end_effector_type(config_file['dobot']['end_effector_type'], 0)

# dobot.set_home_cmd(0)

# move to home position
dobot.set_ptp_cmd(1,
                  config_file['coordinates']['home']['x'],
                  config_file['coordinates']['home']['y'],
                  config_file['coordinates']['home']['z'],
                  0, 1)

while True:
    _, should_run = opcua_connection.read_value(config_file['opcua']['node_ids']['should_run'])

    if should_run:
        camera.get_frame(crop=True)  # retrieve previous frame to clear buffer
        img = camera.get_frame(crop=True)  # retrieve current frame from camera
        save_image(img, 'test.jpg')  # save current frame to file (only for debugging, not used in program)

        color = get_color(img,
                          config_file['colors'],
                          color_space='hsv')  # get color from current frame
        hopper = config_file['colors']['hoppers_matching'][f'{color}']  # get corresponding hopper

        pick_place_ball(hopper)  # pick and place ball to corresponding hopper

        update_opcua(hopper)    # update OPC UA variables
