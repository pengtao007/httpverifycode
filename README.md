# httpverifycode

Http brute with simple verify code!

1、Used tools：

(1)、tesseract（osx:brew install tesseract,kali:apt-get install tesseract-ocr）,google open-source ocr framework

(2)、pytesseract（pip install pytesseract）,python lib with google tesseract

(3)、PIL（kali：apt-get install libjpeg-dev,pip install pillow,if you have installed before,use pip install -I pillow;osx: pip install pillow），the lib for verify code image

(4)、reqeusts (pip install requests), the http request lib

2、usage:

(1)define the username file and password file in main()（user_file,pass_file）

(2)define the webpage of index、post and verifycode image url, the index page maybe not necessary.

(3)define the all post data,eg. post_data={'a':'x','b':'z'}. If the value only have  the user and password ,the post_data can be empty(post_data={})

(4)define the post username,password and verify code name in form  payload_data={'username':'xxx','password':'yyy','verificode':'zzz'}

(5)define the response check in form response_data={'success':'xxx','fail':'yyy'}, you must define one of success or fail.

(6)you can set the max threads and retry count in __init__,default are 10 threads and retry 5 times

