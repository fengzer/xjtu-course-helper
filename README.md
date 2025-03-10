# 西安交通大学选课系统使用说明

## 目录
1. [系统简介](#系统简介)
2. [安装与运行](#安装与运行)
3. [配置文件说明](#配置文件说明)
4. [使用方法](#使用方法)
5. [常见问题](#常见问题)
6. [注意事项](#注意事项)

## 系统简介
本系统是西安交通大学选课系统的辅助工具，支持主修课程、选修课程、体育课程和方案内课程的自动选课功能。系统提供图形界面，操作简单直观。

## 安装与运行
1. 下载程序压缩包并解压
2. 确保解压目录中包含以下文件：
   - `xjtu_lesson.exe`（主程序）
   - `config.yaml`（配置文件）

3. 直接运行`选课系统.exe`即可启动程序

## 配置文件说明
配置文件`config.yaml`的格式如下：

- `username`: 输入你的学号
- `password`: 输入你的密码
- `courses`: 课程列表，可以同时配置多门课程
  - `code`: 课程代码，可在教务系统中查看 
  - `type`: 课程类型，可选值：
    - `major`: 主修课程
    - `elective`: 选修课程
    - `physical`: 体育课程
    - `program`: 方案内课程

## 使用方法
1. 登录系统
   - 启动程序后输入学号和密码
   - 如遇验证码，请先在[网页端](http://org.xjtu.edu.cn/openplatform/login.html)登录一次

2. 选课操作
   - 在主界面可同时配置4门课程
   - 每门课程需设置课程代码和课程类型
   - 点击"开始抢课"按钮开始自动选课
   - 选课成功或需要停止时点击"停止抢课"

3. 课程类型说明
   - major: 主修课程
   - elective: 选修课程
   - physical: 体育课程
   - program: 方案内课程

## 常见问题
1. 登录失败
   - 检查学号密码是否正确
   - 如提示需要验证码，请先在网页端登录一次

2. 选课失败
   - 确认课程代码是否正确
   - 检查是否在选课时间段内
   - 查看具体失败原因并根据提示处理

## 注意事项
- 请合理使用本工具，避免频繁请求对服务器造成压力
- 使用本工具产生的一切后果由用户自行承担

### 首次使用说明
1. 首次运行程序会自动创建`config.yaml`配置文件
2. 请在配置文件中填写：
   - 你的学号(username)
   - 密码(password)
   - 需要选择的课程信息(courses)
3. 保存配置文件后重启程序即可使用

### 课程类型说明
1. 主修课程 (major)
   - 专业必修课程
   - 示例代码：`COMP30072701`（计算机组成原理）

2. 选修课程 (elective)
   - 通识选修课程
   - 示例代码：`CORE10010101`（大学英语）

3. 体育课程 (physical)
   - 体育必修或选修课程
   - 示例代码：`PHED10265003`（篮球）

4. 方案内课程 (program)
   - 培养方案内的课程
   - 示例代码：`AUTO50112701`（自动控制原理）

### 如何获取课程代码
1. 登录教务系统
2. 进入选课界面
3. 找到想要选择的课程
4. 课程代码通常显示在课程名称旁边


