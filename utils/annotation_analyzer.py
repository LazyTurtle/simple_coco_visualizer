import json

def load_coco(ann_path:str) -> dict:
    with open(ann_path) as f:
        return json.load(f)

def info(ann:str|dict) -> dict:
    annotation_file = ann if isinstance(ann,dict) else load_coco(ann)
    info = annotation_file['info']
    return info

def images(ann:str|dict) -> list[str]:
    annotation_file = ann if isinstance(ann,dict) else load_coco(ann)
    images_dicts = annotation_file['images']
    images_path = [img['file_name'] for img in images_dicts]
    return images_path

def super_categories(ann:str|dict) -> set[str]:
    annotation_file = ann if isinstance(ann,dict) else load_coco(ann)
    categories = annotation_file["categories"]
    super_category_list = [category['supercategory'] for category in categories]
    unique_supercaetgories = set(super_category_list)
    return unique_supercaetgories

def categories_of_supercategory(supercategory:str, ann:str|dict) -> set[str]:
    annotation_file = ann if isinstance(ann,dict) else load_coco(ann)
    categories = [category['name'] for category in annotation_file['categories'] if category['supercategory'] == supercategory]
    unique_categories = set(categories)
    return unique_categories