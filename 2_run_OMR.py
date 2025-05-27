"""
Base code taken from https://github.com/Udayraj123/OMRChecker and adapted
"""
import math
import re
import os
import sys
from pathlib import Path
import cv2
import pandas as pd
from glob import glob
from time import time
from PIL import Image
from csv import QUOTE_NONNUMERIC
from collections import defaultdict
import numpy as np

MIN_GAP = 30
MIN_JUMP = 25
OVERLAY_COLOR = (130, 130, 130)
THRESHOLD_CIRCLE = 0.6
ANCHOR_RADIUS_IN_POINTS = 10  # The anchors are 10pt in radius
ANCHOR_DISTANCE_FROM_EDGES_IN_POINTS = 30  # The anchors are 30pt from all edges
BUBBLE_RADIUS_IN_POINTS = 7  # All bubbles have radius 7


def main():
    # Get the arguments that were passed to the script
    _, script_args = sys.argv[0], sys.argv[1:]

    # If less than two arguments were given to the script, we do not have the CSV files we need
    if len(script_args) < 3:
        print("Error: not enough arguments were given to the script")
        sys.exit(1)

    # We expect the first argument to be the path to the omr_marker
    omr_marker_path = Path(script_args[0])
    # We expect the second argument to be the path to the bubbles.csv
    df_bubbles_path = Path(script_args[1])
    # We expect the second argument to be the path to the parsed folder that has one subfolder per page
    parsed_folder_path = Path(script_args[2])

    if not omr_marker_path.is_file():
        print("Error: first argument is not a file")
        sys.exit(1)

    if not df_bubbles_path.is_file() or df_bubbles_path.suffix != ".csv":
        print("Error: second argument is not a CSV file")
        sys.exit(1)

    if not parsed_folder_path.is_dir():
        print("Error: third argument is not a directory")
        sys.exit(1)

    omr_marker = cv2.imread(str(omr_marker_path), cv2.IMREAD_GRAYSCALE)
    overlay_imgs = defaultdict(list)
    df_bubbles = pd.read_csv(df_bubbles_path)

    output_dir = parsed_folder_path.parent.parent / (parsed_folder_path.parent.name + "_OMR") / parsed_folder_path.name
    output_dir.mkdir(parents=True, exist_ok=True)

    process_dir(parsed_folder_path, omr_marker, overlay_imgs, df_bubbles, output_dir)

    # Save the overlays as PDFs
    for filename, overlays in overlay_imgs.items():
        imgs = [Image.fromarray(o) for o in overlays]
        imgs[0].save(output_dir / f"{filename}.pdf", "PDF", resolution=100.0, save_all=True, append_images=imgs[1:])


def process_dir(curr_dir, omr_marker, overlay_imgs, df_bubbles, output_dir):
    # look for images in current dir to process
    exts = ("*.png", "*.jpg", "*.jpeg")
    omr_files = sorted([f for ext in exts for f in glob(os.path.join(curr_dir, ext))])

    subfolders = [f for f in curr_dir.iterdir() if f.is_dir()]
    # subfolders = sorted(subfolders, key=lambda p: int(p.stem))
    if omr_files:
        print("\n------------------------------------------------------------------")
        print(f'Processing directory "{curr_dir}" with settings- ')
        print("\tTotal images       : %d" % (len(omr_files)))
        print("")

        df_out = pd.DataFrame()
        process_files(omr_files, omr_marker, overlay_imgs, df_bubbles, df_out)
        page = curr_dir.stem
        room = curr_dir.parent.parent.name.split("_")[0]
        df_out.to_csv(output_dir / f"{page}_{room}_OMR.csv", quoting=QUOTE_NONNUMERIC)
    elif len(subfolders) == 0:
        # the directory should have images or be non-leaf
        print(f"Note: No valid images or subfolders found in {curr_dir}")

    # recursively process subfolders
    for subfolder in subfolders:
        process_dir(subfolder, omr_marker, overlay_imgs, df_bubbles, output_dir)


def process_files(omr_files, omr_marker, overlay_imgs, df_bubbles, df_out):
    start_time = int(time())
    filesCounter = 0

    for filepath in omr_files:
        filesCounter += 1
        # For windows filesystem support: all '\' will be replaced by '/'
        filepath = filepath.replace(os.sep, "/")

        # Prefixing a 'r' to use raw string (escape character '\' is taken literally)
        finder = re.search(r".*/(.*)/(.*)", filepath, re.IGNORECASE)
        if finder:
            inputFolderName, filename = finder.groups()
            filename = filename.split("_")[0]
        else:
            print("Error: Filepath not matching to Regex: " + filepath)
            continue

        inOMR = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        # TODO: Fix
        # image_dpi = Image.open(filepath).info['dpi']
        image_dpi = (200, 200)
        print(
            "\n[%d] Processing image: \t" % (filesCounter),
            filepath,
            "\tResolution: ",
            inOMR.shape,
        )

        OMRCrop = cv2.GaussianBlur(inOMR, (3, 3), 0)
        OMRCrop = cv2.normalize(OMRCrop, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        anchor = resize_util(omr_marker, u_width=latex_point_to_pixel(ANCHOR_RADIUS_IN_POINTS*2, image_dpi[0]))
        anchor = cv2.GaussianBlur(anchor, (3, 3), 0)
        anchor = cv2.normalize(anchor, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        OMRCrop = handle_markers(OMRCrop, image_dpi, anchor, filename)

        applicable_df_bubbles_rows = df_bubbles.loc[df_bubbles["page"] == int(inputFolderName)]

        OMRresponseDict, overlay_img = read_response(OMRCrop, image_dpi, applicable_df_bubbles_rows, MIN_JUMP)

        # Save OMR info
        items = OMRresponseDict.items()
        keys = [i[0] for i in items]
        values = [i[1] for i in items]
        df_out.loc[filename, keys] = values

        # Save overlay image
        overlay_imgs[filename].append(overlay_img)


    timeChecking = round(time() - start_time, 2) if filesCounter else 1
    print("")
    print(f"Total files processed    : {filesCounter}")

    print(
        "\nFinished Checking %d files in %.1f seconds i.e. ~%.1f minutes."
        % (filesCounter, timeChecking, timeChecking / 60)
    )
    print("OMR Processing Rate  :\t ~ %.2f seconds/OMR" % (timeChecking / filesCounter))
    print(
        "OMR Processing Speed :\t ~ %.2f OMRs/minute"
        % ((filesCounter * 60) / timeChecking)
    )


def getGlobalThreshold(QVals_orig, min_jump, looseness=1):
    """
    Note: Cannot assume qStrip has only-gray or only-white bg (in which case there is only one jump).
          So there will be either 1 or 2 jumps.
    1 Jump :
            ......
            ||||||
            ||||||  <-- risky THR
            ||||||  <-- safe THR
        ....||||||
        ||||||||||

    2 Jumps :
              ......
              |||||| <-- wrong THR
          ....||||||
          |||||||||| <-- safe THR
        ..||||||||||
        ||||||||||||

    The abstract "First LARGE GAP" is perfect for this.
    Current code is considering ONLY TOP 2 jumps(>= MIN_GAP) to be big, gives the smaller one

    """
    # Sort the Q vals
    QVals = sorted(QVals_orig)
    # Find the FIRST LARGE GAP and set it as threshold:
    ls = (looseness + 1) // 2
    l = len(QVals) - ls
    max1, thr1 = min_jump, 255
    for i in range(ls, l):
        jump = QVals[i + ls] - QVals[i - ls]
        if jump > max1:
            max1 = jump
            thr1 = QVals[i - ls] + jump / 2

    return thr1


# TODO: Accept df_out instead of returning dict
def read_response(image, image_dpi, df_bubbles, min_jump):
    img = image.copy()
    overlay_img = image.copy()

    if img.max() > img.min():
        img = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    OMRresponse = {}

    # Get mean vals n other stats
    for _, bubble in df_bubbles.iterrows():
        x, y = bubble[["Xpos", "Ypos"]]

        # x = x - ANCHOR_DISTANCE_FROM_EDGES_IN_POINTS + ANCHOR_RADIUS_IN_POINTS
        # y = y - ANCHOR_DISTANCE_FROM_EDGES_IN_POINTS + ANCHOR_RADIUS_IN_POINTS

        # Calculate OMR stuff
        tl_x_big = latex_point_to_pixel(x-BUBBLE_RADIUS_IN_POINTS, image_dpi[0])
        tl_y_big = latex_point_to_pixel(y-BUBBLE_RADIUS_IN_POINTS, image_dpi[1])
        br_x_big = latex_point_to_pixel(x+BUBBLE_RADIUS_IN_POINTS, image_dpi[0])
        br_y_big = latex_point_to_pixel(y+BUBBLE_RADIUS_IN_POINTS, image_dpi[1])

        offset = BUBBLE_RADIUS_IN_POINTS / math.sqrt(2)
        tl_x_fit = latex_point_to_pixel(x-offset, image_dpi[0])
        tl_y_fit = latex_point_to_pixel(y-offset, image_dpi[1])
        br_x_fit = latex_point_to_pixel(x+offset, image_dpi[0])
        br_y_fit = latex_point_to_pixel(y+offset, image_dpi[1])

        tl_x = round((tl_x_big + tl_x_fit) / 2)
        tl_y = round((tl_y_big + tl_y_fit) / 2)
        br_x = round((br_x_big + br_x_fit) / 2)
        br_y = round((br_y_big + br_y_fit) / 2)

        bubble_brightness = cv2.mean(img[tl_y:br_y, tl_x:br_x])[0]
        question, subquestion, multiple_choice, bubble_x, correct = bubble[["exam", "question", "MC", "Xpos", "correct"]]
        try:
            correct = int(correct)
            columns_x = df_bubbles.loc[(df_bubbles["exam"] == question) & (df_bubbles["question"] == subquestion), "Xpos"]
            columns_x = sorted([int(x) for x in columns_x.unique()])
            other_col_number = columns_x.index(int(bubble_x))
            OMRresponse[f"{question}.{subquestion}_column{other_col_number}_{correct}"] = bubble_brightness
        except ValueError:
            OMRresponse[f"{question}.{subquestion}_{multiple_choice}"] = bubble_brightness

        # Add the box to the overlay image
        cv2.rectangle(overlay_img, (tl_x, tl_y), (br_x, br_y), OVERLAY_COLOR, 3)

    if len(OMRresponse) > 0:
        globalTHR = getGlobalThreshold(OMRresponse.values(), min_jump, looseness=4)

        page = df_bubbles["page"].iat[0]
        OMRresponse[f"page{page}_threshold"] = globalTHR

        print(
            "Thresholding:\t\t globalTHR: ",
            round(globalTHR, 2),
            "\t(Looks like a Xeroxed OMR)" if (globalTHR == 255) else "",
        )

    return OMRresponse, overlay_img


def latex_point_to_pixel(point, image_dpi):
    return round(point * image_dpi / 72.27)


def handle_markers(image_norm, image_dpi, omr_marker, curr_filename):
    image_eroded_sub = cv2.normalize(image_norm, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)


    # Quads on warped image
    quads = {}
    h1, w1 = image_eroded_sub.shape[:2]
    midh, midw = h1 // 3, w1 // 2
    origins = [[0, 0], [midw, 0], [0, midh], [midw, midh]]
    quads[0] = image_eroded_sub[0:midh, 0:midw]
    quads[1] = image_eroded_sub[0:midh, midw:w1]
    quads[2] = image_eroded_sub[midh:h1, 0:midw]
    quads[3] = image_eroded_sub[midh:h1, midw:w1]

    h, w = omr_marker.shape[:2]
    centres = []
    sumT, maxT = 0, 0
    print("Matching Marker:\t", end=" ")
    for k in range(0, 4):
        res = cv2.matchTemplate(quads[k], omr_marker, cv2.TM_CCOEFF_NORMED)
        maxT = res.max()
        print("Q" + str(k + 1) + ": maxT", round(maxT, 3), end="\t")
        if maxT < THRESHOLD_CIRCLE:
            # Warning - code will stop in the middle. Keep Threshold low to
            # avoid.
            print(
                curr_filename,
                "\nError: No circle found in Quad",
                k + 1,
                "maxT",
                maxT)
            return image_norm

        pt = np.argwhere(res == maxT)[0]
        pt = [pt[1], pt[0]]
        pt[0] += origins[k][0]
        pt[1] += origins[k][1]
        image_norm = cv2.rectangle(
            image_norm,
            tuple(pt),
            (pt[0] + w, pt[1] + h),
            (150, 150, 150),
            2
        )
        image_eroded_sub = cv2.rectangle(
            image_eroded_sub,
            tuple(pt),
            (pt[0] + w, pt[1] + h),
            (50, 50, 50),
            4
        )
        centres.append([pt[0] + w / 2, pt[1] + h / 2])
        sumT += maxT

    image_norm = four_point_transform(image_norm, image_dpi, np.array(centres))

    return image_norm


def resize_util(img, u_width=None, u_height=None):
    h, w = img.shape[:2]
    if u_width is None and u_height is None:
        return img
    if u_width is None:
        u_width = int(w * u_height / h)
    if u_height is None:
        u_height = int(h * u_width / w)
    return cv2.resize(img, (int(u_width), int(u_height)))


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect


def four_point_transform(image, image_dpi, pts):
    # obtain a consistent order of the points and unpack them individually
    rect = order_points(pts)
    h, w = image.shape[:2]

    offset = latex_point_to_pixel(ANCHOR_DISTANCE_FROM_EDGES_IN_POINTS, image_dpi[0])
    dst = np.array([
        [offset, offset],
        [w - 1 - offset, offset],
        [w - 1 - offset, h - 1 - offset],
        [offset, h - 1 - offset]], dtype="float32")

    # compute the perspective transform matrix and then apply it

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (w, h))

    # return the warped image
    return warped


if __name__ == "__main__":
    main()
