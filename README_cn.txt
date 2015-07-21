简单校验码的http登录的爆破

使用工具：
一、tesseract（使用osx下brew install tesseract安装，kali下使用apt-get install tesseract-ocr安装），google的开源ocr识别框架
二、pytesseract（使用pip install pytesseract安装），python调用google tesseract的库
三、PIL（使用kali下：apt-get install libjpeg-dev,pip install pillow安装,如果已装了的话，用pip install -I pillow;osx下 pip install pillow），用于验证码图形处理的库
四、reqeusts (使用pip install requests安装)，用于处理http的Python库
五、httpverifycode（自己编写的脚本），使用方法：
	1、在main中定义要使用的爆破的用户名和密码文件（user_file,pass_file）
	2、定义登录页面、登录提交页面和校验码的URL地址（login_url,login_post_url,verifycode_url）,登录页面URL如果没有特殊要求可以不需要。
	3、定义登录界面提交的全部数据post_data={'a':'x','b':'z'}(如果只有用户名、密码和校验码的话，可以定义为空post_data={})
	4、定义提交的用户名、密码和校验码id字段，格式为payload_data={'username':'xxx','password':'yyy','verificode':'zzz'}
	5、定义对爆破结果正确性判断的数据，格式为response_data={'success':'xxx','fail':'yyy'}，至少要定义一种判断依据
	6、在__init__中，可以定义使用的线程数和每一次失败重试的次数（默认为10个线程和5次重试）