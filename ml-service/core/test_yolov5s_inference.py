import cv2
import torch
from PIL import Image
from clearml import Task, Logger

task = Task.init(
    project_name='RecycleIDProject',
    task_name='Detect')

# Model
#model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
model = torch.jit.load('models/v5n_best.pt')

im1 = Image.open('models/01_20221022_145442.jpg')  # PIL image
im2 = cv2.imread('models/05_IMG_20220924_165121.jpg')[..., ::-1]  # OpenCV image (BGR to RGB)

# Inference
results = model([im1, im2], size=640) # batch of images

# Results
results.print()
results.save()  # or .show()

results.xyxy[0]  # im1 predictions (tensor)
results.pandas().xyxy[0]  # im1 predictions (pandas)

task.upload_artifact('Pandas', artifact_object=results.pandas())
#      xmin    ymin    xmax   ymax  confidence  class    name
# 0  749.50   43.50  1148.0  704.5    0.874023      0  person
# 1  433.50  433.50   517.5  714.5    0.687988     27     tie
# 2  114.75  195.75  1095.0  708.0    0.624512      0  person
# 3  986.00  304.00  1028.0  420.0    0.286865     27     tie
