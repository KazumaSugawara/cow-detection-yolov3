#!/usr/bin/env bash

set -eu

DAY="20180323"
BASE_HOUR=9
HOURS=3

python cp_images.py --day $DAY --base_hour $BASE_HOUR --hours $HOURS
python video_demo.py --day $DAY --base_hour $BASE_HOUR --hours $HOURS
