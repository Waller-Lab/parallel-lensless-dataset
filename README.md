# Scalable dataset acquisition for data-driven lensless imaging

This is the software package accompanying the parallel lensless dataset acquisition detailed [in this project page](https://waller-lab.github.io/parallel-lensless-dataset/). This codebase is implemented in Python.

**NOTE:** this repo a work in progress. Code for distortion correction and homography are coming soon!

## Setup
This code can be run python versions 3.11.5 and above. It may run with older versions, though we have not tested it. We recommend setting up a virtual environment of your choice to run the code. 

Install the required packages (this list was generated using [pipreqs](https://github.com/bndr/pipreqs)).

    pip install -r requirements.txt

We recommend reviewing our [hardware setup guide](https://waller-lab.github.io/parallel-lensless-dataset/hardware.html) to understand the hardware components being controlled by our scripts.

## Usage
The software package consists of two main scripts:
- `capture_display.py`: displays the ground truth dataset on the display and captures images in parallel from all imagers.
- `reconstruction.py`: given calibration PSFs and measurement directory, reconstructs lensless measurements.

This codebase is a work in progress and will be updated with intermediate helper scripts.

### `capture_display.py`
The script is controlled with the command:
    
    python3 capture_display.py END START DESTINATION SOURCE DISPLAY &>

- `END`: index of final image in ground truth dataset
- `START`: index of first image in ground truth dataset
- `DESTINATION`: desired path to store data
- `SOURCE`: path to ground truth dataset
- `DISPLAY`: choose display mode. `1` for external display and `0` for current laptop screen. Use `1` by default. If using `0`, we recommend setting `DISPLAY_MODE = pg.RESIZABLE`.

Example:
    
    python3 capture_display.py 1000 0 /path/to/dest/ /path/to/groundtruth/dataset 1 &>

#### Other parameters
- `LOG`: set up logging for acqusition. Generates a `log.txt`.
- `SERIAL_ARR`: array of camera serial numbers.
    - In our project, we used the following indexing scheme:
        - 0: ground truth
        - 1: rml
        - 2: diffusercam
- `CAPTURE_FORMAT`: set the capture format of the camera. For the Basler daA1920-uc, we use `MONO12` or `RGB8`.
- `DISPLAY_MODE`: use `pg.FULLSCREEN` by default. `pg.RESIZABLE` can be used for troubleshooting.
- `NUM_CAMERAS`: number of cameras used in system. 
- `EXPOSURE_TIMES`: array of exposure times for each camera. The order corresponds to 

#### Calibrating image placement on display
Different displays have different aspect ratios and resolutions. Unfortunately, this must be calibrated for your system and can be done in the `CALIBRATE CROP POSITIONING` section in the code. We have included positioning parameters that performed the best in our set up. However, we will provide a summary of the Pygame documentation for display calibration here soon.

### `reconstruction.py`
This script is controlled by the following command:
    
    python3 reconstruction.py DESTINATION SUB_DIR

- `DESTINATION`: desired destination directory for recons. If used with our `capture_display` script, this is the same`DESTINATION` directory.
- `SUB_DIR`: name of the sub directory that includes lensless measurements.

**NOTE:** the `DESTINATION` directory should contain a `psfs` directory. PSFs of each lensless imager should contain `cam_0` for the 0th indexed camera and `cam_1` for the 1st camera, etc. in the filename depending on your indexing convention.

Reconstructions will be saved in `DESTINATION/SUB_DIR/recons`.

#### Undoing lens distortion
The code and calibration file for undoing the lens distortion on the ground truth image can be found in `parallel-dataset/undistort/`

Example Usage:
1. Prepare your images and calibration data:
    - Place all the images you want to undistort in a folder (e.g., `images/`).
    - Ensure you have the ``calibration_data.npz` file containing the camera calibration data 
      The `.npz` file should contain two arrays: `camera_matrix` and `dist_coeffs`.
2. Run the script from the command line:
    ```bash
    python3 undistort.py images ./images calibration_path ./calibration_data.npz --root_path ./output/
    ```
    - `images`: Path to the folder containing images to undistort.
    - `calibration_path`: Path to the `.npz` file containing camera calibration data.
    - `--root_path`: (Optional) Root path to save the undistorted images. Defaults to the current directory (`./`).
3. Output:
    - The undistorted images will be saved in a subdirectory named `undistorted_images/` under the specified `--root_path`.
    - For example, if `--root_path` is `./output/`, the undistorted images will be saved in `./output/undistorted_images/`.

## Troubleshooting
Guide for troubleshooting common bugs coming soon!
