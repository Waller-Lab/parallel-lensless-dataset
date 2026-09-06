from pypylon import pylon as py
import numpy as np
import os
import sys
import datetime, pytz
import pygame as pg
from time import sleep
import json

from capture_display_helpers import *

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add after other global variables
# Email Configuration
SENDER_EMAIL = "TODO"  # Replace with your email
SENDER_PASSWORD = "TODO"   # Replace with your app password
RECIPIENT_EMAIL = "TODO"  # Replace with recipient email

def send_notification_email(start_time, status="success", error_msg=None, num_images=None, source_path=None):
    """Send email notification about script status
    
    Args:
        start_time: Script start time
        status: 'success' or 'error'
        error_msg: Error message if status is 'error'
        num_images: Number of images processed
        source_path: Source directory path
    """
    end_time = datetime.datetime.now(tz=pytz.timezone('US/Pacific'))
    duration = end_time - start_time
    
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    
    if status == "success":
        message["Subject"] = "Image Capture Complete"
        body = f"""
        Image capture process has completed successfully!
        
        Start time: {start_time}
        End time: {end_time}
        Duration: {duration}
        Images processed: {num_images}
        Source path: {source_path}
        Destination: {DESTINATION}
        """
    else:
        message["Subject"] = "⚠️ Image Capture Error"
        body = f"""
        Image capture process encountered an error!
        
        Start time: {start_time}
        Error time: {end_time}
        Duration before error: {duration}
        Error message: {error_msg}
        """
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        server.quit()
        print("Notification email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
    end_time = datetime.datetime.now(tz=pytz.timezone('US/Pacific'))
    duration = end_time - start_time
    
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    message["Subject"] = "Image Capture Complete"
    
    body = f"""
    Image capture process has completed!
    
    Start time: {start_time}
    End time: {end_time}
    Duration: {duration}
    Images processed: {num_images}
    Source path: {source_path}
    Destination: {DESTINATION}
    """
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        server.quit()
        print("Completion email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")



"""
NUM_IMG: total num imgs
NUM_CAMERAS: total num cameras

frames_to_grab: num frames each camera grabs
frame_counts: array storing frame counts of each camera

0: diffuser
1: rml
2: ground truth

python3 capture_display.py END START DESTINATION SOURCE DISPLAY &>
"""
try:
    log = True

    ## TIME TICK TICK
    START_TIME = datetime.datetime.now(tz=pytz.timezone('US/Pacific'))
    DATETIME = START_TIME.strftime('%d-%m-%Y_%H.%M.%S')

    SERIAL_ARR = ['40270065', '40270083', '40412531'] # replace with your camera serial numbers
    CAPTURE_FORMAT = "RGB8"

    ## PATH VARIABLES
    ARGS = sys.argv
    CWD = ARGS[3] if ARGS[3] else os.getcwd()
    SOURCE = ARGS[4]
    DESTINATION = f"{CWD}/{DATETIME}"
    DISPLAY = int(ARGS[5]) if ARGS[5] else 1 # 1 is external monitor, 0 is laptop screen, 0 if debug
    DISPLAY_MODE = pg.FULLSCREEN #pg.RESIZABLE 

    PATH_ARR = set_up_directories_and_log(log, DESTINATION)

    ## CAMERA VARIABLES
    NUM_CAMERAS = 3
    NUM_IMG = int(ARGS[1])
    start_idx = int(ARGS[2])
    frame_counts = [0]*NUM_CAMERAS if NUM_CAMERAS > 1 else [0] * 3
    # max = 80ms, min = 1.5ms
    ## DISPLAY
    # DC, RML, GT
    exposure_times = [25000, 80000, 18000] 

    img = py.PylonImage()

    cam_array = create_camera_env(NUM_CAMERAS, SERIAL_ARR)
    cam_array.Open()

    # set the exposure time for each camera
    set_gain(cam_array, gain=0.0)
    set_pixel_format(cam_array, CAPTURE_FORMAT)
    set_exposure_times(cam_array, exposure_times)
    exposure_test(cam_array, exposure_times)

    ## set white balance once based on calibrated values
    set_white_balance_manual(cam_array)
    set_color_space(cam_array)

    ## Metadata
    metadata = init_metadata(DATETIME, DESTINATION, SOURCE, NUM_IMG, start_idx, CAPTURE_FORMAT, exposure_times)

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
        
        # CROP POSITIONING x, y
        crop_dim = (1100, 1100)
        display_dim = (900, 900)
        rml_pos = (730, 60)
        dc_pos = (30, 165)
        crop_pos = (75, 0)
        dc_dim = (100, 0, 300, 300)
        rml_dim = (100, 0, 300, 300)
        print("Index: ", i)
        display_images(screen, SOURCE, filename, crop_dim, crop_pos, display_dim, rml_pos, dc_pos, dc_dim, rml_dim)
        sleep(0.5) # SECONDS. Reset time between images, 0.5s = 500ms

        # Loop over camera array to capture images, includes 200ms sleep between captures
        _ = capture(cam_array, img, i, PATH_ARR, frame_counts, metadata, timeout=1000)

    cam_array.Close()
    pg.quit()
    with open(f'{DESTINATION}/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    print("Capture Successful: "+ SOURCE)
    send_notification_email(START_TIME, "success", num_images=NUM_IMG, source_path=SOURCE)

except KeyboardInterrupt:
    error_msg = "Script interrupted by user (KeyboardInterrupt)"
    send_notification_email(START_TIME, "error", error_msg)
    raise

except Exception as e:
    error_msg = f"Unexpected error: {str(e)}"
    send_notification_email(START_TIME, "error", error_msg)
    raise

sys.stdout.close()