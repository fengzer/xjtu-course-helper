import requests
import json
import time
from typing import Optional, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

class Login:
    def __init__(self):
        self.cookies = {}
        self.ticket = ""
        self.name = ""
        self.token = ""

    def change_psd(self, password: str) -> str:
        key = b"0725@pwdorgopenp"
        data = password.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)
        padded_data = pad(data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode('utf-8')

    def login_process(self, username: str, password: str) -> Tuple[bool, str]:
        """
        完整的登录流程
        返回: (是否成功, 错误信息)
        """
        if not password:
            return False, "请输入密码"
            
        if not username:
            return False, "请输入账号"

        try:
            login_response = self.login(username, password)
            login_data = json.loads(login_response)
            
            message = login_data.get("message", "")
            if message == "图形验证码不能为空":
                return False, "请自行登录http://org.xjtu.edu.cn/openplatform/login.html输入图片验证码登录再来此处重新登录"
                
            if message != "成功":
                return False, f"登录失败：{message}"

            usertoken = login_data.get("data", {}).get("tokenKey")
            if not usertoken:
                return False, "获取usertoken失败"

            ticket_response = self.get_ticket(username, usertoken)
            ticket_data = json.loads(ticket_response)
            redirect_url = ticket_data.get("data")
            
            if not redirect_url:
                return False, "获取url失败"
            
            self.visit_redirect_url(redirect_url)

            self.get_token(username)

            if not self.token:
                return False, "获取token失败"

            return True, "登录成功"

        except Exception as e:
            return False, f"登录过程出错：{str(e)}"

    def login(self, username: str, password: str) -> str:
        encrypted_pwd = self.change_psd(password)
        login_data = {
            "loginType": 1,
            "username": username,
            "pwd": encrypted_pwd,
            "jcaptchaCode": ""
        }
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        self.cookies = {
            "cur_appId_": "DP8bMYJppEA=",
            "state": "xjdCas",
            "sid_code": "workbench_login_jcaptcha_D5EEE031FFC3F40CEE6041558ED6BBF8"
        }

        for attempt in range(5):
            try:
                response = requests.post(
                    "https://org.xjtu.edu.cn/openplatform/g/admin/login",
                    json=login_data,
                    headers=headers,
                    cookies=self.cookies,
                    timeout=1.5
                )
                self.cookies.update(response.cookies.get_dict())
                return response.text
            except requests.Timeout:
                print(f"请求超时，尝试重试 ({attempt + 1}/5)")
                if attempt == 4:  # 最后一次尝试
                    raise Exception("请求多次超时，请检查网络连接")
            except Exception as e:
                print(f"发生错误：{str(e)}，尝试重试 ({attempt + 1}/5)")
                if attempt == 4:  # 最后一次尝试
                    raise
                continue
    
    def get_ticket(self, username: str, usertoken: str) -> str:
        """
        获取ticket
        """
        current_timestamp = str(int(time.time() * 1000))

        self.cookies.update({
            "open_Platform_User": usertoken,
            "memberId": "860000"
        })
        
        cookies_str = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
        
        full_url = f"https://org.xjtu.edu.cn/openplatform/oauth/auth/getRedirectUrl?userType=1&personNo={username}&_={current_timestamp}"
        headers = {
            "Cookie": cookies_str
        }
        
        response = requests.get(
            full_url,
            headers=headers
        )
        
        self.cookies.update(response.cookies.get_dict())
        
        return response.text
    
    def get_token(self, username: str) -> str:
        """
        获取token
        """
        headers = {
            "Referer": f"http://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do?ticket={self.ticket}"
        }
        
        response = requests.get(
            f"http://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/student/register.do",
            params={"number": username},
            cookies=self.cookies,
            headers=headers
        )
        
        self.cookies.update(response.cookies.get_dict())
        
        response_json = response.json()
        self.name = response_json.get("data", {}).get("name")
        self.token = response_json.get("data", {}).get("token", "")
        
        return response.text

    def visit_redirect_url(self, url: str, max_retries: int = 5, timeout: int = 2) -> None:
        """
        访问重定向URL获取新的cookies和编码转换后的响应
        
        Args:
            url: 重定向URL
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
        """
        headers = {
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://org.xjtu.edu.cn/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    allow_redirects=False,
                    cookies=self.cookies,
                    timeout=timeout
                )
                
                first_cookies = response.cookies.get_dict()
                
                if 'Location' in response.headers:
                    redirect_location = response.headers['Location']
                    if 'ticket=' in redirect_location:
                        self.ticket = redirect_location.split('ticket=')[-1]
                        try:
                            second_response = requests.get(
                                redirect_location,
                                headers=headers,
                                cookies=first_cookies,
                                timeout=timeout
                            )
                            
                            self.cookies = first_cookies.copy()
                            self.cookies.update(second_response.cookies.get_dict())
                            return  # 成功完成，退出函数
                            
                        except requests.Timeout:
                            print(f"第二次请求超时，尝试重试 ({attempt + 1}/{max_retries})")
                            continue
                            
                return
            except requests.Timeout:
                print(f"请求超时，尝试重试 ({attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise Exception("请求多次超时，请检查网络连接")
                    
            except Exception as e:
                print(f"发生错误：{str(e)}，尝试重试 ({attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise
                