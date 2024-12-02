import cv2
import os
import numpy as np
import rasterio
import time
from memory_profiler import memory_usage

def create_gcps(points):
    gcps = []
    for point in points:
        x_of_geo, y_of_geo, x_of_pixel, y_of_pixel = point
        gcps.append(rasterio.control.GroundControlPoint(row=y_of_pixel, col=x_of_pixel, x=y_of_geo, y=x_of_geo))
    return gcps

def write_geotiff(output_path, img_data, gcps, crs, dtype):
    transformation = rasterio.transform.from_gcps(gcps)
    with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=img_data.shape[1],
            width=img_data.shape[2],
            count=3,
            dtype=dtype,
            crs=crs,
            transform=transformation,
    ) as dst:
        dst.write(img_data[0], 1)
        dst.write(img_data[1], 2)
        dst.write(img_data[2], 3)

def test_time_memory_usage_part1(input_file):
    start_time = time.time()

    origin = input_file
    img_path = 'result/compressed.jpg'
    if os.path.exists(img_path):
        img_path = 'result/compressed.jpg'
    else:
        img_path = origin

    output_path = 'result/georefRaster.tif'

    points = np.array([[48.54334883179478, 35.0948654426536, 6641, 9270],
                       [48.542041777503826, 35.09759793192003, 8518, 7017],
                       [48.54071025778341, 35.09941698099394, 10415, 5526],
                       [48.53931743764255, 35.10125316177766, 12402, 4040],
                       [48.54097494166265, 35.10354552977222, 10335, 1848]])

    with rasterio.open(img_path) as unref_raster:
        img_data = unref_raster.read()
        crs = rasterio.crs.CRS.from_epsg(4326)
        dtype = unref_raster.read(1).dtype

        gcps = create_gcps(points)
        write_geotiff(output_path, img_data, gcps, crs, dtype)

        with rasterio.open(output_path) as src:
            geo_lon, geo_lat = src.xy(8619, 9484)
            print("\ntest1 (with 5 primary dots)")
            print(f'pixel 9484, 8619 --> geo {geo_lat} {geo_lon}')

    end_time = time.time()
    print(f"Execution time for part 1: {end_time - start_time} seconds")

    mem_usage = memory_usage()
    print(f"Maximum memory usage for part 1: {max(mem_usage)} MiB")

def test_time_memory_usage_part2(input_file):
    start_time = time.time()

    origin = input_file
    img_path = 'result/compressed.jpg'
    if os.path.exists(img_path):
        img_path = 'result/compressed.jpg'
    else:
        img_path = origin

    output_path = 'result/georefRaster.tif'
    new_output_path = 'result/georefRaster.tif'

    points = np.array([[48.54334883179478, 35.0948654426536, 6641, 9270],
                       [48.542041777503826, 35.09759793192003, 8518, 7017],
                       [48.54071025778341, 35.09941698099394, 10415, 5526],
                       [48.53931743764255, 35.10125316177766, 12402, 4040],
                       [48.54097494166265, 35.10354552977222, 10335, 1848]])

    # Завантаження зображення
    img = cv2.imread("thresholdImage\\adaptive\\best_result.jpg")

    # Створення дескриптора ORB
    orb = cv2.ORB_create(nfeatures=600)
    keypoints, descriptors = orb.detectAndCompute(img, None)

    # Створення BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Збираємо збіги
    matches = bf.match(descriptors, descriptors)

    # Сортуємо збіги за відстанню
    matches = sorted(matches, key=lambda x: x.distance)

    # Обираємо тільки унікальні ключові точки
    unique_keypoints = [keypoints[match.queryIdx] for match in matches]

    # Отримуємо координати унікальних ключових точок
    pixel_coordinates = [(int(kp.pt[0]), int(kp.pt[1])) for kp in unique_keypoints]

    geo_coordinates = []

    with rasterio.open(output_path) as src:
        for pixel in pixel_coordinates:
            geo_lon, geo_lat = src.xy(pixel[1], pixel[0])
            geo_coordinates.append((geo_lat, geo_lon))

    for i in range(len(geo_coordinates)):
        geo = geo_coordinates[i]
        pixel = pixel_coordinates[i]
        new_row = np.array([geo[0], geo[1], pixel[0], pixel[1]])
        points = np.vstack([points, new_row])

    for point in pixel_coordinates:
        x, y = point
        pt = (int(x), int(y))
        cv2.drawMarker(img, pt, (255, 0, 0), cv2.MARKER_CROSS, 50, thickness=5)

    cv2.imwrite('thresholdImage/marked/best_gauss_marked.jpg', img)

    with rasterio.open(img_path) as unref_raster:
        img_data = unref_raster.read()
        crs = rasterio.crs.CRS.from_epsg(4326)
        dtype = unref_raster.read(1).dtype

        gcps = create_gcps(points)
        write_geotiff(new_output_path, img_data, gcps, crs, dtype)

        with rasterio.open(new_output_path) as src:
            geo_lon, geo_lat = src.xy(8619, 9484)
            print("\ntest2 (with additional dots)")
            print(f'pixel 9484, 8619 --> geo {geo_lat} {geo_lon}')

    end_time = time.time()
    print(f"Execution time for part 2: {end_time - start_time} seconds")

    mem_usage = memory_usage()
    print(f"Maximum memory usage for part 2: {max(mem_usage)} MiB")

def compress_image(input_file,output_file = 'result\\compressed.jpg', quality=85):
    file_size_mb = os.path.getsize(input_file) / (1024 * 1024)  # розмір файлу в мегабайтах
    if file_size_mb > 79:
        img = cv2.imread(input_file)
        cv2.imwrite(output_file, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        print(f"\nФайл '{input_file}' був стиснений. Новий розмір: {os.path.getsize(output_file) / (1024 * 1024):.2f} МБ.")
    else:
        print(f"\nФайл '{input_file}' має розмір {file_size_mb:.2f} МБ і не потребує стиснення.")


# Приклад використання
input_file = 'result\\final_image_stitched.jpg'
compress_image(input_file)

test_time_memory_usage_part1(input_file)
test_time_memory_usage_part2(input_file)