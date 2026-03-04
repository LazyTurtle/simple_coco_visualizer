"""
COCO Annotation Visualizer
Usage:
    python coco_visualizer.py --images /path/to/images --annotations /path/to/annotations.json
    python coco_visualizer.py --images ./images --annotations ./annotations.json --category person --limit 20
"""

import json
import random
import argparse
from pathlib import Path

import cv2
import numpy as np

from utils import loading_bar, logging

LOGGER = logging.get_logger('Main', out_folder='logs/')

# Colour palette (colorblind safe)
PALETTE = [
    (0, 0,  0),
    (230, 159, 0), 
    (86, 180, 233),
    (0, 158, 115),
    (240, 228, 66),
    (0, 114, 178),
    (213, 94, 0),
    (204, 121, 167),
    (255, 255, 255),
]

def load_coco(ann_path: str) -> dict:
    with open(ann_path) as f:
        return json.load(f)


def build_index(coco: dict) -> tuple:
    """Return dicts keyed by id for images, annotations-per-image, categories."""
    images      = {img["id"]: img for img in coco.get("images", [])}
    cat_map     = {c["id"]: c["name"] for c in coco.get("categories", [])}
    anns_by_img = {}
    for ann in coco.get("annotations", []):
        anns_by_img.setdefault(ann["image_id"], []).append(ann)
    return images, anns_by_img, cat_map


def colour_for(cat_id: int) -> tuple:
    return PALETTE[cat_id % len(PALETTE)]


def draw_bbox(img, bbox, label, colour):
    x, y, w, h = map(int, bbox)
    cv2.rectangle(img, (x, y), (x + w, y + h), colour, 2)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.rectangle(img, (x, y - th - 6), (x + tw + 4, y), colour, -1)
    cv2.putText(img, label, (x + 2, y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

def rle_to_mask(rle, height, width):
    """Decode a COCO RLE dict {'counts': ..., 'size': [h, w]} into a binary mask."""
    counts = rle["counts"]
    # Uncompressed RLE: counts is a plain list of ints
    if isinstance(counts, list):
        mask = np.zeros(height * width, dtype=np.uint8)
        pos, val = 0, 0
        for run in counts:
            mask[pos:pos + run] = val
            pos += run
            val ^= 1
        return mask.reshape((height, width), order='F')
    # Compressed RLE: counts is a byte string — requires pycocotools
    try:
        from pycocotools import mask as mask_util
        return mask_util.decode(rle).astype(np.uint8)
    except ImportError:
        LOGGER.warning("WARNING: compressed RLE requires pycocotools (`pip install pycocotools`). Skipping mask.")
        return None

def draw_segmentation(img, segmentation, colour):
    h, w = img.shape[:2]
    overlay = img.copy()

    # RLE format: segmentation is a dict with 'counts' and 'size'
    if isinstance(segmentation, dict) and "counts" in segmentation:
        mask = rle_to_mask(segmentation, h, w)
        if mask is not None:
            img[mask == 1] = (
                img[mask == 1] * 0.65 + np.array(colour) * 0.35
            ).astype(np.uint8)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, contours, -1, colour, 2)
        return

    # Polygon format: segmentation is a list of [x1,y1,x2,y2,...] arrays
    for seg in segmentation:
        if isinstance(seg, dict) and "counts" in seg:
            # Per-instance compressed RLE nested inside a list
            mask = rle_to_mask(seg, h, w)
            if mask is not None:
                img[mask == 1] = (
                    img[mask == 1] * 0.65 + np.array(colour) * 0.35
                ).astype(np.uint8)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(img, contours, -1, colour, 2)
        else:
            pts = np.array(seg, dtype=np.int32).reshape(-1, 1, 2)
            cv2.fillPoly(overlay, [pts], colour)
            cv2.polylines(img, [pts], True, colour, 2)

    cv2.addWeighted(overlay, 0.35, img, 0.65, 0, img)

def draw_keypoints(img, keypoints, colour, skeleton=None):
    kps = np.array(keypoints).reshape(-1, 3)  # x, y, visibility
    visible = [(int(x), int(y)) for x, y, v in kps if v > 0]

    if skeleton:
        for a, b in skeleton:
            if a <= len(kps) and b <= len(kps):
                xa, ya, va = kps[a - 1]
                xb, yb, vb = kps[b - 1]
                if va > 0 and vb > 0:
                    cv2.line(img, (int(xa), int(ya)), (int(xb), int(yb)), colour, 2)

    for x, y in visible:
        cv2.circle(img, (x, y), 4, colour, -1)
        cv2.circle(img, (x, y), 4, (255, 255, 255), 1)


def visualize(img_path: str, annotations: list, cat_map: dict,
              show_seg: bool = True, show_kp: bool = True,
              skeleton=None):
    img = cv2.imread(img_path)
    if img is None:
        error = f"Cannot read image: {img_path}"
        LOGGER.error(error)
        raise FileNotFoundError(error)

    for ann in annotations:
        cat_id  = ann.get("category_id", 0)
        colour  = colour_for(cat_id)
        label   = cat_map.get(cat_id, str(cat_id))

        if show_seg and ann.get("segmentation"):
            draw_segmentation(img, ann["segmentation"], colour)

        if "bbox" in ann:
            draw_bbox(img, ann["bbox"], label, colour)

        if show_kp and ann.get("keypoints"):
            draw_keypoints(img, ann["keypoints"], colour, skeleton)

    return img


def display_loop(frames, titles, output_dir=None):
    """Arrow-key navigation; 's' saves current frame; 'q' quits."""
    idx = 0

    def show(i):
        win_title = f"COCO Viewer  [{i + 1}/{len(frames)}]  {titles[i]}"
        cv2.imshow("COCO Viewer", frames[i])
        cv2.setWindowTitle("COCO Viewer", win_title)

    cv2.namedWindow("COCO Viewer", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("COCO Viewer", 1024, 768)
    show(idx)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key in (ord('q'), 27):                    # q / Esc → quit
            break
        elif key in (83, ord('d'), ord('n')):        # → / d / n → next
            idx = (idx + 1) % len(frames)
        elif key in (81, ord('a'), ord('p')):        # ← / a / p → prev
            idx = (idx - 1) % len(frames)
        elif key == ord('s') and output_dir:         # s → save
            out = Path(output_dir) / f"vis_{titles[idx]}"
            cv2.imwrite(str(out), frames[idx])
            LOGGER.info(f"Saved -> {out}")
        show(idx)

    cv2.destroyAllWindows()

def check_missing_images(images: dict, images_folder: str) -> list:
    """Check which images in the annotation file are missing from the image folder."""
    image_dir = Path(images_folder)
    missing = [
        meta["file_name"]
        for meta in images.values()
        if not (image_dir / meta["file_name"]).exists()
    ]
    if missing:
        LOGGER.warning(f"WARNING: {len(missing)}/{len(images)} images not found in '{image_dir}':")
        for f in missing:
            LOGGER.warning(f"  - {f}")
    else:
        LOGGER.info(f"All {len(images)} images found in '{image_dir}'.")
    return missing

def check_unannotated_images(images: dict, images_folder: str) -> list:
    """Check which images in the image folder have no entry in the annotation file."""
    image_dir = Path(images_folder)
    annotated_filenames = {meta["file_name"] for meta in images.values()}
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    unannotated = [
        f.name
        for f in image_dir.iterdir()
        if f.suffix.lower() in extensions and f.name not in annotated_filenames
    ]
    if unannotated:
        LOGGER.warning(f"WARNING: {len(unannotated)} images in '{image_dir}' have no annotation entry:")
        for f in unannotated:
            LOGGER.warning(f"  - {f}")
    else:
        LOGGER.info(f"All images in '{image_dir}' have annotation entries.")
    return unannotated

def main():
    parser = argparse.ArgumentParser(description="Simple COCO visualizer")
    parser.add_argument("--images",      required=True, help="Directory containing images")
    parser.add_argument("--annotations", required=True, help="Path to COCO JSON file")
    parser.add_argument("--category",    default=None,  help="Filter by category name")
    parser.add_argument("--limit",       type=int, default=50, help="Max images to load (default 50)")
    parser.add_argument("--no-seg",      action="store_true",  help="Hide segmentation masks")
    parser.add_argument("--no-kp",       action="store_true",  help="Hide keypoints")
    parser.add_argument("--save-dir",    default=None,  help="Directory to save visualisations (optional)")
    parser.add_argument("--shuffle",     action="store_true",  help="Shuffle images before display")
    args = parser.parse_args()

    LOGGER.info("Loading annotations ...")
    coco = load_coco(args.annotations)
    LOGGER.info('Annotation loaded')
    LOGGER.info('Building index')
    images, anns_by_img, cat_map = build_index(coco)
    LOGGER.info('Index build')

    check_missing_images(images, args.images)
    check_unannotated_images(images, args.images)
    
    # Extract skeleton for keypoint tasks (e.g. COCO person)
    skeleton = None
    for cat in coco.get("categories", []):
        if cat.get("skeleton"):
            skeleton = cat["skeleton"]
            break

    # Filter by category if requested
    if args.category:
        cat_ids = {c["id"] for c in coco.get("categories", [])
                   if c["name"].lower() == args.category.lower()}
        if not cat_ids:
            available = [c["name"] for c in coco.get("categories", [])]
            error = f"Category '{args.category}' not found. Available: {available}"
            LOGGER.error(error)
            raise SystemExit(error)
        
        filtered_img_ids = {a["image_id"] for a in coco.get("annotations", [])
                            if a.get("category_id") in cat_ids}
        images = {k: v for k, v in images.items() if k in filtered_img_ids}
        LOGGER.info(f"Filtered to {len(images)} images containing '{args.category}'")

    

    img_ids = list(images.keys())
    if args.shuffle:
        random.shuffle(img_ids)
    img_ids = img_ids[:args.limit]

    if args.save_dir:
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)

    image_dir = Path(args.images)
    frames, titles = [], []

    LOGGER.info(f"Rendering {len(img_ids)} images ...")
    loading_bar.print_progress_bar(
        0,
        len(img_ids),
        'Rendering images:'
    )
    for i, img_id in enumerate(img_ids):
        meta      = images[img_id]
        img_path  = image_dir / meta["file_name"]
        anns      = anns_by_img.get(img_id, [])

        try:
            frame = visualize(str(img_path), anns, cat_map,
                              show_seg=not args.no_seg,
                              show_kp=not args.no_kp,
                              skeleton=skeleton)
        except FileNotFoundError as e:
            LOGGER.warning(f"  WARNING: {e} - skipping")
            continue

        if args.save_dir:
            out = Path(args.save_dir) / meta["file_name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out), frame)

        frames.append(frame)
        titles.append(meta["file_name"])
        loading_bar.print_progress_bar(
            i+1,
            len(img_ids),
            'Rendering images:'
        )
    LOGGER.info('Rendering complete.')
    if not frames:
        error = "No images could be loaded."
        LOGGER.error(error)
        raise SystemExit(error)

    LOGGER.info(f"\nLoaded {len(frames)} images.")
    LOGGER.info("Controls: <- / -> (or a/d/p/n) to navigate  |  s = save  |  q / Esc = quit\n")
    display_loop(frames, titles, output_dir=args.save_dir)


if __name__ == "__main__":
    main()