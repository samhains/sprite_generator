import numpy as np
import os
import cv2

MIN_CONTOUR_THRESHOLD = 100
BG_BUFFER_WIDTH = 20
BASE_DIR = "./images/sprites"
MIN_FRAMES = 2

def alpha_threshold(image, bg_color):
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]

    mask = ((r == bg_color[0]) & (g == bg_color[1]) & (b == bg_color[2]))
    image[mask] = 0


def threshold(image, bg_color):
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    mask = ((r == bg_color[0]) & (g == bg_color[1]) & (b == bg_color[2]))
    image[np.logical_not(mask)] = 255
    image[mask] = 0


def calc_contours(imgray):
    ret,thresh = cv2.threshold(imgray,127,255,0)
    _, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_THRESHOLD]


def calc_areas(contours):
    return [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > MIN_CONTOUR_THRESHOLD]


def calc_rectangles(contours, areas):
    rectangles = []
    counter = 0

    mean_area = np.mean(areas)
    for i, cnt in enumerate(contours):
        if areas[i] > mean_area*0.8 and areas[i] < mean_area*1.8:
            counter = counter + 1
            if counter:
                rectangles.append(cv2.boundingRect(cnt))

    return rectangles

def add_alpha_channel(img):
    if(img.shape[2] == 4):
        b_channel, g_channel, r_channel, _ = cv2.split(img)
    else:
        b_channel, g_channel, r_channel = cv2.split(img)

    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255 #creating a dummy alpha channel image.
    return cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

def draw_rectangles(rectangles, img_url, preview=False):
    im_raw = cv2.imread(img_url, -1)
    if(len(im_raw.shape) != 3):
        return []
    else:
        im_raw = add_alpha_channel(im_raw)
        alpha_threshold(im_raw, im_raw[0, 0])
        cropped_imgs = []
        b = 2
        for row in rectangles:
            new_row = []
            for (x,y,w,h) in row:
                if w % 2 != 0:
                    w = w + 1
                if h % 2 != 0:
                    h = h + 1
                crop_img = im_raw[y:y+h+b, x:x+w]
                new_row.append(crop_img)
                if preview:
                    cv2.rectangle(im_raw, (x,y), (x+w,y+h),(0,255,0),2)
                    cv2.imshow("cropped", crop_img)
                    cv2.waitKey(0)
            cropped_imgs.append(new_row)

        return cropped_imgs



def read_img(url):
    print(url)
    im = cv2.imread(url)
    threshold(im, im[0,0])
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def adjust_rectangle_row(row, index, element):
    new_row = []
    for rect in row:
        lst = list(rect)
        lst[index] = element
        t = tuple(lst)
        new_row.append(t)
    return new_row


def adjust_rectangles(rectangles):
    try:
        first = rectangles[0]
        # min_y = first[1]
        adjusted_rectangles = []
        row = []
        first_y = first[1]
        for rect in rectangles:
            y = rect[1]
            # print(y)
            if y > 50 + first_y:
                # print("new row!")
                max_height = max(row, key=lambda x:x[3])[3]
                adjusted_rectangles_row = adjust_rectangle_row(row, 3, max_height)
                adjusted_rectangles.append(adjusted_rectangles_row)
                row = []
                first_y = y

            rect = (rect[0], first_y, rect[2], rect[3])
            row.append(rect)

        max_height = max(row, key=lambda x:x[3])[3]
        adjusted_rectangles_row = adjust_rectangle_row(row, 3, max_height)
        adjusted_rectangles.append(adjusted_rectangles_row)
    except:
        adjusted_rectangles = []


    return adjusted_rectangles

def sort_rectangles(rectangles):
    return sorted(rectangles, key=lambda k: [k[1], k[0]])

def save_videos(cropped_imgs, video_name):
    for row_number, row in enumerate(cropped_imgs):
        dir_name = "output/{}_{}".format(video_name, row_number)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        bg_w = max(row, key=lambda x: x.shape[0]).shape[0]+BG_BUFFER_WIDTH
        # enforce evenness
        if bg_w % 2 != 0:
            bg_w = bg_w + 1
        bg_h = max(row, key=lambda x: x.shape[1]).shape[1]+BG_BUFFER_WIDTH
        if bg_h % 2 != 0:
            bg_h = bg_h + 1

        row_num = 1

        print(len(row), MIN_FRAMES)
        if len(row) > MIN_FRAMES:
            for img in row:

                bg_img = np.zeros((bg_w, bg_h, 4), np.uint8)
                img_w, img_h, _ = img.shape
                x_offset, y_offset = ((bg_w - img_w) / 2, (bg_h - img_h) / 2)
                bg_img[x_offset:x_offset + img.shape[0], y_offset:y_offset + img.shape[1], :] = img
                row_num_str = "{0:0>3}".format(row_num)
                cv2.imwrite("{}/{}.png".format(dir_name, row_num_str), bg_img)
                row_num = row_num + 1
        else:
            os.removedirs(dir_name)

        # bg_height = max(row, key=lambda x:x[3])
        # bg_width = max(row, key=lambda x:x[2])
        # print(bg_height)
        # print(bg_width)
        # # bg_img = np.zeros((bg_height,bg_width,3), np.uint8)
        # for img in row:
        #     print(img)
            # img_w = img
            # offset = ((bg_w - img_w) / 2, (bg_h - img_h) / 2)
        # cv2.VideoWriter("video_name_{}".format(i), -1, 1, (width,height))

def extract_animation(fname):
    imgray = read_img('{}/{}.png'.format(BASE_DIR, fname))
    contours = calc_contours(imgray)
    areas = calc_areas(contours)

    rectangles = calc_rectangles(contours, areas)
    rectangles = sort_rectangles(rectangles)
    adjusted_rectangles = adjust_rectangles(rectangles)

    sorted_rectangles = []
    for row in adjusted_rectangles:
        sorted_rectangles.append(sort_rectangles(row))

    cropped_imgs = draw_rectangles(sorted_rectangles, '{}/{}.png'.format(BASE_DIR, fname))
    save_videos(cropped_imgs, fname )

# extract_animation('kirby')
dir_fnames = [fname.split(".png")[0] for fname in os.listdir("{}".format(BASE_DIR)) if fname.endswith(".png")]
for fname in dir_fnames:
    extract_animation(fname)
