
import cv2
import numpy as np

# Load the mask image
# Note: we are reading from 'public' but execution is in root
# Ensure path is correct relative to execution or absolute
img_path = r'public/newspaper_rack_mask_full.png'
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

if img is None:
    print("Error loading image")
    exit(1)

# Threshold to ensure binary (white object, black background)
_, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if not contours:
    print("No contours found")
    exit(1)

# Find the largest contour (the gramophone)
# Sorting by area
contour = max(contours, key=cv2.contourArea)

# Approx poly to smooth it slightly and reduce points
epsilon = 0.002 * cv2.arcLength(contour, True) # Adjust 0.002 for smoothness
approx = cv2.approxPolyDP(contour, epsilon, True)

# Convert to SVG path
# Image coordinates: (x, y)
path_d = "M"
for i, point in enumerate(approx):
    x, y = point[0]
    # Scale if necessary, but request was for "path from this background image"
    # so we keep 1:1 pixel coordinates usually, or normalize?
    # User said "from this background image", usually implies pixel coordinates of the original image size.
    # The browser will handle scaling if the viewbox matches the image size.
    if i == 0:
        path_d += f" {x} {y}"
    else:
        path_d += f" L {x} {y}"

path_d += " Z"

print(f"Image Size: {img.shape[1]}x{img.shape[0]}")
print(f"Path Tokens: {len(approx)}")
print(path_d)
