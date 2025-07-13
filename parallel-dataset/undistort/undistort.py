import cv2
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import numpy as np
import argparse
import gc
import skimage.io as skio

"""
This script takes in three arguments:
python3 undistort.py --images [PATH TO IMAGES] --calibration_path [PATH TO CALIBRATION FILE] --root_path [ROOT DIRECTORY]
"""

def undistort_image(image_path, camera_matrix, dist_coeffs, root_path='./'):
    """
    Undistort an image using the camera matrix and distortion coefficients.
    Saves at ROOT_PATH/undistorted_images/

    :param image_path: Path to the image to be undistorted
    :param camera_matrix: The camera matrix
    :param dist_coeffs: The distortion coefficients
    :param root_path: The root path to save the undistorted images

    :return: The undistorted image

    NOTE: This function flips the image horizontally, then converts from BGR to RGB.
    """
    # Load the distorted image
    img = cv2.imread(image_path)

    # Get the image size
    h, w = img.shape[:2]

    # Obtain the new optimal camera matrix (free of distortion)
    # setting alpha = 0 helped reduce the fringing on the edges
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 0, (w, h))

    # Undistort the image
    undistorted_img = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_camera_matrix)

    undistorted_img = cv2.flip(undistorted_img, 1)
    # Convert from BGR to RGB
    undistorted_img = cv2.cvtColor(undistorted_img, cv2.COLOR_BGR2RGB)

    # Normalize 0-1, convert to float32 -- UNCOMMENT IF USING PLT
    # undistorted_img = undistorted_img.astype(np.float32) / 255.0

    # Create output directory if it doesn't exist
    output_dir = os.path.join(root_path, 'undistorted_images')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'undistorted_' + image_path.split('/')[-1])
    
    # skio saves as RGB, expects as uint8
    skio.imsave(output_path, undistorted_img)

    # plt saves as RGB, expects as float32
    # plt.imsave(output_path, undistorted_img)

    
    # free up memory
    del undistorted_img
    gc.collect()

    return

def undistort_images(images, calibration_path, root_path='./'):
    """
    Undistort a list of images using the camera matrix and distortion coefficients.
    Saves at ROOT_PATH/undistorted_images/

    :param images: List of images to be undistorted
    :param camera_matrix: The camera matrix
    :param dist_coeffs: The distortion coefficients
    :param root_path: The root path to save the undistorted images

    :return: Number of undistorted images
    """
    images = glob.glob(images + '/*.tiff')
    calibration_data = np.load(calibration_path)
    camera_matrix = calibration_data['camera_matrix']
    dist_coeffs = calibration_data['dist_coeffs']
    
    num_imgs = 0
    for image in images:
        undistort_image(image, camera_matrix, dist_coeffs, root_path)
        num_imgs += 1
        
        if num_imgs % 1000 == 0:
            print(f"Undistorted image {num_imgs}")
    
    return num_imgs


def main():
    parser = argparse.ArgumentParser(description="Undistort images using camera calibration data.")
    parser.add_argument("--images", type=str, help="Path to the folder containing images to undistort.")
    parser.add_argument("--calibration_path", type=str, help="Path to the .npz file containing camera calibration data.")
    parser.add_argument("--root_path", type=str, default="./", help="Root path to save the undistorted images.")

    args = parser.parse_args()

    print("Beginning undistortion...")
    undistorted_images = undistort_images(args.images, args.calibration_path, args.root_path)
    print(f"Undistorted {undistorted_images} images and saved to {args.root_path}/undistorted_images/")
if __name__ == "__main__":
    main()