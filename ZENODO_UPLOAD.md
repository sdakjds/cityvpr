# Zenodo Upload Checklist

## 1. Compress Dataset

将 city_vpr_dataset 目录打包：

```powershell
Compress-Archive -Path "D:\Malmo\Malmo-0.36.0-Windows-64bit_withBoost_Python3.6\Python_Examples\city_vpr_dataset" -DestinationPath "D:\Malmo\...\city_vpr_dataset.zip"
```

> 如果 zip 超过 15GB，Zenodo 单文件限制为 50GB，应该没问题。
> 如果太大可以分卷压缩。

## 2. Zenodo 上传内容

| 文件 | 说明 |
|------|------|
| `city_vpr_dataset.zip` | 完整数据集（图片+CSV+record.txt+SVG+JSON） |
| `dataset_metadata.json` | 也可以单独上传一份 |
| `README.md` | 数据集说明文档 |

## 3. Zenodo Metadata 填写

- **Title**: CityVPR: A Multi-Pitch Multi-Speed Visual Place Recognition Dataset in Minecraft Urban Environment
- **Creators**: Chen, Zugang (Aerospace Information Research Institute, CAS)
- **Description**: 从 README.md 复制
- **Resource type**: Dataset
- **License**: CC-BY 4.0
- **Communities**: Scientific Data (如有)
- **Related identifiers**: 填 GitHub 仓库链接 (https://github.com/xxx/cityvpr)，类型选 "isSupplementTo"
- **Funding**: 如有基金支持，填写相关信息

## 4. GitHub 上传内容

GitHub 仓库结构（仅代码，不含数据）：

```
cityvpr/
├── README.md              # 仓库说明
├── LICENSE                # MIT License
├── .gitignore
├── multi_pitch_collector.py    # 采集代码
├── record_to_csv.py            # TXT→CSV 转换
├── generate_metadata.py        # 元数据生成
├── generate_readme.py          # README 生成
├── generate_waypoints.py       # 路径点生成
├── generate_routes.py          # 路线生成
├── generate_city_map.py        # 城市地图生成
├── generate_route_maps.py      # 路线图生成
└── check_data_quality.py       # 质量检查
```

## 5. 操作顺序

1. **先传 GitHub** — 创建仓库 cityvpr，上传所有 .py 文件 + README + LICENSE
2. **再传 Zenodo** — 上传数据集 zip，在 Related Identifiers 填 GitHub 链接
3. **Zenodo 获得DOI后** — 回到 GitHub README，把 DOI 填进去
4. **GitHub + Zenodo 联动** — 可用 Zenodo-GitHub 集成自动给 GitHub 仓库打 DOI

## 6. 论文中引用格式

- **数据集**: "The dataset is available at Zenodo (https://zenodo.org/record/XXXXX, DOI: 10.5281/zenodo.XXXXX)."
- **代码**: "The collection and analysis code is available at GitHub (https://github.com/xxx/cityvpr)."
