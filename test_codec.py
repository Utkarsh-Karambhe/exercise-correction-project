import cv2
import numpy as np
out = cv2.VideoWriter('test.webm', cv2.VideoWriter_fourcc(*'vp80'), 30, (640, 480))
frame = np.zeros((480, 640, 3), dtype=np.uint8)
out.write(frame)
out.release()
print('Done vp80')
