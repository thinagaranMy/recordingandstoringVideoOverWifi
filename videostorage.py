import cv2
import numpy as np
import sys
import datetime 
import matplotlib.pyplot as plt
import threading
import random

def update_video_file(now):
	fourcc = cv2.VideoWriter_fourcc(*'XVID')

	current_time_file = now.strftime("%d-%m-%Y-%H-%M")+str(random.randint(0, 100))+'.avi'
	saved_minute = int(now.strftime("%M"))
	video_file = cv2.VideoWriter(current_time_file, fourcc, 24, (640,480))
	return video_file, saved_minute



def motion_detection(video_capture):
	frame_count = 0
	previous_frame = None
	while True:
		frame_count += 1
		#get time 
		now = datetime.datetime.now()
		current_time = now.strftime("%d/%m/%Y %H:%M:%S")
		#check if the current time every minute and store file accordingly
		# first file creation
		if frame_count == 1:
			video_file, saved_minute = update_video_file(now)
		else:
			# If there is a minute change; change the folder
			if now != now.replace(minute = saved_minute):
				#close the current file
				video_file.release()
				video_file, saved_minute = update_video_file(now)
		ret, frame = video_capture.read()
		
		# Convert the image to grayscale
		try:
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		except "[rtsp @ 00000258c5992d00] method DESCRIBE failed: 404 Stream Not Found":
			break
		except:
			print('skipping frame')
			continue
		
		# Blur the image 
		prepared_frame = cv2.GaussianBlur(src=gray, ksize=(5,5), sigmaX=0)

		# 3. Set previous frame and continue if there is None
		if (previous_frame is None):
		  # First frame; there is no previous one yet
		  previous_frame = prepared_frame
		  continue

		# calculate difference and update previous frame
		diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)
		previous_frame = prepared_frame

		# 4. Dilute the image a bit to make differences more seeable; more suitable for contour detection
		kernel = np.ones((5, 5))
		diff_frame = cv2.dilate(diff_frame, kernel, 1)

		# 5. Only take different areas that are different enough (>50 / 255)
		thresh_frame = cv2.threshold(src=diff_frame, thresh=50, maxval=255, type=cv2.THRESH_BINARY)[1]

		
		# 6. Find and optionally draw contours
		contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
	    # Comment below to stop drawing contours
	    # Draw contours areound the object
		for contour in contours:
			if cv2.contourArea(contour) < 50:
				#too small: skip!
				continue
			(x, y, w, h) = cv2.boundingRect(contour)
			cv2.rectangle(img=frame, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)
		
		# 7. Saves the frame into a video
		resize = cv2.resize(frame, (640,480))
		cv2.putText(img=resize, text=current_time, org=(20, 430), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=0.5, color=(250, 250, 250),thickness=1)

		video_file.write(resize)
		#cv2.imshow('Motion detector', resize)
		if cv2.waitKey(1) & 0xFF == ord('s'):
			break

	# release the video file and vide input
	video_capture.release()
	video_file.release()
	print('Video file released')
	
	cv2.destroyAllWindows()


def main():
	index = 0
	video_details = []
	while index < len(sys.argv):
		if sys.argv[index] == "--h" or sys.argv[index] == "-help":
			print("\tOptions:\n\t\t-h\thelp\n\t\t-v\tvideo capture information format rtsp://username:passwrod@ipAddress/stream")
			break
		if sys.argv[index] == '-v' and index < len(sys.argv):
			video_details.append(sys.argv[index+1])
			
		if sys.argv[index] == '-v' and index > len(sys.argv): 
			print('Insufficient argument for video details')
		index +=1 
	
	for video in video_details:
		video_capture = cv2.VideoCapture(video)
		try: 
			print('Opening video stream from : '+ video)
			video_thread = threading.Thread(target=motion_detection, args=(video_capture,))
			video_thread.start()			
		except:
			print('Failed opening video stream')

if __name__ == "__main__":
    main()