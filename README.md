# Mirrors of LabHub repositories

This repository contains mirrors of the repositories of the [LabHub](https://labhub.eu.org). The indexes are dynamically generated using Python scripts. The script is available in the `scripts` directory.

## How to use

1. Place the script for each type of image in the respective directory. The `scripts/` directory contains the scripts for each type of image.
2. Set the `base_dir` in `index.py` to the directory where you have mounted the LabHub repositories. Then run the script.

```bash
python3 index.py
```

## Directory structure

```bash
UNETLAB/
├── UNETLAB I
│   └── addons
│       ├── dynamips
│       │    └── index.py
│       ├── iol
│       │   └── index.py
│       └── qemu
│           └── index.py
└── UNETLAB II
    └── addons
        ├── iol
        │   └── index.py
        └── qemu
            └── index.py
```

## Main index script `index.py` explanation

The script will run the scripts in each directory and generate the JSON files. The JSON files for each type of image will be generated in the respective directories then copied to the directory where the script is run.  
The script will then merge the JSON files for each type of image into a single JSON file for each type of image.  
After this, the script will sort and add ids to the generated JSON files.  
I know this is a bit confusing, but the script is pretty simple and you can better understand it by reading it. It will work as long as you have the directory structure as shown above. I'm not an experienced Python developer, so I'm sure there are better ways to do this. But this is what I could come up with. Suggestions and PRs are welcome.  

I'm also not great at explaining things, so if you have any questions, feel free to open an issue.

## Scripts in each directory explanation

The `index.py` scripts placed in each type of image directory will generate the JSON files for each type of image constructing the download links based on various patterns. iol and dynamips are easy since they're 1 file per image. QEMU is a bit more complicated since there are multiple files per image. The script will generate the download links for each file and then merge them into a single list.  
For QEMU, the scripts looks for the following patterns:

- Image name: it is taken either from the parent directory name or from the name of the archive file.
- `.qcow2`  
    This is the default image file for QEMU. The script will look for this file and if it exists, it will add it to the list of download links along with any other files in the same directory like other `.qcow2` files, `.yaml` files, etc.
- `.tgz`, `.tar.gz`, `.zip`
    A lot of QEMU images are distributed as `.tgz` files. The script will look for these files and add them to the list of download links.

## JSON structure

The resulting JSON files will have the following structure.

### For individual types

The script in each directory will generate two JSON files for each type of image.

These JSON files will contain the images for each type of image. The structure is as follows:

Types: `qemu`, `iol`, `dynamips`

`index.od.[type].json`, `index.gd.[type].json`

```json
{
        "id": 1,
        "format": "imageFormat",
        "name": "imageName",
        "download_links": [
            "link1",
            "link2",
            "..."
        ],
        "download_path": "path/to/emulator/directory",
        "type": "imageType",
        "size": "imageSize"
}
```

### Structure merged JSON

This JSON will contain all the images from all the types after they are merged from the individually generated JSONs for each image type. The structure is as follows:

`index.od.json`, `index.gd.json`

```json
{
    "QEMU": [{
        "id": 1,
        "format": "imageFormat",
        "name": "imageName",
        "download_links": [
            "link1",
            "link2",
            "..."
        ],
        "download_path": "path/to/emulator/directory",
        "type": "imageType",
        "size": "imageSize"
    }],
    "IOL": [{
        "id": 1,
        "format": "imageFormat",
        "name": "imageName",
        "download_links": [
            "link1",
            "link2",
            "..."
        ],
        "download_path": "path/to/emulator/directory",
        "type": "imageType",
        "size": "imageSize"
    }],
    "DYNAMIPS": [{
        "id": 1,
        "format": "imageFormat",
        "name": "imageName",
        "download_links": [
            "link1",
            "link2",
            "..."
        ],
        "download_path": "path/to/emulator/directory",
        "type": "imageType",
        "size": "imageSize"
    }],
}
```
