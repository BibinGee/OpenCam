import cv2
import os
import time
import platform
from PIL import Image
import numpy as np

def zmMinFilterGray(src, r=7):
    '''最小值滤波，r是滤波器半径'''
    if r <= 0:
        return src
    h, w = src.shape[:2]
    
    #print(h,w)
    
    I = src
 #   res = np.minimum(I  , I[[0]+range(h-1)  , :])
 #   res = np.minimum(res, I[range(1,h)+[h-1], :])
    res = np.minimum(I  , I[[0]+[x for x in range(h-1)]  , :])
    res = np.minimum(res, I[[x for x in range(1,h)]+[h-1], :])
    I = res
##    res = np.minimum(I  , I[:, [0]+range(w-1)])
##    res = np.minimum(res, I[:, range(1,w)+[w-1]])
    
    res = np.minimum(I  , I[:, [0]+[x for x in range(w-1)]])
    res = np.minimum(res, I[:, [x for x in range(1,w)]+[w-1]])
    
    return zmMinFilterGray(res, r-1)
 
def guidedfilter(I, p, r, eps):
    '''引导滤波，直接参考网上的matlab代码'''
    height, width = I.shape
    m_I = cv2.boxFilter(I, -1, (r,r))
    m_p = cv2.boxFilter(p, -1, (r,r))
    m_Ip = cv2.boxFilter(I*p, -1, (r,r))
    cov_Ip = m_Ip-m_I*m_p
 
    m_II = cv2.boxFilter(I*I, -1, (r,r))
    var_I = m_II-m_I*m_I
 
    a = cov_Ip/(var_I+eps)
    b = m_p-a*m_I
 
    m_a = cv2.boxFilter(a, -1, (r,r))
    m_b = cv2.boxFilter(b, -1, (r,r))
    return m_a*I+m_b
 
def getV1(m, r, eps, w, maxV1):  #输入rgb图像，值范围[0,1]
    '''计算大气遮罩图像V1和光照值A, V1 = 1-t/A'''
    V1 = np.min(m,2)                                         #得到暗通道图像
    V1 = guidedfilter(V1, zmMinFilterGray(V1,7), r, eps)     #使用引导滤波优化
    bins = 2000
    ht = np.histogram(V1, bins)                              #计算大气光照A
    d = np.cumsum(ht[0])/float(V1.size)
    for lmax in range(bins-1, 0, -1):
        if d[lmax]<=0.999:
            break
    A  = np.mean(m,2)[V1>=ht[1][lmax]].max()
         
    V1 = np.minimum(V1*w, maxV1)                   #对值范围进行限制
     
    return V1,A
 
def deHaze(m, r=81, eps=0.001, w=0.95, maxV1=0.80, bGamma=False):
    Y = np.zeros(m.shape)
    V1,A = getV1(m, r, eps, w, maxV1)               #得到遮罩图像和大气光照
    for k in range(3):
        Y[:,:,k] = (m[:,:,k]-V1)/(1-V1/A)           #颜色校正
    Y =  np.clip(Y, 0, 1)
    if bGamma:
        Y = Y**(np.log(0.5)/np.log(Y.mean()))       #gamma校正,默认不进行该操作
    return Y


def videoRecord(index):
        # File path and file name
    filename = time.strftime("%Y-%m-%d",time.localtime())
    
    path = '''E:\\Videos\\%s part %s.avi'''%(filename,index)
    print (path)
    if system == 'Windows':
        path = '''E:\\Videos\\%s part %s.avi'''%(filename,index)
        #out = cv2.VideoWriter (path, fourcc ,fps, (640,480) )
        #out = cv2.VideoWriter ('E:\\Videos\\'+filename + '_part'+ index'.avi', fourcc ,fps, (640,480) )
    elif system == 'Linux':
        path = '''/home/pi/Desktop/%s part %s.avi'''%(filename,index)
        #out = cv2.VideoWriter (path, fourcc ,fps, (640,480) )
        #out = cv2.VideoWriter ('/home/pi/Desktop/'+filename +'.avi', fourcc ,fps, (640,480) )
        
    out = cv2.VideoWriter (path, fourcc ,fps, (640,480) )
    return out


if __name__ == '__main__':
    #cap.set(4,720)

    fps = 20
    part = 1
    system = platform.system()

    #XVID MPEG-4 (XVID) info
    #fourcc = cv2.VideoWriter_fourcc(*'XVID')

    #CV_FOURCC('M', 'J', 'P', 'G') = motion-jpeg codec
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')


    begin_time = time.localtime()

    font = cv2.FONT_HERSHEY_SIMPLEX

    expose_factor = 8
    
    video_out = videoRecord(part)
    
 
    cap = cv2.VideoCapture (0)

    while True:
        #读一帧视频
        ret, frame = cap.read()
        
        if ret == True:
            
            frame = cv2.flip(frame,1)
            cv2.imshow("Original",frame)
            #print(frame.depth())
##                print(frame)
            
    ##        gray_img = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    ##        equ_img = cv2.equalizeHist(gray_img)
    ##        img = np.hstack((gray_img,equ_img))
            
            #cv2.imshow("Gray enhencement",img)
            
            blurred = cv2.GaussianBlur(frame,(3,3),1)
            result_img = deHaze(blurred/255.0) * expose_factor
            #print(result_img)

##                cv2.imshow("Gaussian filter + haze removal,value = 15",result_img)
            
            #Noise removing
    ##        blurred = cv2.GaussianBlur(frame,(3,3),1)
    ##        cv2.imshow("Noise removal",blurred)
            
##                timeStame = time.localtime()
            text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            #putText() 各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细         
            image = cv2.putText(result_img, text, (420, 470), font, 0.5, (0, 0, 255), 1)

            cv2.imshow('Gaussian filter + haze removal',image)
            
            # 图像灰度化
##                print(gray)
    ##        edge = cv2.Canny(gray, 80, 160)
    ##        cv2.imshow("Gray", edge)
            
            end_time = time.localtime()
            
            if(end_time.tm_min - begin_time.tm_min > 30):
                print ( 'start a new record.......')
                begin_time = time.localtime()
                
                video_out.release()
                part = part +1
                video_out = videoRecord(part)

            else:
                #写入视频文件
                a = video_out.write(frame)
               # video_out.write(result_img)
               # print ('File size: %d KB, time: %d:%d:%d' %(os.path.getsize('E:\\Videos\\'+filename +'.avi')/1024, end_time.tm_hour,end_time.tm_min, end_time.tm_sec))
                #print (end_time.tm_min - begin_time.tm_min)
                
            #按q推出
            if cv2.waitKey(1) == ord('q'):
                break
              
    cap.release()

    video_out.release()

    cv2.destroyAllWindows ()

