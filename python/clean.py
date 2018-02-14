from PIL import Image
import os

BASE_DIR = "./images/bg/"

dir_fnames = [BASE_DIR+fname for fname in os.listdir("{}".format(BASE_DIR))]
for fname in dir_fnames:
    try:
        im = Image.open(fname)
        im.verify()
        if not fname.endswith(".png"):
            im = Image.open(fname)
            new_fname = "."+fname.split(".")[1]+".png"
            im.save(new_fname, "PNG")
            os.remove(fname)
    except OSError as err:
        print('not a valid img file')
        os.remove(fname)
