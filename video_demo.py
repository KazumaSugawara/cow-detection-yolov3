from __future__ import division
#import time
import torch
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
import cv2
from util import *
from darknet import Darknet
from preprocess import prep_image, inp_to_image
import pandas as pd
import random
import pickle as pkl
import argparse
import os
import glob
import csv
from tqdm import tqdm
from pathlib import Path

def get_test_input(input_dim, CUDA):
    img = cv2.imread("dog-cycle-car.png")
    img = cv2.resize(img, (input_dim, input_dim))
    img_ =  img[:,:,::-1].transpose((2,0,1))
    img_ = img_[np.newaxis,:,:,:]/255.0
    img_ = torch.from_numpy(img_).float()
    img_ = Variable(img_)

    if CUDA:
        img_ = img_.cuda()

    return img_

def prep_image(img, inp_dim):
    """
    Prepare image for inputting to the neural network.

    Returns a Variable
    """
    orig_im = cv2.imread(img)
    dim = orig_im.shape[1], orig_im.shape[0]
    img = cv2.resize(orig_im, (inp_dim, inp_dim))
    img_ = img[:,:,::-1].transpose((2,0,1)).copy()
    img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
    return img_, orig_im, dim

"""
def write(x, img):
    c1 = tuple(x[1:3].int())
    c2 = tuple(x[3:5].int())
    cls = int(x[-1])
    label = "{0}".format(classes[cls])
    color = random.choice(colors)
    cv2.rectangle(img, c1, c2,color, 1)
    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
    c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
    cv2.rectangle(img, c1, c2,color, -1)
    cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1);
    return img
"""

def arg_parse():
    """
    Parse arguements to the detect module

    """
    parser = argparse.ArgumentParser()

    #parser.add_argument("--video", dest = 'video', help = "Video to run detection upon", default = "video.avi", type = str)
    #parser.add_argument("--dataset", dest = "dataset", help = "Dataset on which the network has been trained", default = "pascal")

    """
    日付，時間を指定 base_hourを起点にhours時間分処理を行う
    ex) python video_demo.py --day 20170603 --base_hour 7 --hours 3 
    """
    parser.add_argument("--day", required = True)
    parser.add_argument("--base_hour", type = int, required = True)
    parser.add_argument("--hours", type = int, required = True)

    # 変更必要なし
    parser.add_argument("--confidence", dest = "confidence", help = "Object Confidence to filter predictions", default = 0.5)
    parser.add_argument("--nms_thresh", dest = "nms_thresh", help = "NMS Threshhold", default = 0.4)
    parser.add_argument("--cfg", dest = 'cfgfile', help = "Config file", default = "cfg/yolov3.cfg", type = str)
    parser.add_argument("--weights", dest = 'weightsfile', help = "weightsfile", default = "yolov3.weights", type = str)
    parser.add_argument("--reso", dest = 'reso', help = "Input resolution of the network. Increase to increase accuracy. Decrease to increase speed", default = "416", type = str)

    return parser.parse_args()


if __name__ == '__main__':
    args = arg_parse()
    confidence = float(args.confidence)
    nms_thesh = float(args.nms_thresh)
    #start = 0

    CUDA = torch.cuda.is_available()

    num_classes = 80

    CUDA = torch.cuda.is_available()

    bbox_attrs = 5 + num_classes
    print("Cow detection by YOLO v3...")
    print("Loading network.....")
    model = Darknet(args.cfgfile)
    model.load_weights(args.weightsfile)
    print("Network successfully loaded")

    model.net_info["height"] = args.reso
    inp_dim = int(model.net_info["height"])
    assert inp_dim % 32 == 0
    assert inp_dim > 32

    if CUDA:
        model.cuda()

    model(get_test_input(inp_dim, CUDA), CUDA)

    model.eval()

    #日時，時間
    day = args.day
    base_hour = args.base_hour
    hours = args.hours
    last_hour = base_hour + hours

    img_rootd = './00_data/pics'
    out_rootd = './10_coords'

    out_dir = out_rootd + '/' + day
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    #videofile = args.video
    #cap = cv2.VideoCapture(videofile)
    #assert cap.isOpened(), 'Cannot capture source'

    #frames = 0
    #start = time.time()
    #while cap.isOpened():
    for hour in range(base_hour, last_hour):

        hour = '%02d' % hour
        #ret, frame = cap.read()

        #
        img_dir = Path(img_rootd + '/' + day + '/' + hour + '/')
        #img_list = sorted(glob.glob(os.path.join(img_dir, '*')))
        img_list = sorted(list(img_dir.glob('*.jpg')))

        out_file = out_dir + '/' + day + hour + '.csv'
        #if ret:
        print('write to:',out_file, '-----------------')
        with open(out_file, 'w') as f:
            writer = csv.writer(f, lineterminator='\n')

            for img_path in tqdm(img_list):
                img, orig_im, dim = prep_image(str(img_path), inp_dim)

                im_dim = torch.FloatTensor(dim).repeat(1,2)

                if CUDA:
                    im_dim = im_dim.cuda()
                    img = img.cuda()

                output = model(Variable(img, volatile = True), CUDA)
                output = write_results(output, confidence, num_classes, nms = True, nms_conf = nms_thesh)

                if type(output) == int:
                    """
                    frames += 1
                    print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
                    cv2.imshow("frame", orig_im)
                    key = cv2.waitKey(1)
                    if key & 0xFF == ord('q'):
                        break
                    """
                    continue

                output[:,1:5] = torch.clamp(output[:,1:5], 0.0, float(inp_dim))

                im_dim = im_dim.repeat(output.size(0), 1)/inp_dim
                output[:,1:5] *= im_dim

                #classes = load_classes('data/coco.names')
                #colors = pkl.load(open("pallete", "rb"))

                coords = [ list(map(int, x[1:5])) for x in output ]
                num_box = str(len(coords))
                coords_all = [img_path, num_box]
                for coord in coords:
                    coords_all += coord
                writer.writerow(coords_all)

            """ 
                list(map(lambda x: write(x, orig_im), output))

                cv2.imshow("frame", orig_im)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                frames += 1
                print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))


            else:
                break
            """
