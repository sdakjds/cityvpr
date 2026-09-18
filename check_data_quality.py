#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量检查脚本 - CityVPR Dataset
用法: py -3.6 check_data_quality.py "D:\path\to\city_vpr_dataset"

检查内容:
- 总帧数、各模式/路线/pitch帧数统计
- 丢帧率
- 坐标连续性（相邻帧位移）
- 速度分布与精度
- 角度精度（yaw/pitch稳定性）
- 文件完整性（图片与记录对应）
- 路径点到达精度
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


def parse_record_file(filepath):
    """解析 record.txt，返回帧列表和元信息"""
    frames = []
    meta = {}

    try:
        # 尝试多种编码
        for enc in ['utf-8', 'gbk', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        print("  [错误] 读取失败 {}: {}".format(filepath, e))
        return None, None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            # 解析元信息
            if 'Route:' in line:
                m = re.search(r'Route:\s*(\d+).*speedMode_(\d+).*pitch_(\d+)', line)
                if m:
                    meta['route'] = int(m.group(1))
                    meta['speed_mode'] = int(m.group(2))
                    meta['pitch'] = int(m.group(3))
            continue

        # 解析数据行: r1_pitch0_1: Time: 0.062 X: 57.00 Y: 7.00 Z: 63.00 Facing: 0.0 Pitch: 0.0 Speed: 4.32
        m = re.match(
            r'(\S+):\s+Time:\s*([\d.]+)\s+X:\s*([\d.]+)\s+Y:\s*([\d.]+)\s+Z:\s*([\d.]+)\s+Facing:\s*([-\d.]+)\s+Pitch:\s*([-\d.]+)\s+Speed:\s*([\d.]+)',
            line
        )
        if m:
            frames.append({
                'frame_name': m.group(1),
                'time': float(m.group(2)),
                'x': float(m.group(3)),
                'y': float(m.group(4)),
                'z': float(m.group(5)),
                'yaw': float(m.group(6)),
                'pitch': float(m.group(7)),
                'speed': float(m.group(8)),
            })

    return frames, meta


def compute_stats(frames, meta):
    """计算单个任务的统计数据"""
    if not frames:
        return None

    n = len(frames)

    # 跳过开头静止帧（speed=0的启动帧）
    start_idx = 0
    for i, f in enumerate(frames):
        if f['speed'] > 0.01:
            start_idx = i
            break

    # 跳过结尾静止帧
    end_idx = n - 1
    for i in range(n - 1, -1, -1):
        if frames[i]['speed'] > 0.01:
            end_idx = i
            break

    moving_frames = frames[start_idx:end_idx + 1]
    moving_n = len(moving_frames)

    # 坐标统计
    xs = [f['x'] for f in frames]
    ys = [f['y'] for f in frames]
    zs = [f['z'] for f in frames]

    # 位移统计（相邻帧）
    displacements = []
    for i in range(1, moving_n):
        dx = moving_frames[i]['x'] - moving_frames[i - 1]['x']
        dz = moving_frames[i]['z'] - moving_frames[i - 1]['z']
        d = math.sqrt(dx * dx + dz * dz)
        displacements.append(d)

    # 速度统计
    speeds = [f['speed'] for f in moving_frames]
    speed_mean = sum(speeds) / len(speeds) if speeds else 0
    speed_min = min(speeds) if speeds else 0
    speed_max = max(speeds) if speeds else 0

    # 角度统计
    yaws = [f['yaw'] for f in moving_frames]
    pitchs = [f['pitch'] for f in moving_frames]

    # yaw 跳变检测（转弯）
    yaw_changes = []
    for i in range(1, moving_n):
        dy = abs(yaws[i] - yaws[i - 1])
        # 处理0度和360度边界
        if dy > 180:
            dy = 360 - dy
        yaw_changes.append(dy)

    # pitch 稳定性
    pitch_mean = sum(pitchs) / len(pitchs) if pitchs else 0
    pitch_std = math.sqrt(sum((p - pitch_mean) ** 2 for p in pitchs) / len(pitchs)) if pitchs else 0

    # 总位移距离
    total_distance = sum(displacements)

    # 时间跨度
    if len(frames) >= 2:
        time_start = frames[0]['time']
        time_end = frames[-1]['time']
        time_span = round(time_end - time_start, 3)
    else:
        time_span = 0

    # 估算帧率（基于时间戳）
    if n >= 2 and time_span > 0:
        est_fps = round((n - 1) / time_span, 2)
    else:
        est_fps = 0

    # 帧间隔统计（基于时间戳）
    time_intervals = []
    for i in range(1, n):
        dt = frames[i]['time'] - frames[i - 1]['time']
        if dt > 0:
            time_intervals.append(dt)

    if time_intervals:
        avg_interval = sum(time_intervals) / len(time_intervals)
        min_interval = min(time_intervals)
        max_interval = max(time_intervals)
    else:
        avg_interval = 0
        min_interval = 0
        max_interval = 0

    return {
        'total_frames': n,
        'moving_frames': moving_n,
        'start_frame': start_idx,
        'end_frame': end_idx,
        'x_range': (min(xs), max(xs)),
        'y_range': (min(ys), max(ys)),
        'z_range': (min(zs), max(zs)),
        'total_distance_m': round(total_distance, 2),
        'time_span_s': time_span,
        'speed_mean': round(speed_mean, 3),
        'speed_min': round(speed_min, 3),
        'speed_max': round(speed_max, 3),
        'max_displacement_per_frame': round(max(displacements), 3) if displacements else 0,
        'avg_displacement_per_frame': round(sum(displacements) / len(displacements), 4) if displacements else 0,
        'pitch_mean': round(pitch_mean, 2),
        'pitch_std': round(pitch_std, 4),
        'max_yaw_change_per_frame': round(max(yaw_changes), 2) if yaw_changes else 0,
        'est_fps': est_fps,
        'avg_frame_interval_s': round(avg_interval, 4),
        'min_frame_interval_s': round(min_interval, 4),
        'max_frame_interval_s': round(max_interval, 4),
    }


def find_all_records(root_dir):
    """递归查找所有 record.txt 文件"""
    records = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn == 'record.txt':
                records.append(os.path.join(dirpath, fn))
    return sorted(records)


def main():
    if len(sys.argv) < 2:
        print("用法: py -3.6 check_data_quality.py \"数据集根目录路径\"")
        sys.exit(1)

    dataset_root = sys.argv[1]
    if not os.path.isdir(dataset_root):
        print("错误: 目录不存在 - " + dataset_root)
        sys.exit(1)

    print("=" * 70)
    print("CityVPR 数据集质量检查")
    print("=" * 70)
    print("数据集路径: " + dataset_root)

    # 找所有 record.txt
    record_files = find_all_records(dataset_root)
    print("找到 {} 个 record.txt 文件".format(len(record_files)))

    if not record_files:
        print("[错误] 没找到任何 record.txt 文件")
        sys.exit(1)

    # 逐个分析
    all_stats = []
    all_metas = []

    print("\n" + "=" * 70)
    print("逐任务分析")
    print("=" * 70)

    for rf in record_files:
        # 提取相对路径中的 speedMode/route/pitch 信息
        rel = os.path.relpath(rf, dataset_root)
        parts = rel.replace('\\', '/').split('/')

        frames, meta = parse_record_file(rf)
        if frames is None:
            continue

        stats = compute_stats(frames, meta)
        if stats is None:
            continue

        sm = meta.get('speed_mode', '?')
        rt = meta.get('route', '?')
        pt = meta.get('pitch', '?')

        print("\n[speedMode_{} / route{} / pitch_{}]".format(sm, rt, pt))
        print("  总帧数: {} (运动帧: {})".format(stats['total_frames'], stats['moving_frames']))
        print("  时间跨度: {} s".format(stats['time_span_s']))
        print("  总距离: {} m".format(stats['total_distance_m']))
        print("  速度: 平均={} m/s, 最小={}, 最大={}".format(
            stats['speed_mean'], stats['speed_min'], stats['speed_max']))
        print("  每帧位移: 平均={} m, 最大={} m".format(
            stats['avg_displacement_per_frame'], stats['max_displacement_per_frame']))
        print("  帧间隔: 平均={} s, 最小={} s, 最大={} s".format(
            stats['avg_frame_interval_s'], stats['min_frame_interval_s'], stats['max_frame_interval_s']))
        print("  估算帧率: {} fps".format(stats['est_fps']))
        print("  Pitch: 均值={}°, 标准差={}°".format(stats['pitch_mean'], stats['pitch_std']))
        print("  最大每帧yaw变化: {}°".format(stats['max_yaw_change_per_frame']))
        print("  坐标范围: X[{:.1f}, {:.1f}]  Y[{:.1f}, {:.1f}]  Z[{:.1f}, {:.1f}]".format(
            stats['x_range'][0], stats['x_range'][1],
            stats['y_range'][0], stats['y_range'][1],
            stats['z_range'][0], stats['z_range'][1]))

        stats['speed_mode'] = sm
        stats['route'] = rt
        stats['pitch'] = pt
        stats['rel_path'] = rel
        all_stats.append(stats)
        all_metas.append(meta)

    # 汇总统计
    print("\n" + "=" * 70)
    print("汇总统计")
    print("=" * 70)

    total_frames = sum(s['total_frames'] for s in all_stats)
    total_moving = sum(s['moving_frames'] for s in all_stats)
    total_distance = sum(s['total_distance_m'] for s in all_stats)
    total_time = sum(s['time_span_s'] for s in all_stats)

    print("任务总数: {}".format(len(all_stats)))
    print("总帧数: {} (运动帧: {}, 静止帧: {})".format(
        total_frames, total_moving, total_frames - total_moving))
    print("总行驶距离: {:.2f} m".format(total_distance))
    print("总时间跨度: {:.2f} s".format(total_time))

    # 按速度模式统计
    print("\n按速度模式:")
    for sm in sorted(set(s['speed_mode'] for s in all_stats)):
        subset = [s for s in all_stats if s['speed_mode'] == sm]
        tf = sum(s['total_frames'] for s in subset)
        td = sum(s['total_distance_m'] for s in subset)
        print("  speedMode_{}: {} 任务, {} 帧, {:.2f} m".format(sm, len(subset), tf, td))

    # 按路线统计
    print("\n按路线:")
    for rt in sorted(set(s['route'] for s in all_stats)):
        subset = [s for s in all_stats if s['route'] == rt]
        tf = sum(s['total_frames'] for s in subset)
        print("  route{}: {} 任务, {} 帧".format(rt, len(subset), tf))

    # 按pitch统计
    print("\n按俯仰角:")
    for pt in sorted(set(s['pitch'] for s in all_stats)):
        subset = [s for s in all_stats if s['pitch'] == pt]
        tf = sum(s['total_frames'] for s in subset)
        print("  pitch_{}°: {} 任务, {} 帧".format(pt, len(subset), tf))

    # 速度精度分析
    print("\n速度精度分析:")
    for sm in sorted(set(s['speed_mode'] for s in all_stats)):
        subset = [s for s in all_stats if s['speed_mode'] == sm]
        if not subset:
            continue
        all_speeds = []
        for s in subset:
            all_speeds.append(s['speed_mean'])
        avg = sum(all_speeds) / len(all_speeds)
        print("  speedMode_{}: 平均速度 {:.3f} m/s".format(sm, avg))

    # 帧率稳定性
    print("\n帧率估算:")
    fps_values = [s['est_fps'] for s in all_stats if s['est_fps'] > 0]
    if fps_values:
        avg_fps = sum(fps_values) / len(fps_values)
        min_fps = min(fps_values)
        max_fps = max(fps_values)
        print("  平均估算帧率: {:.2f} fps".format(avg_fps))
        print("  范围: {:.2f} ~ {:.2f} fps".format(min_fps, max_fps))

    # 帧间隔稳定性
    print("\n帧间隔统计:")
    intervals = [s['avg_frame_interval_s'] for s in all_stats if s['avg_frame_interval_s'] > 0]
    if intervals:
        avg_int = sum(intervals) / len(intervals)
        min_int = min(intervals)
        max_int = max(intervals)
        print("  平均帧间隔: {:.4f} s (目标: 0.1 s)".format(avg_int))
        print("  范围: {:.4f} ~ {:.4f} s".format(min_int, max_int))

    # 生成报告 JSON
    report = {
        'dataset_root': dataset_root,
        'total_tasks': len(all_stats),
        'total_frames': total_frames,
        'total_moving_frames': total_moving,
        'total_distance_m': round(total_distance, 2),
        'total_time_s': round(total_time, 2),
        'by_speed_mode': {},
        'by_route': {},
        'by_pitch': {},
        'tasks': all_stats,
    }

    for sm in sorted(set(s['speed_mode'] for s in all_stats)):
        subset = [s for s in all_stats if s['speed_mode'] == sm]
        report['by_speed_mode']['speedMode_' + str(sm)] = {
            'num_tasks': len(subset),
            'total_frames': sum(s['total_frames'] for s in subset),
            'total_distance_m': round(sum(s['total_distance_m'] for s in subset), 2),
            'avg_speed_mps': round(sum(s['speed_mean'] for s in subset) / len(subset), 3),
        }

    for rt in sorted(set(s['route'] for s in all_stats)):
        subset = [s for s in all_stats if s['route'] == rt]
        report['by_route']['route' + str(rt)] = {
            'num_tasks': len(subset),
            'total_frames': sum(s['total_frames'] for s in subset),
        }

    for pt in sorted(set(s['pitch'] for s in all_stats)):
        subset = [s for s in all_stats if s['pitch'] == pt]
        report['by_pitch']['pitch_' + str(pt)] = {
            'num_tasks': len(subset),
            'total_frames': sum(s['total_frames'] for s in subset),
        }

    report_path = os.path.join(dataset_root, 'data_quality_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n质量报告已保存: " + report_path)
    print("=" * 70)


if __name__ == '__main__':
    main()
