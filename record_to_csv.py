#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
record_to_csv.py
将 multi_pitch_collector.py 生成的 record.txt 转换为 trajectory.csv。

record.txt 行格式（每帧一行）：
  r1_pitch0_1:   Time:   0.062  X:   57.00  Y:    7.00  Z:   63.00    Facing:   0.0    Pitch:   0.0    Speed:  0.00

输出 CSV 列: frame_name,time,x,y,z,facing,pitch,speed
"""

import csv
import os
import re
import sys

PATTERN = re.compile(
    r'(\S+?):\s+'          # frame_name
    r'Time:\s+([\d.]+)\s+'  # time
    r'X:\s+([\d.]+)\s+'     # x
    r'Y:\s+([\d.]+)\s+'     # y
    r'Z:\s+([\d.]+)\s+'     # z
    r'Facing:\s+([\d.]+)\s+'  # facing
    r'Pitch:\s+([\d.]+)\s+'   # pitch
    r'Speed:\s+([\d.]+)'       # speed
)


def convert(record_path, csv_path=None):
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(record_path), 'trajectory.csv')

    rows = []
    with open(record_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = PATTERN.search(line)
            if not m:
                continue
            rows.append(m.groups())

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['frame_name', 'time', 'x', 'y', 'z', 'facing', 'pitch', 'speed'])
        writer.writerows(rows)

    print('trajectory.csv written to: {}'.format(csv_path))
    print('Total frames: {}'.format(len(rows)))
    if rows:
        print('First frame: {}'.format(rows[0][0]))
        print('Last frame:  {}'.format(rows[-1][0]))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python record_to_csv.py <record.txt | directory>')
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        # 批量处理目录下所有 record.txt
        for root, dirs, files in os.walk(target):
            for fname in files:
                if fname == 'record.txt':
                    convert(os.path.join(root, fname))
    else:
        convert(target)
