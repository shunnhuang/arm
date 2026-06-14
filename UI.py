import cv2

# =====================================
# CREATE WINDOW
# =====================================

cv2.namedWindow("Control")

# =====================================
# PARTICLES
# =====================================

cv2.createTrackbar(
    "Particle Spread",
    "Control",
    120,
    400,
    lambda x: None
)

cv2.createTrackbar(
    "Particle Count",
    "Control",
    25,
    100,
    lambda x: None
)

# =====================================
# CIRCLE
# =====================================

cv2.createTrackbar(
    "Circle Thickness",
    "Control",
    2,
    20,
    lambda x: None
)

# =====================================
# BOX
# =====================================

cv2.createTrackbar(
    "Box Size",
    "Control",
    20,
    100,
    lambda x: None
)

# =====================================
# TRAIL
# =====================================

cv2.createTrackbar(
    "Trail Thickness",
    "Control",
    2,
    20,
    lambda x: None
)

# =====================================
# DARKNESS
# =====================================

cv2.createTrackbar(
    "Darkness",
    "Control",
    45,
    100,
    lambda x: None
)