import math
import os
import sqlite3
import numpy
import cv2
from detect_card import detect_card
from cv_utils import float_version, show_scaled, sum_squared, ccoeff_normed
import config

def get_card(color_capture, corners):
    target = [(0,0), (223,0), (223,310), (0,310)]
    mat = cv2.CreateMat(3,3, cv2.CV_32FC1)
    cv2.GetPerspectiveTransform(corners, target, mat)
    warped = cv2.CloneImage(color_capture)
    cv2.WarpPerspective(color_capture, warped, mat)
    cv2.SetImageROI(warped, (0,0,223,310) )
    return warped

#*****************
#this is the watch-for-card bit
captures = []

def card_window_clicked(event, x, y, flags, param):
    if event == 6:
    #delete capture array indexed at param, update windows
        global captures
        del captures[param]
        update_windows()

def update_windows(n=3):
    #print "update windows!"
    l = len(captures)
    for i in xrange(1,min(n,l)+1):
        #print "setting ",i
        tmp = cv2.CloneImage(captures[-i])
        cv2.PutText(tmp, "%s" % (l-i+1), (1,24), font, (255,255,255))
        cv2.ShowImage("card_%d" % i, tmp)
        cv2.SetMouseCallback("card_%d" % i, card_window_clicked, l - i)

def watch_for_card(camera):
    has_moved = False
    been_to_base = False

    global captures
    global font
    captures = []

    #font = cv2.initFont(cv2.CV_FONT_HERSHEY_SIMPLEX, 1.0, 1.0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    #img = cv2.queryFrame(camera)
    result, img = camera.read()
    print(img)
    if result:
        size = cv2.getSize(img)
        n_pixels = size[0]*size[1]
    else:
        size = (0, 0)
        n_pixels = 0
        return []

    grey = cv2.createImage(size, 8, 1)
    recent_frames = [cv2.CloneImage(grey)]
    base = cv2.CloneImage(grey)
    cv2.cvtColor(img, base, cv2.CV_RGB2GRAY)
    #cv2.ShowImage('card', base)
    tmp = cv2.CloneImage(grey)


    while True:
        #img = cv2.QueryFrame(camera)
        result, img = camera.read()
        cv2.cvtColor(img, grey, cv2.CV_RGB2GRAY)

        biggest_diff = max(sum_squared(grey, frame) / n_pixels for frame in recent_frames)

        #display the cam view
        cv2.PutText(img, "%s" % biggest_diff, (1,24), font, (255,255,255))
        cv2.ShowImage('win',img)
        recent_frames.append(cv2.CloneImage(grey))
        if len(recent_frames) > 3:
            del recent_frames[0]

        #check for keystroke
        c = cv2.WaitKey(10)
        #if there was a keystroke, reset the last capture
        if c == 27:
            return captures
        elif c == 32:
            has_moved = True
            been_to_base = True
        elif c == 114:
            base = cv2.CloneImage(grey)


        #if we're stable-ish
        if biggest_diff < 10:
            #if we're similar to base, update base
            #else, check for card
            #base_diff = max(sum_squared(base, frame) / n_pixels for frame in recent_frames)
            base_corr = min(ccoeff_normed(base, frame) for frame in recent_frames)
            #cv2.ShowImage('debug', base)

            """for i, frame in enumerate(recent_frames):
                tmp = cv2.CloneImage(base)
                cv2.Sub(base, frame, tmp)
                cv2.Pow(tmp, tmp, 2.0)
                cv2.PutText(tmp, "%s" % (i+1), (1,24), font, (255, 255, 255))
                #my_diff = sum_squared(base, frame) / n_pixels
                my_diff = ccoeff_normed(base, frame) #score(base, frame, cv2.CV_TM_CCOEFF_NORMED)
                cv2.PutText(tmp, "%s" % my_diff, (40, 24), font, (255, 255, 255))
                cv2.ShowImage('dbg%s' % (i+1), tmp)"""
            #print "stable. corr = %s. moved = %s. been_to_base = %s" % (base_corr, has_moved, been_to_base)
            if base_corr > 0.75 and not been_to_base:
                base = cv2.CloneImage(grey)
            #	cv2.ShowImage('debug', base)
                has_moved = False
                been_to_base = True
                print("STATE: been to base. waiting for move")
            elif has_moved and been_to_base:
                corners = detect_card(grey, base)
                if corners is not None:
                    card = get_card(grey, corners)
                    cv2.Flip(card,card,-1)
                    captures.append(card)
                    update_windows()
                    #cv2.ShowImage('card', card)
                    has_moved = False
                    been_to_base = False
                    print("STATE: detected. waiting for go to base")
        else:
            if not has_moved:
                print("STATE: has moved. waiting for stable")
            has_moved = True


def setup_windows():
    cv2.namedWindow('card_1')
    cv2.namedWindow('card_2')
    cv2.namedWindow('card_3')
    #cv2.NamedWindow('base')
    cv2.namedWindow('win')
    cv2.startWindowThread()


#cv2.EncodeImage('.PNG',img).tostring()
def save_captures(num, captures):
    dir = "capture_%02d" % num
    if not os.path.exists(dir):
        os.mkdir(dir)
    for i, img in enumerate(captures):
        path = os.path.join(dir, "card_%04d.png" % i)
        if os.path.exists(path):
            raise Exception("path %s already exists!" % path)
        cv2.SaveImage(path, img)

def folder_to_db(num):
    connection = sqlite3.connect(config.db_file)
    try:
        cursor = connection.cursor()

        dir = "capture_%02d" % num
        names = sorted(os.listdir(dir))
        for i, name in enumerate(names):
            path = os.path.join(dir, name)
            img = open(path).read()

            cursor.execute('insert into inv_cards (scan_png, box, box_index, recognition_status, inventory_status) values (?, ?, ?, ?, ?)', [sqlite3.Binary(img), num, i, "scanned", "present"])
        connection.commit()
    finally:
        connection.close()

'''
import cv
import scan_card
base = cv2.LoadImage("base.png", 0)
known = cv2.LoadImage("known/swamp_m12_03.jpg")
capture = cv2.LoadImage("swamp_02.png", 0)
corners =  scan_card.detect_card(capture, base)
card = scan_card.get_card(cv2.LoadImage("swamp_02.png"), corners)

cv2.NamedWindow("win")
cv2.StartWindowThread()
cv2.ShowImage("win", card)
'''


'''
test 1
base = cv2.LoadImage("base.png", 0)
capture = cv2.LoadImage("swamp_02.png", 0)
corners =  scan_card.detect_card(capture, base)
corners should not be None
corners should be close to [(253, 44), (503, 44), (530, 400), (244, 402)]


test 2
base = cv2.LoadImage("base_03.png", 0)
capture = cv2.LoadImage("swamp_03.png", 0)
corners =  scan_card.detect_card(capture, base)
corners should not be none
corners should be close to [(167, 126), (384, 69), (460, 366), (235, 423)]
'''


'''
for dirname, dirnames, filenames in os.walk('known'):
    for filename in filenames:
    path = os.path.join(dirname, filename)
    img = cv2.LoadImage(path,0)
    cv2.SetImageROI(img, (0,0,223,310))
    known.append( (path, img) )



r = cv2.CreateMat(1, 1, cv2.CV_32FC1)
'''

'''
import cv
import scan_card
cv2.NamedWindow('win')
cv2.NamedWindow('base')
cv2.NamedWindow('card')
cv2.StartWindowThread()
cam = cv2.CreateCameraCapture(0)
scan_card.watch_for_card(cam)
'''


'''
cards = scan_card.load_sets(base_dir, ['ISD', 'DKA'])
c2 = [(name, scan_card.gradient(the_card)[1]) for name, the_card in cards]

for i in xrange(9):
    card = cv2.LoadImage('captures/card_%04d.png' % i,0)
    cv2.ShowImage('card',card); g = scan_card.gradient(card)[1]
    f = sorted([(score(g, the_card_g, cv2.CV_TM_CCOEFF), name) for name,the_card_g in c2], reverse=True)[0:5]
    print f
    raw_input()
'''

