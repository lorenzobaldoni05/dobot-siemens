import DobotDllType as dType


class Dobot:
    def __init__(self, port, baudrate=115200):
        self.api = dType.load()
        self.port = port
        self.baudrate = baudrate

    # connect to robot arm
    def connect(self):
        try:
            dType.ConnectDobot(self.api, f'{self.port}', self.baudrate)
        except:
            raise Exception("Failed to connect to Dobot Magician")

    # set home coordinates
    def set_home_params(self, x, y, z, r, is_queued):
        dType.SetHOMEParams(self.api, x, y, z, r, isQueued=is_queued)

    # command: home robot arm
    def set_home_cmd(self, is_queued):
        dType.SetHOMECmd(self.api, temp=0, isQueued=is_queued)
        # busy loop that waits the movement to be completed
        while not dType.GetQueuedCmdMotionFinish(self.api)[0]:
            if dType.GetQueuedCmdMotionFinish(self.api)[0]:
                break

    # set end effector type
    def set_end_effector_type(self, end_effector, is_queued):
        dType.SetEndEffectorType(self.api, endType=end_effector, isQueued=is_queued)

    # command: set suction cup state
    def set_end_effector_suction_cup(self, enable_control, state, is_queued):
        dType.SetEndEffectorSuctionCup(self.api, enable_control, state, isQueued=is_queued)

    # command: move to waypoint
    def set_ptp_cmd(self, ptp_mode, x, y, z, r, is_queued):
        dType.SetPTPCmd(self.api, ptp_mode, x, y, z, r, isQueued=is_queued)
        # busy loop that waits the movement to be completed
        while not dType.GetQueuedCmdMotionFinish(self.api)[0]:
            if dType.GetQueuedCmdMotionFinish(self.api)[0]:
                break
