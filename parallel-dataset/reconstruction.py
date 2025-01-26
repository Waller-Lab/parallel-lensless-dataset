import numpy as np
import matplotlib.pyplot as plt
import os
from fista_files.helper_functions import *
import fista_spectral_cupy as FSC
import sys


"""
USAGE:
    python3 reconstruction.py DESTINATION SUB_DIR
"""

ARGS = sys.argv
DESTINATION = ARGS[1]
SUB_DIR = DESTINATION + ARGS[2]

## This section can be tailored to your system
RML_PATH = f"{SUB_DIR}/rml"
DC_PATH = f"{SUB_DIR}/diffusercam"
PSF_PATH = f"{DESTINATION}/psf"
PATH_ARR = [DC_PATH, RML_PATH]
INDEX_ARR = ["cam_0", "cam_1"]

grayscale = False 
npy_save = False

f = 8 # downsample factor

def check_imgname(img_name):
    if img_name[0] == '.':
        return False
    if 'psf' in img_name or not ('.tiff' in img_name):
        return False
    return True

def check_psfname(psf_name):
    if psf_name[0] == '.':
        return False
    if 'psf' in psf_name:
        return True
    return False

## PROCESSING LOOP
print("Reconstructing captured images from: ", SUB_DIR)
for cam, ind in list(zip(PATH_ARR, INDEX_ARR)):
    data_capture = [img for img in os.listdir(cam) if check_imgname(img)]
    psf_list = [f for f in os.listdir(PSF_PATH) if check_psfname(f) and f'{ind}' in f]
    psf_name = f'{PSF_PATH}/{psf_list[0]}' if len(psf_list) > 0 else f'{cam}/psf.tiff'
    
    print("Using PSF: ", psf_name)
    for f_img in data_capture:
        img_path = f"{cam}/{f_img}"
        result_path = f'{cam}/results'
        result_name = f'{result_path}/reconned_{f_img}'

        if not os.path.exists(result_path):
            os.mkdir(f'{cam}/results')

        print("Starting recon for: ", f_img)
        psf, img, mask = preprocess(psf_name, img_path, f, gray_image=grayscale)
        fista = FSC.fista_spectral_numpy(psf[:,:,1:2], mask[:,:,1:2], gray=grayscale)
        
        # set FISTA parameters
        fista.iters = 200 # Default: 200
        # Default: tv, Options: 'native' for native sparsity, 'non-neg' for enforcing non-negativity only
        fista.prox_method = 'tv'  
        fista.tv_lambda  = 1e-2  #1e-3, 1e-2, 1e-1
        fista.tv_lambdaw = 0.01 
        fista.print_every = 20

        out_img = fista.run(img)
        plotted_img = preplot(out_img[0][0])

        plt.imsave(result_name, plotted_img)
        if npy_save:
            np.save(f'{result_path}/reconned_{f_img}.npy', plotted_img)
        # plt.imshow(plotted_img, cmap='gray')
        # plt.title(f'FISTA after {fista.iters} iterations')
        print("Completed and saved recon for: ", f_img)