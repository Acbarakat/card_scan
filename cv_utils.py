import numpy
import cv2

def img_from_buffer(buffer):
	np_arr = numpy.fromstring(buffer,'uint8')
	np_mat = cv2.imdecode(np_arr,0)
	return cv2.fromarray(np_mat)

def show_scaled(win, img):
	min, max, pt1, pt2 = cv2.MinMaxLoc(img)
	cols, rows = cv2.GetSize(img)
	tmp = cv2.CreateMat(rows, cols,cv2.CV_32FC1)
	cv2.Scale(img, tmp, 1.0/(max-min), 1.0*(-min)/(max-min))
	cv2.ShowImage(win,tmp)

def float_version(img):
	tmp = cv2.CreateImage( cv2.GetSize(img), 32, 1)
	cv2.ConvertScale(img, tmp, 1/255.0)
	return tmp

def sum_squared(img1, img2):
	tmp = cv2.CreateImage(cv2.GetSize(img1), 8,1)
	cv2.Sub(img1,img2,tmp)
	cv2.Pow(tmp,tmp,2.0)
	return cv2.Sum(tmp)[0]

def ccoeff_normed(img1, img2):
	size = cv2.GetSize(img1)
	tmp1 = float_version(img1)
	tmp2 = float_version(img2)

	cv2.SubS(tmp1, cv2.Avg(tmp1), tmp1)
	cv2.SubS(tmp2, cv2.Avg(tmp2), tmp2)

	norm1 = cv2.CloneImage(tmp1)
	norm2 = cv2.CloneImage(tmp2)
	cv2.Pow(tmp1, norm1, 2.0)
	cv2.Pow(tmp2, norm2, 2.0)

	#cv2.Mul(tmp1, tmp2, tmp1)

	return cv2.DotProduct(tmp1, tmp2) /  (cv2.Sum(norm1)[0]*cv2.Sum(norm2)[0])**0.5

