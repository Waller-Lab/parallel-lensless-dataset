import os
from typing import List

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

def load_images(path='./results', gray=True):
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

    # Load images
    rml_imgs = load_images(os.path.join(args.recon_path), gray=gray)
    # Warp images and save
    os.makedirs(args.output_dir, exist_ok=True)
    for i, img in enumerate(rml_imgs):
        if len(img.shape) == 3: # Add batch and channel dimensions
            img = img[None, ...]
        else:
            img = img[None, None, ...]
        warped_img = transform.warp_perspective(img.float(), M.float(), dsize=(img.shape[2], img.shape[3])).squeeze().detach().cpu()
        
        if not gray:
            warped_img = warped_img.permute(1, 2, 0) # switch to (H, W, C)

        output_path = os.path.join(args.output_dir, f"warped_image_{i}.tiff")
        plt.imsave(output_path, warped_img.numpy(), cmap=None if not args.gray else 'gray')
    
    print(f"Saved warped images to {args.output_dir}")

if __name__ == "__main__":
    main()
