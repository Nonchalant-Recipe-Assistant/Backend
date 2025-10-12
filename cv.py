import cv2
import numpy as np

# Parameters (adjust these)
input_video = "C:\\Users\\unluckyme\\Desktop\\input.mp4"
output_video = "output_blurred.mp4"
blur_strength = 51  # Must be odd number (higher = stronger blur)
x, y, w, h = 0, 0, 1080, 120  # Region to blur (x, y, width, height)

# Open video
cap = cv2.VideoCapture(input_video)
if not cap.isOpened():
    print("Error opening video")
    exit()

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Setup output video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Extract ROI (Region of Interest)
    roi = frame[y:y+h, x:x+w]
    
    # Apply blur to ROI
    blurred_roi = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
    
    # Replace original ROI with blurred version
    frame[y:y+h, x:x+w] = blurred_roi
    
    # Write frame to output
    out.write(frame)

# Cleanup
cap.release()
out.release()
cv2.destroyAllWindows()
print("Processing complete!")