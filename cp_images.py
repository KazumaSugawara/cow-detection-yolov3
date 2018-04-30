#!/usr/bin/env python
# -* coding:utf-8 *-

import cv2
import argparse
import os
import glob
import shutil
from tqdm import tqdm

"""
自分のdockerコンテナ内に画像をコピーしてくるスクリプト
ex)2017年7月8日，9時から3時間分の画像をコピーしたい場合
python cp_images.py --day 20170708 --base_hour 9 --hours 3
"""

def arg_parse():

    parser = argparse.ArgumentParser()
    parser.add_argument("--day", required = True)
    parser.add_argument("--base_hour", type = int, required = True)
    parser.add_argument("--hours", type = int, required = True)

    return parser.parse_args()

if __name__ == "__main__":

    args = arg_parse()

    day = args.day
    base_hour = args.base_hour
    hours = args.hours
    last_hour = base_hour + hours

    if not os.path.exists('./00_data/videos/' + day):
        os.makedirs('./00_data/videos/' + day)

    if not os.path.exists('./00_data/pics/' + day):
        os.makedirs('./00_data/pics/' + day)

    #平畜産に変更
    img_rootd = '/var/docker/data/hira/pics'
    
    print('cp images...')
    for hour in range(base_hour, last_hour):
        hour = '%02d' % hour
        img_dir = img_rootd + '/' + args.day + '/' + hour
        img_list = sorted(glob.glob(os.path.join(img_dir, '*')))

        out_dir = './00_data/pics/' + args.day + '/' + hour

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        print(args.day, ":", hour, "----------")

        for i in tqdm(range(len(img_list))):
            img_path = img_list[i]
            out_path = out_dir + '/' +  img_path.split("/")[-1]
            shutil.copy(img_path, out_path)
