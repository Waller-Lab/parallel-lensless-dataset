import os
import sys
from pypylon import pylon as py
import pygame as pg
import numpy as np
from natsort import natsorted
from time import sleep

FORMAT_LST = ['.tiff', '.jpg', '.png']

def set_up_directories_and_log(log, DESTINATION):
    """
    sets up output directories and log file if log==True
    """
    GT_PATH = f"{DESTINATION}/ground_truth"
    RML_PATH = f"{DESTINATION}/rml"
    DC_PATH = f"{DESTINATION}/diffuser"
    PATH_ARR = [DC_PATH, RML_PATH, GT_PATH]

    os.makedirs(DESTINATION)
    os.makedirs(GT_PATH)
    os.makedirs(RML_PATH)
    os.makedirs(DC_PATH)

    if log:
        ## SET UP LOGGING
        sys.stdout = open(f'{DESTINATION}/log.txt', 'w') 

    return PATH_ARR

def create_camera_env(NUM_CAMERAS, SERIAL_ARR, index=None):
    """
    sets up basler pylon camera environment.
    defines camera indicies:
    - 0 = Diffuser
    - 1 = RML
    - 2 = Ground Truth
    """
    os.environ["PYLON_CAMEMU"] = f"{NUM_CAMERAS}"
    tlf = py.TlFactory.GetInstance()
    devices = tlf.EnumerateDevices()
    for d in devices:
        print("Cameras detected: ", d.GetModelName(), d.GetSerialNumber())

    # create array to store and attach cameras
    cam_array = py.InstantCameraArray(NUM_CAMERAS)
    if index != None and len(SERIAL_ARR) == 1:
        # logic for using just one camera
        print(f"Using just one camera with serial number {SERIAL_ARR[0]}") 
        for cam in cam_array:
            cam.Attach(tlf.CreateDevice(devices[index]))
    else:
        for idx, cam in enumerate(cam_array):
            cam.Attach(tlf.CreateDevice(devices[idx]))

    # store a unique number for each camera to identify the incoming images
    for _, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        if index != None and len(SERIAL_ARR) == 1:
            # NOTE: this first if-statement is for using just ONE camera.
            idx = index 
        elif camera_serial == SERIAL_ARR[0]:
            idx = 0
            # cam.Name = f"Diffuser"
        elif camera_serial == SERIAL_ARR[1]:
            idx = 1
            # cam.Name = f"RML"
        elif camera_serial == SERIAL_ARR[2]:
            idx = 2
            # cam.Name = f"Ground Truth"
        cam.SetCameraContext(idx)
        
        print(f"Set context {idx} for camera {camera_serial}.")
    return cam_array

def reset_white_balance(cam_array, light_source="Off"):
    """
    resets the white balance value to LIGHT_SOURCE.

    default LIGHT_SOURCE = "Off"
    """
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set White Balance {light_source} for camera {idx} - {camera_serial}")
        cam.BslLightSourcePreset.Value = light_source
        cam.BalanceWhiteReset.Execute()

def set_white_balance_manual(cam_array):
    """
    manually set the white balance of cameras by turning off the AWB
    and setting to calibrated values.
    
    Notes:
    - By default, ROI2 should be assigned to AWB: https://docs.baslerweb.com/auto-function-roi#overlap-between-auto-function-roi-and-image-roi
    - By default, AWB should be OFF, but it can be faulty so turn off again
    - Based on documentation: https://docs.baslerweb.com/balance-white-auto
    """

    for idx, cam in enumerate(cam_array):

        cam.AutoFunctionROISelector.Value = "ROI2"
        # Enable the Balance White Auto auto function for the auto function ROI selected
        cam.AutoFunctionROIUseWhiteBalance.Value = True
        # Disable AWB
        cam.BalanceWhiteAuto.Value = "Off"

        # Manually adjust WB parameters.
        #   Documentation: https://docs.baslerweb.com/balance-white#python_1
        #   See documentation for how to adjust parameters.
        #   (Optional)
        #   - Before doing this manually, check Pylon Viewer to see if there's an option to do this in the GUI
        #   - If GUI option, display grey image and calibrate values in the GUI, then input them below.

        # Set red intensity to 108.789%
        cam.BalanceRatioSelector.Value = "Red"
        cam.BalanceRatio.Value = 1.08789
        # Set green intensity to 100%
        cam.BalanceRatioSelector.Value = "Green"
        cam.BalanceRatio.Value = 1.0
        # Set blue intensity to 219.678%
        cam.BalanceRatioSelector.Value = "Blue"
        cam.BalanceRatio.Value = 2.19678
        # verify AWB is off and values have been set 
        print(f"Auto white balance is {cam.BalanceWhiteAuto.Value} for camera {idx}")
        print(f"set manually set white balance for camera {idx}")

def set_gain(cam_array, gain=0):
    """
    set camera gain to zero
    """
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set Gain {idx} for camera {camera_serial}")
        cam.Gain = 0.0 

def set_pixel_format(cam_array, CAPTURE_FORMAT):
    """
    set pixel format to selected
    """

    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set PixelFormat {idx} for camera {camera_serial}")
        cam.PixelFormat.SetValue(CAPTURE_FORMAT)
        print("Pixel Format: ", cam.PixelFormat.GetValue())

def set_color_space(cam_array):
    """
    set color space
    default disables any additional color space correction
    """
    for idx, cam in enumerate(cam_array):
        # disable any additional color space correction
        cam.BslColorSpace.Value = "Off"
        print(f"Color space correction is {cam.BslColorSpace.Value} for camera {idx}")

def init_metadata(DATETIME, DESTINATION, SOURCE, NUM_IMG, start_idx, CAPTURE_FORMAT, exposure_times):
    """
    initialise metadata information.
    this will be saved as a dictionary later.
    """
    
    metadata = {
        "Acquisition Date/Time: ": DATETIME,
        "Destination Data Path": DESTINATION,
        "Source Image Path": SOURCE,
        "Number of Images": NUM_IMG,
        "Image Start Index": start_idx,
        "Capture Format": CAPTURE_FORMAT,
        
        "DiffuserCam": {
            "Exposure": 0 if len(exposure_times) == 1 else exposure_times[0]
        },
        "RML": {
            "Exposure" : exposure_times[0] if len(exposure_times) == 1 else exposure_times[1]
        },
        "Ground Truth" : {
            "Exposure": 0 if len(exposure_times) < 3 else exposure_times[2]
        },

        "Failed Images": []
    }
    
    return metadata

def append_metadata(metadata, values: tuple):
    """
    function for appending to the metadata dictionary
    """
    metadata[str(values[0])] = values[1]

def filter_sort_images(SOURCE, FORMAT_LST):
    """
    filters and sorts images for display
    """
    source_imgs = os.listdir(SOURCE)
    source_imgs = [img for img in source_imgs if any([fmt in img for fmt in FORMAT_LST])]
    source_imgs = [img for img in source_imgs if not img.startswith('.')]
    source_imgs = natsorted(source_imgs)
    return source_imgs

def set_exposure_times(cam_array, exposure_times):
    """
    sets exposure times to calibrated values
    """
    for idx, cam in enumerate(cam_array):
        camera_serial = cam.DeviceInfo.GetSerialNumber()
        print(f"set Exposuretime {idx} for camera {camera_serial} as {exposure_times[idx]}")
        cam.ExposureTime = exposure_times[idx]

def init_display(display=1, mode=pg.FULLSCREEN, flip=False):
    """
    initalise display surface for displaying images

    Recall that display=1 is external monitor, 0 is laptop screen
    Set display dims to be that of the EXTERNAL MONITOR so it stays CONSISTENT across devices.
    """

    pg.init()

    screen_sizes = pg.display.get_desktop_sizes() 
    width, height = screen_sizes[1] if len(screen_sizes) > 1 else screen_sizes[0]
    print(f"Screen Size: {width} x {height}")

    # Creates a canvas the same size as the display. Everything drawn to this canvas.
    screen = pg.display.set_mode((width, height), mode, display=display)
    black_color = (0, 0, 0) # modifying in case different
    screen.fill(black_color)
    if flip:
        pg.display.flip()
    
    return screen

def capture(cam_array, img, i, PATH_ARR, frame_counts, metadata, timeout=1000):
    """
    main image capture loop.
    """
    max_vals = []
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
                max_vals.append(np.max(array_value))
            else:
                print(f"Failed: Image #{img_nr} of Cam #{cam_id}")
                metadata["Failed Images"].append(( "Image: " + str(img_nr), filename, "Camera: " + str(cam_id)))
        cam.StopGrabbing()
    return max_vals

def display_images(screen, SOURCE, filename, crop_dim=(1100, 1100), crop_pos=(75, 0), display_dim=(900, 900), rml_pos=(730, 60), dc_pos=(30, 165), dc_dim=(100, 0, 300, 300), rml_dim=(100, 0, 300, 300)):
    """"
    places two images on display for RML and diffuser

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

    # Create a canvas of size CROP_DIM that will be placed onto screen.
    crop = pg.Surface(crop_dim)

    #Transpose img if vertical --> all horizontal
    # image = pg.transform.rotate(image, 90) #Rotate for EFOV
    if img_size[0] < img_size[1]:
        image = pg.transform.flip(image, True , False)

    # Crop the images to RML_DIM
    # Place on the crop surface at RML_POS for upper left-hand corner
    # Ex: (image, (top left corner of image), (square positions and dimensions of image))
    crop.blits(((image, dc_pos, dc_dim), (image, rml_pos, rml_dim)))

    # Rescale the crop surfqace to DISPLAY_DIM at CROP_POS on the display
    # Remember, this is in display coordinates.
    screen.blit(pg.transform.scale(crop, display_dim), crop_pos)
    pg.display.flip()

def display_single_image(screen, SOURCE, filename, crop_dim=(1100, 1100), crop_pos=(75, 0), display_dim=(900, 900), rml_pos=(730, 60), dc_pos=(30, 165), dc_dim=(100, 0, 300, 300), rml_dim=(100, 0, 300, 300), camera=0):
    """"
    places one image on display for one camera

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
    crop = pg.Surface(crop_dim)

    #Transpose img if vertical --> all horizontal
    if img_size[0] < img_size[1]:
        image = pg.transform.flip(image, True , False)

    # Overlay images onto crop --- (image, (top left corner of image), (square positions and dimensions of image))
    if camera == 0:
        crop.blit(image, dc_pos, dc_dim)
    elif camera == 1:
        crop.blit(image, rml_pos, rml_dim)
    
    # resize to new size on screen.
    screen.blit(pg.transform.scale(crop, display_dim), crop_pos)
    pg.display.flip()

def exposure_test(cam_array, exposure_times):
    """
    tests and checks exposure values
    """
    for idx, cam in enumerate(cam_array):
       assert cam.ExposureTime.GetValue() == exposure_times[idx], "Exposure time not set correctly."