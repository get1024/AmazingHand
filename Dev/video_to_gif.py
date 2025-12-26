import cv2
import os
import glob
from PIL import Image
import math
import shutil  # 新增：用于清理文件夹

def extract_frames_smart(video_path, output_folder, target_frames=150, max_width=480):
    """
    算法1：视频智能抽帧
    
    为了防止GIF间断性过大（跳跃感太强）同时控制文件大小：
    1. 根据视频总时长和想要生成的GIF总帧数（target_frames），动态计算抽取间隔。
    2. 在抽取过程中直接进行画面缩放（max_width），大幅减少内存占用和最终体积。
    
    参数:
    - video_path: 视频文件路径
    - output_folder: 图片保存文件夹
    - target_frames: 期望GIF包含的总帧数（建议100-200之间，太高文件会很大）
    - max_width: 图片最大宽度（3D打印主要看轮廓，建议320-480px，越小体积越小）
    """
    
    # 1. 读取视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return

    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"视频总帧数: {total_frames}, FPS: {fps}")

    # 2. 计算步长 (Step)
    # 如果视频帧数少于目标帧数，则全取；否则按比例跳过
    if total_frames <= target_frames:
        step = 1
    else:
        step = total_frames / target_frames

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    print(f"开始抽帧... 预计抽取 {int(total_frames/step)} 张图片")

    count = 0
    saved_count = 0
    
    while True:
        # 设置读取位置，避免逐帧读取的性能浪费
        # 注意：set操作在某些编码格式下可能稍慢，但在长视频跳跃读取时效率更高
        current_pos = int(count * step)
        if current_pos >= total_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
        ret, frame = cap.read()

        if not ret:
            break

        # 3. 图像缩放 (控制体积的关键)
        h, w = frame.shape[:2]
        scale = max_width / float(w)
        new_h = int(h * scale)
        
        # 使用插值算法进行缩放
        resized_frame = cv2.resize(frame, (max_width, new_h), interpolation=cv2.INTER_AREA)

        # 保存图片，文件名使用前导零填充，方便排序 (0001.jpg, 0002.jpg)
        filename = os.path.join(output_folder, f"{saved_count:05d}.jpg")
        cv2.imwrite(filename, resized_frame)
        
        saved_count += 1
        count += 1
        
        # 简单的进度显示
        if saved_count % 20 == 0:
            print(f"已保存 {saved_count} 帧...")

    cap.release()
    print(f"抽帧完成！共保存 {saved_count} 张图片至 '{output_folder}'")


def create_gif_from_folder(image_folder, output_gif_path, duration=100, loop=0):
    """
    算法2：文件夹图片拼接GIF
    
    参数:
    - image_folder: 图片所在文件夹
    - output_gif_path: 输出GIF路径
    - duration: 每帧停留时间(毫秒)，越小速度越快。100ms = 10fps
    - loop: 循环次数，0表示无限循环
    """
    
    # 1. 获取所有图片并排序
    # glob读取的文件顺序可能是乱的 (1.jpg, 10.jpg, 2.jpg)，需要按数字排序
    images_path = glob.glob(os.path.join(image_folder, "*.jpg"))
    
    if not images_path:
        print("文件夹中没有找到jpg图片")
        return

    # 关键排序算法：按照文件名中的数字大小排序
    # 假设文件名是 0001.jpg, 0002.jpg 或者是 1.jpg, 2.jpg
    try:
        images_path.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    except ValueError:
        # 如果文件名不是纯数字，退回默认排序
        images_path.sort()

    print(f"正在加载 {len(images_path)} 张图片...")

    # 2. 读取图片到内存
    frames = []
    for i, img_path in enumerate(images_path):
        try:
            # 打开图片并转换为RGB模式（防止颜色模式不兼容）
            img = Image.open(img_path).convert('P', palette=Image.ADAPTIVE, colors=256)
            frames.append(img)
        except IOError:
            print(f"无法读取图片: {img_path}")

    if not frames:
        return

    print("正在生成GIF (这可能需要几秒钟)...")

    # 3. 保存GIF
    # save_all=True: 保存所有帧
    # append_images: 后续帧列表
    # optimize=True: 尝试压缩调色板，减小体积
    # duration: 每帧持续时间
    # loop: 0为无限循环
    frames[0].save(
        output_gif_path,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        optimize=True, 
        duration=duration,
        loop=loop
    )
    
    print(f"GIF生成成功！保存为: {output_gif_path}")
    print(f"文件大小: {os.path.getsize(output_gif_path) / 1024 / 1024:.2f} MB")


# --- 使用示例 ---
if __name__ == "__main__":
    # 配置区域
    # 1. 输入和输出设置
    INPUT_FOLDER = r"D:\AAA-personalData\project\AmazingHand\Docs\TestVlog"                 # 视频所在的文件夹 (默认为当前文件夹)
    OUTPUT_FOLDER = r"D:\AAA-personalData\project\AmazingHand\Docs\TestVlog"      # GIF输出保存的文件夹
    TEMP_FOLDER_BASE = r"D:\AAA-personalData\project\AmazingHand\Docs\TestVlog\temp_frames"   # 临时存放图片的文件夹
    
    # 支持的视频格式
    VIDEO_EXTENSIONS = ['*.mp4', '*.mov', '*.avi', '*.mkv']

    # 2. GIF参数设置
    TARGET_FRAMES = 150   # 每个GIF的目标总帧数
    WIDTH = 480           # 图片宽度
    GIF_SPEED_MS = 60     # 帧间隔(ms)

    # 确保输出目录存在
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 扫描所有视频文件
    video_files = []
    for ext in VIDEO_EXTENSIONS:
        # 查找当前文件夹下的视频文件
        video_files.extend(glob.glob(os.path.join(INPUT_FOLDER, ext)))
    
    # 过滤掉已经生成的GIF文件（防止误读）
    video_files = [f for f in video_files if f.lower().endswith(tuple(ext.replace('*', '') for ext in VIDEO_EXTENSIONS))]

    print(f"=== 批量处理模式 ===")
    print(f"在 '{INPUT_FOLDER}' 中找到 {len(video_files)} 个视频文件")

    if not video_files:
        print("未找到视频文件，请检查路径或文件扩展名。")
    
    for i, video_file in enumerate(video_files):
        print(f"\n[{i+1}/{len(video_files)}] 正在处理: {video_file}")
        
        # 获取文件名（不带后缀）
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        
        # 为每个视频创建一个独立的临时文件夹，防止混淆
        current_temp_folder = os.path.join(TEMP_FOLDER_BASE, base_name)
        
        # 设置输出GIF路径
        output_gif = os.path.join(OUTPUT_FOLDER, f"{base_name}.gif")
        
        try:
            # 步骤 1: 抽帧
            extract_frames_smart(video_file, current_temp_folder, target_frames=TARGET_FRAMES, max_width=WIDTH)
            
            # 步骤 2: 合成GIF
            create_gif_from_folder(current_temp_folder, output_gif, duration=GIF_SPEED_MS)
            
            # 步骤 3: 清理临时文件 (处理完一个清理一个，节省空间)
            if os.path.exists(current_temp_folder):
                shutil.rmtree(current_temp_folder)
                print(f"已清理临时文件夹: {current_temp_folder}")
                
        except Exception as e:
            print(f"ERROR: 处理视频 {video_file} 时出错: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n=== 所有任务完成！ GIF已保存在文件夹 {OUTPUT_FOLDER} 中 ===")
