from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from collections import defaultdict, deque
import os

app = Flask(__name__)
CORS(app)

# Dữ liệu môn học CNTT (mô phỏng)
COURSES_DATA = {
    "courses": {
        "MATH101": {"name": "Toán cao cấp 1", "credits": 3, "semester": 1},
        "MATH102": {"name": "Toán cao cấp 2", "credits": 3, "semester": 2},
        "MATH103": {"name": "Toán rời rạc", "credits": 3, "semester": 2},
        "MATH104": {"name": "Xác suất thống kê", "credits": 3, "semester": 3},
        "PROG101": {"name": "Nhập môn lập trình", "credits": 4, "semester": 1},
        "PROG102": {"name": "Lập trình hướng đối tượng", "credits": 4, "semester": 2},
        "PROG103": {"name": "Cấu trúc dữ liệu và giải thuật", "credits": 4, "semester": 3},
        "PROG104": {"name": "Lập trình web", "credits": 4, "semester": 4},
        "DB101": {"name": "Cơ sở dữ liệu", "credits": 4, "semester": 4},
        "DB102": {"name": "Quản trị cơ sở dữ liệu", "credits": 3, "semester": 5},
        "NET101": {"name": "Mạng máy tính", "credits": 3, "semester": 4},
        "NET102": {"name": "Bảo mật mạng", "credits": 3, "semester": 6},
        "SE101": {"name": "Công nghệ phần mềm", "credits": 4, "semester": 5},
        "SE102": {"name": "Kiểm thử phần mềm", "credits": 3, "semester": 6},
        "AI101": {"name": "Trí tuệ nhân tạo", "credits": 4, "semester": 6},
        "AI102": {"name": "Học máy", "credits": 3, "semester": 7},
        "AI103": {"name": "Xử lý ngôn ngữ tự nhiên", "credits": 3, "semester": 7},
        "ML101": {"name": "Thị giác máy tính", "credits": 3, "semester": 8},
        "SYS101": {"name": "Hệ điều hành", "credits": 3, "semester": 5},
        "SYS102": {"name": "Kiến trúc máy tính", "credits": 3, "semester": 3},
        "PROJ101": {"name": "Đồ án 1", "credits": 2, "semester": 6},
        "PROJ102": {"name": "Đồ án 2", "credits": 3, "semester": 7},
        "PROJ103": {"name": "Đồ án tốt nghiệp", "credits": 10, "semester": 8},
    },
    "prerequisites": {
        "MATH102": ["MATH101"],
        "MATH104": ["MATH102"],
        "PROG102": ["PROG101"],
        "PROG103": ["PROG102", "MATH103"],
        "PROG104": ["PROG102", "DB101"],
        "DB101": ["PROG102"],
        "DB102": ["DB101"],
        "NET102": ["NET101"],
        "SE101": ["PROG103"],
        "SE102": ["SE101"],
        "AI101": ["PROG103", "MATH104"],
        "AI102": ["AI101"],
        "AI103": ["AI101", "AI102"],
        "ML101": ["AI102"],
        "SYS101": ["PROG103"],
        "PROJ101": ["SE101", "DB101"],
        "PROJ102": ["PROJ101"],
        "PROJ103": ["PROJ102", "AI101"],
    }
}

class CourseRecommendationSystem:
    def __init__(self, courses_data):
        self.courses = courses_data["courses"]
        self.prerequisites = courses_data["prerequisites"]
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Xây dựng đồ thị từ dữ liệu môn học"""
        graph = defaultdict(list)
        for course, prereqs in self.prerequisites.items():
            for prereq in prereqs:
                graph[prereq].append(course)
        return graph
    
    def baseline_recommendation(self, completed_courses, max_recommendations=5):
        """
        Mô hình Baseline: Tìm kiếm trên đồ thị bằng BFS
        """
        recommendations = []
        visited = set()
        queue = deque(completed_courses)
        
        # BFS để tìm các môn có thể học tiếp
        while queue and len(recommendations) < max_recommendations:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # Tìm các môn học có thể học sau môn hiện tại
            for next_course in self.graph[current]:
                if next_course not in completed_courses and next_course not in [r['code'] for r in recommendations]:
                    # Kiểm tra xem tất cả điều kiện tiên quyết đã được thỏa mãn chưa
                    if self._can_take_course(next_course, completed_courses):
                        recommendations.append({
                            'code': next_course,
                            'name': self.courses[next_course]['name'],
                            'credits': self.courses[next_course]['credits'],
                            'semester': self.courses[next_course]['semester'],
                            'reason': f"Có thể học sau khi hoàn thành {current}"
                        })
        
        # Sắp xếp theo học kỳ đề xuất
        recommendations.sort(key=lambda x: x['semester'])
        return recommendations[:max_recommendations]
    
    def _can_take_course(self, course, completed_courses):
        """Kiểm tra xem có thể học môn này không"""
        if course not in self.prerequisites:
            return True  # Không có điều kiện tiên quyết
        
        prereqs = self.prerequisites[course]
        return all(prereq in completed_courses for prereq in prereqs)
    
    def logic_based_recommendation(self, completed_courses, max_recommendations=5):
        """
        Mô hình Logic vị từ: Suy diễn logic
        """
        recommendations = []
        
        # Suy diễn logic: Tìm tất cả môn có thể học
        for course_code, course_info in self.courses.items():
            if course_code not in completed_courses:
                if self._can_take_course(course_code, completed_courses):
                    # Tính điểm ưu tiên dựa trên logic
                    priority_score = self._calculate_priority(course_code, completed_courses)
                    
                    recommendations.append({
                        'code': course_code,
                        'name': course_info['name'],
                        'credits': course_info['credits'],
                        'semester': course_info['semester'],
                        'priority_score': priority_score,
                        'reason': self._generate_reason(course_code, completed_courses)
                    })
        
        # Sắp xếp theo điểm ưu tiên và học kỳ
        recommendations.sort(key=lambda x: (-x['priority_score'], x['semester']))
        return recommendations[:max_recommendations]
    
    def _calculate_priority(self, course_code, completed_courses):
        """Tính điểm ưu tiên cho môn học"""
        score = 0
        
        # Ưu tiên môn có nhiều môn tiền đề đã học
        if course_code in self.prerequisites:
            prereqs_completed = sum(1 for prereq in self.prerequisites[course_code] 
                                  if prereq in completed_courses)
            score += prereqs_completed * 10
        
        # Ưu tiên môn học kỳ thấp hơn
        semester = self.courses[course_code]['semester']
        score += (10 - semester) * 2
        
        # Ưu tiên môn cốt lõi
        if course_code.startswith(('PROG', 'AI', 'SE')):
            score += 20
        
        # Ưu tiên môn mở khóa cho nhiều môn khác
        unlocked_courses = len(self.graph[course_code])
        score += unlocked_courses * 5
        
        return score
    
    def _generate_reason(self, course_code, completed_courses):
        """Tạo lý do gợi ý"""
        reasons = []
        
        if course_code in self.prerequisites:
            completed_prereqs = [prereq for prereq in self.prerequisites[course_code] 
                               if prereq in completed_courses]
            if completed_prereqs:
                reasons.append(f"Đã hoàn thành điều kiện tiên quyết: {', '.join(completed_prereqs)}")
        
        unlocked_courses = self.graph[course_code]
        if unlocked_courses:
            reasons.append(f"Sẽ mở khóa {len(unlocked_courses)} môn học khác")
        
        return "; ".join(reasons) if reasons else "Môn học cơ bản, phù hợp để học tiếp"

# Khởi tạo hệ thống
recommendation_system = CourseRecommendationSystem(COURSES_DATA)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/courses')
def get_courses():
    """API trả về danh sách tất cả môn học"""
    return jsonify(COURSES_DATA)

@app.route('/api/recommend', methods=['POST'])
def recommend_courses():
    """API gợi ý môn học"""
    data = request.json
    completed_courses = data.get('completed_courses', [])
    model_type = data.get('model', 'baseline')  # 'baseline' hoặc 'logic'
    max_recommendations = data.get('max_recommendations', 5)
    
    if model_type == 'baseline':
        recommendations = recommendation_system.baseline_recommendation(
            completed_courses, max_recommendations
        )
    else:  # logic
        recommendations = recommendation_system.logic_based_recommendation(
            completed_courses, max_recommendations
        )
    
    return jsonify({
        'model_used': model_type,
        'completed_courses_count': len(completed_courses),
        'recommendations': recommendations
    })

@app.route('/api/course-analysis')
def course_analysis():
    """API phân tích thống kê môn học"""
    total_courses = len(COURSES_DATA["courses"])
    total_prerequisites = len(COURSES_DATA["prerequisites"])
    
    # Phân tích theo học kỳ
    semester_stats = defaultdict(int)
    for course_info in COURSES_DATA["courses"].values():
        semester_stats[course_info["semester"]] += 1
    
    return jsonify({
        'total_courses': total_courses,
        'total_prerequisites': total_prerequisites,
        'semester_distribution': dict(semester_stats),
        'average_credits': sum(course['credits'] for course in COURSES_DATA["courses"].values()) / total_courses
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)