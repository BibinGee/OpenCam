#!/usr/bin/env python3

# Home video monitor
# Developed by bibin_zhi@163.com
# Date: 2018-10-12
# Revision: 1.0.0
# Hardware:
# 1. Raspberry 3B+ board
# 2. general camera
# 3. 8G byte usb disk

import cv2
import os
import time
import platform
from PIL import Image
import numpy as np
import threading
import subprocess
import shutil



image_h = 320
image_w = 240
##image_h = 640
##image_w = 480

lock = threading.Lock()
lock_for_avi2mp4 = threading.Lock()

#gamma值越大，图像越暗
def gamma_trans(img,gamma):
    #具体做法先归一化到1，然后gamma作为指数值求出新的像素值再还原
    gamma_table = [np.power(x/255.0,gamma)*255.0 for x in range(256)]
    gamma_table = np.round(np.array(gamma_table)).astype(np.uint8)
    #实现映射用的是Opencv的查表函数
    return cv2.LUT(img,gamma_table)

## create a video writer

def vWriter(index):
    global root_dir
    
    system = platform.system()

    #XVID MPEG-4 (XVID) info
    fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')


    filename = time.strftime("%Y-%m-%d",time.localtime())

    
    if system == 'Windows':
        fps = 18
        path = root_dir + '''%s part %s.avi'''%(filename,index)

    elif system == 'Linux':
        fps = 9
##        path = '''/home/pi/Desktop/videos/%s_part_%s.avi'''%(filename,index)
        path = root_dir + '''%s_part_%s.avi'''%(filename,index)
        
    out = cv2.VideoWriter (path, fourcc ,fps, (image_h,image_w) )
    
    return out, path


## Start a video record

def vRecord(cam,writer,v_string):
    
    lock.acquire()

    try:
        t1 = time.time()

        font = cv2.FONT_HERSHEY_SIMPLEX

        ret, frame = cam.read()
        
        if ret == True:
            
            if(platform.system() == "Windows"):
                frame = cv2.flip(frame,1)
            # cv2.imshow("Original_" + v_string, frame)
            
            t = time.localtime()
            text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
    ##        determine if day time use use original exposure
    ##        if night time use equalizeHist to enhance image
            if ( t.tm_hour >= 20 or t.tm_hour <= 6):
    ##            img_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV )
    ##            img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
    ##        
    ##            img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
                img_output = gamma_trans(frame,0.25)
    ##           add time on image        
                #putText() 各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细
                if(image_h == 640):
                    img_output = cv2.putText(img_output, text, (400, 460), font, 0.5, (0, 0, 255), 1)
                else:
                    img_output = cv2.putText(img_output, text, (100, 230), font, 0.5, (0, 0, 255), 1)
            else:
                img_output = gamma_trans(frame,0.7)
                if(image_h == 640):
                    img_output = cv2.putText(img_output, text, (400, 460), font, 0.5, (0, 0, 255), 1)
                else:
                    img_output = cv2.putText(img_output, text, (100, 230), font, 0.5, (0, 0, 255), 1)            


            cv2.imshow(v_string, img_output)
    ##        print(img_output.shape)
    ##        record a videos
            a = writer.write(img_output)
            print('%s cost: %s'%(threading.current_thread().name, time.time() - t1))
            print('Thread ended: ', threading.current_thread().name)
    finally:
        lock.release()


## covert avi to mp4:
## purpose is to save storage
def avi2mp4():

    global last_file   
    global mp4_dir
    
    lock_for_avi2mp4.acquire()
    try:
        ofile = last_file
        
        t1 = time.time()
        print('file will be converted ', ofile)
        
        t = ofile.split('/')
    ##    to determine the file path
        nfile = mp4_dir + '/' + t[len(t)-1]
    ##    to keep the path, but replace suffix from .avi to .mp4
        nfile = nfile.replace('avi', 'mp4')
        print('new file: ',nfile)
        
    ##    cmd = 'ffmpeg -i %s -ac 2 -b:v 2000k -c:a aac -c:v libx264 -b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 %s'%(ofile, nfile)
    ##    start avi to mp4 converttion
        cmd = 'ffmpeg -i \'%s\' \'%s\''%(ofile, nfile)
        print('convert command started ', cmd)
    ##    call terminal to perform the ffmpeg command.
        res = subprocess.call(cmd,shell = True)
        
        print('remove ', ofile)
    ##    after convertion complete, delete the avi file, to save storage
        os.remove(ofile)
        print('total time cost: ', time.time() - t1)        
        print('thread %s ended.' % threading.current_thread().name)

    finally:
        lock_for_avi2mp4.release()
    
 

def videoThread(cap, string):
    global last_file, mp4_dir
    
    global root_dir

##    root_dir = '/home/pi/Desktop/videos/'
##    select a U disk
    if(platform.system() == 'Windows'):
        root_dir = 'E:\\videos\\' + string + '\\'
        if(os.path.exists(root_dir) == False):
            os.mkdir(root_dir)       
    else:
        root_dir = '/media/pi/USB DISK/videos/' + string +'/'
        if(os.path.exists(root_dir) == False):
            os.mkdir(root_dir)  
##        root_dir = '/home/pi/Desktop/videos/'
    
    part = 1

    video_out, last_file = vWriter(part)
    
    mp4_dir = root_dir + time.strftime("%Y-%m-%d", time.localtime())
    if(os.path.exists(mp4_dir) == False):
        os.mkdir(mp4_dir)
    
    print(last_file)

    # set up heihg for image
    cap.set(3,image_h)
    # set up width for image
    cap.set(4,image_w)

## recoard the begin time
    begin_time = time.localtime()
    
##    t1 = time.time()
    while True:
        
## call vRecoard to start video record
        vRecord(cap, video_out, string)
##        t2 = time.time()
##        print(1/(t2 - t1))
##        t1 = t2

        end_time = time.localtime()
##        print('stamp = %s', end_time.tm_min - begin_time.tm_min)
        
# each hour save a videos file, start a new file record
# each day changed, create a new folder to save mp4 video, and update part index to 1
        if(abs(end_time.tm_hour - begin_time.tm_hour) >= 1):

    ##        check if day changed, then create a new directory.
            if(abs(end_time.tm_mday - begin_time.tm_mday) >= 1):

                # begin_time = time.localtime()
                
                # start a new record
                video_out.release()
                part = 1               
    ##          start a avi to mp4 convertion in a individual thread
                t = threading.Thread(target=avi2mp4, name='avi2mp4')
                t.start()
                
                # update a writer and file name
                video_out, last_file = vWriter(part)

                # Create a new directory
                mp4_dir = root_dir + time.strftime("%Y-%m-%d",time.localtime())
                print('create a new folder:',mp4_dir)

                if(os.path.exists(mp4_dir) == False):
                    os.mkdir(mp4_dir)
                    
                # delete videos in last 2 day 
                fs = os.listdir(root_dir)
                for i in range(len(fs)):
                    if os.path.isdir(root_dir + fs[i]):
                        t = time.strptime(fs[i],"%Y-%m-%d")
                        if (begin_time.tm_mday - t.tm_mday >= 2):
                            shutil.rmtree(root_dir + fs[i])
                            print('remove old vides: ', root_dir + fs[i])

            # if only hour changed, just update video writer and file name
            else:

                ## release current video recording.
                video_out.release()
    ##          start a avi to mp4 convertion in a individual thread
                if platform.system() == "Linux":
                    t = threading.Thread(target=avi2mp4, name='avi2mp4')
                    t.start()
        
    ##          start a new file record 
                part = part +1

    ##          to make sure the last file already pass to ffmpeg mp4 convertion progress.
                video_out, last_file = vWriter(part)
                print('create a new video: ', last_file)
            # update time
            begin_time = time.localtime()
            print(begin_time)
            
        #按q推出
        if cv2.waitKey(1) == ord('q'):
            break
          
    cap.release()

    video_out.release()

    cv2.destroyAllWindows ()

    print('Thread ended: ', threading.current_thread().name)


# Main thread:
if __name__ == '__main__':

#     global last_file, mp4_dir
    
#     global root_dir

# ##    root_dir = '/home/pi/Desktop/videos/'
# ##    select a U disk
#     if(platform.system() == 'Windows'):
#         root_dir = 'E:\\videos\\'
#     else:
#         root_dir = '/media/pi/USB DISK/videos/'
# ##        root_dir = '/home/pi/Desktop/videos/'
    
#     part = 1

#     video_out, last_file = vWriter(part)
    
#     mp4_dir = root_dir + time.strftime("%Y-%m-%d", time.localtime())
#     if(os.path.exists(mp4_dir) == False):
#         os.mkdir(mp4_dir)
    
#     print(last_file)
##  open camera
    try:
        cap1 = cv2.VideoCapture (0)

        if cap1.isOpened():
            t = threading.Thread(target = videoThread, args = (cap1, 'video0') ,name='videoThread0')
            t.start()

        else:
            cap1.release()

        cap2 = cv2.VideoCapture (1)

        if cap2.isOpened():
            t = threading.Thread(target = videoThread, args = (cap2, 'video1') ,name='videoThread1')
            t.start()
        else:
            cap2.release()
    except Exception as e:
        print(e)
    # finally:
    #     cap1.release()
    #     cap2.release()
    #     print('Thread ended: ', threading.current_thread().name)

    #     # set up heihg for image
    #     cap.set(3,image_h)
    #     # set up width for image
    #     cap.set(4,image_w)

    # ## recoard the begin time
    #     begin_time = time.localtime()
        
    # ##    t1 = time.time()
    #     while True:
            
    # ## call vRecoard to start video record
    #         vRecord(cap,video_out)
    # ##        t2 = time.time()
    # ##        print(1/(t2 - t1))
    # ##        t1 = t2

    #         end_time = time.localtime()
    # ##        print('stamp = %s', end_time.tm_min - begin_time.tm_min)
            
    # # each hour save a videos file, start a new file record
    # # each day changed, create a new folder to save mp4 video, and update part index to 1
    #         if(abs(end_time.tm_hour - begin_time.tm_hour) >= 1):

    #     ##        check if day changed, then create a new directory.
    #             if(abs(end_time.tm_mday - begin_time.tm_mday) >= 1):

    #                 # begin_time = time.localtime()
                    
    #                 # start a new record
    #                 video_out.release()
    #                 part = 1               
    #     ##          start a avi to mp4 convertion in a individual thread
    #                 t = threading.Thread(target=avi2mp4, name='avi2mp4')
    #                 t.start()
                    
    #                 # update a writer and file name
    #                 video_out, last_file = vWriter(part)

    #                 # Create a new directory
    #                 mp4_dir = root_dir + time.strftime("%Y-%m-%d",time.localtime())
    #                 print('create a new folder:',mp4_dir)

    #                 if(os.path.exists(mp4_dir) == False):
    #                     os.mkdir(mp4_dir)
                        
    #                 # delete videos in last 2 day 
    #                 fs = os.listdir(root_dir)
    #                 for i in range(len(fs)):
    #                     if os.path.isdir(root_dir + fs[i]):
    #                         t = time.strptime(fs[i],"%Y-%m-%d")
    #                         if (begin_time.tm_mday - t.tm_mday >= 2):
    #                             shutil.rmtree(root_dir + fs[i])
    #                             print('remove old vides: ', root_dir + fs[i])

    #             # if only hour changed, just update video writer and file name
    #             else:

    #                 ## release current video recording.
    #                 video_out.release()
    #     ##          start a avi to mp4 convertion in a individual thread
    #                 if platform.system() == "Linux":
    #                     t = threading.Thread(target=avi2mp4, name='avi2mp4')
    #                     t.start()
            
    #     ##          start a new file record 
    #                 part = part +1

    #     ##          to make sure the last file already pass to ffmpeg mp4 convertion progress.
    #                 video_out, last_file = vWriter(part)
    #                 print('create a new video: ', last_file)
    #             # update time
    #             begin_time = time.localtime()
    #             print(begin_time)
                
    #         #按q推出
    #         if cv2.waitKey(1) == ord('q'):
    #             break
              
    # cap.release()

    # video_out.release()

    # cv2.destroyAllWindows ()

    # print('Thread ended: ', threading.current_thread().name)
