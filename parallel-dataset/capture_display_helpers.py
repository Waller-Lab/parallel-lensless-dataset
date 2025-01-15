import os
import sys
from pypylon import pylon as py
import pygame as pg
import numpy as np
from natsort import natsorted
from time import sleep

FORMAT_LST = ['.tiff', '.jpg', '.png']

def set_up_directories_and_log(log, DESTINATION):
    GT_PATH = f"{DESTINATION}/ground_truth"
    RML_PATH = f"{DESTINATION}/rml"
    DC_PATH = f"{DESTINATION}/diffusercam"
    PATH_ARR = [DC_PATH, RML_PATH, GT_PATH]

    os.makedirs(DESTINATION)
    os.makedirs(GT_PATH)
    os.makedirs(RML_PATH)
    os.makedirs(DC_PATH)

    if log:
        ## SET UP LOGGING
        sys.stdout = open(f'{DESTINATION}/log.txt', 'w') 

    return PATH_ARR

def create_camera_env(NUM_CAMERAS, SERIAL_ARR):
    # setup environment with 4 cameras 
    os.environ["PYLON_CAMEMU"] = f"{NUM_CAMERAS}"
    tlf = py.TlFactory.GetInstance()
    devices = tlf.EnumerateDevices()
    for d in devices:
        print("Cameras detected: ", d.GetModelName(), d.GetSerialNumber())

    # create array to store and attach cameras
    cam_array = py.InstantCameraArray(NUM_CAMERAS)
    for idx, cam in enumerate(cam_array):
        cam.Attach(tlf.CreateDevice(devices[idx]))

    # store a unique number for each camera to identify the incoming images
    for _, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        #TODO: USE SERIAL NUMBER TO DEFINE THE CAMERA!!!
        if camera_serial == SERIAL_ARR[0]:
            idx = 0
            # cam.Name = f"Diffusercam"
        if camera_serial == SERIAL_ARR[1]:
            idx = 1
            # cam.Name = f"RML"
        if camera_serial == SERIAL_ARR[2]:
            idx = 2
            # cam.Name = f"Ground Truth"
        cam.SetCameraContext(idx)
        
        print(f"Set context {idx} for camera {camera_serial}.")
        
    return cam_array

def set_gain(cam_array, gain=0):
     # set the gain for each camera - zero gain
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set Gain {idx} for camera {camera_serial}")
        cam.Gain = 0.0 

def set_pixel_format(cam_array, CAPTURE_FORMAT):
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set PixelFormat {idx} for camera {camera_serial}")
        cam.PixelFormat.SetValue(CAPTURE_FORMAT)
        print("Pixel Format: ", cam.PixelFormat.GetValue())

def init_metadata(DATETIME, DESTINATION, SOURCE, NUM_IMG, start_idx, CAPTURE_FORMAT, exposure_times):
        metadata = {
            "Acquisition Date/Time: ": DATETIME,
            "Destination Data Path": DESTINATION,
            "Source Image Path": SOURCE,
            "Number of Images": NUM_IMG,
            "Image Start Index": start_idx,
            "Capture Format": CAPTURE_FORMAT,
            
            "DiffuserCam": {
                "Exposure": exposure_times[0]
            },
            "RML": {
                "Exposure" : exposure_times[1]
            },
            "Ground Truth" : {
                "Exposure": 0 if len(exposure_times) < 3 else exposure_times[2]
            },

            "Failed Images": []
        }
        
        return metadata

def append_metadata(metadata, values: tuple):
    metadata[str(values[0])] = values[1]

def filter_sort_images(SOURCE, FORMAT_LST):
    source_imgs = os.listdir(SOURCE)
    source_imgs = [img for img in source_imgs if any([fmt in img for fmt in FORMAT_LST])]
    source_imgs = [img for img in source_imgs if not img.startswith('.')]
    source_imgs = natsorted(source_imgs)
    return source_imgs

def set_exposure_times(cam_array, exposure_times):
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set Exposuretime {idx} for camera {camera_serial} as {exposure_times[idx]}")
        cam.ExposureTime = exposure_times[idx]

def init_display(display=1, mode=pg.FULLSCREEN):
    pg.init()
    screen_info = pg.display.Info()
    print(pg.display.Info())
    width, height = screen_info.current_w, screen_info.current_h

    # Creates a canvas of the desired size. Everything drawn to this canvas.
    #   Set according to system params.
    screen = pg.display.set_mode((width, height), mode, display=display)
    black_color = (0, 0, 0) # modifying in case different
    screen.fill(black_color)
    pg.display.flip()
    
    return screen

def capture(cam_array, img, i, PATH_ARR, frame_counts, metadata, timeout=1000):
    for cam in cam_array:
        cam.StartGrabbing(py.GrabStrategy_LatestImageOnly) # exposure delay = 46ms
        sleep(0.2) # 200ms delay
        with cam.RetrieveResult(timeout) as res:
            cam_id = res.GetCameraContext()
            img_nr = frame_counts[cam_id]
            
            if res.GrabSucceeded():
                cam_path = PATH_ARR[cam_id]
                frame_counts[cam_id] += 1

                print(f"Captured Image #{img_nr} using Cam #{cam_id}", '\n')

                img.AttachGrabResultBuffer(res)
                # print maximum value of image
                array_value = img.GetArray()
                print(f"Max value: {np.max(array_value)}, Min value: {np.min(array_value)}, Mean value: {np.mean(array_value)}")
                
                # save image
                filename = f"{cam_path}/img_{i}_cam_{cam_id}.tiff"
                img.Save(py.ImageFileFormat_Tiff, filename)
                img.Release()
            else:
                print(f"Failed: Image #{img_nr} of Cam #{cam_id}")
                metadata["Failed Images"].append(( "Image: " + str(img_nr), filename, "Camera: " + str(cam_id)))
        cam.StopGrabbing()

# TODO: descriptive parameters for shifting images

def display_images(screen, SOURCE, filename, crop_dim=(625, 625), crop_pos=(400, 0), display_dim=(500, 500), rml_pos=(200, 0), dc_pos=(0, 0), dc_dim=(100, 0, 300, 300), rml_dim=(100, 0, 300, 300)):
    """"
    crop_dim: dimensions of crop surface
    display_dim: dimensions of display surface
    rml_pos: position of rml image on crop surface
    dc_pos: position of diffusercam image on crop surface
    crop_pos: position of crop surface on display surface
    """
    screen.fill("black")
    print("Displaying: ", SOURCE + filename)
    image = pg.image.load(SOURCE + filename)
    img_size = image.get_size() # (width,height)
    print(f"Image Size: {img_size}")

    ## initialize the surface
    # Create a canvas of size that will be placed onto screen.
    # OLD --- 
    crop = pg.Surface(crop_dim)

    ### IPAD:
    # crop = pg.Surface((300, 300))

    #Transpose img if vertical --> all horizontal
    if img_size[0] < img_size[1]:
        image = pg.transform.flip(image, True , False)

    # Overlay images onto crop --- (image, (top left corner of image), (square positions and dimensions of image))
    # OLD: 
    crop.blits(((image, dc_pos, dc_dim), (image, rml_pos, rml_dim)))


    ### IPAD COORDS
    # Creates a 300x300 image
    # crop.blit(image, (0, 0), area=(0, 0, 300, 300))
    # # RML
    # screen.blit(pg.transform.scale(crop, (600, 600)), (1500, 250))   # Draw the resized image on the screen
    # # DC
    # screen.blit(pg.transform.scale(crop, (600, 600)), (0, 500))   # Draw the resized image on the screen

    ###OLD
    # resize to new size on screen.
    screen.blit(pg.transform.scale(crop, display_dim), crop_pos)
    pg.display.flip()

def display_single_image(screen, SOURCE, filename, crop_dim=(625, 625), crop_pos=(400, 0), display_dim=(500, 500), rml_pos=(200, 0), dc_pos=(0, 0), dc_dim=(100, 0, 300, 300), rml_dim=(100, 0, 300, 300), camera=0):
    """"
    crop_dim: dimensions of crop surface
    display_dim: dimensions of display surface
    rml_pos: position of rml image on crop surface
    dc_pos: position of diffusercam image on crop surface
    crop_pos: position of crop surface on display surface
    """
    screen.fill("black")
    print("Displaying: ", SOURCE + filename)
    image = pg.image.load(SOURCE + filename)
    img_size = image.get_size() # (width,height)
    print(f"Image Size: {img_size}")

    ## initialize the surface
    # Create a canvas of size that will be placed onto screen.
    # OLD --- 
    crop = pg.Surface(crop_dim)

    ### IPAD:
    # crop = pg.Surface((300, 300))

    #Transpose img if vertical --> all horizontal
    if img_size[0] < img_size[1]:
        image = pg.transform.flip(image, True , False)

    # Overlay images onto crop --- (image, (top left corner of image), (square positions and dimensions of image))
    # OLD: 
    if camera == 0:
        crop.blit(image, dc_pos, dc_dim)
    elif camera == 1:
        crop.blit(image, rml_pos, rml_dim)
    
    # crop.blits(((image, dc_pos, dc_dim), (image, rml_pos, rml_dim)))


    ### IPAD COORDS
    # Creates a 300x300 image
    # crop.blit(image, (0, 0), area=(0, 0, 300, 300))
    # # RML
    # screen.blit(pg.transform.scale(crop, (600, 600)), (1500, 250))   # Draw the resized image on the screen
    # # DC
    # screen.blit(pg.transform.scale(crop, (600, 600)), (0, 500))   # Draw the resized image on the screen

    ###OLD
    # resize to new size on screen.
    screen.blit(pg.transform.scale(crop, display_dim), crop_pos)
    pg.display.flip()

def exposure_test(cam_array, exposure_times):
    for idx, cam in enumerate(cam_array):
       assert cam.ExposureTime.GetValue() == exposure_times[idx], "Exposure time not set correctly."