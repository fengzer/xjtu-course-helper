import requests
import json
import time
from typing import Dict, Tuple

class CourseSelection:
    def __init__(self, cookies: Dict[str, str], token: str, ticket: str, student_code: str):
        """
        初始化选课客户端
        
        Args:
            cookies: Cookie信息
            token: 用户token
            ticket: 用户ticket
            student_code: 学生学号
        """
        self.cookies = cookies
        self.token = token
        self.ticket = ticket
        self.student_code = student_code
        
        self.CLASS_TYPES = {
            "major": "TJKC",     # 主修课程
            "elective": "XGXK",  # 选修课程
            "physical": "TYKC",  # 体育课程
            "program": "FANKC"   # 方案内课程
        }
        
        self.batch_code, self.batch_info = self.get_available_batch(student_code)
        self.TERM_PREFIX = self.get_course_prefix(student_code, self.batch_code)

    def select_course(self, class_code: str, course_type: str) -> str:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "token": self.token
        }
        
        if course_type == "physical":
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36"
        
        data = {
            "addParam": json.dumps({
                "data": {
                    "operationType": "1",
                    "studentCode": self.student_code,
                    "electiveBatchCode": self.batch_code,
                    "teachingClassId": f"{self.TERM_PREFIX}{class_code}",
                    "isMajor": "1",
                    "campus": "1",
                    "teachingClassType": self.CLASS_TYPES[course_type]
                }
            })
        }
        
        response = requests.post(
            "https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/elective/volunteer.do",
            headers=headers,
            cookies=self.cookies,
            data=data
        )
        
        return response.json()["msg"]

    def get_person(self) -> dict:
        headers = {
            "Referer": f"http://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do?ticket={self.ticket}"
        }
        
        timestamp = int(time.time() * 1000)
        response = requests.get(
            f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/publicinfo/onlineUsers.do?timestamp={timestamp}",
            headers=headers,
            cookies=self.cookies
        )
        
        result = response.json()
        return result.get('data', {}).get('onlineUsers', 0)

    def get_batch_info(self, student_code: str) -> dict:
        response = self._get_raw_batch_info(student_code)
        if response['code'] != '1':
            raise Exception(f"获取选课批次信息失败：{response['msg']}")
            
        data = response['data']
        student_info = {
            'name': data['name'],
            'student_code': data['code'],
            'college': data['collegeName'],
            'department': data['departmentName'],
            'class_name': data['schoolClassName'],
            'grade': data['grade'],
            'campus': data['campusName']
        }
        
        batch_list = []
        for batch in data['electiveBatchList']:
            batch_info = {
                'batch_code': batch['code'],
                'name': batch['name'],
                'term': batch['schoolTerm'],
                'term_name': batch['schoolTermName'],
                'begin_time': batch['beginTime'],
                'end_time': batch['endTime'],
                'can_select': batch['canSelect'] == '1',
                'course_types': {
                    'major': batch['displayTJKC'] == '1', 
                    'program': batch['displayFANKC'] == '1', 
                    'physical': batch['displayTYKC'] == '1', 
                    'elective': batch['displayXGXK'] == '1' 
                }
            }
            batch_list.append(batch_info)
        
        return {
            'student': student_info,
            'batches': batch_list
        }

    def _get_raw_batch_info(self, student_code: str) -> dict:
        headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "token": self.token,
            "Referer": f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do?ticket={self.ticket}"
        }
        
        timestamp = int(time.time() * 1000)
        response = requests.get(
            f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/student/{student_code}.do?timestamp={timestamp}",
            headers=headers,
            cookies=self.cookies
        )
        
        return response.json()

    def major_course(self, class_code: str) -> str:
        return self.select_course(class_code, "major")
        
    def elective_course(self, class_code: str) -> str:
        return self.select_course(class_code, "elective")
        
    def physical_course(self, class_code: str) -> str:
        return self.select_course(class_code, "physical")
        
    def program_course(self, class_code: str) -> str:
        return self.select_course(class_code, "program")

    def get_available_batch(self, student_code: str) -> Tuple[str, dict]:
        batch_info = self.get_batch_info(student_code)
        
        for batch in batch_info['batches']:
            if (batch['can_select'] and 
                "本科生选课" in batch['name'] and 
                any(batch['course_types'].values())):
                return batch['batch_code'], batch
                
        raise Exception("未找到可用的选课批次")

    def get_course_prefix(self, student_code: str, batch_code: str, course_type: str = "major") -> str:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "token": self.token,
            "Referer": f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token={self.token}"
        }
        
        query_data = {
            "data": {
                "studentCode": student_code,
                "campus": "1",
                "electiveBatchCode": batch_code,
                "isMajor": "1",
                "teachingClassType": self.CLASS_TYPES[course_type],
                "checkConflict": "2",
                "checkCapacity": "2",
                "queryContent": ""
            },
            "pageSize": "10",
            "pageNumber": "0",
            "order": ""
        }
        
        data = {
            "querySetting": json.dumps(query_data)
        }
        
        response = requests.post(
            "https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/elective/recommendedCourse.do",
            headers=headers,
            cookies=self.cookies,
            data=data
        )
        
        result = response.json()
        if result.get("code") != "1":
            raise Exception(f"获取课程信息失败：{result.get('msg')}")
        
        data_list = result.get("dataList", [])
        if not data_list:
            raise Exception("未找到任何课程信息")
        
        first_course = data_list[0]
        first_class = first_course.get("tcList", [])[0]
        teaching_class_id = first_class.get("teachingClassID", "")
        
        prefix = teaching_class_id.split(first_course["courseNumber"])[0]
        return prefix