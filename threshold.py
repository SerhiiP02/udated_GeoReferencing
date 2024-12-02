import cv2
import numpy as np
import os
def adaptive_threshold_search(image_path, output_dir, method=cv2.ADAPTIVE_THRESH_GAUSSIAN_C):
    # Завантажуємо зображення
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    white_pixels = np.sum(img == 255)
    total_pixels = img.size
    white_ratio = white_pixels / total_pixels
    #умова на визначення зимнього знімку
    if 0.61 < white_ratio < 0.98:
        threshold_img = cv2.adaptiveThreshold(img, 255, method, cv2.THRESH_BINARY, 3, 5)
        cv2.imwrite(os.path.join(output_dir, 'best_result.jpg'), threshold_img)
    else:
        # Діапазон для blockSize і C
        block_sizes = range(3, 30, 2)
        C_values = range(-10, 10, 2)

        best_image = None
        best_score = float('-inf')
        best_params = (11, 2)

        for block_size in block_sizes:
            for C in C_values:
                # Застосовуємо адаптивний треш-холдинг
                threshold_img = cv2.adaptiveThreshold(
                    img, 255, method, cv2.THRESH_BINARY, block_size, C)

                # Зберігаємо результати для подальшого аналізу
                output_path = os.path.join(output_dir, f'gaussian_b{block_size}_C{C}.jpg')
                # cv2.imwrite(output_path, threshold_img)
                print("file path: " + output_path + " PROCESSED")
                # Оцінюємо якість сегментації
                white_pixels = np.sum(threshold_img == 255)
                total_pixels = threshold_img.size
                white_ratio = white_pixels / total_pixels

                print(f"white ratio: {white_ratio}")
                score = white_ratio
                if 0.61 < white_ratio < 0.93 and score > best_score:
                    best_score = score
                    best_image = threshold_img
                    best_params = (block_size, C)

        # Виводимо найкращі параметри
        print(f"Найкращі параметри: blockSize={best_params[0]}, C={best_params[1]}")
        # Зберігаємо найкраще зображення
        cv2.imwrite(os.path.join(output_dir, 'best_result.jpg'), best_image)
        print("file best_result.jpg SAVED")

# Виклик функції для пошуку
adaptive_threshold_search('result\\final_image_stitched.jpg', 'thresholdImage\\adaptive')