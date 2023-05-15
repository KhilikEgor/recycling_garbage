import torch
import cv2
import os
import argparse
from scanf import scanf
from pathlib import Path

BOX_COLOR = (0, 255, 0)  # Green
TEXT_COLOR = (255, 255, 255)  # White

parser = argparse.ArgumentParser()
#parser.add_argument("-m", "--model", help="path to model", required=True)
parser.add_argument("-m", "--model", help="path to model", default="models/v5s0112.pt")
#parser.add_argument("-i", "--input_image", help="path to input image or path to image folder", required=True)
parser.add_argument("-i", "--input_image", help="path to input image or path to image folder", default=".")

parser.add_argument("-fr", "--find_images_recursively", help="find files recursively in image folder", action='store_true')
parser.add_argument("-v", "--visualize", help="visualize result of detection", action='store_true')
parser.add_argument("-sc", "--save_crops", help="save crop results", action='store_true')
parser.add_argument("-o", "--output_template_path", help="template path to output image", default="runs/mdetect/exp")
parser.add_argument("-oi", "--increment_output_path", help="need to increment template path to output image", action='store_true')
parser.add_argument("-no-oi", "--no_increment_output_path", help="not need to increment template path to output image", dest="increment_output_path", action='store_false')
parser.add_argument("-cml", "--clearml", help="enable logger", action='store_true')
parser.add_argument("-p", "--project_name", help="clearml project_name", default="RecycleIDProject")
parser.add_argument("-t", "--task_name", help="clearml task_name", default="Detect")
parser.set_defaults(find_images_recursively=False, visualize=False, save_crops=False, increment_output_path=True, clearml=False)
args = parser.parse_args()
print(f"Input args: {args}")


if args.clearml:
    from clearml import Task, Logger
    task = Task.init(
        project_name=args.project_name,
        task_name=args.task_name)

def visualize_bbox(img, bbox, class_name, color=BOX_COLOR, thickness=20):
    """Visualizes a single bounding box on the image"""
    x_min, x_max, y_min, y_max = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color=color, thickness=thickness)

    ((text_width, text_height), _) = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_DUPLEX, 1, 1)

    cv2.rectangle(img, (x_min, y_min - int(1.7 * text_height)), (x_min + text_width, y_min), BOX_COLOR, -1)
    cv2.putText(
        img,
        text=class_name,
        org=(x_min, y_min - int(0.5 * text_height)),
        fontFace=cv2.FONT_HERSHEY_DUPLEX,
        fontScale=1,
        color=TEXT_COLOR,
        lineType=cv2.LINE_AA,
        thickness=2
    )
    return img

def visualize(image, preds, category_id_to_name):
    img = image.copy()
    try:
        for pred in preds[0]:
            bbox = pred[0:4].tolist()
            conf = pred[4].tolist()
            category_id = int(pred[5].tolist())
            class_name = category_id_to_name[int(category_id)]
            img = visualize_bbox(img, bbox, f"{class_name} ({conf:0.3f})")

        if args.visualize:
            cv2.namedWindow("img", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("img", 1000, 1000)
            cv2.imshow("img", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    except:
        print("[visualize] No detections\n")
    return img

def increment_path(path, exist_ok=False, sep='', mkdir=False):
    # Increment file or directory path, i.e. runs/exp --> runs/exp{sep}2, runs/exp{sep}3, ... etc.
    path = Path(path)  # os-agnostic
    if path.exists() and not exist_ok:
        path, suffix = (path.with_suffix(''), path.suffix) if path.is_file() else (path, '')

        # Method 1
        for n in range(2, 9999):
            p = f'{path}{sep}{n}{suffix}'  # increment path
            if not os.path.exists(p):  #
                break
        path = Path(p)
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)  # make directory

    return path

def mainloop(img_fname, model, iteration):
    img_fname = img_fname
    image = cv2.imread(img_fname) #[..., ::-1]

    # get labels and bounding box (BB) coords
    results = model(image)  # inference
    img = visualize(image, results.xyxy, results.names)

    if args.increment_output_path:
        res_imgfname = f"{increment_path(args.output_template_path, exist_ok=False, mkdir=True)}/labeled_{img_fname}"
    else:
        res_imgfname = f"{args.output_template_path}/labeled_{img_fname}"
    cv2.imwrite(res_imgfname, img)

    # print results to stdout
    results.print()  # or .show(), .save(), .crop(), .pandas(), etc.Results
    print("Saved results to : ", res_imgfname)

    if args.save_crops:
        crops = results.crop(save=True)  # specify save dir - save_dir='runs/detect/exp'

    if args.clearml:
        try:
            Logger.current_logger().report_image(f"Image {iteration}", "Input image", image=image)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

        try:
            Logger.current_logger().report_image("Image", "Labeled image", image=img)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

        try:
            Task.current_task().upload_artifact('Output results', artifact_object=results.pandas())
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

    # get and print to stdout BB coords
    #print("pandas: ", results.pandas())
    #print("pred: ", results.pred[0], len(results.pred[0]))
    preds = [(results.names[int(x[-1])], float(x[-2])) for x in results.pred[0]] if len(results.pred[0]) > 0 else None

    if args.clearml:
        Task.current_task().upload_artifact('Statistics', artifact_object=results.pandas())

    return {'image_path': res_imgfname, 'labels_preds': preds}


if __name__ == "__main__":
        # create instance of our model
    try:
        model = torch.hub.load('ultralytics/yolov5', 'custom', args.model)
    except:
        model = torch.hub.load('ultralytics/yolov5', args.model)

    if os.path.isdir(args.input_image):
        ext = ['png', 'jpg', 'gif']
        files = []
        if args.find_images_recursively:
            [files.extend(Path(args.input_image).rglob(f'*.{e}')) for e in ext]
        else:
            [files.extend(Path(args.input_image).glob(f'*.{e}')) for e in ext]
        for i, im in enumerate(files):
            res = mainloop(im, model, i)
            print(im, res)
    else:
        res = mainloop(args.input_image, model, "")
        print(args.input_image, res)

    if args.clearml:
        Task.current_task().close()

