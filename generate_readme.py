# -*- coding: utf-8 -*-
"""
生成 README.md - 数据集说明文档
用法: py -3.6 generate_readme.py "D:\path\to\city_vpr_dataset"
"""

from __future__ import print_function
import os
import sys
import json
import math

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
else:
    import functools
    print = functools.partial(print, flush=True)

SPEED_MODES = [
    {"id": 1, "name": "speedMode_1", "type": "constant", "move_value": 1.0,
     "speed_mps": 4.32, "desc": "Constant 4.32 (normal walking)"},
    {"id": 2, "name": "speedMode_2", "type": "constant", "move_value": 0.6,
     "speed_mps": 2.59, "desc": "Constant 2.59 (slow walking)"},
    {"id": 3, "name": "speedMode_3", "type": "accelerating",
     "speed_start": 2.59, "speed_max": 5.18,
     "desc": "Accelerating 2.59 to 5.18"},
]

PITCH_ANGLES = [
    {"name": "pitch_0",  "value": 0,  "desc": "Forward (horizontal)"},
    {"name": "pitch_30", "value": 30, "desc": "30 degrees downward"},
    {"name": "pitch_60", "value": 60, "desc": "60 degrees downward"},
    {"name": "pitch_90", "value": 90, "desc": "Straight down"},
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


def scan_stats(dataset_root):
    """扫描统计"""
    stats = {
        "total_frames": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_size_bytes": 0,
        "per_sm": {},
        "per_route": {},
        "per_pitch": {},
    }
    for sm in SPEED_MODES:
        stats['per_sm'][sm['name']] = {"frames": 0}
    for rn in ROUTE_NAMES:
        stats['per_route'][rn] = {"frames": 0}
    for pa in PITCH_ANGLES:
        stats['per_pitch'][pa['name']] = {"frames": 0}

    for sm in SPEED_MODES:
        sm_dir = os.path.join(dataset_root, sm['name'])
        if not os.path.isdir(sm_dir):
            continue
        for rn in ROUTE_NAMES:
            route_dir = os.path.join(sm_dir, rn)
            if not os.path.isdir(route_dir):
                continue
            for pa in PITCH_ANGLES:
                pitch_dir = os.path.join(route_dir, pa['name'])
                if not os.path.isdir(pitch_dir):
                    continue
                record_path = os.path.join(pitch_dir, "record.txt")
                if os.path.exists(record_path):
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
                    stats['per_sm'][sm['name']]['frames'] += frames
                    stats['per_route'][rn]['frames'] += frames
                    stats['per_pitch'][pa['name']]['frames'] += frames
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


def calc_distance(route):
    d = 0.0
    for i in range(1, len(route)):
        x1, z1 = WAYPOINTS[route[i-1]]
        x2, z2 = WAYPOINTS[route[i]]
        d += math.sqrt((x2-x1)**2 + (z2-z1)**2)
    return round(d, 2)


def generate_readme(dataset_root, stats):
    total_dist = sum(calc_distance(r) for r in ROUTES)

    lines = []
    w = lines.append

    w("# CityVPR Dataset")
    w("")
    w("> A Multi-Pitch Multi-Speed Visual Place Recognition Dataset in Minecraft Urban Environment")
    w("")
    w("---")
    w("")

    # 1. Overview
    w("## Overview")
    w("")
    w("CityVPR is a synthetic visual place recognition (VPR) dataset collected in a carefully designed Minecraft-based virtual city environment. It provides first-person RGB images from 11 distinct navigation routes, captured at 4 different pitch angles and 3 different speed modes, with precise pose information for each frame.")
    w("")
    w("| Property | Value |")
    w("|----------|-------|")
    w("| Total frames | {:,} |".format(stats['total_frames']))
    w("| Navigation routes | {} |".format(len(ROUTES)))
    w("| Waypoints | {} |".format(len(WAYPOINTS)))
    w("| Pitch angles | {} (0, 30, 60, 90) |".format(len(PITCH_ANGLES)))
    w("| Speed modes | {} |".format(len(SPEED_MODES)))
    w("| Tasks (complete) | {}/{} |".format(stats['completed_tasks'], stats['total_tasks']))
    w("| Total size | {:.2f} GB |".format(stats['total_size_bytes'] / (1024**3)))
    w("| Image resolution | 1280 x 720 |")
    w("| Frame rate | 10 fps |")
    w("| Image format | PNG |")
    w("| City size | 100 m x 100 m |")
    w("| Buildings | 38 |")
    w("")

    # 2. Directory Structure
    w("## Directory Structure")
    w("")
    w("```")
    w("city_vpr_dataset/")
    w("├── speedMode_1/          # Constant 4.32")
    w("│   ├── route1/")
    w("│   │   ├── pitch_0/      # Forward view")
    w("│   │   │   ├── *.png     # Image frames")
    w("│   │   │   ├── record.txt")
    w("│   │   │   └── trajectory.csv")
    w("│   │   ├── pitch_30/")
    w("│   │   ├── pitch_60/")
    w("│   │   └── pitch_90/")
    w("│   ├── route2/")
    w("│   └── ... (route3 ~ route11)")
    w("├── speedMode_2/          # Constant 2.59")
    w("├── speedMode_3/          # Accelerating 2.59~5.18")
    w("├── waypoints.json        # 32 waypoint coordinates")
    w("├── routes.json           # 11 route definitions")
    w("├── buildings.json        # 38 building annotations")
    w("├── city_map.svg          # City map visualization")
    w("├── route_maps/           # 11 route visualization SVGs")
    w("├── dataset_metadata.json # Structured metadata")
    w("├── data_quality_report.txt")
    w("└── README.md             # This file")
    w("```")
    w("")

    # 3. Coordinate System
    w("## Coordinate System")
    w("")
    w("The dataset uses Minecraft's coordinate convention:")
    w("")
    w("- **X axis**: East direction (positive = right)")
    w("- **Y axis**: Vertical direction (positive = up)")
    w("- **Z axis**: South direction (positive = forward when facing South)")
    w("- **Yaw**: 0 = South, 90 = West, 180 = North, 270 = East (clockwise)")
    w("- **Pitch**: 0 = horizontal, positive = looking downward, 90 = straight down")
    w("- **Units**: meters (1 block = 1 meter)")
    w("- **Ground level**: y = 7")
    w("")

    # 4. Speed Modes
    w("## Speed Modes")
    w("")
    w("| Mode | Type | Speed | Description |")
    w("|------|------|-------|-------------|")
    for sm in SPEED_MODES:
        if sm['type'] == 'constant':
            w("| {} | {} | {:.2f} | {} |".format(
                sm['name'], sm['type'], sm['speed_mps'], sm['desc']))
        else:
            w("| {} | {} | {:.2f} ~ {:.2f} | {} |".format(
                sm['name'], sm['type'], sm['speed_start'], sm['speed_max'], sm['desc']))
    w("")

    # 5. Pitch Angles
    w("## Pitch Angles")
    w("")
    w("| Name | Pitch | Description |")
    w("|------|-------|-------------|")
    for pa in PITCH_ANGLES:
        w("| {} | {} | {} |".format(pa['name'], pa['value'], pa['desc']))
    w("")

    # 6. Routes
    w("## Routes")
    w("")
    w("| Route | Waypoints | Distance (m) |")
    w("|-------|-----------|-------------|")
    for i, route in enumerate(ROUTES):
        w("| route{} | {} | {:.1f} |".format(i+1, len(route), calc_distance(route)))
    w("| **Total** | - | **{:.1f}** |".format(total_dist))
    w("")

    # 7. File Formats
    w("## File Formats")
    w("")
    w("### trajectory.csv")
    w("")
    w("Structured trajectory data for each navigation task. Columns:")
    w("")
    w("| Column | Type | Unit | Description |")
    w("|--------|------|------|-------------|")
    w("| frame_name | string | - | Image filename without extension |")
    w("| time | float | s | Timestamp relative to task start |")
    w("| x | float | m | X coordinate (East) |")
    w("| y | float | m | Y coordinate (vertical) |")
    w("| z | float | m | Z coordinate (South) |")
    w("| facing | float | deg | Yaw angle (Minecraft convention) |")
    w("| pitch | float | deg | Pitch angle (Minecraft convention) |")
    w("| speed | float | blocks/s | Walking speed |")
    w("")
    w("### waypoints.json")
    w("")
    w("32 navigation waypoints with world coordinates. Each waypoint has:")
    w("- `waypoint_id`: W0 ~ W31")
    w("- `name`: e.g., W0")
    w("- `world_x`, `world_z`: world coordinates (meters)")
    w("- `y`: ground level (7.0)")
    w("")
    w("### routes.json")
    w("")
    w("11 route definitions. Each route has:")
    w("- `route_id`, `route_name`")
    w("- `num_waypoints`: number of waypoints")
    w("- `total_distance_meters`: route length")
    w("- `waypoints`: ordered list of waypoint objects")
    w("")
    w("### buildings.json")
    w("")
    w("38 building annotations. Each building has:")
    w("- `building_id`: B01 ~ B38")
    w("- `name`: building name")
    w("- `corner_nw`, `corner_ne`, `corner_sw`, `corner_se`: four corner coordinates")
    w("- `width_blocks`, `depth_blocks`, `area_blocks`: size")
    w("")

    # 8. Statistics
    w("## Dataset Statistics")
    w("")
    w("### Frames per Speed Mode")
    w("")
    w("| Speed Mode | Frames |")
    w("|------------|--------|")
    for sm in SPEED_MODES:
        w("| {} | {:,} |".format(sm['name'], stats['per_sm'][sm['name']]['frames']))
    w("")
    w("### Frames per Pitch Angle")
    w("")
    w("| Pitch | Frames |")
    w("|-------|--------|")
    for pa in PITCH_ANGLES:
        w("| {} | {:,} |".format(pa['name'], stats['per_pitch'][pa['name']]['frames']))
    w("")
    w("### Frames per Route")
    w("")
    w("| Route | Frames |")
    w("|-------|--------|")
    for rn in ROUTE_NAMES:
        w("| {} | {:,} |".format(rn, stats['per_route'][rn]['frames']))
    w("")

    # 9. Citation
    w("## Citation")
    w("")
    w("If you use this dataset in your research, please cite:")
    w("")
    w("```")
    w("Chen, Zugang. A multi-pitch multi-speed dataset for embodied spatial")
    w("cognition evaluation in a virtual urban environment. Figshare (2026).")
    w("https://doi.org/10.6084/m9.figshare.33944731")
    w("```")
    w("")
    w("Also please cite the Malmo platform:")
    w("")
    w("```")
    w("Johnson M., Hofmann K., Hutton T., Bignell D. (2016) The Malmo Platform for")
    w("Artificial Intelligence Experimentation. Proc. 25th International Joint")
    w("Conference on Artificial Intelligence, Ed. Kambhampati S., p. 4246.")
    w("AAAI Press, Palo Alto, California USA.")
    w("https://github.com/Microsoft/malmo")
    w("```")
    w("")

    # 10. License
    w("## License")
    w("")
    w("This dataset is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).")
    w("")
    w("You are free to:")
    w("- Share — copy and redistribute the material in any medium or format")
    w("- Adapt — remix, transform, and build upon the material for any purpose")
    w("")
    w("Under the following terms:")
    w("- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.")
    w("")

    # 11. Contact
    w("## Contact")
    w("")
    w("For questions about the dataset, please contact:")
    w("")
    w("- **Zugang Chen** (Corresponding Author)")
    w("  - Aerospace Information Research Institute, Chinese Academy of Sciences")
    w("  - Email: 15039802183@163.com")
    w("")

    # 12. Acknowledgments
    w("## Acknowledgments")
    w("")
    w("The authors thank the developers of Project Malmo for providing the AI experimentation platform used to generate this dataset.")
    w("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: py -3.6 generate_readme.py \"数据集目录路径\"")
        sys.exit(1)

    dataset_root = sys.argv[1]
    if not os.path.isdir(dataset_root):
        print("错误: 目录不存在 - " + dataset_root)
        sys.exit(1)

    print("=" * 60)
    print("生成 README.md")
    print("=" * 60)

    print("\n扫描数据集统计...")
    stats = scan_stats(dataset_root)
    print("  总帧数: {:,}".format(stats['total_frames']))
    print("  完成任务: {}/{}".format(stats['completed_tasks'], stats['total_tasks']))

    print("\n生成 README.md...")
    content = generate_readme(dataset_root, stats)

    output_path = os.path.join(dataset_root, "README.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  生成成功: " + output_path)
    print("=" * 60)


if __name__ == "__main__":
    main()
