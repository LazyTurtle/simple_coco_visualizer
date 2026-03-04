# Simple COCO Visualizer

## About The Project

This project makes a simple GUI to visualize datasets in the COCO format with superimposed annotation regions.

## Getting Started

### Prerequisites

`Python` is the only prerequisite to run this project. Follow [this](https://www.python.org/) page to install it on your machine.

### Installation

1. Clone the repo

    1. Using Git
      ```sh
      git clone https://github.com/LazyTurtle/simple_coco_visualizer.git
      ```
      
    2. Or downloading the Zip file and extract it on your folder of choice

2. Install required packages
   ```sh
   pip install -r requirements.txt
   ```

## Usage


Run the GUI via terminal:
```sh
python cocoviewer.py [-h] --images IMAGES --annotations ANNOTATIONS [--category CATEGORY] [--limit LIMIT] [--no-seg] [--no-kp] [--save-dir SAVE_DIR] [--shuffle]
```

Such as:
```sh
python cocoviewer.py --images 'path/to/images/folder' --annotations 'path/to/annotation_file.json' --limit 100 --shuffle
```

Use arrow-keys `<` and `>` to navigate the samples. `s` saves current frame. `q` to quit the GUI.

Use the `--help` comand to explore the command line arguments.

```
usage: cocoviewer.py [-h] --images IMAGES --annotations ANNOTATIONS [--category CATEGORY] [--limit LIMIT] [--no-seg] [--no-kp] [--save-dir SAVE_DIR] [--shuffle]

Simple COCO visualizer

options:
  -h, --help            show this help message and exit
  --images IMAGES       Directory containing images
  --annotations ANNOTATIONS
                        Path to COCO JSON file
  --category CATEGORY   Filter by category name
  --limit LIMIT         Max images to load (default 50)
  --no-seg              Hide segmentation masks
  --no-kp               Hide keypoints
  --save-dir SAVE_DIR   Directory to save visualisations (optional)
  --shuffle             Shuffle images before display
```

## License

Distributed under the AGPLv3 license. See `LICENSE.txt` for more information.