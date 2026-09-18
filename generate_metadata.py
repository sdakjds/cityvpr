# -*- coding: utf-8 -*-
"""
生成 dataset_metadata.json - 数据集结构化元数据
用法: py -3.6 generate_metadata.py "D:\path\to\city_vpr_dataset"
"""

from __future__ import print_function
import os
import sys
import json
import re
import math

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
else:
    import functools
    print = functools.partial(print, flush=True)

# ============================================================
# 配置
# ============================================================
SPEED_MODES = [
    {"id": 1, "name": "speedMode_1", "type": "constant", "move_value": 1.0,
     "speed_mps": 4.32, "description": "Constant speed at 4.32 m/s (normal walking)"},
    {"id": 2, "name": "speedMode_2", "type": "constant", "move_value": 0.6,
     "speed_mps": 2.59, "description": "Constant slow speed at 2.59 m/s"},
    {"id": 3, "name": "speedMode_3", "type": "accelerating", "move_value_start": 0.6,
     "move_value_max": 1.2, "speed_mps_start": 2.59, "speed_mps_max": 5.18,
     "increment_per_waypoint": 0.2,
     "description": "Accelerating from 2.59 m/s to 5.18 m/s, +0.2 move value per waypoint"},
]

PITCH_ANGLES = [
    {"name": "pitch_0",  "value": 0,  "description": "Looking forward (horizontal)"},
    {"name": "pitch_30", "value": 30, "description": "Looking 30 degrees downward"},
    {"name": "pitch_60", "value": 60, "description": "Looking 60 degrees downward"},
    {"name": "pitch_90", "value": 90, "description": "Looking straight down (90 degrees)"},
]

ROUTE_NAMES = ["route1", "route2", "route3", "route4", "route5",
               "route6", "route7", "route8", "route9", "route10", "route11"]

WAYPOINTS = [
    (41, 63), (57, 63), (68, 63), (79, 63), (26, 63),
    (34, 82), (41, 82), (45, 82), (57, 82), (68, 82),
    (79, 82), (79, 90), (78, 98), (34, 102), (45, 102),
    (57, 102), (68, 102), (76, 102), (87, 102), (34, 112),
    (67, 113), (30, 116), (57, 123), (14, 57), (14, 82),
    (14, 115), (87, 89), (90, 89), (90, 63), (5, 142),
    (68, 141), (87, 141),
]

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


def load_json(path):
    """加载JSON文件"""
    with open(path, 'r') as f:
        return json.load(f)


def calc_route_distance(route):
    """计算路线总距离"""
    dist = 0.0
    for i in range(1, len(route)):
        x1, z1 = WAYPOINTS[route[i-1]]
        x2, z2 = WAYPOINTS[route[i]]
        dist += math.sqrt((x2-x1)**2 + (z2-z1)**2)
    return round(dist, 2)


def scan_dataset_stats(dataset_root):
    """扫描数据集统计信息"""
    stats = {
        "total_frames": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_size_bytes": 0,
        "per_speed_mode": {},
        "per_route": {},
        "per_pitch": {},
    }

    for sm in SPEED_MODES:
        stats['per_speed_mode'][sm['name']] = {"frames": 0, "tasks": 0}

    for rn in ROUTE_NAMES:
        stats['per_route'][rn] = {"frames": 0, "tasks": 0}

    for pa in PITCH_ANGLES:
        stats['per_pitch'][pa['name']] = {"frames": 0, "tasks": 0}

    for sm in SPEED_MODES:
        sm_dir = os.path.join(dataset_root, sm['name'])
        if not os.path.isdir(sm_dir):
            continue
        for ri, rn in enumerate(ROUTE_NAMES):
            route_dir = os.path.join(sm_dir, rn)
            if not os.path.isdir(route_dir):
                continue
            for pa in PITCH_ANGLES:
                pitch_dir = os.path.join(route_dir, pa['name'])
                if not os.path.isdir(pitch_dir):
                    continue

                record_path = os.path.join(pitch_dir, "record.txt")
                if os.path.exists(record_path):
                    # 统计帧数
                    frames = 0
                    try:
                        with open(record_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and 'X:' in line:
                                    frames += 1
                    except Exception:
                        pass

                    stats['total_frames'] += frames
                    stats['completed_tasks'] += 1
                    stats['per_speed_mode'][sm['name']]['frames'] += frames
                    stats['per_speed_mode'][sm['name']]['tasks'] += 1
                    stats['per_route'][rn]['frames'] += frames
                    stats['per_route'][rn]['tasks'] += 1
                    stats['per_pitch'][pa['name']]['frames'] += frames
                    stats['per_pitch'][pa['name']]['tasks'] += 1

                    # 统计PNG文件大小
                    png_size = 0
                    try:
                        for f in os.listdir(pitch_dir):
                            if f.lower().endswith('.png'):
                                png_size += os.path.getsize(os.path.join(pitch_dir, f))
                    except Exception:
                        pass
                    stats['total_size_bytes'] += png_size

    stats['total_tasks'] = len(SPEED_MODES) * len(ROUTE_NAMES) * len(PITCH_ANGLES)
    return stats


def generate_metadata(dataset_root, stats, buildings):
    """生成完整元数据"""

    # 路线信息
    routes_info = []
    total_distance = 0.0
    for i, route in enumerate(ROUTES):
        d = calc_route_distance(route)
        total_distance += d
        routes_info.append({
            "route_id": i + 1,
            "route_name": ROUTE_NAMES[i],
            "num_waypoints": len(route),
            "distance_meters": d,
            "waypoint_ids": route,
        })

    # 建筑统计
    building_types = set()
    for b in buildings:
        building_types.add(b.get("type", "unknown"))

    total_frames = stats['total_frames']

    metadata = {
        # ===== 基本信息 =====
        "dataset_title": "CityVPR: A Multi-Pitch Multi-Speed Visual Place Recognition Dataset in Minecraft Urban Environment",
        "dataset_version": "1.0.0",
        "date_published": "2026-09-15",
        "date_collected": "2026",
        "repository": "Zenodo",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",

        # ===== 作者 =====
        "authors": [
            {
                "name": "Zugang Chen",
                "name_zh": "陈祖刚",
                "affiliation": "Aerospace Information Research Institute, Chinese Academy of Sciences",
                "affiliation_zh": "中国科学院空天信息创新研究院",
                "is_corresponding": True,
                "email": "15039802183@163.com"
            }
        ],

        # ===== 关键词 =====
        "keywords": [
            "visual place recognition",
            "VPR",
            "synthetic dataset",
            "Minecraft",
            "urban environment",
            "multi-view",
            "multi-pitch",
            "varying speed",
            "first-person vision",
            "robot navigation",
            "SLAM"
        ],

        # ===== 数据集描述 =====
        "description": {
            "abstract": (
                "CityVPR is a synthetic visual place recognition dataset collected in a "
                "carefully designed Minecraft-based virtual city environment. The dataset "
                "provides first-person RGB images from 11 distinct navigation routes, "
                "captured at 4 different pitch angles (0, 30, 60, 90 degrees downward) and "
                "3 different speed modes (constant 4.32 m/s, constant 2.59 m/s, and "
                "accelerating 2.59-5.18 m/s). Each frame is accompanied by precise "
                "pose information including timestamp, position (x, y, z), yaw, pitch, and speed. "
                "The dataset contains {:,} frames across {} navigation tasks, "
                "making it suitable for research in visual place recognition, SLAM, "
                "and robot navigation under varying camera viewpoints and motion speeds."
            ).format(total_frames, stats['completed_tasks']),
            "background": (
                "Visual place recognition (VPR) is a fundamental problem in robotics "
                "and computer vision. Most existing VPR datasets are collected in "
                "real-world environments, which introduces challenges such as "
                "uncontrolled lighting, weather conditions, and ground truth "
                "measurement errors. Synthetic datasets provide a controlled "
                "environment with precise ground truth, enabling systematic evaluation "
                "of VPR algorithms under varying conditions. CityVPR complements "
                "existing datasets by providing a large-scale synthetic urban "
                "environment with systematic variations in both camera pitch angle "
                "and navigation speed."
            ),
            "potential_applications": [
                "Visual place recognition algorithm evaluation",
                "Simultaneous Localization and Mapping (SLAM)",
                "Robot navigation research",
                "Viewpoint-invariant image matching",
                "Speed-invariant place recognition",
                "Multi-view VPR methods"
            ]
        },

        # ===== 实验环境 =====
        "environment": {
            "platform": "Minecraft 1.11.2 with Project Malmo 0.36.0",
            "city_size": "100 x 100 blocks (100m x 100m)",
            "city_area_sqm": 10000,
            "num_buildings": len(buildings),
            "num_streets": 9,
            "num_intersections": 32,
            "building_count_by_type": {},
            "ground_truth_precision": "sub-block (0.01 block precision)",
            "player_eye_height_meters": 1.62,
            "ground_level_y": 7,
        },

        # ===== 数据采集 =====
        "data_collection": {
            "sensor": {
                "type": "First-person RGB camera",
                "resolution_width": 1280,
                "resolution_height": 720,
                "frame_rate_hz": 10,
                "image_format": "PNG",
                "color_space": "RGB",
                "bits_per_channel": 8,
                "field_of_view_degrees": 70,
            },
            "recording": {
                "pose_frequency_hz": 10,
                "pose_source": "Minecraft/Malmo agent position",
                "pose_units": "meters and degrees",
            },
            "agent": {
                "type": "Malmo AI agent",
                "navigation_method": "Waypoint-following with turn-and-move state machine",
                "waypoint_reach_threshold_blocks": 1.0,
            }
        },

        # ===== 导航路线 =====
        "navigation": {
            "num_routes": len(ROUTES),
            "num_waypoints": len(WAYPOINTS),
            "total_distance_meters": round(total_distance, 2),
            "routes": routes_info,
        },

        # ===== 俯仰角 =====
        "pitch_angles": [
            {
                "name": pa['name'],
                "pitch_degrees": pa['value'],
                "description": pa['description'],
                "mc_pitch_convention": "Positive pitch looks downward (Minecraft convention)"
            }
            for pa in PITCH_ANGLES
        ],

        # ===== 速度模式 =====
        "speed_modes": SPEED_MODES,

        # ===== 坐标系统 =====
        "coordinate_system": {
            "units": "meters (1 block = 1 meter)",
            "origin": "Northwest corner of the city grid",
            "axes": {
                "x": {
                    "direction": "East",
                    "positive": "Rightward (increasing to the east)",
                    "range": "0 to 100"
                },
                "y": {
                    "direction": "Vertical",
                    "positive": "Upward",
                    "ground_level": 7,
                    "player_eye_level": "~8.6"
                },
                "z": {
                    "direction": "South",
                    "positive": "Downward (increasing to the south)",
                    "range": "50 to 150"
                }
            },
            "yaw": {
                "unit": "degrees",
                "0_degrees": "South (+Z direction)",
                "90_degrees": "West (-X direction)",
                "180_degrees": "North (-Z direction)",
                "270_degrees": "East (+X direction)",
                "convention": "Minecraft yaw convention (clockwise from South)"
            },
            "pitch": {
                "unit": "degrees",
                "0_degrees": "Horizontal forward",
                "positive": "Looking downward",
                "90_degrees": "Looking straight down",
                "convention": "Minecraft pitch convention"
            }
        },

        # ===== 文件结构 =====
        "file_structure": {
            "root_directory": "city_vpr_dataset/",
            "pattern": "speedMode_{id}/route{route_id}/pitch_{pitch_id}/",
            "files_per_task": [
                "PNG image frames (r{route}_pitch{pitch}_{frame}.png)",
                "record.txt (raw trajectory log)",
                "trajectory.csv (structured trajectory data)"
            ],
            "metadata_files": [
                "waypoints.json - 32 navigation waypoints with coordinates",
                "routes.json - 11 route definitions with waypoint sequences",
                "buildings.json - 38 building annotations with corner coordinates",
                "city_map.svg - City map visualization",
                "README.md - Dataset documentation",
                "dataset_metadata.json - This file"
            ]
        },

        # ===== 数据统计 =====
        "statistics": {
            "total_frames": stats['total_frames'],
            "total_tasks": stats['total_tasks'],
            "completed_tasks": stats['completed_tasks'],
            "completion_rate_percent": round(
                100.0 * stats['completed_tasks'] / stats['total_tasks']
                if stats['total_tasks'] > 0 else 0, 1),
            "total_size_gb": round(stats['total_size_bytes'] / (1024**3), 2),
            "total_size_mb": round(stats['total_size_bytes'] / (1024**2), 1),
            "average_frames_per_task": round(
                stats['total_frames'] / stats['completed_tasks'], 0
                if stats['completed_tasks'] > 0 else 0),
            "per_speed_mode": stats['per_speed_mode'],
            "per_route": stats['per_route'],
            "per_pitch": stats['per_pitch'],
        },

        # ===== 轨迹数据格式 =====
        "trajectory_format": {
            "file": "trajectory.csv",
            "format": "CSV with header row",
            "columns": [
                {"name": "frame_name", "type": "string", "description": "Image filename without extension"},
                {"name": "time", "type": "float", "unit": "seconds", "description": "Timestamp relative to task start"},
                {"name": "x", "type": "float", "unit": "meters", "description": "X coordinate (East direction)"},
                {"name": "y", "type": "float", "unit": "meters", "description": "Y coordinate (vertical)"},
                {"name": "z", "type": "float", "unit": "meters", "description": "Z coordinate (South direction)"},
                {"name": "facing", "type": "float", "unit": "degrees", "description": "Yaw angle (Minecraft convention)"},
                {"name": "pitch", "type": "float", "unit": "degrees", "description": "Pitch angle (Minecraft convention)"},
                {"name": "speed", "type": "float", "unit": "m/s", "description": "Walking speed in meters per second"},
            ]
        },

        # ===== 引用 =====
        "citation": "Chen Z. (2026). CityVPR: A Multi-Pitch Multi-Speed Visual Place Recognition Dataset in Minecraft Urban Environment. Scientific Data. [DOI: TBD]",
        "references": [
            {
                "title": "The Malmo Platform for Artificial Intelligence Experimentation",
                "authors": "Johnson M., Hofmann K., Hutton T., Bignell D.",
                "venue": "Proc. 25th International Joint Conference on Artificial Intelligence (IJCAI 2016)",
                "pages": "4246",
                "publisher": "AAAI Press, Palo Alto, California USA",
                "year": 2016,
                "url": "https://github.com/Microsoft/malmo"
            }
        ],

        # ===== 致谢/资助 =====
        "acknowledgments": "The authors thank the developers of Project Malmo for providing the AI experimentation platform used to generate this dataset.",
    }

    return metadata


def main():
    if len(sys.argv) < 2:
        print("用法: py -3.6 generate_metadata.py \"数据集目录路径\"")
        sys.exit(1)

    dataset_root = sys.argv[1]
    if not os.path.isdir(dataset_root):
        print("错误: 目录不存在 - " + dataset_root)
        sys.exit(1)

    print("=" * 60)
    print("生成 dataset_metadata.json")
    print("=" * 60)

    # 加载建筑数据
    buildings_path = os.path.join(dataset_root, "buildings.json")
    buildings = []
    if os.path.exists(buildings_path):
        with open(buildings_path, 'r') as f:
            buildings = json.load(f)
        print("已加载建筑数据: {} 栋".format(len(buildings)))
    else:
        print("[警告] 未找到 buildings.json")

    # 扫描数据集统计
    print("\n扫描数据集统计...")
    stats = scan_dataset_stats(dataset_root)
    print("  总帧数: {:,}".format(stats['total_frames']))
    print("  完成任务: {}/{}".format(stats['completed_tasks'], stats['total_tasks']))
    print("  总大小: {:.2f} GB".format(stats['total_size_bytes'] / (1024**3)))

    # 生成元数据
    print("\n生成元数据...")
    metadata = generate_metadata(dataset_root, stats, buildings)

    # 保存
    output_path = os.path.join(dataset_root, "dataset_metadata.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n生成成功: " + output_path)
    print("=" * 60)
    print("注意: 以下字段为占位符，请手动替换:")
    print("  - authors (作者信息)")
    print("  - citation (引用格式)")
    print("  - acknowledgments (致谢/资助)")
    print("=" * 60)


if __name__ == "__main__":
    main()
