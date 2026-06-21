from ultralytics import YOLO
import cv2
import numpy as np
import os
import time
import random
from datetime import datetime
from collections import deque
import UI
from ServoController import ServoController

servo = ServoController()

# =====================================
# YOLO
# =====================================

model = YOLO("yolov8n.pt")

# =====================================
# CAMERA
# =====================================

cap = cv2.VideoCapture(2)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera started")

# =====================================
# SETTINGS
# =====================================

WIDTH  = 640
HEIGHT = 480
FPS    = 30

cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS,          FPS)

# =====================================
# OUTPUT
# =====================================

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# =====================================
# RECORDING
# =====================================

recording = False
writer    = None

last_detect_time = 0
STOP_DELAY       = 2

# =====================================
# SERVO SMOOTHING
# =====================================

current_pan  = 90
current_tilt = 90

PAN_DEADZONE  = 3
TILT_DEADZONE = 3

last_servo_time = 0
SERVO_INTERVAL  = 0.05

# =====================================
# TARGET CLASSES
# yolov8n.pt supports: person, bird, airplane
# drone/uav usually needs a custom trained model
# =====================================

TARGET_CLASSES = [
    "person",
    "bird",
    "airplane",
    "aeroplane",
    "drone",
    "uav"
]

# =====================================
# TRAIL
# =====================================

trail_points = deque(maxlen=40)

# =====================================
# PARTICLES
# =====================================

particles = []
last_particle_update = 0
particle_anchor = (WIDTH // 2, HEIGHT // 2)

# =====================================
# PARTICLE FUNCTION
# =====================================

def add_particle(x, y):
    particles.append({
        "x":  x,
        "y":  y,
        "vx": random.uniform(-0.3, 0.3),
        "vy": random.uniform(-0.3, 0.3),
        "life": random.randint(40, 120),
        "size": random.randint(1, 2)
    })

# =====================================
# MAIN LOOP
# =====================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("Can't receive frame")
        break

    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    # =====================================
    # UI VALUES
    # =====================================

    particle_spread  = cv2.getTrackbarPos("Particle Spread",  "Control")
    particle_count   = cv2.getTrackbarPos("Particle Count",   "Control")
    circle_thickness = cv2.getTrackbarPos("Circle Thickness", "Control")
    box_size         = cv2.getTrackbarPos("Box Size",         "Control")
    trail_thickness  = cv2.getTrackbarPos("Trail Thickness",  "Control")
    darkness         = cv2.getTrackbarPos("Darkness",         "Control") / 100

    # =====================================
    # DARKEN FRAME
    # =====================================

    dark_frame = cv2.convertScaleAbs(frame, alpha=darkness, beta=0)

    # =====================================
    # YOLO DETECTION
    # person recognition is kept
    # bird / drone / airplane recognition added
    # =====================================

    results = model(frame, verbose=False)
    boxes   = results[0].boxes
    detected = False

    # =====================================
    # PROCESS DETECTION
    # =====================================

    for box in boxes:

        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        confidence = float(box.conf[0])

        if class_name not in TARGET_CLASSES:
            continue

        if confidence < 0.4:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        center   = (center_x, center_y)

        trail_points.append(center)
        detected = True
        last_detect_time = time.time()

        # =====================================
        # SERVO: frame coordinate to servo angle
        # =====================================

        target_pan  = int(center_x / WIDTH  * 180)
        target_tilt = int((1 - center_y / HEIGHT) * 180)

        now = time.time()

        if now - last_servo_time > SERVO_INTERVAL:

            pan_diff  = abs(target_pan  - current_pan)
            tilt_diff = abs(target_tilt - current_tilt)

            if pan_diff > PAN_DEADZONE or tilt_diff > TILT_DEADZONE:
                servo.send_pan_tilt(target_pan, target_tilt)
                current_pan  = target_pan
                current_tilt = target_tilt
                last_servo_time = now

        # =====================================
        # SMALL CENTER BOX
        # =====================================

        small_size = max(5, box_size)

        cv2.rectangle(
            dark_frame,
            (center_x - small_size, center_y - small_size),
            (center_x + small_size, center_y + small_size),
            (255, 255, 255), 1
        )

        # =====================================
        # BIG ENCLOSING CIRCLE
        # =====================================

        w = x2 - x1
        h = y2 - y1

        radius = int(max(w, h) * 0.8)

        cv2.circle(dark_frame, center, radius, (255, 255, 255), circle_thickness)

        # =====================================
        # HUD TEXT
        # =====================================

        label = f"{class_name.upper()} {confidence:.2f}  PAN:{target_pan}  TILT:{target_tilt}"

        cv2.putText(
            dark_frame, label,
            (center_x + 20, center_y - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (255, 255, 255), 1, cv2.LINE_AA
        )

        # =====================================
        # UPDATE PARTICLE FIELD
        # =====================================

        if time.time() - last_particle_update > 1.5:

            last_particle_update = time.time()

            px = random.randint(
                max(0,     center_x - particle_spread),
                min(WIDTH, center_x + particle_spread)
            )

            py = random.randint(
                max(0,      center_y - particle_spread),
                min(HEIGHT, center_y + particle_spread)
            )

            particle_anchor = (px, py)

            for _ in range(max(1, particle_count)):
                add_particle(particle_anchor[0], particle_anchor[1])

    # =====================================
    # CURVED TRAIL
    # =====================================

    if len(trail_points) >= 3:

        pts = np.array(trail_points, np.int32).reshape((-1, 1, 2))

        cv2.polylines(
            dark_frame, [pts], False,
            (255, 255, 255), max(1, trail_thickness), cv2.LINE_AA
        )

    # =====================================
    # UPDATE PARTICLES
    # =====================================

    new_particles = []

    for p in particles:

        p["x"] += p["vx"]
        p["y"] += p["vy"]

        dx = particle_anchor[0] - p["x"]
        dy = particle_anchor[1] - p["y"]

        p["x"] += dx * 0.001
        p["y"] += dy * 0.001

        p["life"] -= 1

        if p["life"] > 0:

            alpha = p["life"] / 120
            color = int(255 * alpha)

            cv2.circle(
                dark_frame,
                (int(p["x"]), int(p["y"])),
                p["size"], (color, color, color), -1
            )

            new_particles.append(p)

    particles = new_particles

    # =====================================
    # RECORDING
    # =====================================

    if detected and not recording:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath  = os.path.join(VIDEO_DIR, f"motion_{timestamp}.mp4")
        fourcc    = cv2.VideoWriter_fourcc(*'mp4v')

        writer    = cv2.VideoWriter(filepath, fourcc, FPS, (WIDTH, HEIGHT))
        recording = True

        print(f"Recording started: {filepath}")

    if recording:

        writer.write(dark_frame)

        if time.time() - last_detect_time > STOP_DELAY:
            recording = False
            writer.release()
            writer = None
            print("Recording saved")

    # =====================================
    # SHOW
    # =====================================

    cv2.imshow("Cinematic Tracking System", dark_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# =====================================
# CLEANUP
# =====================================

if writer is not None:
    writer.release()

cap.release()
cv2.destroyAllWindows()
servo.close()