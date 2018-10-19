import cv2
import os
import time
import platform
from PIL import Image
import numpy as np
import threading
import subprocess

global last_file , mp4_dir

image_h = 320
image_w = 240



def vWriter(index):
    
    fps = 10

    system = platform.system()

    #XVID MPEG-4 (XVID) info
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

        
    filename = time.strftime("%Y-%m-%d",time.localtime())

    
    if system == 'Windows':
        path = '''E:\\Videos\\%s part %s.avi'''%(filename,index)
        root_dir = 'E:\\Videos\\'
    elif system == 'Linux':
        path = '''/home/pi/Desktop/videos/%s_part_%s.avi'''%(filename,index)
        root_dir = '/home/pi/Desktop/videos/'
        
    out = cv2.VideoWriter (path, fourcc ,fps, (image_h,image_w) )
    
    return out, path



def vRecord(cam,writer):
    
    font = cv2.FONT_HERSHEY_SIMPLEX

    
    ret, frame = cam.read()
    
    if ret == True:
        
        frame = cv2.flip(frame,1)
##        cv2.imshow("Original", frame)

        img_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV )
        t = time.localtime()
        if ( t.tm_hour >= 20 or t.tm_hour <= 6):
            img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
##        img_yuv[:,0,:] = cv2.equalizeHist(img_yuv[:,0,:])
##        img_yuv[0,:,:] = cv2.equalizeHist(img_yuv[0,:,:] )
        
            img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        else:
            image_output = frame

        text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        #putText() 各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细         
##        image = cv2.putText(result_img, text, (100, 230), font, 0.5, (0, 0, 255), 1)
        img_output = cv2.putText(img_output, text, (100, 230), font, 0.5, (0, 0, 255), 1)

##        cv2.imshow('Gaussian filter + haze removal',image)
        cv2.imshow('Histogram equalized', img_output)
        a = writer.write(img_output)    



def avi2mp4():

    global last_file
    
##    file_list = os.listdir(path)
    
##    for i in range(len(file_list)):
        
    ofile = last_file
    
    print('file will be converted ', ofile)
    
    t = ofile.split('/')
    nfile = mp4_dir + '/' + t[len(t)-1]
    nfile = nfile.replace('avi', 'mp4')
    print('new file: ',nfile)
    
##    cmd = 'ffmpeg -i %s -ac 2 -b:v 2000k -c:a aac -c:v libx264 -b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 %s'%(ofile, nfile)
    cmd = 'ffmpeg -i %s %s'%(ofile, nfile)
    print('convert command started ', cmd)
    res = subprocess.call(cmd,shell = True)
    
    print('remove ', ofile)
    
    os.remove(ofile)
            
    print('thread %s ended.' % threading.current_thread().name)
    
    

if __name__ == '__main__':

    global last_file, mp4_dir
    
    #cap.set(4,720)
##    cmd = 'record'
    root_dir = 'E:\\Videos\\'
    part = 1

    video_out, last_file = vWriter(part)
    
    mp4_dir = root_dir + time.strftime("%Y-%m-%d",time.localtime())
    os.mkdir(mp4_dir)
    
    print(last_file)

    cap = cv2.VideoCapture (0)
    cap.set(3,image_h)
    cap.set(4,image_w)

##    capture = cv2.VideoCapture('E:\\Videos\\2018-10-09 part 2.avi')
    begin_time = time.localtime()
    while True:

        vRecord(cap,video_out)
        
        end_time = time.localtime()
##        print('stamp = %s', end_time.tm_min - begin_time.tm_min)
            
        if(abs(end_time.tm_hour - begin_time.tm_hour) >= 1):
            
            begin_time = time.localtime()
            
            print ( 'start a new record.......')
            
            print('last file:%s '%last_file)
            
            new = last_file.replace('avi','mp4')
            print(new)

            t = threading.Thread(target=avi2mp4, name='avi2mp4')
            t.start()
##                print(os.popen('ffmpeg -i %s %s'%(last_file,new)).read())
            
            
            
            video_out.release()
            
            part = part +1
            
            video_out, last_file = vWriter(part)

        if(abs(end_time.tm_mday - begin_time.tm_mday)>1):
            part = 1
            mp4_dir = root_dir + time.strftime("%Y-%m-%d",time.localtime())
            os.mkdir(mp4_dir)
           # video_out.write(result_img)
##            print ('File size: %d KB, time: %d:%d:%d' %(os.path.getsize('E:\\Videos\\'+filename +'.avi')/1024, end_time.tm_hour,end_time.tm_min, end_time.tm_sec))

            
        #按q推出
        if cv2.waitKey(1) == ord('q'):
            break
              
    cap.release()

    video_out.release()

    cv2.destroyAllWindows ()


