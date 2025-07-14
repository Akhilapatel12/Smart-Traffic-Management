import cv2
import numpy as np
from ultralytics import YOLO
import os
import tkinter as tk
from tkinter import filedialog, messagebox, Canvas
import logging
from datetime import datetime
import green_time_signal
import time

# Set up logging
logging.basicConfig(
    filename="traffic_app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class TrafficApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Traffic Management - Login")
        self.root.geometry("300x200")
        self.model = None
        self.flashing = False

        # Login window
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 12))
        self.username_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Password:", font=("Arial", 12)).pack()
        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 12))
        self.password_entry.pack(pady=5)

        tk.Button(self.login_frame, text="Login", command=self.check_login, font=("Arial", 12)).pack(pady=10)

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == "admin" and password == "traffic123":
            logging.info("Login successful")
            self.login_frame.destroy()
            self.setup_main_window()
        else:
            messagebox.showerror("Error", "Invalid username or password")
            logging.error("Login failed: Invalid credentials")

    def setup_main_window(self):
        self.root.title("Smart Traffic Management")
        self.root.geometry("400x600")

        # Main window elements
        self.label = tk.Label(self.root, text="Upload an image to calculate green signal time", font=("Arial", 12))
        self.label.pack(pady=10)

        self.upload_btn = tk.Button(self.root, text="Upload Image", command=self.upload_image, font=("Arial", 12))
        self.upload_btn.pack(pady=10)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 12, "bold"))
        self.result_label.pack(pady=10)

        # Traffic light canvas
        self.canvas = Canvas(self.root, width=100, height=200)
        self.canvas.pack(pady=10)
        self.red_light = self.canvas.create_oval(30, 20, 70, 60, fill="grey")
        self.yellow_light = self.canvas.create_oval(30, 80, 70, 120, fill="grey")
        self.green_light = self.canvas.create_oval(30, 140, 70, 180, fill="grey")

        # Progress bar canvas
        self.progress_canvas = Canvas(self.root, width=300, height=20)
        self.progress_canvas.pack(pady=10)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="blue")

        self.load_model()

    def load_model(self):
        logging.info("Loading YOLOv8 model")
        for attempt in range(3):
            try:
                self.model = YOLO("yolov8l.pt")  # Use yolov8l.pt for better accuracy
                logging.info("YOLOv8 large model loaded successfully")
                return
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}/3: Error loading YOLOv8 large model: {e}")
                try:
                    self.model = YOLO("yolov8m.pt")
                    logging.info("YOLOv8 medium model loaded successfully")
                    return
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1}/3: Error loading YOLOv8 medium model: {e}")
                    time.sleep(1)
        messagebox.showerror("Error", "Failed to load YOLOv8 model after 3 attempts")
        logging.error("Failed to load YOLOv8 model after 3 attempts")
        self.root.quit()

    def upload_image(self):
        logging.info("Opening file dialog for image upload")
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JPEG files", "*.jpg;*.jpeg")])
            if not file_path:
                logging.info("No file selected")
                return
            self.process_image(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error processing image: {e}")
            logging.error(f"Error in upload_image: {e}")

    def update_progress(self, progress):
        width = 300 * progress
        self.progress_canvas.coords(self.progress_bar, 0, 0, width, 20)
        self.root.update()

    def flash_text(self):
        if self.flashing:
            current_color = self.result_label.cget("foreground")
            new_color = "black" if current_color == "red" else "red"
            self.result_label.config(foreground=new_color)
            self.root.after(500, self.flash_text)

    def process_image(self, file_path):
        logging.info(f"Processing image: {file_path}")
        # Show red light and start progress bar
        self.canvas.itemconfig(self.red_light, fill="red")
        self.canvas.itemconfig(self.yellow_light, fill="grey")
        self.canvas.itemconfig(self.green_light, fill="grey")
        self.result_label.config(text="Processing...", foreground="black")
        self.flashing = False
        self.root.update()

        # Simulate progress (2-5 seconds)
        for i in range(1, 11):
            self.update_progress(i / 10)
            time.sleep(0.3)  # Simulate processing time

        # Clear previous vehicle_count.txt
        count_file = "vehicle_count.txt"
        if os.path.exists(count_file):
            os.remove(count_file)
            logging.info(f"Deleted previous {count_file}")

        vehicle_count = self.detect_vehicles(file_path)
        if vehicle_count is None:
            self.canvas.itemconfig(self.red_light, fill="grey")
            self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 20)
            messagebox.showwarning("Warning", "No vehicles detected or image processing failed.")
            logging.warning("No vehicles detected or image processing failed")
            return

        green_time = green_time_signal.adjust_green_signal_time(vehicle_count)
        self.result_label.config(text=f"Detected {vehicle_count} vehicles\nGreen Signal Time: {green_time} seconds", foreground="black")
        logging.info(f"Vehicle count: {vehicle_count}, Green signal time: {green_time} seconds")

        # Start flashing text
        self.flashing = True
        self.flash_text()

        # Show green light animation
        self.canvas.itemconfig(self.red_light, fill="grey")
        self.canvas.itemconfig(self.green_light, fill="green")
        self.root.update()
        self.root.after(int(green_time * 1000), self.reset_animations)

    def reset_animations(self):
        self.canvas.itemconfig(self.green_light, fill="grey")
        self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 20)
        self.result_label.config(text="")
        self.flashing = False
        self.root.update()

    def detect_vehicles(self, image_path):
        logging.info(f"Detecting vehicles in: {image_path}")
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Could not load image: {image_path}")
                return None
            logging.info(f"Image loaded, Shape: {image.shape}")

            # Enhance contrast
            image = cv2.convertScaleAbs(image, alpha=1.2, beta=10)
            logging.info("Applied contrast enhancement")

            # Resize image (preserve aspect ratio)
            max_width, max_height = 1280, 720
            height, width = image.shape[:2]
            scale = min(max_width / width, max_height / height, 1.0)
            new_width, new_height = int(width * scale), int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            logging.info(f"Image resized to: {new_width}x{new_height}")

            # Detect objects
            results = self.model(image, conf=0.5, iou=0.7)
            vehicle_count = 0
            vehicle_classes = [2, 3, 5, 7]
            colors = {
                2: (0, 255, 0),
                3: (0, 0, 255),
                5: (255, 0, 0),
                7: (0, 255, 255)
            }

            detected_vehicles = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if class_id in vehicle_classes:
                        vehicle_count += 1
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = box.conf[0]
                        label = f"{self.model.names[class_id]} {conf:.2f}"
                        color = colors.get(class_id, (0, 255, 0))
                        cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
                        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        detected_vehicles.append(label)
            logging.info(f"Detection complete: {vehicle_count} vehicles detected: {detected_vehicles}")

            # Add vehicle count to image
            cv2.putText(image, f"Vehicles: {vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

            # Save annotated image
            output_dir = "images"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_image = os.path.join(output_dir, f"output_{os.path.basename(image_path).split('.')[0]}_{timestamp}.jpg")
            try:
                cv2.imwrite(output_image, image)
                logging.info(f"Annotated image saved: {output_image}")
            except Exception as e:
                logging.error(f"Error saving output image: {e}")

            # Save vehicle count
            try:
                with open("vehicle_count.txt", "w") as f:
                    f.write(str(vehicle_count))
                logging.info(f"Vehicle count saved to vehicle_count.txt: {vehicle_count}")
            except Exception as e:
                logging.error(f"Error writing to vehicle_count.txt: {e}")

            return vehicle_count
        except Exception as e:
            logging.error(f"Error in detect_vehicles: {e}")
            return None

if __name__ == "__main__":
    try:
        logging.info("Starting TrafficApp")
        root = tk.Tk()
        app = TrafficApp(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")