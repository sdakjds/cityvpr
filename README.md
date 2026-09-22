# CityVPR Dataset Tools

Collection of scripts for generating and analyzing the **CityVPR Dataset** — a multi-pitch multi-speed dataset for embodied spatial cognition evaluation in a virtual urban environment.

## Dataset

The full dataset (57,349 frames, ~12.25 GB) is archived on Figshare:

> **DOI:** [10.6084/m9.figshare.33944731](https://doi.org/10.6084/m9.figshare.33944731)

The Minecraft world save (100 x 100 map) is also included in the Figshare deposit. To use it, extract and paste the save folder into:
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

To collect your own custom routes using this codebase, follow these steps:

### 1. Install Project Malmo

Download and install [Project Malmo](https://github.com/Microsoft/malmo) (Minecraft 1.11.2 + Python 3.6). See the [Malmo documentation](https://github.com/Microsoft/malmo/blob/master/doc/install_windows.md) for Windows setup.

### 2. Load the CityVPR world save

Download the world save from [Figshare](https://doi.org/10.6084/m9.figshare.33944731) and paste it into:
```
Malmo\Malmo-0.36.0-Windows-64bit_withBoost_Python3.6\Minecraft\run\saves
```
The city includes 32 predefined waypoints (W0–W31). See `waypoints.json` for coordinates.

### 3. Define custom routes

Edit `generate_routes.py` to define your own routes using the existing 32 waypoints:

```python
# In generate_routes.py, modify the ROUTES list:
ROUTES = [
    {"name": "route12", "waypoints": ["W0", "W5", "W10", "W15"]},   # your route
    {"name": "route13", "waypoints": ["W2", "W8", "W12", "W20"]},   # your route
    # ... add your routes
]
```

Run it to generate `routes.json`:

```bash
py -3.6 generate_routes.py
```

### 4. Configure collection parameters

In `multi_pitch_collector.py`, modify these parameters as needed:

```python
# Speed modes
SPEED_MODES = {
    1: {"type": "constant", "speed": 4.32},
    2: {"type": "constant", "speed": 2.59},
    3: {"type": "accelerate", "start": 2.59, "end": 5.18},
}

# Pitch angles (degrees)
PITCH_ANGLES = [0, 30, 60, 90]

# Image settings
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
FRAME_RATE = 10  # fps
```

### 5. Run collection

```bash
py -3.6 multi_pitch_collector.py
```

This will generate data in the same directory structure as the original dataset.

### 6. Post-processing

After collection, run the same processing scripts:

```bash
py -3.6 record_to_csv.py "your_output_directory"
py -3.6 generate_metadata.py "your_output_directory"
py -3.6 generate_readme.py "your_output_directory"
py -3.6 check_data_quality.py "your_output_directory"
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

```bibtex
@inproceedings{johnson2016malmo,
  title={The Malmo Platform for Artificial Intelligence Experimentation},
  author={Johnson, Matthew and Hofmann, Katja and Hutton, Tim and Bignell, David},
  booktitle={Proc. 25th International Joint Conference on Artificial Intelligence},
  pages={4246},
  year={2016},
  publisher={AAAI Press}
}
```

## License

- **Code**: [MIT License](LICENSE)
- **Dataset**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Contact

- **Zugang Chen** (Corresponding Author)
- Aerospace Information Research Institute, Chinese Academy of Sciences
- Email: 15039802183@163.com
