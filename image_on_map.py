import cv2
import rasterio
import numpy as np
import os

def calculate_psnr(original, rotated):
    original = cv2.imread(original)
    rotated = cv2.imread(rotated)

    mse = np.mean((original - rotated) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

# Відкриття GeoTIFF-файлу
with rasterio.open('result\\georefRaster.tif') as src:
    # Отримання просторових метаданих
    bounds = src.bounds
    # Визначення extent зображення
    extent = [bounds.left, bounds.bottom, bounds.right, bounds.top]
    # Визначення imageBounds
    imageBounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    # Отримання геотрансформації
    transform = src.transform
    # Визначення повороту зображення
    rotation = np.arctan2(transform[1], transform[0]) * (180 / np.pi)  # у градусах

# Запис imageBounds та rotation у текстовий файл
with open('imageBounds.txt', 'w') as f:
    for row in imageBounds:
        f.write(' '.join(map(str, row)) + '\n')
    f.write('Rotation: ' + str(rotation))


# Load the JPEG photo
original_img = 'result\\final_image_stitched.jpg'
image_path = 'result\\compressed.jpg'
if os.path.exists(image_path):
    image_path = 'result/compressed.jpg'
else:
    image_path = 'result/final_image_stitched.jpg'

image = cv2.imread(image_path)
# Calculate the center of the image
height, width = image.shape[:2]
center = (width / 2, height / 2)
# Load rotation angle from the text file
rotation_angle = rotation
# Perform rotation
rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height), flags=cv2.INTER_LINEAR)
# Save the rotated image
rotated_image_path = 'result\\rotated_final.jpg'
cv2.imwrite(rotated_image_path, rotated_image)
print("Image rotated and saved successfully.")

psnr_value = calculate_psnr(original_img, rotated_image_path)
print(f'PSNR between original and rotated image: {psnr_value} дБ')