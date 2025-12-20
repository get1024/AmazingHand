import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import time
import math

# ==========================================
# 模块 1: 手部检测器 (HandDetector)
# 封装 MediaPipe 的底层细节，提供简洁的接口
# ==========================================
class HandDetector:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        # 新的MediaPipe API配置
        import os
        base_options = python.BaseOptions(
            model_asset_path=os.path.join(os.path.dirname(__file__), 'models', 'hand_landmarker.task')
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            min_hand_presence_confidence=self.track_con,
            min_tracking_confidence=self.track_con,
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        self.tip_ids = [4, 8, 12, 16, 20]  # 指尖的 Landmark ID
        self.lm_list = []
        self.results = None
        
        # 定义手部关键点连接
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # 拇指
            (0, 5), (5, 6), (6, 7), (7, 8),  # 食指
            (0, 9), (9, 10), (10, 11), (11, 12),  # 中指
            (0, 13), (13, 14), (14, 15), (15, 16),  # 无名指
            (0, 17), (17, 18), (18, 19), (19, 20),  # 小指
            (5, 9), (9, 13), (13, 17)  # 掌骨
        ]

    def _draw_landmarks(self, img, hand_landmarks):
        """绘制手部关键点和连接"""
        h, w, c = img.shape
        
        # 绘制关键点
        for idx, landmark in enumerate(hand_landmarks):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(img, (x, y), 5, (255, 0, 255), cv2.FILLED)
            cv2.putText(img, str(idx), (x-10, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 绘制连接
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start_x = int(hand_landmarks[start_idx].x * w)
            start_y = int(hand_landmarks[start_idx].y * h)
            end_x = int(hand_landmarks[end_idx].x * w)
            end_y = int(hand_landmarks[end_idx].y * h)
            cv2.line(img, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        
        return img

    def find_hands(self, img, draw=True):
        """检测手部并绘制骨架"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 将numpy数组转换为MediaPipe Image对象
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # 使用新API进行检测
        self.results = self.detector.detect(mp_image)
        
        if self.results and self.results.hand_landmarks:
            for hand_landmarks in self.results.hand_landmarks:
                if draw:
                    self._draw_landmarks(img, hand_landmarks)
        return img

    def find_position(self, img, hand_no=0):
        """获取所有关键点的坐标"""
        self.lm_list = []
        x_list = []
        y_list = []
        bbox = []

        if self.results and self.results.hand_landmarks:
            if hand_no < len(self.results.hand_landmarks):
                my_hand = self.results.hand_landmarks[hand_no]
                h, w, c = img.shape

                for id, lm in enumerate(my_hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    x_list.append(cx)
                    y_list.append(cy)
                    self.lm_list.append([id, cx, cy])

                if x_list and y_list:
                    xmin, xmax = min(x_list), max(x_list)
                    ymin, ymax = min(y_list), max(y_list)
                    bbox = xmin, ymin, xmax, ymax

        return self.lm_list, bbox

    def fingers_up(self):
        """判断哪些手指是竖立的"""
        fingers = []
        if len(self.lm_list) == 0:
            return []

        # 拇指 (比较 x 坐标，注意左右手差异，这里假设右手或自适应)
        # 如果是右手，拇指指尖 x < 拇指指节 x 表示张开 (在画面左侧)
        # 这里简化逻辑：比较指尖和指节的相对位置
        if self.lm_list[self.tip_ids[0]][1] < self.lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 其他 4 根手指 (比较 y 坐标，指尖 < 指节 表示竖起，因为图像原点在左上角)
        for id in range(1, 5):
            if self.lm_list[self.tip_ids[id]][2] < self.lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def find_distance(self, p1, p2, img=None):
        """计算两个关键点之间的距离"""
        if len(self.lm_list) == 0:
            return 0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if img is not None:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]


# ==========================================
# 模块 2: 虚拟鼠标控制器 (AiVirtualMouse)
# 核心业务逻辑
# ==========================================
class AiVirtualMouse:
    def __init__(self):
        # 摄像头参数
        self.w_cam, self.h_cam = 640, 480
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.w_cam)
        self.cap.set(4, self.h_cam)

        # 屏幕参数
        self.w_scr, self.h_scr = pyautogui.size()
        
        # 控制参数
        self.frame_reduction = 100  # 画面边缘保留多少像素不作为控制区 (Frame Margin)
        self.smoothening = 5        # 平滑系数 (越大越平滑但延迟越高)
        self.click_distance = 30    # 捏合点击的距离阈值
        
        # 状态变量
        self.p_loc_x, self.p_loc_y = 0, 0 # Previous Location
        self.c_loc_x, self.c_loc_y = 0, 0 # Current Location
        self.is_dragging = False

        self.detector = HandDetector(max_hands=1)

    def run(self):
        p_time = 0
        print("AI Mouse Started. Press 'q' to exit.")
        print(f"Screen Size: {self.w_scr}x{self.h_scr}")

        while True:
            # 1. 读取并翻转图像 (镜像模式更符合直觉)
            success, img = self.cap.read()
            if not success:
                break
            img = cv2.flip(img, 1)

            # 2. 检测手部
            img = self.detector.find_hands(img)
            lm_list, bbox = self.detector.find_position(img)

            # 3. 如果检测到手
            if len(lm_list) != 0:
                # 获取食指(8)和中指(12)的尖端坐标
                x1, y1 = lm_list[8][1:] 
                x2, y2 = lm_list[12][1:]

                # 检查手指状态
                fingers = self.detector.fingers_up()
                # 绘制控制活动区域 (Frame Reduction)
                cv2.rectangle(img, (self.frame_reduction, self.frame_reduction),
                              (self.w_cam - self.frame_reduction, self.h_cam - self.frame_reduction),
                              (255, 0, 255), 2)

                # =================================================
                # 模式 A: 移动模式 (只有食指竖起)
                # =================================================
                if fingers[1] == 1 and fingers[2] == 0:
                    self._handle_movement(x1, y1)
                    # 确保不在拖拽状态
                    if self.is_dragging:
                        pyautogui.mouseUp()
                        self.is_dragging = False
                        print("Release Drag")

                # =================================================
                # 模式 B: 点击与拖拽模式 (食指和拇指捏合)
                # =================================================
                # 计算食指(8)和拇指(4)的距离
                length, img, line_info = self.detector.find_distance(4, 8, img)

                # 如果处于移动模式（食指竖起）且捏合
                if fingers[1] == 1:
                    # 距离小于阈值 -> 按下
                    if length < self.click_distance:
                        # 视觉反馈：捏合中心变绿
                        cv2.circle(img, (line_info[4], line_info[5]), 15, (0, 255, 0), cv2.FILLED)
                        
                        if not self.is_dragging:
                            pyautogui.mouseDown()
                            self.is_dragging = True
                            print("Mouse Down / Drag Start")
                        
                        # 处于拖拽状态下，依然允许移动
                        self._handle_movement(x1, y1)
                    
                    # 距离大于阈值 -> 如果之前是按下状态，则抬起
                    elif length > self.click_distance and self.is_dragging:
                        pyautogui.mouseUp()
                        self.is_dragging = False
                        print("Mouse Up / Click / Drop")

            # 4. 显示 FPS
            c_time = time.time()
            fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
            p_time = c_time
            cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

            # 5. 显示画面
            cv2.imshow("AI Virtual Mouse", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def _handle_movement(self, x1, y1):
        """处理光标移动，包含坐标映射和平滑处理"""
        # 1. 坐标转换：将摄像头坐标映射到屏幕坐标
        # np.interp(当前值, [输入范围], [输出范围])
        x3 = np.interp(x1, (self.frame_reduction, self.w_cam - self.frame_reduction), (0, self.w_scr))
        y3 = np.interp(y1, (self.frame_reduction, self.h_cam - self.frame_reduction), (0, self.h_scr))

        # 2. 平滑处理 (Smoothing)
        # 当前位置 = 上次位置 + (目标位置 - 上次位置) / 平滑系数
        self.c_loc_x = self.p_loc_x + (x3 - self.p_loc_x) / self.smoothening
        self.c_loc_y = self.p_loc_y + (y3 - self.p_loc_y) / self.smoothening

        # 3. 移动鼠标
        # 这里的 (self.w_scr - self.c_loc_x) 是因为如果没做镜像翻转可能需要反向，
        # 但我们在主循环做了 cv2.flip(img, 1)，所以这里直接用 self.c_loc_x 即可。
        # 注意：pyautogui 在 mac 上某些全屏应用可能有权限问题
        try:
            pyautogui.moveTo(self.c_loc_x, self.c_loc_y)
        except Exception:
            pass # 防止边缘溢出报错

        # 4. 更新上一帧位置
        self.p_loc_x, self.p_loc_y = self.c_loc_x, self.c_loc_y

# 启动程序
if __name__ == "__main__":
    # macOS 安全设置提醒：
    # 如果运行报错 KeyError: 'DISPLAY' 或无法控制鼠标，
    # 请确保终端(Terminal)或IDE拥有 "辅助功能 (Accessibility)" 权限
    
    # 禁用 PyAutoGUI 的自动防故障功能 (把鼠标移到角落会抛出异常)，
    # 因为在全屏映射下很容易碰到角落。
    pyautogui.FAILSAFE = False
    
    app = AiVirtualMouse()
    app.run()