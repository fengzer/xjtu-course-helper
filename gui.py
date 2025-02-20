import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from login import Login
from course_selection import *
import threading
import time
import datetime
import os

class CourseSelectionUI:
    def __init__(self, root, course_client, user_name):
        self.window = ttk.Toplevel(root)
        self.window.title("选课系统")
        self.window.geometry("480x1200")
        
        # 添加窗口关闭事件处理
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.course_client = course_client
        self.user_name = user_name
        self.running_threads = {}
        
        # 读取配置文件
        self.config = self.load_config()
        
        # 添加登录相关的属性
        self.root = root
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.last_relogin_attempt = time.time()
        self.relogin_interval = 5  # 重新登录间隔（秒）
        self.is_logged_in = True   # 登录状态标志
        
        self.main_frame = ttk.Frame(self.window, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_label = ttk.Label(
            self.main_frame,
            text=f"欢迎，{user_name}",
            font=("Microsoft YaHei UI", 16, "bold")
        )
        welcome_label.pack(pady=20)
        
        self.course_entries = []
        courses = self.config.get('courses', [])
        for i in range(4):
            frame = self.create_course_frame(i)
            frame.pack(fill=tk.X, pady=10)
            
            if i < len(courses):
                course = courses[i]
                self.course_entries[i]['entry'].insert(0, course.get('code', ''))
                self.course_entries[i]['type'].set(course.get('type', 'major'))
        
        self.info_text = tk.Text(
            self.main_frame,
            height=10,
            wrap=tk.WORD,
            font=("Microsoft YaHei UI", 10)
        )
        self.info_text.pack(fill=tk.BOTH, pady=10, expand=True)
        
        scrollbar = ttk.Scrollbar(self.info_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)
        
        # 启动在线人数更新
        self.update_online_users()
        self.window.after(1000, self.update_online_users)
    
    def create_course_frame(self, index):
        """创建单个课程的输入框架"""
        frame = ttk.LabelFrame(self.main_frame, text=f"课程 {index + 1}", padding="10")
        
        course_frame = ttk.Frame(frame)
        course_frame.pack(fill=tk.X, pady=5)
        
        course_label = ttk.Label(
            course_frame,
            text="课程代码：",
            font=("Microsoft YaHei UI", 10)
        )
        course_label.pack(side=tk.LEFT, padx=5)
        
        course_entry = ttk.Entry(course_frame, width=25)
        course_entry.pack(side=tk.LEFT, padx=5)

        course_type = tk.StringVar(value="major")
        type_frame = ttk.Frame(frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        for type_text, type_value in [
            ("主修课程", "major"),
            ("选修课程", "elective"),
            ("体育课程", "physical"),
            ("方案内课程", "program")
        ]:
            ttk.Radiobutton(
                type_frame,
                text=type_text,
                value=type_value,
                variable=course_type
            ).pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        start_button = ttk.Button(
            button_frame,
            text="开始抢课",
            style="primary.TButton",
            width=15,
            command=lambda: self.start_course_selection(index, course_entry, course_type, start_button)
        )
        start_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = ttk.Button(
            button_frame,
            text="停止抢课",
            style="danger.TButton",
            width=15,
            command=lambda: self.stop_course_selection(index)
        )
        stop_button.pack(side=tk.LEFT, padx=5)
        
        self.course_entries.append({
            'entry': course_entry,
            'type': course_type,
            'start_button': start_button,
            'stop_button': stop_button
        })
        
        return frame
    
    def start_course_selection(self, index, entry, type_var, start_button):
        """开始抢课"""
        course_code = entry.get().strip()
        if not course_code:
            messagebox.showerror("错误", "请输入课程代码")
            return
        
        if index in self.running_threads:
            thread = self.running_threads[index]
            if thread is not None and thread.is_alive():
                return
        
        # 创建新线程
        thread = threading.Thread(
            target=self.course_selection_loop,
            args=(index, course_code, type_var.get()),
            daemon=True
        )
        self.running_threads[index] = thread
        thread.start()
        
        start_button.config(state="disabled")
    
    def stop_course_selection(self, index):
        """停止抢课"""
        if index in self.running_threads:
            thread = self.running_threads[index]
            self.running_threads[index] = None
            self.course_entries[index]['start_button'].config(state="normal")
    
    def relogin(self):
        """重新登录"""
        current_time = time.time()
        if not self.is_logged_in and current_time - self.last_relogin_attempt < self.relogin_interval:
            return False

        self.last_relogin_attempt = current_time
        try:
            client = Login()
            success, message = client.login_process(self.username, self.password)
            
            if success:
                self.course_client = CourseSelection(
                    cookies=client.cookies,
                    token=client.token,
                    ticket=client.ticket,
                    student_code=self.username
                )
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.info_text.insert(tk.END, f"[{current_time}] 重新登录成功\n")
                self.info_text.see(tk.END)
                self.is_logged_in = True
                return True
            else:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.info_text.insert(tk.END, f"[{current_time}] 重新登录失败：{message}，5秒后重试\n")
                self.info_text.see(tk.END)
                self.is_logged_in = False
                return False
        except Exception as e:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.info_text.insert(tk.END, f"[{current_time}] 重新登录错误：{str(e)}，5秒后重试\n")
            self.info_text.see(tk.END)
            self.is_logged_in = False
            return False

    def course_selection_loop(self, index, course_code, course_type):
        """抢课循环"""
        while index in self.running_threads and self.running_threads[index]:
            try:
                # 如果未登录，尝试重新登录
                if not self.is_logged_in:
                    if not self.relogin():
                        time.sleep(0.5)
                        continue

                if course_type == "major":
                    result = self.course_client.major_course(course_code)
                elif course_type == "elective":
                    result = self.course_client.elective_course(course_code)
                elif course_type == "physical":
                    result = self.course_client.physical_course(course_code)
                else:
                    result = self.course_client.program_course(course_code)
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if "登录者身份" in result or "登录失效" in result:
                    self.is_logged_in = False
                    self.info_text.insert(tk.END, f"[{current_time}] 登录已失效，准备重新登录\n")
                    self.info_text.see(tk.END)
                    continue
                
                self.info_text.insert(tk.END, f"[{current_time}] 课程 {course_code}：{result}\n")
                self.info_text.see(tk.END)
                
                if "成功" in result:
                    self.stop_course_selection(index)
                    break
                
            except Exception as e:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.info_text.insert(tk.END, f"[{current_time}] 发生错误：{str(e)}\n")
                self.info_text.see(tk.END)
            
            time.sleep(0.3)
    
    def update_online_users(self):
        """更新在线人数"""
        try:
            online_users = self.course_client.get_person()
            self.window.title(f"选课系统 - {self.user_name} - 当前在线人数：{online_users}")
        except Exception as e:
            pass
        
        self.window.after(1000, self.update_online_users)

    def load_config(self):
        """读取配置文件，如果不存在则创建默认配置"""
        try:
            import yaml
            config_path = 'config.yaml'
            
            # 如果配置文件不存在，创建默认配置
            if not os.path.exists(config_path):
                default_config = {
                    'username': '',  # 默认空用户名
                    'password': '',  # 默认空密码
                    'courses': [
                        {'code': 'COMP30072701', 'type': 'major'},     # 计算机组成原理
                        {'code': 'CORE10010101', 'type': 'elective'},  # 大学英语
                        {'code': 'PHED10265003', 'type': 'physical'},  # 篮球
                        {'code': 'AUTO50112701', 'type': 'program'}    # 自动控制原理
                    ]
                }
                
                # 写入默认配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, allow_unicode=True, sort_keys=False)
                
                # 提示用户
                messagebox.showinfo(
                    "提示", 
                    "已创建默认配置文件 config.yaml\n请在文件中填写你的账号信息"
                )
                
                return default_config
                
            # 读取现有配置
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            print(f"读取配置文件失败：{str(e)}")
            return {}

    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.root.destroy()  # 完全退出程序

class LoginUI:
    def __init__(self):
        self.root = ttk.Window(themename="cosmo")
        self.root.title("西安交通大学选课系统")
        self.root.geometry("400x300")
        
        # 读取配置文件
        self.config = self.load_config()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            self.main_frame, 
            text="选课系统登录", 
            font=("Microsoft YaHei UI", 16, "bold")
        )
        title_label.pack(pady=20)
        
        username_frame = ttk.Frame(self.main_frame)
        username_frame.pack(fill=tk.X, pady=10)
        
        username_label = ttk.Label(
            username_frame, 
            text="学号：", 
            font=("Microsoft YaHei UI", 10)
        )
        username_label.pack(side=tk.LEFT)
        
        self.username_entry = ttk.Entry(username_frame, width=30)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        self.username_entry.insert(0, self.config.get('username', ''))  # 从配置文件读取默认学号
        
        password_frame = ttk.Frame(self.main_frame)
        password_frame.pack(fill=tk.X, pady=10)
        
        password_label = ttk.Label(
            password_frame, 
            text="密码：", 
            font=("Microsoft YaHei UI", 10)
        )
        password_label.pack(side=tk.LEFT)
        
        self.password_entry = ttk.Entry(password_frame, width=30, show="*")
        self.password_entry.pack(side=tk.LEFT, padx=5)
        self.password_entry.insert(0, self.config.get('password', ''))
        
        self.login_button = ttk.Button(
            self.main_frame,
            text="登录",
            command=self.login,
            style="primary.TButton",
            width=20
        )
        self.login_button.pack(pady=20)
        
        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            font=("Microsoft YaHei UI", 9),
            wraplength=350
        )
        self.status_label.pack(pady=10)
        
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("错误", "请输入学号和密码")
            return
            
        self.status_label.config(text="正在登录...")
        self.login_button.config(state="disabled")
        
        try:
            client = Login()
            success, message = client.login_process(username, password)
            
            if success:
                self.status_label.config(
                    text=f"登录成功：{client.name}",
                    foreground="green"
                )
                
                # 创建选课客户端
                course_client = CourseSelection(
                    cookies=client.cookies,
                    token=client.token,
                    ticket=client.ticket,
                    student_code=username
                )
                
                CourseSelectionUI(self.root, course_client, client.name)
                self.root.withdraw()
                
            else:
                messagebox.showerror("登录失败", message)
                self.status_label.config(
                    text="登录失败",
                    foreground="red"
                )
                
        except Exception as e:
            messagebox.showerror("错误", f"发生错误：{str(e)}")
            self.status_label.config(
                text="登录失败",
                foreground="red"
            )
            
        finally:
            self.login_button.config(state="normal")
            
    def run(self):
        self.root.mainloop()

    def load_config(self):
        """读取配置文件，如果不存在则创建默认配置"""
        try:
            import yaml
            config_path = 'config.yaml'
            
            # 如果配置文件不存在，创建默认配置
            if not os.path.exists(config_path):
                default_config = {
                    'username': '',  # 默认空用户名
                    'password': '',  # 默认空密码
                    'courses': [
                        {'code': 'COMP30072701', 'type': 'major'},     # 计算机组成原理
                        {'code': 'CORE10010101', 'type': 'elective'},  # 大学英语
                        {'code': 'PHED10265003', 'type': 'physical'},  # 篮球
                        {'code': 'AUTO50112701', 'type': 'program'}    # 自动控制原理
                    ]
                }
                
                # 写入默认配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, allow_unicode=True, sort_keys=False)
                
                # 提示用户
                messagebox.showinfo(
                    "提示", 
                    "已创建默认配置文件 config.yaml\n请在文件中填写你的账号信息"
                )
                
                return default_config
                
            # 读取现有配置
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            print(f"读取配置文件失败：{str(e)}")
            return {}

if __name__ == "__main__":
    app = LoginUI()
    app.run() 