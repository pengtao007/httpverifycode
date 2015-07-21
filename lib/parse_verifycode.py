#!/usr/bin/env python
#-*- coding: utf-8 -*-
try:
    from PIL import Image
except:
    print "import PIL fail,please install by : pip install pillow "
    raise SystemExit
try:
    import pytesseract
except:
    print "import pytesseract fail,please install first !"
    print "install google tesseract : brew install tesseract (osx) or apt-get install tesseract-ocr (kali linux)"
    print "intall pytesseract : pip install pytesseract"
    raise SystemExit
try:
    import requests
except:
    print "import requests fail,please install by : pip install requests"
    raise SystemExit
from StringIO import StringIO
import random
import string
import os


def __get_http_image(url,req=None,pic_type='JPEG',pic_type_name='jpg'):
    '''
    get http image to local picture file
    '''
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

    if req == None:
        r = requests.get(url, headers = headers, stream = True)
    else:
        r = req.get(url, headers = headers, stream = True)
    file_name = 'temp_'+''.join(random.sample(string.lowercase,8))+'.'+pic_type_name
    if r.status_code == requests.codes.ok:
        try:
            i = Image.open(StringIO(r.content))
            i .save(file_name, pic_type)
            return file_name
        except:
            return None
    return None   

def get_verifycode_from_http(url,req=None,pic_type='JPEG',pic_type_name='jpg'):
    '''
    get a http image verify code
    '''
    file_name  = __get_http_image(url,req,pic_type,pic_type_name)
    if file_name != None:
        code = get_verifycode_from__file(file_name)
        try:
            os.remove(file_name)
        except:
            pass
        return code
    else:
        return None

def get_verifycode_from__file(file_name):
    '''
    get a local image file verify code 
    '''
    try:
        i = Image.open(file_name)
        code = pytesseract.image_to_string(i)

        return code
    except:
        return None

def __check_verifycode(code):
    '''
        check the verifycode wheater is right
    '''
    if code == None:
        return False
    #check the length
    if len(code)!=4 :
        return False
    #check the char
    import re
    regex=r'[^\w]'
    p=re.compile(regex)
    m=p.findall(code)
    if m and len(m)>0:
        return False

    return True

def __test_verifycode():
    '''
        Test http verifycode success rate
    '''
    url = 'http://www.sepc.edu.cn/Admin/VerifyCode.aspx?VerifyCodeName=WebFort_Admin_Login'
    code_checked_right = 0
    test_count = 100
    for i in range(0,test_count):
        code = get_verifycode_from_http(url)
        if __check_verifycode(code):
            code_checked_right += 1
        print "test code %d ,the code is :%s" % (i,code)
    rate = code_checked_right * 100 / test_count
    print "finish test, success is :%d%%" %rate  

def main():
    __test_verifycode()
    
if __name__ == '__main__':
    main()
