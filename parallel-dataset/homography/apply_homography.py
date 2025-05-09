import os
from typing import List
import glob
import kornia as K
import matplotlib.pyplot as plt
import numpy as np
import torch
import kornia.geometry.transform as transform
from kornia.geometry import resize
from natsort import natsorted
from kornia.augmentation import CenterCrop
from skimage.transform import rescale, resize
import argparse
import skimage.io as skio

def load_images(path='./results', gray=True, output_shape=(150, 240)):
    images = [img for img in os.listdir(path) if img.endswith('.jpg') or img.endswith('.png') or img.endswith('.tiff')]
    images = natsorted(images)
    
    img_lst = []
    num_imgs = 0

    for img in images:
        # print(img)
        if 'jpg' and 'png' and 'tiff' not in img:
            continue
            
        if gray:
            img = skio.imread(os.path.join(path, img))[:, :, 0]
        else:
            img = skio.imread(os.path.join(path, img))[:, :, 0:3]

        img = img / np.max(img)  # normalize to 1

        if output_shape != (0, 0):
            img = resize(img, output_shape, anti_aliasing=True)

        # Convert to tensor
        img = torch.from_numpy(img).to(torch.float32)

        if len(img.shape) == 3:  # If image has channels
            img = img.permute(2, 0, 1)  # Change from (H,W,C) to (C,H,W)

        img_lst.append(img)
        
        num_imgs += 1

    # Stack tensors
    img_lst = torch.stack(img_lst, dim=0)
    print(f"Finished processing {num_imgs} images!")
    return img_lst


def main():
    """
    Apply a homography transformation to a set of images and save the warped images.
    This script takes a directory of images, applies a homography transformation
    using a provided transformation matrix, and saves the resulting warped images
    to an output directory.
    Arguments:
        --recon_path (str): Path to the directory containing the input images.
        --matrix_path (str): Path to the .npy file containing the transformation matrix.
        --output_dir (str): Path to the directory where the warped images will be saved.
        --gray (str): True if recons are grayscale.
    
    Example (if terminal in source directory):
        python parallel-dataset/homography/apply_homography.py \
            --recon_path /path/to/recon/images \
            --matrix_path /path/to/transformation_matrix.npy \
            --output_dir /path/to/output/directory \
            --gray False
    """
    parser = argparse.ArgumentParser(description="Apply homography transformation to images.")
    parser.add_argument("--recon_path", type=str, required=True, help="Path to the recon directory.")
    parser.add_argument("--matrix_path", type=str, required=True, help="Path to the transformation matrix (.npy file).")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save the warped images.")
    parser.add_argument("--gray", type=str, required=True, help="True if grayscale images.")
    args = parser.parse_args()

    # Load transformation matrix
    M = torch.load(args.matrix_path).to(torch.float32)

    gray = True if args.gray == 'True' else False

    # Get list of image paths
    images = glob.glob(os.path.join(args.recon_path, '*.tiff'))
    images = natsorted(images)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    num_imgs = 0
    for image_path in images:
        # Load and process single image
        img = plt.imread(image_path)

        if img.shape != (150, 240):
            img = resize(img, (150, 240), anti_aliasing=True)
        
        # Convert to tensor and ensure C-contiguous
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(torch.float32)
        img = img.contiguous() # Ensure tensor is contiguous
        
        if len(img.shape) == 3:  # If image has channels
            img = img.permute(2, 0, 1)  # Change from (H,W,C) to (C,H,W)
            img = img.contiguous() # Ensure contiguous after permute
            img = img[None, ...]  # Add batch dimension
        else:
            img = img[None, None, ...]  # Add batch and channel dimensions
            
        # Apply homography transform
        warped_img = transform.warp_perspective(img.float(), M.float(), 
                                              dsize=(img.shape[2], img.shape[3])).squeeze().detach().cpu()
        
        if not gray:
            warped_img = warped_img.permute(1, 2, 0)  # switch to (H, W, C)
            warped_img = warped_img.contiguous() # Ensure contiguous after permute

        # Normalize to 0-1
        warped_img = warped_img / torch.max(warped_img)

        # Convert to numpy array and ensure C-contiguous before saving
        warped_img_np = np.ascontiguousarray(warped_img.detach().numpy())
        
        # Save warped image
        output_path = os.path.join(args.output_dir, f"warped_{os.path.basename(image_path)}")
        plt.imsave(output_path, warped_img_np, cmap=None if not gray else 'gray')
        
        num_imgs += 1
        if num_imgs % 1000 == 0:
            print(f"Processed {num_imgs} images")
    
    print(f"Saved warped images to {args.output_dir}")

if __name__ == "__main__":
    main()
