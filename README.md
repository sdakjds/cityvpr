# CityVPR Dataset Tools

Collection of scripts for generating and analyzing the **CityVPR Dataset** — a Multi-Pitch Multi-Speed Visual Place Recognition dataset in a Minecraft urban environment.

## Dataset

The full dataset (images + trajectory data) is archived on [Zenodo](https://zenodo.org/) with a assigned DOI.

> **DOI:** [TBD after Zenodo upload]

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

## Dataset Structure

```
city_vpr_dataset/
├── speedMode_1/          # Constant 4.32 m/s
│   ├── route1/
│   │   ├── pitch_0/      # Forward view
│   │   │   ├── *.png     # Image frames (1280x720)
│   │   │   ├── record.txt
│   │   │   └── trajectory.csv
│   │   ├── pitch_30/
│   │   ├── pitch_60/
│   │   └── pitch_90/
│   ├── route2/
│   └── ... (route3 ~ route11)
├── speedMode_2/          # Constant 2.59 m/s
├── speedMode_3/          # Accelerating 2.59~5.18 m/s
├── waypoints.json
├── routes.json
├── buildings.json
├── city_map.svg
├── route_maps/           # 11 route visualization SVGs
├── dataset_metadata.json
├── data_quality_report.json
└── README.md
```

## Citation

If you use this dataset or code in your research, please cite:

```bibtex
@article{chen2026cityvpr,
  title={CityVPR: A Multi-Pitch Multi-Speed Visual Place Recognition Dataset in Minecraft Urban Environment},
  author={Chen, Zugang},
  journal={Scientific Data},
  year={2026},
  doi={TBD}
}
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
