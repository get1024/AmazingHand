# AmazingHand 项目知识库

本文档提供了 AmazingHand 项目中 `Dev` 目录的全面概述，详细介绍了代码库结构、舵机配置、手部追踪和仿真模块。

## 知识大纲

`Dev` 目录包含以下核心组件：

*   **AHControl/**：基于 Rust 的驱动程序和机械手控制逻辑。
    *   `config/`：用于舵机映射和校准的 TOML 配置文件。
    *   `src/bin/`：用于舵机管理的实用二进制文件（`change_id`, `goto`, `get_zeros`, `set_zeros`）。
    *   `src/main.rs`：**Dora-rs** 管道的主控制节点。它读取 TOML 配置，监听来自仿真的关节位置更新（例如 `mj_r_joints_pos`），应用配置的偏移/反转，并同步写入舵机。
*   **AHSimulation/**：基于 MuJoCo 的物理仿真和逆运动学 (IK) 解算器。
    *   `Src/`：运行仿真的 Python 脚本（`mj_mink_right.py`）。
    *   `mjcf/`：手部的 XML 模型文件和 STL 资源。
    *   `examples/`：示例脚本（例如 `finger_angle_control.py`）。
*   **HandTracking/**：使用 MediaPipe 追踪人手动作的计算机视觉模块。
    *   `Src/main.py`：捕捉网络摄像头输入并输出手部关键点的主追踪节点。
*   **CVCursor/**：一个独立的模块，用于使用手势控制鼠标光标（AI 鼠标），包含 UI 交互逻辑。
*   **example/**：用于测试的独立示例。
    *   `PythonExample/`：直接控制舵机的 Python 脚本（不经过完整的 Dora 管道）。
    *   `ArduinoExample/`：用于底层测试的 Arduino 程序。
*   **数据流文件 (`*.yml`)**：**Dora-rs** 数据流的配置文件，定义了追踪、仿真和控制节点如何通信。

---

## 1. 舵机配置与定义

### 舵机是如何定义的？
代码与物理舵机之间的映射在 `AHControl/config/` 下的 **TOML** 配置文件中定义。
*   **主要配置：** [r_hand.toml](file:///d:/AAA-personalData/project/AmazingHand/Dev/AHControl/config/r_hand.toml)

**配置结构：**
该文件定义了一个 `[Fingers]` 部分，包含 `[[motors]]` 列表。每根手指分配两个电机（`motor1` 和 `motor2`）。

```toml
[[motors]]
finger_name="r_finger1" # 例如：食指
motor1.id = 1
motor1.offset = 0.122 # 零位偏移量（弧度）
motor1.invert = false
motor1.model = "SCS0009"
# ... motor2 配置 ...
```

### 如何配置舵机？
您可以通过直接编辑 `r_hand.toml` 文件或使用提供的 Rust 实用程序来生成配置来进行配置。

*   **手动编辑：** 打开 `AHControl/config/r_hand.toml` 并修改 ID 或偏移量。
*   **自动校准 (`get_zeros`)：**
    1.  运行 `get_zeros` 二进制文件。这将禁用扭矩（柔顺模式），允许您手动将手移动到所需的“零位”。
    2.  该工具读取所有舵机的当前位置。
    3.  它将新的配置（带有更新的偏移量）输出到控制台，您可以将其保存到 TOML 文件中。

## 2. 舵机详情与关节映射

### 舵机映射
基于配置和 [AmazingHand_Demo.py](file:///d:/AAA-personalData/project/AmazingHand/Dev/example/PythonExample/AmazingHand_Demo.py)，右手使用 **8 个舵机** (Feetech SCS0009)，每根手指 2 个舵机。

> **注意：** `AmazingHand_Demo.py` 示例使用硬编码的度数校准值（`MiddlePos` 数组），这与 Rust 控制器使用的 `r_hand.toml` 配置是独立的。使用 Rust 控制器时，仅应用 `r_hand.toml` 中的偏移量。

| 手指 | 关节/功能 | 舵机 ID |
| :--- | :--- | :--- |
| **食指** (`r_finger1`) | 屈曲/伸展 & 张开 | **1, 2** |
| **中指** (`r_finger2`) | 屈曲/伸展 & 张开 | **3, 4** |
| **无名指** (`r_finger3`) | 屈曲/伸展 & 张开 | **5, 6** |
| **拇指** (`r_finger4`) | 屈曲/伸展 & 旋转 | **7, 8** |

### 调试命令
您可以使用 `AHControl` 中的 Rust 二进制文件调试单个舵机。在 `Dev` 目录下运行这些命令：

*   **移动单个舵机：**
    ```bash
    cargo run --bin goto -- --id 1 --pos 0.5
    ```
    *   `--id`: 舵机 ID (1-8)。
    *   `--pos`: 目标位置，单位为弧度（大约 -1.5 到 1.5，取决于限制）。0.0 是配置的零位。

*   **修改舵机 ID：**
    ```bash
    cargo run --bin change_id -- --old_id 1 --new_id 9
    ```
    *   如果您更换了舵机并需要为其分配正确的 ID，这很有用。

*   **将手设置为零位：**
    ```bash
    cargo run --bin set_zeros
    ```
    *   将所有舵机移动到 `r_hand.toml` 中定义的偏移量位置。

*   **获取零位偏移量（校准）：**
    ```bash
    cargo run --bin get_zeros
    ```
    *   将舵机设置为柔顺模式并打印当前位置。

## 3. 手部追踪模块 (HandTracking)

### 这是什么？
位于 `Dev/HandTracking`，该模块使用 **Google MediaPipe** 从网络摄像头源检测手部关键点。它被设计为一个 **Dora** 节点，向其他模块发布手部位置数据。

**依赖项：**
*   `dora-rs`
*   `mediapipe`
*   `loop-rate-limiters`
*   `Python 3.9 - 3.12`

### 详细实现指南 (Step-by-Step)

要实现“摄像头捕捉手部 -> 机器人跟随”的功能，请按照以下步骤操作：

#### 1. 环境准备 (Prerequisites)

确保你已经安装了以下基础工具：
*   **Rust & Cargo**: 用于编译控制代码。
*   **Python 3.10+**: 建议使用 Conda 创建虚拟环境。
*   **Dora CLI**: 用于运行数据流。
    ```bash
    cargo install dora-cli --locked
    ```

#### 2. 安装 Python 依赖

我们需要为 `HandTracking` (视觉) 和 `AHSimulation` (IK解算) 安装依赖。

**建议步骤：**
在项目根目录 (`Dev/`) 下，通过 pip 安装这两个模块（以编辑模式安装，方便调试）：

```bash
# 激活你的 Python 虚拟环境
# 安装 HandTracking 依赖
pip install -e HandTracking

# 安装 AHSimulation 依赖
pip install -e AHSimulation
```

> **注意**: `AHSimulation` 依赖 `mujoco` 和 `mink`，安装时可能会下载较大的二进制文件，请保持网络通畅。

#### 3. 硬件连接与检查

1.  **摄像头**: 将 USB 摄像头连接到电脑。
2.  **灵巧手**:
    *   连接 USB 转 TTL 串口模块。
    *   连接 7.4V 电源给舵机供电。
    *   确认串口号（Windows 下通常是 `COMx`，Linux 下是 `/dev/ttyUSB0` 或 `/dev/ttyACM0`）。

#### 4. 配置数据流 (Dataflow)

打开 `d:/AAA-personalData/project/AmazingHand/Dev/dataflow_tracking_real.yml` 文件，根据你的实际情况进行微调：

*   **修改串口号**:
    找到 `hand_controller` 节点，修改 `args` 中的串口路径：
    ```yaml
    - id: hand_controller
      # ...
      args: --serialport COM3 --config AHControl/config/r_hand.toml # Windows 示例
      # args: --serialport /dev/ttyACM0 --config AHControl/config/r_hand.toml # Linux 示例
    ```

*   **确认 Python 路径**:
    配置文件中默认使用了相对路径。如果你在 `Dev` 目录下运行 dora，默认配置通常是正确的（请确保路径与实际文件结构匹配，如果代码在 `Src` 目录下，请修改 YAML）：
    ```yaml
    - id: hand_tracker
      path: HandTracking/Src/main.py
    # ...
    - id: hand_simulation
      path: AHSimulation/Src/mj_mink_right.py
    ```

#### 5. 运行系统

一切准备就绪后，启动 Dora 数据流：

1.  **启动 Dora 守护进程 (Daemon)**:
    打开一个新的终端：
    ```bash
    dora up
    ```

2.  **启动数据流**:
    打开另一个终端，在 `Dev` 目录下运行：
    ```bash
    dora start dataflow_tracking_real.yml
    ```

#### 6. 预期效果与调试

*   **HandTracking 窗口**: 应该会弹出一个显示摄像头画面的窗口，当你的手出现在画面中时，会绘制出手部骨架。
*   **MuJoCo 仿真窗口**: 会弹出一个仿真界面，显示虚拟灵巧手正在跟随你的手部动作（这是中间层 IK 解算的结果）。
*   **实体灵巧手**: 应该会实时跟随仿真手的动作。

**常见问题排查：**
*   **摄像头打不开**: 检查 `HandTracking/src/main.py` 中的 `cv2.VideoCapture(0)`，如果多摄像头可能需要改为 `1` 或 `2`。
*   **舵机没反应**:
    *   检查电源是否开启。
    *   检查串口号是否正确。
    *   使用 `cargo run --bin scan` 检查能否扫描到舵机 ID。
*   **手部动作错乱**: 可能是坐标系映射问题。HandTracking 输出的是相对坐标，AHSimulation 将其映射到 MuJoCo 空间。如果方向反了，可能需要调整 `main.py` 中的坐标轴方向。
*   **代码报错**：
    ```bash
    (AmazingHand) PS D:\AAA-personalData\project\AmazingHand\Dev> dora start dataflow_tracking_real.yml
    dataflow start triggered: 019b55ec-cd64-77bf-b681-82421d30f4d8
    attaching to dataflow (use `--detach` to run in background)
    hand_controller: WARN   daemon::pending    node exited before initializing dora connection
    hand_simulation: INFO   spawner    spawning: "D:\\AAA-applications\\anaconda3\\envs\\AmazingHand\\python.exe" -u \\?\D:\AAA-personalData\project\AmazingHand\Dev\AHSimulation\Src\mj_mink_right.py
    hand_tracker: INFO   spawner    spawning: "D:\\AAA-applications\\anaconda3\\envs\\AmazingHand\\python.exe" -u \\?\D:\AAA-personalData\project\AmazingHand\Dev\HandTracking\Src\main.py
    hand_simulation: WARN   daemon::pending    node exited before initializing dora connection
    hand_tracker: WARN   daemon::pending    node exited before initializing dora connection
    INFO   daemon    dataflow finished on machine `3d1370b4-a125-4ced-a58c-a80850d6bb87` 
    INFO   coordinator    dataflow finished


    [ERROR]
    Dataflow 019b55ec-cd64-77bf-b681-82421d30f4d8 failed:

    Node `hand_controller` failed: failed to spawn node: preparing for spawn failed: failed to resolve node source `target/debug/AHControl`

    Caused by:
        Could not find source path target/debug/AHControl.exe

    Location:
        C:\Users\DELL\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\dora-core-0.3.13\src\descriptor\mod.rs:237:9


    There are 2 consequential errors. Check the `out/019b55ec-cd64-77bf-b681-82421d30f4d8` folder for full details.

    Location:
        C:\Users\DELL\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\dora-cli-0.3.13\src\common.rs:27:17
    (AmazingHand) PS D:\AAA-personalData\project\AmazingHand\Dev> 
    ```

    这是一个 `Rust` 编译产物缺失 导致的问题。这意味着 `Dora` 试图启动 `hand_controller` 节点，但在 `target/debug/` 目录下找不到编译好的 `AHControl.exe` 可执行文件。这通常是因为 `Rust` 项目尚未编译，或者 `Dora` 自动触发的构建步骤没有成功执行。

    ```bash
    cargo build -p AHControl
    ```

    成功后，再次运行

    ```bash
    dora start dataflow_tracking_real.yml
    ```

## 4. 仿真模块 (AHSimulation)

### 这是什么？
位于 `Dev/AHSimulation`，该模块使用 **MuJoCo** 提供手部的物理仿真。它在控制环路中起着关键作用，充当 **逆运动学 (IK) 解算器**（使用 `mink` 库）。它将高级目标（如来自摄像头的指尖位置）转换为舵机的低级关节角度。

**依赖项：**
*   `dora-rs`
*   `mujoco`
*   `mink`
*   `qpsolvers`
*   Python >= 3.12

### 如何在 Python 中使用它？
*   **作为管道的一部分：** 启动 Dora 数据流时自动运行。
*   **独立/自定义 Python 脚本：**
    您可以编写一个使用 `dora` 向仿真发送命令的 Python 脚本。
    *   参见 [finger_angle_control.py](file:///d:/AAA-personalData/project/AmazingHand/Dev/AHSimulation/examples/finger_angle_control.py) 示例。
    *   该脚本创建一个 Dora 节点，生成正弦波运动并将其作为 `hand_quat`（方向目标）或 `hand_pos`（位置目标）发布。

**运行仿真演示：**
您通常会定义一个数据流（如 `dataflow_angle_simu.yml` 或 `dataflow_tracking_simu.yml`），将您的 Python 控制脚本连接到 `mj_mink_right.py` 仿真节点。
