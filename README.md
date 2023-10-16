# Mirrors of LabHub repositories

This repository contains mirrors of the repositories of the [LabHub](https://labhub.eu.org). The indexes are dynamically generated using Python scripts. The script is available in the `scripts` directory.

## JSON structure

### For all types

`index.od.json`, `index.gd.json`

```json
{
    "QEMU": [{
        "format": imageFormat,
        "name": imageName,
        "download_links": [
            link1,
            link2,
            ...
        ],
        "download_path": path/to/emulator/directory,
        "type": imageType,
        "size": imageSize
    }],
    "IOL": [{
        "format": imageFormat,
        "name": imageName,
        "download_links": [
            link1,
            link2,
            ...
        ],
        "download_path": path/to/emulator/directory,
        "type": imageType,
        "size": imageSize
    }],
    "DYNAMIPS": [{
        "format": imageFormat,
        "name": imageName,
        "download_links": [
            link1,
            link2,
            ...
        ],
        "download_path": path/to/emulator/directory,
        "type": imageType,
        "size": imageSize
    }],
}
```

### For individual types

Types: `qemu`, `iol`, `dynamips`

`index.od.[type].json`, `index.gd.[type].json`

```json
{
        "format": imageFormat,
        "name": imageName,
        "download_links": [
            link1,
            link2,
            ...
        ],
        "download_path": path/to/emulator/directory,
        "type": imageType,
        "size": imageSize
}
```
