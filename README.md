# Scalable dataset acquisition for data-driven lensless imaging

This is the software package accompanying the Parallel Lensless Dataset detailed in [ConvRML: high-quality lensless imaging with multi-focal lenslets](https://lakabuli.github.io/ConvRML/) and its previous iteration [in this project page](https://waller-lab.github.io/parallel-lensless-dataset/). This codebase is implemented in Python.

## Setup
This code can be run using Python versions 3.11.5 and above. It may run with older versions, though we have not tested it. We recommend setting up a virtual environment of your choice to run the code. 

Install the required packages. (This list was generated using [pipreqs](https://github.com/bndr/pipreqs)).

    pip install -r requirements.txt

We recommend reviewing our [hardware setup guide](https://waller-lab.github.io/parallel-lensless-dataset/hardware.html) to understand the hardware components being controlled by our scripts.

## Tutorial
For help using our captured dataset for training machine learning models, refer to our tutorial notebook:
- `tutorials/preprocess_4x_PLD.ipynb`
<!-- : **Most up-to-date**, corresponding to the 100,000 image PLD dataset in the [ConvRML](https://lakabuli.github.io/ConvRML/) project at 4x downsampling. -->

## Usage
The main scripts in this codebase are:
- `parallel-dataset/capture_display.py`: displays the ground truth dataset on the display and captures images in parallel from all imagers.
<!-- - `reconstruction.py`: given calibration PSFs and measurement directory, reconstructs lensless measurements. -->
- `parallel-dataset/undistort/undistort.py`: undos the lens distortion on ground truth measurements.
- `parallel-dataset/homography/apply_homography.py`: warps images to different imager coordinate spaces.

<!-- This codebase is a work in progress and will be updated with intermediate helper scripts. -->

### `parallel-dataset/capture_display.py`
----
The script is controlled with the command:
    
    python3 capture_display.py END START DESTINATION SOURCE DISPLAY &>

- `END`: index of final image in ground truth dataset to be captured
- `START`: index of first image in ground truth dataset
- `DESTINATION`: path to save measurements
- `SOURCE`: path to ground truth dataset
- `DISPLAY`: choose display mode. `1` for external display and `0` for current laptop screen. Use `1` by default. If using `0`, we recommend setting `DISPLAY_MODE = pg.RESIZABLE`.

Example to capture 1000 images:
    
    python3 capture_display.py 1000 0 /path/to/dest/ /path/to/groundtruth/dataset 1 &>

#### Other script parameters
- `LOG`: set up logging for acqusition. If set to `TRUE`, generates a `log.txt`.
- `SERIAL_ARR`: array of camera serial numbers.
    - In our project, we used the following indexing scheme:
        - 0: ground truth
        - 1: rml
        - 2: diffuser
- `CAPTURE_FORMAT`: set the capture format of the camera. For the Basler daA1920-uc, we use `RGB8`.
- `DISPLAY_MODE`: use `pg.FULLSCREEN` by default. `pg.RESIZABLE` can be used for troubleshooting.
- `NUM_CAMERAS`: number of cameras used in system. 
- `EXPOSURE_TIMES`: array of exposure times for each camera. The order corresponds to the order of cameras in `SERIAL_ARR`.

#### Calibrating image placement on display
Different displays have different aspect ratios and resolutions. This must be calibrated for your system and can be done in the `CALIBRATE CROP POSITIONING` section in `parallel-dataset/capture_display.py`. We have included position parameters used in our set up. We recommend reviewing the [Pygame Surface documentation](https://www.pygame.org/docs/ref/surface.html) for further customization. 

The image being displayed is cropped, with two copies placed on the screen, one for each lensless imager.
- `crop_dim` : (w, h) - initalizes a canvas of size `CROP_DIM` on the display
- `display_dim` : (w, h) - rescale of crop to screen
- `rml_pos` : (x, y) - position of the image for rml on crop surface
- `dc_pos` : (x, y) - position of the image for diffuser on crop surface
- `crop_pos` : (x, y) - location of crop on screen
- `dc_dim` : (x, y, w, h) - (x, y) are positions of top left corner of image and (w, h) are dimensions of crop
- `rml_dim` : (x, y, w, h) - (x, y) are positions of top left corner of image and (w, h) are dimensions of crop

The code does the following operations:
- First, create a surface of `crop_dim`.
- Crop image to `rml_dim` and `dc_dim` and place upper left corner at `rml_pos` and `dc_pos`.
- Then, resize this to `display_dim` and place at `crop_pos`.

#### Calibrating white balance
For consistency, we turn off auto white balancing (AWB) and set calibrated white balance parameters based on our cameras. You may want to calibrate white balance parameters for your system. Instructions can be found in the `set_white_balance_manual` function in `parallel-dataset/capture_display_helpers.py`.

<!-- ### `reconstruction.py`
----
This script is controlled by the following command:
    
    python3 reconstruction.py DESTINATION SUB_DIR

- `DESTINATION`: desired destination directory for recons. If used with our `capture_display` script, this is the same`DESTINATION` directory.
- `SUB_DIR`: name of the sub directory that includes lensless measurements.

**NOTE:** the `DESTINATION` directory should contain a `psfs` directory. PSFs of each lensless imager should contain `cam_0` for the 0th indexed camera and `cam_1` for the 1st camera, etc. in the filename depending on your indexing convention.

Reconstructions will be saved in `DESTINATION/SUB_DIR/recons`. -->

### `parallel-dataset/undistort/undistort.py`
----
Code for undoing the lens distortion on the ground truth measurements can be found in `parallel-dataset/undistort/`.

Example Usage:
1. Prepare your images and calibration data:
    - Place all the images you want to undistort in a folder (e.g., `images/`).
    - Ensure you have the ``PLD_calibration.npz`` file containing the camera calibration data 
      The `.npz` file should contain two arrays: `camera_matrix` and `dist_coeffs`.
2. Run the script from the command line. The script takes in 3 inputs:
    ```
    python3 undistort.py --images [PATH TO IMAGES] --calibration_path [PATH TO CALIBRATION FILE] --root_path [ROOT DIRECTORY]
    ```

    Example:
    ```
    python3 undistort.py --images ./images --calibration_path ./calibration_data.npz --root_path ./output/
    ```
    - `--images`: Path to the folder containing images to undistort.
    - `--calibration_path`: Path to the `.npz` file containing camera calibration data.
    - `--root_path`: (Optional) Root path to save the undistorted images. Defaults to the current directory (`./`).
3. Output:
    - The undistorted images will be saved in a subdirectory named `undistorted_images/` under the specified `--root_path`.
    - For example, if `--root_path` is `./output/`, the undistorted images will be saved in `./output/undistorted_images/`.

### `parallel-dataset/homography/apply_homography.py`
----
The code for computationally aligning the lensed and lensless imagers can be found in `parallel-dataset/homography/`. Transformation matrices can be found in [this Google Drive folder](https://drive.google.com/drive/folders/1hfcoBQc2XNIkmWxK5hOzHYO0GE6Fdfsj?usp=drive_link), which includes 4 files:
- `GT2DC_homography_4x_2026.torch`: from ground truth to Diffuser
- `GT2RML_homography_4x_2026.torch`: from ground truth to RML
- `DC2GT_homography_4x_2026.torch`: from Diffuser to ground truth
- `RML2GT_homography_4x_2026.torch`: from RML to ground truth

The `parallel-dataset/homography/apply_homography.py` script takes a directory of images, applies a homography transformation using a provided transformation matrix, and saves the resulting warped images to an output directory.

Example usage:
1. Prepare your images and homographies:
    - Place all the images you want to transform in a folder.
    - Choose the right homography matrix. E.g. if you want to map to ground truth, your input image directory should be of a lensless imager.
    - Code is run at x4 downsampling by default. Make sure to change the downsampling dimensions to match desired output if not at x4.
2. Run the script from the command line. The script takes in 4 inputs:
    - `--recon_path`: Path to the directory containing the input images.
    - `--matrix_path`: Path to the .npy file containing the transformation matrix.
    - `--output_dir`: Path to the directory where the warped images will be saved.
    - `--gray` (str): True if recons are grayscale.

    ```
    Example:

        python parallel-dataset/homography/apply_homography.py --recon_path /path/to/recon/images --matrix_path /path/to/transformation_matrix.npy --output_dir /path/to/output/directory --gray False
    ```
3. Output:
    - The undistorted images will be saved in the specified `--output_dir`.

## Automatic White Balance (AWB) PLD
If you are using the 25,000 image AWB-PLD from [an earlier iteration](https://waller-lab.github.io/parallel-lensless-dataset/) of this project, please refer to the files under the folder `previous_AWB_dataset/`.

## Citation
If you use any of the code in this repo, please cite:

```
@article{Kabuli2026ConvRML,
  author = {Leyla A. Kabuli and Clara S. Hung and Vasilisa Ponomarenko and Eric Markley and Laura Waller},
  title = {ConvRML: high-quality lensless imaging with random multi-focal lenslets},
  journal = {Optics Express},
  number = {18},
  pages = {33992--34005},
  publisher = {Optica Publishing Group},
  volume = {34},
  year = {2026},
  doi = {10.1364/OE.608614},
  url = {https://opg.optica.org/oe/abstract.cfm?URI=oe-34-18-33992}
}
```
