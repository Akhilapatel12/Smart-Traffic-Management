import cv2
import numpy as np
from ultralytics import YOLO
import os
from datetime import datetime

def detect_vehicles(image_path, output_file="vehicle_count.txt"):
    # Clear previous vehicle_count.txt
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted previous {output_file}")

    # Load YOLOv8 model (use yolov8l.pt for better accuracy if available)
    try:
        model = YOLO("yolov8l.pt")  # Switch to yolov8l.pt if downloaded
        print("YOLOv8 large model loaded successfully")
    except Exception as e:
        print(f"Error loading YOLOv8 model, falling back to yolov8m.pt: {e}")
        try:
            model = YOLO("yolov8m.pt")
            print("YOLOv8 medium model loaded successfully")
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
            return 0

    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return 0
    print(f"Image loaded: {image_path}, Shape: {image.shape}")

    # Enhance contrast
    image = cv2.convertScaleAbs(image, alpha=1.2, beta=10)
    print("Applied contrast enhancement")

    # Resize image (preserve aspect ratio, max 1280x720)
    max_width, max_height = 1280, 720
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height, 1.0)
    new_width, new_height = int(width * scale), int(height * scale)
    image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    print(f"Image resized to: {new_width}x{new_height}")

    # Detect objects with higher confidence and IoU threshold
    results = model(image, conf=0.5, iou=0.7)
    vehicle_count = 0
    vehicle_classes = [2, 3, 5, 7]  # COCO: car, motorcycle, bus, truck
    colors = {
        2: (0, 255, 0),   # Car: Green
        3: (0, 0, 255),   # Motorcycle: Red
        5: (255, 0, 0),   # Bus: Blue
        7: (0, 255, 255)  # Truck: Cyan
    }

    # Process detections
    detected_vehicles = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            if class_id in vehicle_classes:
                vehicle_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                label = f"{model.names[class_id]} {conf:.2f}"
                color = colors.get(class_id, (0, 255, 0))
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
                cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                detected_vehicles.append(label)
    print(f"Detection complete: {vehicle_count} vehicles detected: {detected_vehicles}")

    # Add vehicle count to image
    cv2.putText(image, f"Vehicles: {vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    # Save annotated image
    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_image = os.path.join(output_dir, f"output_{os.path.basename(image_path).split('.')[0]}_{timestamp}.jpg")
    try:
        cv2.imwrite(output_image, image)
        print(f"Annotated image saved: {output_image}")
    except Exception as e:
        print(f"Error saving output image: {e}")

    # Save vehicle count
    try:
        with open(output_file, "w") as f:
            f.write(str(vehicle_count))
        print(f"Vehicle count saved to {output_file}: {vehicle_count}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

    return vehicle_count