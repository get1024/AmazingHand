# AmazingHand 控制实例教程

## 1. 知识大纲

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
*   **example/**：用于测试的独立示例。
    *   `PythonExample/`：直接控制舵机的 Python 脚本（不经过完整的 Dora 管道）。
    *   `ArduinoExample/`：用于底层测试的 Arduino 程序。
*   **数据流文件 (`*.yml`)**：**Dora-rs** 数据流的配置文件，定义了追踪、仿真和控制节点如何通信。

## 2. 使用方法

### 2.1 安装 C++生成工具 和 Windows 10/11 SDK

去 [Visual Studio](https://visualstudio.microsoft.com/zh-hans/) 官方下载 `Visual Studio Installer`

下载完成后双击  `VisualStudioInstaller.exe` 程序，选择 C++ 生成工具、Windows 10/11 SDK；

### 2.2 安装 Rust

去 [Rust](https://www.rust-lang.org/tools/install) 官网，点击 `Install Rust`

等待一段时间，你会得到 `rustup-init.exe`，先不着急双击运行。为了保证快速安装，先配置下载源。

编辑或新建文件：

```bash
C:\Users\<你的用户名>\.rustup\settings.toml
```

内容改成 / 确保包含：

```toml
default_toolchain = "stable-x86_64-pc-windows-msvc"

[dist]
server = "https://mirrors.tuna.tsinghua.edu.cn/rustup"
```

没有这个文件就自己新建，UTF-8 保存即可。

双击运行 `rustup-init.exe`，你会看到一个命令行窗口，内容大概是：

```sh
Welcome to Rust!

1) Proceed with installation (default)
2) Customize installation
3) Cancel installation
> 
```

直接按 `Enter` 键即可。等待一段时间，看到下述内容即安装完成：

```sh
Rust is installed now. Great!
```

重启终端，`VSCode`、`Trae`、`Cursor` 等编辑器也需要重启。在终端中依次输入：

```sh
rustc --version
cargo --version
```

看到版本信息就是安装成功了。

### 2.3 安装 Conda

[Conda 官方](https://www.anaconda.com/download)

### 2.4 安装 dora-rs

[dora-rs 官方](https://dora-rs.ai/docs/guides/Installation/installing)

```bash
cargo install dora-cli --locked
```

### 2.5 运行 Python 示例

创建环境并激活

```sh
conda create -n AmazingHand python=3.12.0
conda activate AmazingHand
```

安装依赖

```sh
pip install rustypot numpy opencv-python pillow pyserial mediapipe==0.10.14
```

运行演示脚本

```sh
python ./FixedAction/Python/AmazingHand_Demo.py
```

### 2.6 运行 Rust 示例

您可以使用 `AHControl` 中的 Rust 二进制文件调试单个舵机。在 `Dev` 目录下运行这些命令：

**移动单个舵机：**

```bash
cargo run --bin goto -- --id 1 --pos 0.5
```

- `--id`: 舵机 ID (1-8)。
- `--pos`: 目标位置，单位为弧度（大约 -1.5 到 1.5，取决于限制）。0.0 是配置的零位。

**修改舵机 ID：**

```bash
cargo run --bin change_id -- --old_id 1 --new_id 9
```

- 如果您更换了舵机并需要为其分配正确的 ID，这很有用。

**将手设置为零位：**

```bash
cargo run --bin set_zeros
```

- 将所有舵机移动到 `r_hand.toml` 中定义的偏移量位置。

**获取零位偏移量（校准）：**

```bash
cargo run --bin get_zeros
```

- 将舵机设置为柔顺模式并打印当前位置。

### 2.7 运行 HandTrackinig 示例

位于 `Dev/HandTracking`，该模块使用 **Google MediaPipe** 从网络摄像头源检测手部关键点。它被设计为一个 **Dora** 节点，向其他模块发布手部位置数据。

我们需要为 `HandTracking` (视觉) 和 `AHSimulation` (IK解算) 安装依赖。

在项目根目录 (`Dev/`) 下，通过 pip 安装这两个模块（以编辑模式安装，方便调试）：

```bash
# 激活你的 Python 虚拟环境
# 安装 HandTracking 依赖
pip install -e HandTracking

# 安装 AHSimulation 依赖
pip install -e AHSimulation
```

> **注意**: `AHSimulation` 依赖 `mujoco` 和 `mink`，安装时可能会下载较大的二进制文件，请保持网络通畅。

一切准备就绪后，启动 Dora 数据流：

**启动 Dora 守护进程 (Daemon)**:
打开一个新的终端：
```bash
dora up
```

**启动数据流**:
打开另一个终端，在 `Dev` 目录下运行：

- 仅在仿真环境中运行摄像头手部追踪演示程序：
  
```bash
dora build dataflow_tracking_simu.yml
dora run dataflow_tracking_simu.yml
```

- 要在真实硬件上运行摄像头手部追踪演示程序：

```bash
dora build dataflow_tracking_real.yml
dora run dataflow_tracking_real.yml
```

- 要在仿真环境中运行简单的示例来控制手指角度：

```bash
dora build dataflow_angle_simu.yml
dora run dataflow_angle_simu.yml
```

## 3. 手部配置

| ![Motors naming](/Docs/Assets/finger.png "Motors naming for each finger") | ![Fingers naming](/Docs/Assets/r_hand.png "Fingers naming for each hand") |
|:-:|:-:|
| **_手指的舵机名称_** | **_每个手指的名称_** |

- 请务必根据你的实际手部设备，适配配置文件 [r_hand.toml](AHControl/config/r_hand.toml);
- 你可以使用 [AHControl](AHControl) 文件夹内的软件工具完成配置。