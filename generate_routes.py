# -*- coding: utf-8 -*-
"""
生成 routes.json - 路线元数据
用法: py -3.6 generate_routes.py "D:\path\to\city_vpr_dataset"
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

# ============================================================
# 路径点 (真实世界坐标, 与 waypoints.json 一致)
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

# 11条路线的路径点序列 (与采集代码一致)
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


def calc_distance(p1, p2):
    """计算两点距离 (米 = 格数)"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def generate_routes_json(output_path):
    """生成 routes.json"""
    data = []
    for i, route in enumerate(ROUTES):
        waypoint_list = []
        total_distance = 0.0

        for j, wp_idx in enumerate(route):
            wx, wz = WAYPOINTS[wp_idx]
            waypoint_list.append({
                "waypoint_id": wp_idx,
                "waypoint_name": "W{}".format(wp_idx),
                "world_x": float(wx),
                "world_z": float(wz),
            })
            if j > 0:
                prev = WAYPOINTS[route[j-1]]
                curr = WAYPOINTS[wp_idx]
                total_distance += calc_distance(prev, curr)

        data.append({
            "route_id": i + 1,
            "route_name": ROUTE_NAMES[i],
            "num_waypoints": len(route),
            "total_distance_meters": round(total_distance, 2),
            "waypoints": waypoint_list,
        })

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print("=" * 60)
    print("生成成功: " + output_path)
    print("路线数量: {}".format(len(data)))
    print("=" * 60)

    # 打印每条路线概览
    print("\n路线概览:")
    print("-" * 60)
    print("  {:<10} {:>12} {:>16}".format("路线", "路径点数", "总距离(米)"))
    print("-" * 60)
    for r in data:
        wp_str = "W" + "→W".join(
            str(wp['waypoint_id']) for wp in r['waypoints'][:4])
        if len(r['waypoints']) > 4:
            wp_str += "→..."
        print("  {:<10} {:>12} {:>16.2f}  {}".format(
            r['route_name'], r['num_waypoints'],
            r['total_distance_meters'], wp_str))


def main():
    if len(sys.argv) < 2:
        print("用法: py -3.6 generate_routes.py \"数据集目录路径\"")
        print("例如: py -3.6 generate_routes.py \"D:\\...\\city_vpr_dataset\"")
        sys.exit(1)

    dataset_root = sys.argv[1]
    if not os.path.isdir(dataset_root):
        print("错误: 目录不存在 - " + dataset_root)
        sys.exit(1)

    output_path = os.path.join(dataset_root, "routes.json")
    generate_routes_json(output_path)


if __name__ == "__main__":
    main()
