import cv2
import numpy as np
import sys
try:
    import mediapipe as mp
except Exception as e:
    mp = None
    _mediapipe_import_error = e
else:
    _mediapipe_import_error = None
import pyautogui
import time
import math
try:
    import ApplicationServices as AS
except Exception:
    try:
        import Quartz as AS
    except Exception:
        AS = None


class MacUiSnapper:
    def __init__(
        self,
        enabled=True,
        stick_margin_px=28,
        inner_padding_px=8,
        min_w=30,
        min_h=18,
        query_interval_s=0.08,
        refresh_interval_s=0.6,
    ):
        self.enabled = enabled and AS is not None
        self.stick_margin_px = stick_margin_px
        self.inner_padding_px = inner_padding_px
        self.min_w = min_w
        self.min_h = min_h
        self.query_interval_s = query_interval_s
        self.refresh_interval_s = refresh_interval_s
        self._system = AS.AXUIElementCreateSystemWide() if self.enabled else None
        self._last_query_t = 0.0
        self._last_refresh_t = 0.0
        self._active_bounds = None
        self._disabled_reason = None

    def _ax_copy_attr(self, element, attr):
        err, value = AS.AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0:
            return None
        return value

    def _rect_to_bounds(self, rect):
        try:
            x = float(rect.origin.x)
            y = float(rect.origin.y)
            w = float(rect.size.width)
            h = float(rect.size.height)
        except Exception:
            try:
                x = float(rect["X"])
                y = float(rect["Y"])
                w = float(rect["Width"])
                h = float(rect["Height"])
            except Exception:
                return None
        return x, y, x + w, y + h

    def _ax_value_to_point(self, ax_value):
        ok, pt = AS.AXValueGetValue(ax_value, AS.kAXValueCGPointType, None)
        if not ok:
            return None
        return float(pt.x), float(pt.y)

    def _ax_value_to_size(self, ax_value):
        ok, sz = AS.AXValueGetValue(ax_value, AS.kAXValueCGSizeType, None)
        if not ok:
            return None
        return float(sz.width), float(sz.height)

    def _is_interesting_role(self, role):
        return role in {
            "AXButton",
            "AXTextField",
            "AXTextArea",
            "AXSearchField",
            "AXComboBox",
            "AXPopUpButton",
            "AXCheckBox",
            "AXRadioButton",
            "AXLink",
            "AXMenuItem",
            "AXCell",
        }

    def _find_element_bounds(self, x, y):
        if not self.enabled:
            return None
        try:
            err, element = AS.AXUIElementCopyElementAtPosition(self._system, float(x), float(y), None)
        except Exception as e:
            self.enabled = False
            self._disabled_reason = str(e)
            return None
        if err != 0 or element is None:
            return None

        cur = element
        for _ in range(6):
            role = self._ax_copy_attr(cur, AS.kAXRoleAttribute)
            if role is not None and self._is_interesting_role(str(role)):
                pos_v = self._ax_copy_attr(cur, AS.kAXPositionAttribute)
                size_v = self._ax_copy_attr(cur, AS.kAXSizeAttribute)
                if pos_v is None or size_v is None:
                    return None
                pos = self._ax_value_to_point(pos_v)
                size = self._ax_value_to_size(size_v)
                if pos is None or size is None:
                    return None
                px, py = pos
                w, h = size
                x1, y1, x2, y2 = px, py, px + w, py + h
                if (x2 - x1) >= self.min_w and (y2 - y1) >= self.min_h:
                    return x1, y1, x2, y2
                return None
            parent = self._ax_copy_attr(cur, AS.kAXParentAttribute)
            if parent is None:
                break
            cur = parent
        return None

    def _in_bounds(self, x, y, bounds, margin=0.0):
        x1, y1, x2, y2 = bounds
        return (x1 - margin) <= x <= (x2 + margin) and (y1 - margin) <= y <= (y2 + margin)

    def _clamp_to_inner(self, x, y, bounds):
        x1, y1, x2, y2 = bounds
        pad = float(self.inner_padding_px)
        ix1, iy1, ix2, iy2 = x1 + pad, y1 + pad, x2 - pad, y2 - pad
        if ix2 <= ix1:
            ix1, ix2 = x1, x2
        if iy2 <= iy1:
            iy1, iy2 = y1, y2
        cx = min(max(x, ix1), ix2)
        cy = min(max(y, iy1), iy2)
        return cx, cy

    def snap(self, x, y):
        if not self.enabled:
            return x, y, False

        now = time.time()
        if self._active_bounds is not None and self._in_bounds(x, y, self._active_bounds, self.stick_margin_px):
            sx, sy = self._clamp_to_inner(x, y, self._active_bounds)
            if now - self._last_refresh_t > self.refresh_interval_s:
                self._last_refresh_t = now
            return sx, sy, True

        if now - self._last_query_t < self.query_interval_s:
            return x, y, False

        self._last_query_t = now
        bounds = self._find_element_bounds(x, y)
        if bounds is None:
            self._active_bounds = None
            return x, y, False

        self._active_bounds = bounds
        self._last_refresh_t = now
        sx, sy = self._clamp_to_inner(x, y, bounds)
        return sx, sy, True

# ==========================================
# 模块 1: 手部检测器 (HandDetector)
# 封装 MediaPipe 的底层细节，提供简洁的接口
# ==========================================
class HandDetector:
    def __init__(
        self,
        mode=False,
        max_hands=1,
        detection_con=0.7,
        track_con=0.5,
        model_complexity=0,
        process_scale=0.5,
    ):
        if mp is None:
            raise RuntimeError(
                "无法导入 mediapipe。\n"
                f"Python: {sys.version}\n"
                f"错误: {_mediapipe_import_error}\n"
                "请确认你在安装 mediapipe 的同一个解释器里运行脚本，并使用 Python 3.9~3.12。\n"
                "安装命令：\n"
                "  python -m pip install -U pip\n"
                "  python -m pip install mediapipe\n"
            )
        if not hasattr(mp, "solutions"):
            mp_file = getattr(mp, "__file__", None)
            mp_version = getattr(mp, "__version__", None)
            raise RuntimeError(
                "当前导入的 mediapipe 不包含 mp.solutions。\n"
                "这通常意味着：安装了错误的 mediapipe 包/版本，或 Python 环境不一致导致导入到异常包。\n"
                f"Python: {sys.version}\n"
                f"mediapipe.__file__: {mp_file}\n"
                f"mediapipe.__version__: {mp_version}\n"
                "建议在当前 python 下重装官方 mediapipe：\n"
                "  python -m pip uninstall -y mediapipe\n"
                "  python -m pip install mediapipe==0.10.14\n"
            )
        if process_scale <= 0 or process_scale > 1:
            raise ValueError("process_scale 必须在 (0, 1] 范围内")
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        self.model_complexity = model_complexity
        self.process_scale = process_scale

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]  # 指尖的 Landmark ID
        self.lm_list = []

    def find_hands(self, img, draw=True):
        """检测手部并绘制骨架"""
        if self.process_scale != 1:
            small = cv2.resize(img, None, fx=self.process_scale, fy=self.process_scale, interpolation=cv2.INTER_LINEAR)
            img_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0):
        """获取所有关键点的坐标"""
        self.lm_list = []
        x_list = []
        y_list = []
        bbox = []

        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, c = img.shape

            for id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                x_list.append(cx)
                y_list.append(cy)
                self.lm_list.append([id, cx, cy])

            xmin, xmax = min(x_list), max(x_list)
            ymin, ymax = min(y_list), max(y_list)
            bbox = xmin, ymin, xmax, ymax

        return self.lm_list, bbox

    def _point(self, lm_id):
        if len(self.lm_list) == 0:
            return None
        if lm_id < 0 or lm_id >= len(self.lm_list):
            return None
        return self.lm_list[lm_id][1], self.lm_list[lm_id][2]

    def cursor_anchor_point(self, anchor="palm"):
        if anchor == "wrist":
            return self._point(0)
        if anchor == "palm":
            ids = (0, 5, 9, 13, 17)
            pts = [self._point(i) for i in ids]
            pts = [p for p in pts if p is not None]
            if not pts:
                return None
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return int(sum(xs) / len(xs)), int(sum(ys) / len(ys))
        raise ValueError("anchor 只支持 'palm' 或 'wrist'")

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
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            raise RuntimeError(
                "摄像头打开失败。macOS 下常见原因是没有给当前终端/IDE 授予相机权限。\n"
                "请到 系统设置 → 隐私与安全性 → 相机，打开对 Terminal/你的 IDE 的授权后重试。"
            )
        self.cap.set(3, self.w_cam)
        self.cap.set(4, self.h_cam)

        # 屏幕参数
        self.w_scr, self.h_scr = pyautogui.size()
        
        # 控制参数
        self.frame_reduction = 100  # 画面边缘保留多少像素不作为控制区 (Frame Margin)
        self.smoothening = 5        # 平滑系数 (越大越平滑但延迟越高)
        self.pinch_down_distance = 30
        self.pinch_up_distance = 45
        self.min_move_interval_s = 1 / 120
        self.min_move_pixels = 0.5
        self.smoothening_in_control = 12
        self.debug = False
        self.cursor_anchor = "palm"
        self.enable_ui_snap = True
        
        # 状态变量
        self.p_loc_x, self.p_loc_y = 0, 0 # Previous Location
        self.c_loc_x, self.c_loc_y = 0, 0 # Current Location
        self.is_dragging = False
        self._last_move_t = 0.0

        self.detector = HandDetector(max_hands=1, model_complexity=0, process_scale=0.5)
        self.ui_snapper = MacUiSnapper(enabled=self.enable_ui_snap)

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
                anchor_pt = self.detector.cursor_anchor_point(self.cursor_anchor)
                if anchor_pt is None:
                    anchor_x, anchor_y = x1, y1
                else:
                    anchor_x, anchor_y = anchor_pt

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
                    self._handle_movement(anchor_x, anchor_y)
                    # 确保不在拖拽状态
                    if self.is_dragging:
                        pyautogui.mouseUp()
                        self.is_dragging = False
                        if self.debug:
                            print("Release Drag")

                # =================================================
                # 模式 B: 点击与拖拽模式 (食指和拇指捏合)
                # =================================================
                # 计算食指(8)和拇指(4)的距离
                length, img, line_info = self.detector.find_distance(4, 8, img)

                # 如果处于移动模式（食指竖起）且捏合
                if fingers[1] == 1:
                    # 距离小于阈值 -> 按下
                    if length < self.pinch_down_distance:
                        # 视觉反馈：捏合中心变绿
                        cv2.circle(img, (line_info[4], line_info[5]), 15, (0, 255, 0), cv2.FILLED)
                        
                        if not self.is_dragging:
                            pyautogui.mouseDown()
                            self.is_dragging = True
                            if self.debug:
                                print("Mouse Down / Drag Start")
                        
                        # 处于拖拽状态下，依然允许移动
                        self._handle_movement(anchor_x, anchor_y)
                    
                    # 距离大于阈值 -> 如果之前是按下状态，则抬起
                    elif length > self.pinch_up_distance and self.is_dragging:
                        pyautogui.mouseUp()
                        self.is_dragging = False
                        if self.debug:
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
        target_x = float(np.interp(x1, (self.frame_reduction, self.w_cam - self.frame_reduction), (0, self.w_scr)))
        target_y = float(np.interp(y1, (self.frame_reduction, self.h_cam - self.frame_reduction), (0, self.h_scr)))
        in_control = False
        if self.enable_ui_snap:
            target_x, target_y, in_control = self.ui_snapper.snap(target_x, target_y)

        # 2. 平滑处理 (Smoothing)
        # 当前位置 = 上次位置 + (目标位置 - 上次位置) / 平滑系数
        smooth = self.smoothening_in_control if in_control else self.smoothening
        self.c_loc_x = self.p_loc_x + (target_x - self.p_loc_x) / smooth
        self.c_loc_y = self.p_loc_y + (target_y - self.p_loc_y) / smooth

        # 3. 移动鼠标
        # 这里的 (self.w_scr - self.c_loc_x) 是因为如果没做镜像翻转可能需要反向，
        # 但我们在主循环做了 cv2.flip(img, 1)，所以这里直接用 self.c_loc_x 即可。
        # 注意：pyautogui 在 mac 上某些全屏应用可能有权限问题
        now = time.time()
        dx = abs(self.c_loc_x - self.p_loc_x)
        dy = abs(self.c_loc_y - self.p_loc_y)
        min_px = self.min_move_pixels * (2 if in_control else 1)
        if (now - self._last_move_t) < self.min_move_interval_s or (dx < min_px and dy < min_px):
            self.p_loc_x, self.p_loc_y = self.c_loc_x, self.c_loc_y
            return
        try:
            pyautogui.moveTo(self.c_loc_x, self.c_loc_y)
            self._last_move_t = now
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
    pyautogui.PAUSE = 0
    
    app = AiVirtualMouse()
    app.run()
