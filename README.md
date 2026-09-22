# CityVPR Dataset Tools

Collection of scripts for generating and analyzing the **CityVPR Dataset** — a multi-pitch multi-speed dataset for embodied spatial cognition evaluation in a virtual urban environment.

## Dataset

The full dataset (57,349 frames, ~12.25 GB) is archived on Figshare:

> **DOI:** [10.6084/m9.figshare.33944731](https://doi.org/10.6084/m9.figshare.33944731)

The Minecraft world save (100 x 100 map) is available in this GitHub repository. To use it, paste the save folder into:
```
Malmo\Malmo-0.36.0-Windows-64bit_withBoost_Python3.6\Minecraft\run\saves
```

## Requirements

- Python 3.6+ (tested with Python 3.6 on Windows)
- [Project Malmo](https://github.com/Microsoft/malmo) (only needed for data collection)

## Scripts

### Data Collection

| Script | Description |
|--------|-------------|
| `multi_pitch_collector.py` | Main data collection agent — navigates 11 routes x 4 pitch angles x 3 speed modes in the Minecraft city, capturing RGB frames at 10 fps |

### Data Processing

| Script | Description |
|--------|-------------|
| `record_to_csv.py` | Converts `record.txt` to `trajectory.csv` with columns: frame_name, time, x, y, z, facing, pitch, speed |
| `generate_metadata.py` | Generates `dataset_metadata.json` with structured dataset metadata |
| `generate_readme.py` | Generates `README.md` for the dataset directory |

### Visualization

| Script | Description |
|--------|-------------|
| `generate_waypoints.py` | Generates `waypoints.json` (32 waypoint coordinates) |
| `generate_routes.py` | Generates `routes.json` (11 route definitions) |
| `generate_city_map.py` | Generates `city_map.svg` — full city map with roads, buildings, and waypoints |
| `generate_route_maps.py` | Generates 11 individual route SVGs in `route_maps/` directory |

### Quality Check

| Script | Description |
|--------|-------------|
| `check_data_quality.py` | Validates data quality — frame counts, coordinate continuity, speed distribution, frame rate stability |

## Usage

### Collect data (requires Malmo)

```bash
py -3.6 multi_pitch_collector.py
```

### Batch convert record.txt to trajectory.csv

```bash
py -3.6 record_to_csv.py "D:\path\to\city_vpr_dataset"
```

### Generate metadata and documentation

```bash
py -3.6 generate_metadata.py "D:\path\to\city_vpr_dataset"
py -3.6 generate_readme.py "D:\path\to\city_vpr_dataset"
```

### Generate visualizations

```bash
py -3.6 generate_city_map.py "D:\path\to\city_vpr_dataset"
py -3.6 generate_route_maps.py "D:\path\to\city_vpr_dataset"
```

### Run quality check

```bash
py -3.6 check_data_quality.py "D:\path\to\city_vpr_dataset"
```

## Custom Data Collection

To collect your own data using this codebase, modify `multi_pitch_collector.py` and run it with the Malmo environment.

### 1. Install Project Malmo

Download and install [Project Malmo](https://github.com/Microsoft/malmo) (Minecraft 1.11.2 + Python 3.6). See the [Malmo documentation](https://github.com/Microsoft/malmo/blob/master/doc/install_windows.md) for Windows setup.

### 2. Load the CityVPR world save

The Minecraft world save (100x100map) is included in this GitHub repository. Paste the `100x100map` save folder into:
```
Malmo\Malmo-0.36.0-Windows-64bit_withBoost_Python3.6\Minecraft\run\saves
```

The city includes 32 predefined waypoints (W0–W31). Their coordinates are defined in the `WAYPOINTS` list in `multi_pitch_collector.py`:

```python
WAYPOINTS = [
    (41, 63), (57, 63), (68, 63), (79, 63), (26, 63),
    (34, 82), (41, 82), (45, 82), (57, 82), (68, 82),
    (79, 82), (79, 90), (78, 98), (34, 102), (45, 102),
    (57, 102), (68, 102), (76, 102), (87, 102), (34, 112),
    (67, 113), (30, 116), (57, 123), (14, 57), (14, 82),
    (14, 115), (87, 89), (90, 89), (90, 63), (5, 142),
    (68, 141), (87, 141),
]
```

The `GRAPH` dictionary in the same file defines the connectivity between waypoints for reference when designing routes. The agent navigates directly between consecutive waypoints in each route, so any sequence of valid indices can be used.

### 3. Define custom routes

In `multi_pitch_collector.py`, edit the `ROUTES` list to add your own routes. Each route is a list of waypoint indices (0-based) that the agent will visit sequentially:

```python
ROUTES = [
    [1, 8, 10, 11, 12, 17, 20, 22],   # route1 (original)
    [21, 19, 13, 5, 7, 8, 15, 22],    # route2 (original)
    # ... existing routes 3-11 ...
    # Add your own:
    [0, 6, 5, 13, 15, 22],            # custom route12
    [4, 0, 1, 2, 3, 10, 11],          # custom route13
]
ROUTE_NAMES = ["route1", "route2", ..., "route11", "route12", "route13"]
```

The script automatically validates that all waypoint indices are in range (0–31) at startup.

### 4. Configure speed modes and pitch angles (optional)

The default configuration defines 3 speed modes and 4 pitch angles. Modify `SPEED_MODES` and `PITCH_ANGLES` in `multi_pitch_collector.py` to customize:

```python
BASE_WALK_SPEED = 4.317  # Minecraft base walking speed (blocks/sec at move=1.0)

SPEED_MODES = [
    {'id': 1, 'name': 'speedMode_1', 'type': 'constant', 'base_speed': 1.0, 'desc': 'constant 1.0'},
    {'id': 2, 'name': 'speedMode_2', 'type': 'constant', 'base_speed': 0.6, 'desc': 'constant 0.6'},
    {'id': 3, 'name': 'speedMode_3', 'type': 'accel', 'base_speed': 0.6, 'increment': 0.2, 'max_speed': 1.2, 'desc': '0.6 start +0.2 max 1.2'},
]

PITCH_ANGLES = [
    {'name': '90', 'mc_pitch': 90, 'desc': 'straight down'},
    {'name': '60', 'mc_pitch': 60, 'desc': '60 degrees downward'},
    {'name': '30', 'mc_pitch': 30, 'desc': '30 degrees downward'},
    {'name': '0',  'mc_pitch': 0,  'desc': 'forward'},
]

CAPTURE_INTERVAL = 0.1   # 10 fps
# Resolution is set in Mission XML: 1280 x 720
```

- `base_speed` is the Malmo `move` command value. Actual speed = `base_speed * BASE_WALK_SPEED`.
- For `accel` type, speed increases by `increment` at each waypoint passed, up to `max_speed`.
- Speeds above 1.0 automatically apply speed potions via `/effect` commands.

### 5. Configure output directory (optional)

By default, frames are saved to `city_vpr_dataset/` in the following structure:

```
city_vpr_dataset/
  └── speedMode_X/
      └── routeY/
          └── pitch_Z/
              ├── rY_pitchZ_1.png
              ├── rY_pitchZ_2.png
              ├── ...
              └── record.txt
```

To change the output root, modify `FRAME_ROOT` in `multi_pitch_collector.py`:

```python
FRAME_ROOT = "city_vpr_dataset"
```

### 6. Run collection

Full collection (all routes x pitch angles x speed modes):

```bash
py -3.6 multi_pitch_collector.py
```

Test a single task (route and speed are 1-indexed, pitch is the angle value):

```bash
py -3.6 multi_pitch_collector.py --test route=1 speed=1 pitch=0
```

The script automatically:
- Enables cheats in the world save (for `/tp` and `/effect` commands)
- Teleports the agent to the starting waypoint with correct yaw and pitch
- Navigates between waypoints using a turn-then-move state machine
- Captures frames at 10 fps using a background save thread
- Records timestamp, XYZ, yaw, pitch, and speed to `record.txt`

### 7. Post-processing

After collection, run the processing scripts on the output directory:

```bash
py -3.6 record_to_csv.py "city_vpr_dataset"
py -3.6 generate_metadata.py "city_vpr_dataset"
py -3.6 generate_readme.py "city_vpr_dataset"
py -3.6 check_data_quality.py "city_vpr_dataset"
```

## Dataset Structure

```
Dataset Statistics:
  Total frames: 57,349
  Navigation tasks: 132 (11 routes x 4 pitch angles x 3 speed modes)
  Total size: ~12.25 GB
  Image resolution: 1280 x 720 (PNG)
  Frame rate: 10 fps
  City size: 100 x 100 m
  Buildings: 38
  Waypoints: 32

Speed Modes:
  sm1 = constant 4.32
  sm2 = constant 2.59
  sm3 = accelerating from 2.59 to 5.18

File naming:
  city_vpr_smi_routej.zip  (i = speed mode 1-3, j = route 1-11)
  city_vpr_metadata.zip    (auxiliary files)

city_vpr_metadata.zip
  ├── route_maps/              # 11 route map SVGs (top-down view)
  ├── buildings.json           # Building positions and dimensions
  ├── city_map.svg             # City road map (top-down view)
  ├── data_quality_report.json # Quality check report
  ├── dataset_metadata.json    # Structured metadata
  ├── README.md
  ├── routes.json              # Waypoint sequence for each of 11 routes
  └── waypoints.json           # 32 waypoint coordinates

city_vpr_smi_routej.zip (e.g. city_vpr_sm1_route1.zip)
  ├── pitch_0/                 # Forward horizontal
  │   ├── r1_pitch0_1.png      # Image frames
  │   ├── ...
  │   ├── record.txt           # timestamp, XYZ, facing, pitch, speed
  │   └── trajectory.csv      # frame_name, time, x, y, z, facing, pitch, speed
  ├── pitch_30/                # 30 degrees downward (same structure)
  ├── pitch_60/                # 60 degrees downward (same structure)
  └── pitch_90/                # Straight down (same structure)

Trajectory Data Format (trajectory.csv):
  frame_name | time(s) | x | y | z | facing(deg) | pitch(deg) | speed

Data Collection Platform:
  Collected using Project Malmo (Microsoft) in Minecraft 1.11.2
```

## Citation

If you use this dataset or code in your research, please cite:

```
Chen, Zugang. A multi-pitch multi-speed dataset for embodied spatial cognition evaluation in a virtual urban environment. Figshare (2026). https://doi.org/10.6084/m9.figshare.33944731
```

Also cite the Malmo platform:

```
Johnson M., Hofmann K., Hutton T., Bignell D. (2016) The Malmo Platform for Artificial Intelligence Experimentation. Proc. 25th International Joint Conference on Artificial Intelligence, Ed. Kambhampati S., p. 4246. AAAI Press, Palo Alto, California USA. https://github.com/Microsoft/malmo
```

## License

- **Dataset**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Contact

- **Zugang Chen** 
- Aerospace Information Research Institute, Chinese Academy of Sciences
- Email: chenzg@aircas.ac.cn
- **Shijie Guo** 
- Aerospace Information Research Institute, Chinese Academy of Sciences
- Email: sjguo@gs.zzu.edu.cn