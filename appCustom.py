import webbrowser
import subprocess
import customtkinter as ctk
import tkintermapview
from tkinterweb import HtmlFrame
from tkinter import filedialog, messagebox, Tk, Button, Frame, Scrollbar, HORIZONTAL, VERTICAL, Canvas, Toplevel
from PIL import Image, ImageTk
from tkhtmlview import HTMLLabel
import os
import folium
import threading
import time
Image.MAX_IMAGE_PIXELS = None

class GeoTaggingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GeoTagging Application")
        self.geometry("1000x580")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Змінні
        self.photo_image = None
        self.photo_original = None
        self.photo_tk = None
        self.points_map = []  # Точки на карті
        self.points_photo = []  # Точки на фото
        self.selecting_map = True  # Вибір карти або фото
        self.photo_loaded = False

        # Віджети
        self.map_frame = tkintermapview.TkinterMapView(self, width=600, height=600,  corner_radius = 0)
        self.map_frame.set_position(48.54, 35.1)
        self.map_frame.grid(row=0, column=0, padx=10, pady=10)

        # Photo Frame with scrollbars
        self.photo_frame = Frame(self, bg="white")
        self.photo_frame.grid(row=0, column=1, padx=10, pady=10)

        # Scrollbars for photo
        self.h_scroll = Scrollbar(self.photo_frame, orient=HORIZONTAL)
        self.v_scroll = Scrollbar(self.photo_frame, orient=VERTICAL)
        self.photo_canvas = Canvas(
            self.photo_frame,
            width=590,
            height=590,
            bg="grey",
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
        )
        self.h_scroll.config(command=self.photo_canvas.xview)
        self.v_scroll.config(command=self.photo_canvas.yview)
        self.photo_canvas.grid(row=0, column=0)
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        # Buttons
        self.load_photo_button = ctk.CTkButton(self, text="Завантажити Фото", command=self.load_photo)
        self.load_photo_button.grid(row=1, column=1, pady=10)
        self.finish_button = ctk.CTkButton(self, text="Завершити Вибір Точок", command=self.finish_selection)
        self.finish_button.grid(row=1, column=0, pady=10)

        # Bind zoom and pan for photo canvas
        self.photo_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.photo_canvas.bind("<B1-Motion>", self.pan_photo)

        self.current_selection = "photo"  # Відстежує активне полотно для вибору точок
        self.zoom_factor = 1.0
        self.start_x = 0
        self.start_y = 0

        # Bind mouse clicks to photo and map (for selecting points)
        self.map_frame.add_right_click_menu_command(label="Add Marker", command=self.select_map_point, pass_coords=True)
        self.photo_canvas.bind("<Button-3>", self.select_photo_point)

    def load_photo(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.tiff")])
        if filepath:
            try:
                # Завантаження оригінального зображення
                self.photo_original = Image.open(filepath)
                self.update_photo_canvas()
                self.photo_loaded = True
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")

    def update_photo_canvas(self):
        scaled_image = self.photo_original.resize(
            (int(self.photo_original.width * self.zoom_factor), int(self.photo_original.height * self.zoom_factor)),
            Image.Resampling.LANCZOS,
        )
        self.photo_tk = ImageTk.PhotoImage(scaled_image)
        self.photo_canvas.create_image(0, 0, anchor="nw", image=self.photo_tk)
        self.photo_canvas.config(scrollregion=self.photo_canvas.bbox("all"))

    def pan_photo(self, event):
        if not self.photo_loaded:
            return

        # Визначення зміщення
        dx = self.start_x - event.x
        dy = self.start_y - event.y

        # Переміщення області перегляду
        self.photo_canvas.xview_scroll(int(dx), "units")
        self.photo_canvas.yview_scroll(int(dy), "units")

        # Оновлення початкової точки для наступного руху
        self.start_x = event.x
        self.start_y = event.y

    def start_pan(self, event):
        # Фіксуємо початкову точку кліку для початку панорамування
        self.start_x = event.x
        self.start_y = event.y


    def select_map_point(self, coords):
        if self.selecting_map and self.photo_loaded:
            new_marker = self.map_frame.set_marker(coords[0], coords[1])
            # Отримуємо координати кліку
            x, y = coords[0], coords[1]
            self.points_map.append((x, y))
            print(f"Вибрано точку на карті: {x}, {y}")
            self.selecting_map = False  # Переходимо до вибору фото
        else:
            if self.photo_loaded:
                print("Спочатку виберіть точку на фото!")
            else:
                print("Необхідно спочатку завантажити фото!")

    def select_photo_point(self, event):
        if not self.selecting_map and self.photo_loaded:
            # Визначення позиції кліку на зображенні
            x = self.photo_canvas.canvasx(event.x)  # Врахування горизонтального скролінгу
            y = self.photo_canvas.canvasy(event.y)  # Врахування вертикального скролінгу

            # Перетворення координат до оригінального масштабу зображення
            true_x = x / self.zoom_factor
            true_y = y / self.zoom_factor

            # Збереження "справжніх" координат
            self.points_photo.append((true_x, true_y))

            # Відображення точки на полотні
            self.photo_canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3, fill="blue"
            )
            print(f"Вибрано точку на фото (оригінальні координати): {true_x:.2f}, {true_y:.2f}")
            self.selecting_map = True  # Повертаємося до вибору точки на карті
        else:
            print("Спочатку виберіть точку на карті!")


    def finish_selection(self):
        if len(self.points_map) == len(self.points_photo) and len(self.points_map) <= 5: #and len(self.points_map) != 0  ################################################
            combined_points = [
                [map_x, map_y, photo_x, photo_y]
                for (map_x, map_y), (photo_x, photo_y) in zip(
                    self.points_map, self.points_photo
                )
            ]
            print("Вибрані точки:")
            for point in combined_points:
                print(point)

            # Створення нового вікна, передача масиву координат
            new_window = NewWindow(self, combined_points)
            new_window.grab_set()  # Блокування основного вікна, поки відкрите нове

        else:
            print("Необхідно завершити вибір пар точок!")



class NewWindow(ctk.CTkToplevel):
    def __init__(self, parent, coordinates):
        super().__init__(parent)

        self.title("Adjust section")
        self.geometry("540x300")

        # Отримуємо масив координат, який передали з основного вікна
        self.coordinates = coordinates

        # Перший рядок: Заголовок і масив координат
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.pack(pady=10, padx=20, fill="x")

        self.label1 = ctk.CTkLabel(self.frame1, text="Ваш масив")
        self.label1.pack()

        # Форматуємо масив для відображення та показуємо
        self.array_display = ctk.CTkLabel(self.frame1, text=self.format_coordinates(self.coordinates))
        self.array_display.pack()

        # Другий рядок: Заголовок і порожнє місце для результатів гео-прив'язки
        self.frame2 = ctk.CTkFrame(self)
        self.frame2.pack(pady=10, padx=20, fill="x")

        self.label2 = ctk.CTkLabel(self.frame2, text="Результати гео-прив'язки")
        self.label2.pack()

        self.progress_bar = ctk.CTkProgressBar(self.frame2, width=300)
        self.progress_bar.pack(pady=10, padx=20)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Ховаємо прогрес-бар

        self.results_label = ctk.CTkLabel(self.frame2, text="")
        self.results_label.pack(fill="x")

        # Третій рядок: Дві кнопки
        self.frame3 = ctk.CTkFrame(self)
        self.frame3.pack(pady=10, padx=20, fill="x")

        self.button1 = ctk.CTkButton(self.frame3, text="Гео-прив'язка", command=self.start_process)
        self.button1.pack(side="left", pady=10, padx=10)

        self.button2 = ctk.CTkButton(self.frame3, text="Карта", command=self.button2_function)
        self.button2.pack(side="right", pady=10, padx=10)

    def format_coordinates(self, coordinates):
        """Форматуємо масив для відображення"""
        formatted_text = ""
        for coord in coordinates:
            formatted_text += f"Geo: {coord[0]}, {coord[1]} | Pixel: {coord[2]}, {coord[3]}\n"
        return formatted_text

    def start_process(self):
        """Запуск прогрес-бара і підпроцесу."""
        # Запуск прогрес-бара
        self.button1.configure(state="disabled")  # Вимикаємо кнопку під час виконання
        self.progress_bar.pack()  # Показуємо прогрес-бар
        threading.Thread(target=self.run_progress_bar, daemon=True).start()

        # Запуск підпроцесу
        threading.Thread(target=self.run_subprocess, daemon=True).start()

    def run_progress_bar(self):
        """Заповнення прогрес-бара синхронно із виконанням підпроцесу."""
        progress = 0
        while progress < 1 and getattr(self, "process_running", True):  # Чекаємо, поки завершиться підпроцес
            time.sleep(0.5)  # Частота оновлення
            progress += 0.008  # Збільшуємо прогрес
            self.progress_bar.set(progress)
        self.progress_bar.set(1)  # Встановлюємо повний прогрес

    def run_subprocess(self):
        """Запуск підпроцесу."""
        self.process_running = True  # Встановлюємо прапорець виконання
        try:
            result = subprocess.run(['python', 'newGeo_reference.py'], capture_output=True, text=True, check=True)

            # Отримання результату
            if result.returncode == 0:
                output = result.stdout
            else:
                output = f"Помилка:\n{result.stderr}"
        except subprocess.CalledProcessError as e:
            output = f"Помилка: {e.stderr}"
        except Exception as e:
            output = f"Неочікувана помилка: {str(e)}"

        # Показуємо результат після завершення
        self.results_label.configure(text=output)
        self.process_running = False  # Процес завершено
        self.button1.configure(state="normal")  # Знову активуємо кнопку
        self.progress_bar.pack_forget()
        self.geometry(f"540x460")

    def button2_function(self):
        # Запустити локальний сервер у фоні
        subprocess.Popen(["python", "-m", "http.server", "8000"], cwd="D:\Lessons\Stitching_algoritme")
        # Відкрити сторінку в браузері
        webbrowser.open("http://localhost:8000/view.html")


if __name__ == "__main__":
    app = GeoTaggingApp()
    app.mainloop()
