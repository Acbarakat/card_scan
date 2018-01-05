import cv2
import scan_card

from panacea import session, setup_all
import sqlalchemy
from sqlalchemy import func
from models import *
import re

setup_all(True)

cam = cv2.VideoCapture(0)
print(cam.isOpened())
print(cam)
while(True):
    # Capture frame-by-frame
    ret, frame = cam.read()
    print(ret)
    print(frame)

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame', gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
scan_card.setup_windows()

def capture_box(cam, boxnum):
	while True: #retry loop
		retry = False
		captures = scan_card.watch_for_card(cam)
		scan_card.save_captures(boxnum, captures)
		print("captured %d cards. is this correct?" % len(captures))
		answer = input()
		print("got answer: ", answer)
		if re.search('[yc]',answer):
			break #finish the function
		else:
			print("try editing captures_%02d to match" % boxnum)
			answer = ""
			while not re.match('[cra]', answer):
				print("when done - (c)orrected? (r)etry scan? or (a)bort?")
				answer = input()
			if re.search('c',answer):
				break
			elif re.search('r',answer):
				continue
			elif re.search('a',answer):
				return #abort the scan
			#default will retry

	scan_card.folder_to_db(boxnum)


if __name__ == '__main__':
	#main loop
	while True:
		q = session.query(func.max(sqlalchemy.cast(InvCard.box, sqlalchemy.Integer)))
		q = q.first()[0]
		next_box = q + 1 if q else 1
		print("scanning %02d" % next_box)
		capture_box(cam, next_box)
