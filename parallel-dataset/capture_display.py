from pypylon import pylon as py
import os
import sys
import datetime, pytz
import pygame as pg
from time import sleep
import json

from capture_display_helpers import *

"""
USAGE:
    python3 main_loop_modular.py END START DESTINATION SOURCE DISPLAY &>
"""

LOG = False
SERIAL_ARR = ['00000000', '11111111', '22222222']
CAPTURE_FORMAT = "Mono12"
DISPLAY_MODE = pg.FULLSCREEN # pg.RESIZABLE -or- pg.FULLSCREEN

## TIME VARIABLES
START_TIME = datetime.datetime.now(tz=pytz.timezone('US/Pacific'))
DATETIME = START_TIME.strftime('%d-%m-%Y_%H.%M.%S')

## PATH VARIABLES
ARGS = sys.argv
CWD = ARGS[3] if ARGS[3] else os.getcwd()
SOURCE = ARGS[4]
DESTINATION = f"{CWD}/{DATETIME}"
DISPLAY = int(ARGS[5]) if ARGS[5] else 1 # 1 is external monitor, 0 is laptop screen

PATH_ARR = set_up_directories_and_log(LOG, DESTINATION)

## CAMERA VARIABLES
NUM_CAMERAS = 3    # CHANGE BASED ON YOUR SETUP
NUM_IMG = int(ARGS[1])
start_idx = int(ARGS[2])
frame_counts = [0] * NUM_CAMERAS
EXPOSURE_TIMES = [80000, 80000, 1500]
# max = 80ms, min = 1.5ms

img = py.PylonImage()
cam_array = create_camera_env(NUM_CAMERAS, SERIAL_ARR)
cam_array.Open()

# set the exposure time for each camera
set_gain(cam_array, gain=0.0)
set_pixel_format(cam_array, CAPTURE_FORMAT)
set_exposure_times(cam_array, EXPOSURE_TIMES)
exposure_test(cam_array, EXPOSURE_TIMES)

## Metadata
metadata = init_metadata(DATETIME, DESTINATION, SOURCE, NUM_IMG, start_idx, CAPTURE_FORMAT, EXPOSURE_TIMES)

## INIT DISPLAY
screen = init_display(display=DISPLAY, mode=DISPLAY_MODE)

# natural sorting for source images so deterministic
source_imgs = filter_sort_images(SOURCE, FORMAT_LST)

## GRAB LOOP
# Loop over each image in source
for i in range(start_idx, NUM_IMG):
    filename = source_imgs[i]
    
    #checks if file is an image. if not, skip
    if not any([fmt in filename for fmt in FORMAT_LST]):
        continue
    
    for event in pg.event.get():
        if event.type == pg.QUIT or event.type == pg.KEYDOWN:
            pg.quit()
            raise SystemExit
    
    # CALIBRATE CROP POSITIONING -- tweak based on your display
    crop_dim = (1100, 1100)
    display_dim = (900, 900)
    rml_pos = (730, 60) #x, y
    dc_pos = (0, 130)
    crop_pos = (75, 0)
    dc_dim = (100, 0, 300, 300)
    rml_dim = (100, 0, 300, 300)
    print("Index: ", i)
    display_images(screen, SOURCE, filename, crop_dim, crop_pos, display_dim, rml_pos, dc_pos, dc_dim, rml_dim)
    sleep(0.5) # Reset time between images, 0.5s = 500ms

    # Loop over camera array to capture images
    capture(cam_array, img, i, PATH_ARR, frame_counts, metadata, timeout=1000)

cam_array.Close()
pg.quit()

with open(f'{DESTINATION}/metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=4)

print("Capture Successful: "+ SOURCE)

sys.stdout.close()