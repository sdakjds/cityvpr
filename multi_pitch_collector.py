# ============================================================
# 多俯仰角+多速度模式画面采集系统
# 11条路线 x 4个俯仰角 x 3个速度模式 = 132个任务
# 速度模式: 1=恒定1.0, 2=恒定0.6, 3=0.6起步每路径点+0.2最大1.2
# 采集频率: 10fps, 分辨率: 1280x720
# 使用方法: py -3.6 multi_pitch_collector.py
# ============================================================

from __future__ import print_function
from builtins import range
import MalmoPython
import json
import math
import os
import sys
import time
import threading
try:
    import queue
except ImportError:
    import Queue as queue

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
else:
    import functools
    print = functools.partial(print, flush=True)

# ============================================================
# 0. 自动启用作弊模式
# ============================================================
def enable_cheats_in_world():
    import gzip
    possible_paths = [
        "saves/100x100map/level.dat",
        os.path.join(os.getcwd(), "saves", "100x100map", "level.dat"),
    ]
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            possible_paths.append(os.path.join(appdata, '.minecraft', 'saves', '100x100map', 'level.dat'))
        localappdata = os.environ.get('LOCALAPPDATA', '')
        if localappdata:
            possible_paths.append(os.path.join(localappdata, 'minecraft', 'saves', '100x100map', 'level.dat'))
    else:
        possible_paths.append(os.path.expanduser("~/.minecraft/saves/100x100map/level.dat"))

    level_dat_path = None
    for path in possible_paths:
        if os.path.exists(path):
            level_dat_path = path
            break
    if not level_dat_path:
        print("[警告] 未找到 level.dat, 请手动启用作弊模式")
        return False

    print("[找到世界文件] " + level_dat_path)
    try:
        try:
            from nbt.nbt import NBTFile, TAG_Byte, TAG_String, TAG_Compound
        except ImportError:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nbt", "--quiet"])
            from nbt.nbt import NBTFile, TAG_Byte, TAG_String, TAG_Compound

        nbtfile = NBTFile(level_dat_path, gzipped=True)
        if 'Data' not in nbtfile:
            return False
        data = nbtfile['Data']
        changed = False
        if 'cheatsEnabled' not in data or int(data['cheatsEnabled'].value) != 1:
            data['cheatsEnabled'] = TAG_Byte(1)
            changed = True
        if 'allowCommands' not in data or int(data['allowCommands'].value) != 1:
            data['allowCommands'] = TAG_Byte(1)
            changed = True
        if changed:
            backup_path = level_dat_path + ".bak"
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(level_dat_path, backup_path)
            nbtfile.write_file(level_dat_path, gzipped=True)
            print("[成功] 已启用作弊模式!")
        else:
            print("[跳过] 作弊模式已启用")
        return True
    except Exception as e:
        print("[警告] 修改 level.dat 失败: " + str(e))
        return False


# ============================================================
# 1. 拐点位置和连通图
# ============================================================
WAYPOINTS = [
    (41, 63), (57, 63), (68, 63), (79, 63), (26, 63),
    (34, 82), (41, 82), (45, 82), (57, 82), (68, 82),
    (79, 82), (79, 90), (78, 98), (34, 102), (45, 102),
    (57, 102), (68, 102), (76, 102), (87, 102), (34, 112),
    (67, 113), (30, 116), (57, 123), (14, 57), (14, 82),
    (14, 115), (87, 89), (90, 89), (90, 63), (5, 142),
    (68, 141), (87, 141),
]

GRAPH = {
    0: [(6, 19), (1, 16)], 1: [(8, 19), (0, 16), (2, 11)],
    2: [(9, 19), (1, 11), (3, 11)], 3: [(10, 19), (2, 11)],
    4: [(23, 13)], 5: [(13, 20), (6, 7), (24, 20)],
    6: [(0, 19), (5, 7), (7, 4)], 7: [(14, 20), (6, 4), (8, 12)],
    8: [(1, 19), (15, 20), (7, 12), (9, 11)], 9: [(2, 19), (16, 20), (8, 11), (10, 11)],
    10: [(3, 19), (11, 8), (9, 11)], 11: [(10, 8), (26, 8)], 12: [],
    13: [(5, 20), (14, 11)], 14: [(7, 20), (13, 11), (15, 12)],
    15: [(8, 20), (22, 21), (14, 12), (16, 11)], 16: [(9, 20), (15, 11), (17, 9)],
    17: [(16, 9), (18, 10)], 18: [(17, 10), (26, 13), (31, 39)], 19: [],
    20: [(30, 28)], 21: [(25, 16), (29, 36)], 22: [(15, 21)],
    23: [(24, 25), (4, 13)], 24: [(23, 25), (5, 20), (25, 33)], 25: [(24, 33), (21, 16)],
    26: [(11, 8), (18, 13), (27, 3)], 27: [(26, 3), (28, 26)], 28: [(27, 26)],
    29: [(21, 36)], 30: [(20, 28)], 31: [(18, 39)],
}

BASE_WALK_SPEED = 4.317

# ============================================================
# 2. 路线定义 (11条)
# ============================================================
ROUTES = [
    [1, 8, 10, 11, 12, 17, 20, 22],
    [21, 19, 13, 5, 7, 8, 15, 22],
    [18, 17, 16, 15, 8, 7, 5, 19, 22],
    [4, 0, 6, 5, 13, 15, 22],
    [11, 10, 9, 8, 15, 22],
    [23, 24, 25, 21, 19, 22],
    [23, 4, 5, 10, 12, 17, 20, 22],
    [28, 27, 26, 18, 15, 22],
    [29, 21, 19, 13, 5, 8, 15, 22],
    [30, 20, 17, 13, 19, 22],
    [31, 18, 26, 11, 10, 3, 1, 8, 22],
]
ROUTE_NAMES = ["route1", "route2", "route3", "route4", "route5",
               "route6", "route7", "route8", "route9", "route10", "route11"]

# ============================================================
# 3. 俯仰角定义 (4个角度, 按MC pitch)
# ============================================================
PITCH_ANGLES = [
    {'name': '90', 'mc_pitch': 90,  'desc': '正下方'},
    {'name': '60', 'mc_pitch': 60,  'desc': '低头60°'},
    {'name': '30', 'mc_pitch': 30,  'desc': '低头30°'},
    {'name': '0',  'mc_pitch': 0,   'desc': '正前方'},
]

# ============================================================
# 4. 速度模式定义 (3个模式)
# ============================================================
# 模式1: 恒定1.0  -> 4.32格/秒
# 模式2: 恒定0.6  -> 2.59格/秒
# 模式3: 0.6起步, 每经过一个路径点+0.2, 最大1.2 -> 2.59~5.18格/秒
SPEED_MODES = [
    {'id': 1, 'name': 'speedMode_1', 'type': 'constant',  'base_speed': 1.0, 'desc': '恒定1.0'},
    {'id': 2, 'name': 'speedMode_2', 'type': 'constant',  'base_speed': 0.6, 'desc': '恒定0.6'},
    {'id': 3, 'name': 'speedMode_3', 'type': 'accel',     'base_speed': 0.6, 'increment': 0.2, 'max_speed': 1.2, 'desc': '0.6起步+0.2最大1.2'},
]

# 采集间隔: 0.1秒 = 10fps
CAPTURE_INTERVAL = 0.1

# ============================================================
# 5. 画面保存配置
# ============================================================
FRAME_ROOT = "city_vpr_dataset"

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ============================================================
# 6. 路径检查
# ============================================================
for ridx, route in enumerate(ROUTES):
    if not route:
        print("错误: 路线{}为空!".format(ridx + 1))
        sys.exit(1)
    for wp_idx in route:
        if wp_idx < 0 or wp_idx >= len(WAYPOINTS):
            print("错误: 路线{}中的拐点索引 W{} 超出范围".format(ridx + 1, wp_idx))
            sys.exit(1)

print("=" * 60)
print("多俯仰角+多速度模式画面采集程序")
print("路线数: {} | 俯仰角数: {} | 速度模式数: {}".format(
    len(ROUTES), len(PITCH_ANGLES), len(SPEED_MODES)))
print("总任务数: {} (路线 x 角度 x 速度)".format(
    len(ROUTES) * len(PITCH_ANGLES) * len(SPEED_MODES)))
print("采集频率: 10fps | 分辨率: 1280x720")
print("根目录: " + os.path.abspath(FRAME_ROOT))
print("=" * 60)
for sm in SPEED_MODES:
    print("  {}: {} ({}格/秒)".format(sm['name'], sm['desc'], sm['base_speed'] * BASE_WALK_SPEED))
for pa in PITCH_ANGLES:
    print("  pitch_{}: {} (MC pitch={})".format(pa['name'], pa['desc'], pa['mc_pitch']))
print("=" * 60)

# ============================================================
# 7. Mission XML
# ============================================================
def GetMissionXML(start_x, start_z, start_yaw, start_pitch, time_limit_ms=300000):
    xml_str = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <About>
    <Summary>Multi-Pitch Multi-Speed Data Collection</Summary>
  </About>
  <ServerSection>
    <ServerInitialConditions>
      <Time>
        <StartTime>6000</StartTime>
        <AllowPassageOfTime>false</AllowPassageOfTime>
      </Time>
      <Weather>clear</Weather>
      <AllowSpawning>false</AllowSpawning>
    </ServerInitialConditions>
    <ServerHandlers>
      <FileWorldGenerator src="saves/100x100map" forceReset="true"/>
      <ServerQuitFromTimeUp timeLimitMs="{time_limit_ms}"/>
    </ServerHandlers>
  </ServerSection>
  <AgentSection mode="Creative">
    <Name>Collector</Name>
    <AgentStart>
      <Placement x="{start_x}" y="8" z="{start_z}" yaw="{start_yaw}" pitch="{start_pitch}"/>
    </AgentStart>
    <AgentHandlers>
      <ObservationFromFullStats/>
      <VideoProducer viewpoint="0" want_depth="false">
        <Width>1280</Width>
        <Height>720</Height>
      </VideoProducer>
      <ContinuousMovementCommands turnSpeedDegs="90"/>
      <ChatCommands/>
      <MissionQuitCommands/>
    </AgentHandlers>
  </AgentSection>
</Mission>'''.format(start_x=start_x, start_z=start_z, start_yaw=start_yaw,
                     start_pitch=start_pitch, time_limit_ms=time_limit_ms)
    return xml_str


# ============================================================
# 8. 速度药水辅助函数
# ============================================================
def get_potion_level_for_speed(move_speed):
    """根据move命令值计算需要的速度药水等级
    MC基础速度 move 1.0 = 4.317格/秒
    速度药水每级+20%速度: 1级=1.2x, 2级=1.4x, ...
    move 1.2 需要: 1.2/1.0 = 1.2倍 -> 药水1级(1.2x)
    """
    if move_speed <= 1.0:
        return 0
    ratio = move_speed / 1.0
    # 每级药水+0.2, 向上取整
    level = math.ceil((ratio - 1.0) / 0.2)
    return max(1, level)

def apply_speed_potion(agent_host, move_speed):
    """给玩家施加速度药水效果"""
    level = get_potion_level_for_speed(move_speed)
    if level > 0:
        # /effect @p speed 持续时间 等级
        # 1000000秒 = 近似永久
        cmd = "/effect @p speed 1000000 {}".format(level)
        agent_host.sendCommand("chat " + cmd)
        print("[药水] 速度药水等级={} (move={:.1f})".format(level, move_speed))
        time.sleep(0.5)

def clear_speed_potion(agent_host):
    """清除速度药水效果"""
    agent_host.sendCommand("chat /effect @p clear")
    time.sleep(0.3)


# ============================================================
# 9. 导航器 (支持俯仰角+速度模式)
# ============================================================
class PitchSpeedNavigator(object):
    def __init__(self, agent_host, frame_dir, route_num, pitch_config, speed_mode):
        self.agent_host = agent_host
        self.frame_dir = frame_dir
        self.route_num = route_num
        self.pitch_config = pitch_config
        self.speed_mode = speed_mode

        self.target_pitch = pitch_config['mc_pitch']
        self.pitch_name = pitch_config['name']

        # 速度模式参数
        self.sm_type = speed_mode['type']
        self.sm_base = speed_mode['base_speed']
        self.sm_increment = speed_mode.get('increment', 0)
        self.sm_max = speed_mode.get('max_speed', 1.0)
        self.sm_name = speed_mode['name']

        self.frame_count = 0
        self.curr_wp_idx = None
        self.target_wp_idx = None
        self.path = []
        self.path_idx = 0
        self.path_complete = False
        self.REACH_DIST = 1.0
        self.current_speed = 0.0  # 实际格/秒
        self.current_move = 0.0   # move命令值
        self.record_lines = []
        self.mission_start_time = 0.0  # 任务起始时间戳（秒）

        # 后台保存线程（避免PNG保存阻塞采集）
        self.save_queue = queue.Queue()
        self.save_thread = None
        self._save_running = False

        # 路径点计数 (用于加速模式)
        self.waypoints_passed = 0

        # 转向状态机
        self.nav_state = "TURN"
        self.TURN_SPEED = 90.0
        self.turn_start_time = 0
        self.turn_duration = 1.0
        self.turn_direction = 0
        self.turn_val = 0

        # 俯仰角校准
        self.pitch_calibrated = False
        self.last_pitch_check = 0

        # 当前药水等级
        self.current_potion_level = 0

    def grid_to_world(self, gx, gz):
        return float(gx), float(gz)

    def set_path(self, waypoint_indices):
        self.path = waypoint_indices
        self.path_idx = 0
        self.path_complete = False
        self.turn_start_time = 0
        self.waypoints_passed = 0
        if self.path:
            self.curr_wp_idx = self.path[0]
            if len(self.path) > 1:
                self.target_wp_idx = self.path[1]
                self.path_idx = 1
            else:
                self.target_wp_idx = None
                self.path_complete = True

    def compute_yaw_to_target(self, x, z, target_x, target_z):
        dx = target_x - x
        dz = target_z - z
        return math.degrees(math.atan2(-dx, dz))

    def normalize_yaw(self, yaw):
        yaw = yaw % 360
        if yaw < 0:
            yaw += 360
        return yaw

    def angle_diff(self, current_yaw, target_yaw):
        diff = (target_yaw - current_yaw) % 360
        if diff > 180:
            diff -= 360
        return diff

    def start_turn(self, curr_yaw, target_yaw):
        diff = self.angle_diff(curr_yaw, target_yaw)
        self.turn_direction = 1.0 if diff > 0 else -1.0
        needed_speed = abs(diff) / self.turn_duration
        turn_val = min(needed_speed / self.TURN_SPEED, 1.0)
        self.turn_val = turn_val
        self.turn_start_time = time.time()

    def get_move_speed(self):
        """根据速度模式计算当前move命令值"""
        if self.sm_type == 'constant':
            return self.sm_base
        elif self.sm_type == 'accel':
            speed = self.sm_base + self.waypoints_passed * self.sm_increment
            return min(speed, self.sm_max)
        return 1.0

    def update_potion_if_needed(self, move_speed):
        """如果move速度超过1.0, 更新药水等级"""
        needed_level = get_potion_level_for_speed(move_speed)
        if needed_level != self.current_potion_level:
            if needed_level > 0:
                apply_speed_potion(self.agent_host, move_speed)
            else:
                clear_speed_potion(self.agent_host)
            self.current_potion_level = needed_level

    # ====== 俯仰角控制 ======
    def calibrate_pitch(self):
        if self.pitch_calibrated:
            return True
        ws = self.agent_host.getWorldState()
        if not ws.is_mission_running or len(ws.observations) == 0:
            return False
        obs = json.loads(ws.observations[-1].text)
        curr_pitch = obs.get(u'Pitch', 0)
        diff = self.target_pitch - curr_pitch
        if abs(diff) < 2.0:
            self.agent_host.sendCommand("pitch 0")
            self.pitch_calibrated = True
            print("[俯仰角] 已校准到 {}° (MC pitch={})".format(
                self.pitch_config['desc'], self.target_pitch))
            return True
        direction = 1.0 if diff > 0 else -1.0
        if abs(diff) > 10:
            self.agent_host.sendCommand("pitch " + str(direction))
        else:
            self.agent_host.sendCommand("pitch " + str(0.3 * direction))
        return False

    def maintain_pitch(self, obs):
        curr_time = time.time()
        if curr_time - self.last_pitch_check < 1.0:
            return
        self.last_pitch_check = curr_time
        curr_pitch = obs.get(u'Pitch', 0)
        diff = self.target_pitch - curr_pitch
        if abs(diff) > 5.0:
            direction = 1.0 if diff > 0 else -1.0
            self.agent_host.sendCommand("pitch " + str(0.5 * direction))
        elif abs(diff) > 2.0:
            direction = 1.0 if diff > 0 else -1.0
            self.agent_host.sendCommand("pitch " + str(0.2 * direction))
        else:
            self.agent_host.sendCommand("pitch 0")

    # ====== 导航逻辑 ======
    def act(self, obs):
        if self.path_complete:
            self.agent_host.sendCommand("move 0")
            self.agent_host.sendCommand("turn 0")
            self.agent_host.sendCommand("pitch 0")
            self.current_speed = 0.0
            return

        # 先校准俯仰角
        if not self.pitch_calibrated:
            self.agent_host.sendCommand("move 0")
            self.agent_host.sendCommand("turn 0")
            self.calibrate_pitch()
            return

        curr_x = obs.get(u'XPos', 0)
        curr_z = obs.get(u'ZPos', 0)
        curr_yaw = obs.get(u'Yaw', 0)

        if self.target_wp_idx is None:
            self.agent_host.sendCommand("move 0")
            self.agent_host.sendCommand("turn 0")
            self.current_speed = 0.0
            return

        tx, tz = self.grid_to_world(*WAYPOINTS[self.target_wp_idx])
        dist = math.sqrt((curr_x - tx) ** 2 + (curr_z - tz) ** 2)
        target_yaw = self.compute_yaw_to_target(curr_x, curr_z, tx, tz)

        # 到达路径点
        if dist < self.REACH_DIST:
            print("到达 W{}! (dist={:.1f})".format(self.target_wp_idx, dist))
            self.agent_host.sendCommand("move 0")
            self.agent_host.sendCommand("turn 0")
            self.path_idx += 1
            self.waypoints_passed += 1

            # 更新药水 (加速模式速度可能增加)
            new_speed = self.get_move_speed()
            self.update_potion_if_needed(new_speed)
            print("[速度] move={:.1f} -> {:.2f}格/秒 (经过{}个点)".format(
                new_speed, new_speed * BASE_WALK_SPEED, self.waypoints_passed))

            if self.path_idx < len(self.path):
                self.target_wp_idx = self.path[self.path_idx]
                print("下一个目标: W{}".format(self.target_wp_idx))
                self.nav_state = "TURN"
                self.turn_start_time = 0
                self.current_speed = 0.0
                return
            else:
                print("路径完成! 已到达终点 W{}".format(self.path[-1]))
                self.target_wp_idx = None
                self.path_complete = True
                self.current_speed = 0.0
                return

        # TURN状态: 非阻塞转向
        if self.nav_state == "TURN":
            self.agent_host.sendCommand("move 0")
            self.current_speed = 0.0

            if self.turn_start_time == 0:
                diff = self.angle_diff(curr_yaw, target_yaw)
                if abs(diff) < 2.0:
                    self.agent_host.sendCommand("turn 0")
                    self.nav_state = "MOVE"
                else:
                    self.start_turn(curr_yaw, target_yaw)
                    print("[转向] Yaw={:.1f} -> {:.1f} 差={:.1f}".format(
                        curr_yaw, target_yaw, diff))

            elapsed = time.time() - self.turn_start_time
            if elapsed >= self.turn_duration:
                self.agent_host.sendCommand("turn 0")
                self.turn_start_time = 0
                diff_after = self.angle_diff(curr_yaw, target_yaw)
                if abs(diff_after) > 5.0:
                    print("[转后再校验] 差{:.1f}度, 需要再转".format(diff_after))
                    self.turn_start_time = 0
                else:
                    self.nav_state = "MOVE"
            else:
                self.agent_host.sendCommand("turn " + str(self.turn_val * self.turn_direction))

        # MOVE状态: 直线走, 不减速
        else:
            move_cmd = self.get_move_speed()
            self.current_move = move_cmd
            self.current_speed = move_cmd * BASE_WALK_SPEED

            # 如果需要, 更新药水
            self.update_potion_if_needed(move_cmd)

            # 微调转向校准
            diff = self.angle_diff(curr_yaw, target_yaw)
            if abs(diff) < 1.0:
                turn_cmd = 0.0
            elif abs(diff) < 10.0:
                turn_cmd = 0.15 * (1.0 if diff > 0 else -1.0)
            else:
                turn_cmd = 0.4 * (1.0 if diff > 0 else -1.0)

            self.agent_host.sendCommand("move " + str(move_cmd))
            if turn_cmd != 0.0:
                self.agent_host.sendCommand("turn " + str(turn_cmd))
            else:
                self.agent_host.sendCommand("turn 0")

            # 维持俯仰角
            self.maintain_pitch(obs)

    # ====== 后台保存线程 ======
    def _save_worker(self):
        """后台线程：从队列取帧数据并保存PNG"""
        while self._save_running or not self.save_queue.empty():
            try:
                item = self.save_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            img_name, width, height, pixels, rel_time = item

            if HAS_PIL:
                image = Image.frombytes('RGB', (width, height), pixels)
                filename = os.path.join(self.frame_dir, img_name + ".png")
                image.save(filename)
            else:
                filename = os.path.join(self.frame_dir, img_name + ".raw")
                with open(filename, 'wb') as f:
                    f.write(pixels)

            self.save_queue.task_done()

    def start_save_thread(self):
        """启动后台保存线程"""
        self._save_running = True
        self.save_thread = threading.Thread(target=self._save_worker)
        self.save_thread.daemon = True
        self.save_thread.start()

    def stop_save_thread(self):
        """停止后台保存线程（等待队列清空）"""
        self._save_running = False
        if self.save_thread:
            self.save_thread.join(timeout=60)

    def queue_size(self):
        """当前待保存的帧数"""
        return self.save_queue.qsize()

    # ====== 画面保存 ======
    def saveFrame(self, world_state, obs, capture_time):
        """Queue exactly one newest video frame for this sampling instant."""
        if not world_state.video_frames:
            return False

        frame = world_state.video_frames[-1]
        self.frame_count += 1
        img_name = "r{}_pitch{}_{}".format(
            self.route_num, self.pitch_name, self.frame_count)
        rel_time = capture_time - self.mission_start_time

        # Copy while the Malmo world state is valid; PNG writing stays off the control loop.
        pixels_copy = bytes(frame.pixels)
        self.save_queue.put((img_name, frame.width, frame.height, pixels_copy, rel_time))

        if obs:
            x = obs.get(u'XPos', 0)
            y = obs.get(u'YPos', 0)
            z = obs.get(u'ZPos', 0)
            yaw = obs.get(u'Yaw', 0)
            pitch = obs.get(u'Pitch', 0)
            facing = self.normalize_yaw(yaw)
            record_line = "{:<30}  Time:{:>8.3f}  X:{:>8.2f}  Y:{:>8.2f}  Z:{:>8.2f}    Facing:{:>6.1f}    Pitch:{:>6.1f}    Speed:{:>6.2f}".format(
                img_name + ":", rel_time, x, y, z, facing, pitch, self.current_speed)
            self.record_lines.append(record_line)
        return True

    def saveRecord(self):
        record_path = os.path.join(self.frame_dir, "record.txt")
        with open(record_path, 'w') as f:
            f.write("# Route: {} | {} | pitch_{} ({})\n".format(
                self.route_num, self.speed_mode['name'],
                self.pitch_name, self.pitch_config['desc']))
            f.write("# Image                          X       Y       Z    Facing   Pitch   Speed\n")
            for line in self.record_lines:
                f.write(line + "\n")
        print("坐标记录已保存: {} (共{}条)".format(record_path, len(self.record_lines)))


# ============================================================
# 10. 单条路线+俯仰角+速度模式执行函数
# ============================================================
def run_task(agent_host, route_idx, route, route_name, pitch_config, speed_mode):
    """执行单个任务: 路线 + 俯仰角 + 速度模式"""

    # 目录: city_vpr_dataset/speedMode_1/route1/pitch_0/
    task_dir = os.path.join(FRAME_ROOT, speed_mode['name'], route_name, "pitch_" + pitch_config['name'])
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)

    start_wp = route[0]
    start_gx, start_gz = WAYPOINTS[start_wp]
    start_wx = float(start_gx)
    start_wz = float(start_gz)

    # 计算初始朝向
    if len(route) > 1:
        next_wp = route[1]
        next_gx, next_gz = WAYPOINTS[next_wp]
        next_wx = float(next_gx)
        next_wz = float(next_gz)
        dx = next_wx - start_wx
        dz = next_wz - start_wz
        start_yaw = math.degrees(math.atan2(-dx, dz))
    else:
        start_yaw = 0.0

    start_pitch = pitch_config['mc_pitch']

    # 时间限制
    base_time = len(route) * 20000 + 30000
    time_limit_ms = max(base_time, 120000)

    print("\n" + "=" * 60)
    print("路线 {}/{} : {} | {} | pitch_{} ({})".format(
        route_idx + 1, len(ROUTES), route_name,
        speed_mode['name'], pitch_config['name'], pitch_config['desc']))
    print("路径: W" + " -> W".join(map(str, route)))
    print("起点: W{} 世界坐标({:.0f}, {:.0f}) Yaw={:.1f} Pitch={}".format(
        start_wp, start_wx, start_wz, start_yaw, start_pitch))
    print("速度: {} ({:.2f}格/秒)".format(speed_mode['desc'], speed_mode['base_speed'] * BASE_WALK_SPEED))
    print("截图目录: {}".format(task_dir))
    print("图片命名: r{}_pitch{}_序号.png".format(route_idx + 1, pitch_config['name']))
    print("=" * 60)

    mission_xml = GetMissionXML(start_wx, start_wz, start_yaw, start_pitch, time_limit_ms)
    my_mission = MalmoPython.MissionSpec(mission_xml, True)
    my_mission_record = MalmoPython.MissionRecordSpec()

    # 启动mission (带重试)
    max_retries = 5
    started = False
    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, my_mission_record)
            print("成功连接Malmo客户端!")
            started = True
            break
        except RuntimeError as err:
            if retry == max_retries - 1:
                print("连接失败:", err)
                return 0
            print("第{}次连接失败，等待3秒...".format(retry + 1))
            time.sleep(3)

    if not started:
        return 0

    # 等待任务开始
    print("等待任务开始", end="")
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        print(".", end="")
        time.sleep(0.2)
        world_state = agent_host.getWorldState()
        for err in world_state.errors:
            print("\n错误:", err.text)
    print("\n任务开始!")

    # 等待画面稳定
    print("3秒后开始...", end="")
    for i in range(3, 0, -1):
        print(" {}".format(i), end="")
        time.sleep(1)
    print(" 开始!")

    # 用/tp命令设置精确位置和俯仰角
    tp_cmd = "/tp @p {:.1f} 8 {:.1f} {:.1f} {}".format(
        start_wx, start_wz, start_yaw, start_pitch)
    agent_host.sendCommand("chat " + tp_cmd)
    time.sleep(1)
    print("[TP] 已设置位置和俯仰角: pitch={}".format(start_pitch))

    # 如果是加速模式且初始速度>1.0, 施加药水
    nav = PitchSpeedNavigator(agent_host, task_dir, route_idx + 1, pitch_config, speed_mode)
    nav.set_path(route)

    # 初始药水 (模式3起步0.6不需要药水, 但如果模式变化需要)
    initial_speed = nav.get_move_speed()
    if initial_speed > 1.0:
        apply_speed_potion(agent_host, initial_speed)
        nav.current_potion_level = get_potion_level_for_speed(initial_speed)

    # 主循环: 导航 + 采集 (10fps)
    # monotonic() is unaffected by wall-clock adjustments and supplies a fixed 10 fps timeline.
    nav.mission_start_time = time.monotonic()
    nav.start_save_thread()
    next_capture_time = nav.mission_start_time
    while world_state.is_mission_running:
        # Keep the original Malmo control cadence. Faster polling can starve the game client.
        time.sleep(0.05)
        world_state = agent_host.getWorldState()
        if world_state.is_mission_running:
            obs = None
            if len(world_state.observations) > 0:
                obs = json.loads(world_state.observations[-1].text)

            for err in world_state.errors:
                print("[Malmo错误] " + err.text)

            # 采集画面 (10fps, 只在路径未完成时采集)
            curr_time = time.monotonic()
            if not nav.path_complete and curr_time >= next_capture_time:
                # Do not advance the schedule until a real Malmo video frame was queued.
                if nav.saveFrame(world_state, obs, curr_time):
                    # Advance from the scheduled deadline, not from processing completion.
                    # This removes the 0.12-0.13 s drift seen in record.txt.
                    next_capture_time += CAPTURE_INTERVAL
                    while next_capture_time <= curr_time:
                        next_capture_time += CAPTURE_INTERVAL

            # 导航
            # Navigation uses the original control-loop cadence.
            if obs:
                nav.act(obs)

            # 路径完成后结束
            if nav.path_complete:
                print("已到达终点, 结束当前任务...")
                # 清除药水
                clear_speed_potion(agent_host)
                agent_host.sendCommand("quit")
                while world_state.is_mission_running:
                    time.sleep(0.2)
                    world_state = agent_host.getWorldState()
                break

            # 进度打印
            if nav.frame_count > 0 and nav.frame_count % 25 == 0:
                curr_pitch = obs.get(u'Pitch', 0) if obs else 0
                print("[导航中] {}帧 | pitch={:.1f}° | move={:.1f} | speed={:.2f}格/秒".format(
                    nav.frame_count, curr_pitch, nav.current_move, nav.current_speed))

    # 清除药水 (防止残留)
    clear_speed_potion(agent_host)

    # 等待后台保存线程完成所有图片
    print("等待图片保存完成 (剩余{}张)...".format(nav.queue_size()), end="")
    nav.stop_save_thread()
    print(" 完成!")

    # 保存坐标记录
    nav.saveRecord()

    print("\n路线 {} {} pitch_{} 完成! 总采集帧数: {}".format(
        route_name, speed_mode['name'], pitch_config['name'], nav.frame_count))
    print("截图保存在: " + os.path.abspath(task_dir))
    return nav.frame_count


# ============================================================
# 11. 主程序
# ============================================================
if __name__ == "__main__":
    agent_host = MalmoPython.AgentHost()
    try:
        agent_host.parse(sys.argv)
    except RuntimeError as e:
        print("启动参数错误:", e)
        sys.exit(1)
    if agent_host.receivedArgument("help"):
        print(agent_host.getUsage())
        sys.exit(0)

    # 创建根目录
    if not os.path.exists(FRAME_ROOT):
        os.makedirs(FRAME_ROOT)

    # 启用作弊模式
    print("=" * 60)
    print("启用作弊模式...")
    enable_cheats_in_world()
    print("=" * 60)

    print("\n多俯仰角+多速度模式画面采集程序")
    print("路线数: {} | 俯仰角数: {} | 速度模式数: {}".format(
        len(ROUTES), len(PITCH_ANGLES), len(SPEED_MODES)))
    print("总任务数: {} (路线 x 角度 x 速度)".format(
        len(ROUTES) * len(PITCH_ANGLES) * len(SPEED_MODES)))
    print("根目录: " + os.path.abspath(FRAME_ROOT))
    print("=" * 60)

    # 测试模式: py -3.6 multi_pitch_collector.py --test route=1 speed=1 pitch=0
    test_mode = False
    test_route = 0
    test_speed = 0
    test_pitch = 0
    for arg in sys.argv[1:]:
        if arg.startswith('--test'):
            test_mode = True
        elif arg.startswith('route='):
            test_route = int(arg.split('=')[1]) - 1  # 转0-based
        elif arg.startswith('speed='):
            test_speed = int(arg.split('=')[1]) - 1
        elif arg.startswith('pitch='):
            test_pitch = int(arg.split('=')[1])

    if test_mode:
        # 找到对应pitch配置
        test_pa = None
        for pa in PITCH_ANGLES:
            if int(pa['name']) == test_pitch:
                test_pa = pa
                break
        if test_pa is None:
            print("错误: 找不到 pitch={}".format(test_pitch))
            sys.exit(1)

        print("\n" + "=" * 60)
        print("[测试模式] 单任务采集")
        print("  路线: route{}".format(test_route + 1))
        print("  速度模式: speedMode_{}".format(test_speed + 1))
        print("  俯仰角: pitch_{}".format(test_pitch))
        print("=" * 60)

        route = ROUTES[test_route]
        route_name = ROUTE_NAMES[test_route]
        sm = SPEED_MODES[test_speed]
        frame_count = run_task(agent_host, test_route, route, route_name, test_pa, sm)
        print("\n测试完成! 采集了 {} 帧".format(frame_count))
        print("截图目录: " + os.path.join(FRAME_ROOT, sm['name'], route_name, "pitch_" + test_pa['name']))
        sys.exit(0)

    # 依次执行: 每条路线 x 每个速度模式 x 每个俯仰角
    results = []
    for i, route in enumerate(ROUTES):
        route_name = ROUTE_NAMES[i]
        for sm in SPEED_MODES:
            for pa in PITCH_ANGLES:
                frame_count = run_task(agent_host, i, route, route_name, pa, sm)
                results.append((route_name, sm['name'], "pitch_" + pa['name'], frame_count))

                # 任务之间等待5秒
                print("\n等待5秒后开始下一个任务...")
                time.sleep(5)

    # ====== 单独调试 (取消注释即可) ======
    # route_idx = 0       # 第1条路线
    # sm_idx = 0          # 0=speedMode_1, 1=speedMode_2, 2=speedMode_3
    # pa_idx = 3          # 0=pitch_90(下方), 1=60, 2=30, 3=pitch_0(前方)
    # route = ROUTES[route_idx]
    # route_name = ROUTE_NAMES[route_idx]
    # sm = SPEED_MODES[sm_idx]
    # pa = PITCH_ANGLES[pa_idx]
    # frame_count = run_task(agent_host, route_idx, route, route_name, pa, sm)
    # results = [(route_name, sm['name'], "pitch_" + pa['name'], frame_count)]

    # 打印总结
    print("\n" + "=" * 60)
    print("全部采集完成!")
    print("=" * 60)
    total = 0
    for name, sm_name, pitch, count in results:
        print("  {}/{}/{}: {}帧".format(name, sm_name, pitch, count))
        total += count
    print("  总计: {}帧".format(total))
    print("截图根目录: " + os.path.abspath(FRAME_ROOT))
    print("=" * 60)