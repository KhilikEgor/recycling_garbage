import torch
from .interface_model_3 import mainloop

async def detect_from_image(image_path):
    need_end = False
    busy = False
    res = None

    # create instance of our model
    model = torch.hub.load('ultralytics/yolov5', 'custom', "core/models/v5s0112.pt")

    while not need_end:
        busy = True
        res = mainloop(image_path, model, "")
        print(image_path, res, res['image_path'], res['labels_preds'])

        busy = False

        need_end = not need_end

    return res

# DEFAULT
# input_image = "alu.jpg"
# if __name__ == "__main__":
#     need_end = False
#     busy = False
#     # create instance of our model
#     model = torch.hub.load('ultralytics/yolov5', 'custom', "models/v5s0112.pt")
#
#     while not need_end:
#         busy = True
#         res = interface_model_3.mainloop(input_image, model, "")
#         print(input_image, res, res['image_path'], res['labels_preds'])
#
#         busy = False
#
#         need_end = not need_end
