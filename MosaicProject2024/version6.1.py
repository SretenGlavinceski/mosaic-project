import math
import pathlib
import json
import os
import random
import numpy as np
import cv2

def get_average_color(img):
    average_color = np.average(np.average(img, axis=0), axis=0)
    average_color = np.around(average_color, decimals=-1)
    average_color = tuple(int(i) for i in average_color)
    return average_color

def get_closest_color(color, colors):
    cr, cg, cb = color

    min_difference = float("inf")
    closest_color = None
    for c in colors:
        r, g, b = eval(c)
        difference = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if difference < min_difference:
            min_difference = difference
            closest_color = eval(c)
    return closest_color

def place_tile(target_area, tile_size, color_data, img):
    y0, y1, x0, x1 = target_area
    tile_height, tile_width = tile_size
    area_height = y1 - y0
    area_width = x1 - x0

    if area_height != tile_height or area_width != tile_width:
        tile_height = area_height
        tile_width = area_width

    average_color = get_average_color(img[y0:y1, x0:x1])
    closest_color = get_closest_color(average_color, color_data.keys())

    if closest_color is None:
        print(f"No matching color found for {average_color}")
        return False

    i_paths = color_data[str(closest_color)]
    random.shuffle(i_paths)

    for i_path in i_paths:
        i = cv2.imread(i_path)
        if i is None:
            continue

        i_resized = cv2.resize(i, (area_width, area_height))

        try:
            img[y0:y1, x0:x1] = i_resized
            return True
        except ValueError as e:
            print(f"Error placing tile: {e}")
            continue

    print(f"Failed to place tile for color {closest_color}")
    return False

def place_tiles_in_row(start_x, start_y, end_x, end_y, tile_size, mask, color_data, img):
    x = start_x
    while x < end_x:
        mask_intersection = np.any(mask[start_y:end_y, x:x + tile_size[0]] == 255)

        if mask_intersection:

            tile_end_x = min(x + tile_size[0], end_x)
            tile_area = (start_y, end_y, x, tile_end_x)

            if not place_tile(tile_area, tile_size, color_data, img):
                print(f"Failed to place tile at {tile_area}")

        x += tile_size[0]

def create_masks(img, faces):
    mask_face = np.zeros_like(img[:, :, 0], dtype=np.uint8)
    mask_background = np.ones_like(img[:, :, 0], dtype=np.uint8) * 255

    for (x, y, w, h) in faces:
        mask_face[y:y + h, x:x + w] = 255
        mask_background[y:y + h, x:x + w] = 0

    return mask_face, mask_background

cache_face_file = "cache_face.json"
if not os.path.exists(cache_face_file):
    imgs_dir_face = pathlib.Path('images')
    images_face = list(imgs_dir_face.glob("*.jpg"))

    data_face = {}
    for img_path in images_face:
        img = cv2.imread(str(img_path))
        if img is not None:
            average_color = get_average_color(img)
            if str(tuple(average_color)) in data_face:
                data_face[str(tuple(average_color))].append(str(img_path))
            else:
                data_face[str(average_color)] = [str(img_path)]

    with open(cache_face_file, "w") as file:
        json.dump(data_face, file, indent=2, sort_keys=True)

    print("Face tiles caching done")
else:
    print("Face tiles cache file already exists")

with open(cache_face_file, "r") as file:
    data_face = json.load(file)

cache_background_file = "cache_background.json"
if not os.path.exists(cache_background_file):
    imgs_dir_background = pathlib.Path('pool')
    images_background = list(imgs_dir_background.glob("*.png"))

    data_background = {}
    for img_path in images_background:
        img = cv2.imread(str(img_path))
        if img is not None:
            average_color = get_average_color(img)
            if str(tuple(average_color)) in data_background:
                data_background[str(tuple(average_color))].append(str(img_path))
            else:
                data_background[str(average_color)] = [str(img_path)]

    with open(cache_background_file, "w") as file:
        json.dump(data_background, file, indent=2, sort_keys=True)

    print("Background tiles caching done")
else:
    print("Background tiles cache file already exists")

with open(cache_background_file, "r") as file:
    data_background = json.load(file)

img = cv2.imread('Mona_Lisa.jpg')
if img is not None:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))

    face_tile_size = (10, 10)
    background_tile_size = (20, 20)

    mask_face, mask_background = create_masks(img, faces)

    img_height, img_width, _ = img.shape
    for y in range(0, img_height, background_tile_size[1]):
        end_y = min(y + background_tile_size[1], img_height)
        place_tiles_in_row(0, y, img_width, end_y, background_tile_size, mask_background, data_background, img)

    for (x, y, w, h) in faces:
        face_img = img[y:y+h, x:x+w]
        face_height, face_width, _ = face_img.shape
        for y0 in range(0, face_height, face_tile_size[1]):
            end_y = min(y0 + face_tile_size[1], face_height)
            for x0 in range(0, face_width, face_tile_size[0]):
                end_x = min(x0 + face_tile_size[0], face_width)
                place_tile((y+y0, y+end_y, x+x0, x+end_x), face_tile_size, data_face, img)

    cv2.imshow("Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imwrite("output_face_and_background_mosaic.jpg", img)

else:
    print("Failed to load the image")