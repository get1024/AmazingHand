# 基于MuJoCo的手部仿真

本项目包含 MuJoCo 仿真模型及资源文件，同时提供一个用于构建逆运动学求解问题的 Python 节点。

**[Mink](https://github.com/kevinzakka/mink)** 工具用于将逆运动学（IK）问题转化为二次规划（QP）问题进行求解。

用户可选择两种控制模式：一是指尖位置控制（pos）（适用于 **[手部追踪](../HandTracking/README.md)** 演示场景），二是远节指骨姿态控制（quat）。

AmazingHand 仿真模型由 CAD 文件导出，导出工具使用的是 **[onshape-to-robot](https://github.com/Rhoban/onshape-to-robot)**

# 文件说明与使用指南

## 1. 仿真节点 (**[Src/mj_mink_right.py](./Src/mj_mink_right.py)** / **[Src/mj_mink_left.py](./Src/mj_mink_left.py)**)

**功能**:
这两个文件分别对应右手和左手的 MuJoCo 仿真节点。它们使用 **[Mink](https://github.com/kevinzakka/mink)** 库来求解逆运动学 (IK)，根据输入的目标（位置或姿态）驱动仿真模型，并将计算出的关节角度输出。

**控制模式**:
- **`pos` (位置控制)**:
    - **描述**: 控制指尖在 3D 空间中的位置。
    - **适用场景**: 配合手部追踪 (**[HandTracking](../HandTracking/README.md)**) 使用，仿真手跟随真实手部动作。
    - **参数**: `lm_damping=0.05` (低阻尼，响应快，适合实时追踪，但是会产生一定的抖动，如果想要减少抖动，可以调高阻尼值)。
- **`quat` (姿态控制)**:
    - **描述**: 控制指尖的朝向 (四元数)。
    - **适用场景**: 精确角度控制测试 (如 **[finger_angle_control.py](./examples/finger_angle_control.py)**)。
    - **参数**: `lm_damping=1.0` (高阻尼，运动平滑稳定)。

**使用方法**:
通常作为 Dora 数据流的一部分运行，_**即不需要单独启动**_。
在 **[dataflow YAML 文件](../dataflow_tracking_real.yml)** 中配置：

```yaml
- id: hand_simulation
  build: pip install -e AHSimulation
  path: AHSimulation/Src/mj_mink_right.py
  inputs:
      hand_pos: hand_tracker/r_hand_pos
      tick: dora/timer/millis/2
      tick_ctrl: dora/timer/millis/10
  outputs:
      - mj_r_joints_pos
```

**运行结果**:
启动后会弹出一个 MuJoCo 被动查看器窗口，显示机械手的仿真模型。模型会根据输入数据实时运动。

## 2. 角度控制示例 (**[finger_angle_control.py](./examples/finger_angle_control.py)**)

**功能**:
这是一个测试节点，用于生成正弦波形式的手指角度控制信号 (四元数)。它演示了如何通过程序精确控制手指的弯曲和摆动。

**输出**:
`hand_quat`: 包含左右手各手指目标四元数的 PyArrow 数组。

**使用方法**:
配合 `quat` 模式的仿真节点使用。
在 dataflow YAML 文件中配置：
```yaml
- id: angle_control
  path: AHSimulation/examples/finger_angle_control.py
  inputs:
    tick: dora/timer/millis/20
  outputs:
    - hand_quat
```

**运行结果**:
仿真中的机械手手指会按照预定的正弦波规律不断弯曲和伸展。

## 3. 模型资源 (**[AH_Right/mjcf/](./Src/AH_Right/mjcf/)** & **[AH_Left/mjcf/](./Src/AH_Left/mjcf/)**)

**功能**:
包含机械手的 MuJoCo 模型定义文件 (`.xml`) 和 3D 网格文件 (`.stl`)。
- `scene.xml`: 定义了完整的仿真场景，包括光照、地面和机械手模型引用。
- `robot.xml`: 定义了机械手的物理属性、关节和传动关系。
- `assets/`: 存放所有零部件的 STL 模型文件。

**说明**:
这些文件通常不需要直接运行，而是被 Python 仿真节点加载。

## 4. 项目配置 (**[pyproject.toml](./pyproject.toml)**)

**功能**:
定义了 `AHSimulation` Python 包的元数据和依赖项。

**安装**:
在开发环境中安装此包：
```bash
pip install -e .
```