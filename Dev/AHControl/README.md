# 电机控制节点

电机配置在 TOML 文件中设置（参见 **[r_hand.toml](./config/r_hand.toml)**）。
在该文件中可以设置电机的 ID，以及每根手指的角度偏移。

- 使用 Feetech 软件设置 ID 及串行总线驱动教程：[https://www.robot-maker.com/forum/tutorials/article/168-brancher-et-controler-le-servomoteur-feetech-sts3032-360/]
- 通过 Feetech 软件设置 ID：[https://github.com/Robot-Maker-SAS/FeetechServo/tree/main/feetech%20debug%20tool%20master/FD1.9.8.2]、已经下载到 **[本地](../../../Tools/飞特舵机上位机软件/FD.exe)** 了

# 工具
- **[change_id](./src/bin/change_id.rs)**：帮助你更改电机的 ID。使用 `cargo run --bin=change_id -- -h` 查看参数列表
- **[goto](./src/bin/goto.rs)**：将单个电机移动到指定位置。使用 `cargo run --bin=goto -- -h` 查看参数列表
- **[get_zeros](./src/bin/get_zeros.rs)**：帮助设置电机零位，它会将电机置于柔顺模式并把 TOML 配置输出到控制台。使用 `cargo run --bin=get_zeros -- -h` 查看参数列表
- **[set_zeros](./src/bin/set_zeros.rs)**：根据配置文件将机械手移动到“零位”。使用 `cargo run --bin=set_zeros -- -h` 查看参数列表

# 入口文件
- **[main](./src/main.rs)**：程序的入口文件，包含初始化和主循环。它是一个 Dora 数据流节点，主要负责连接 Dora 框架 （接收指令）和 真实的机械手硬件 （发送控制信号）。

## 核心功能分析
1. 硬件初始化 ：
   - 读取配置文件（如 **[r_hand.toml](./config/r_hand.toml)** ），解析机械手的手指、电机 ID 和偏移量等信息。
   - 初始化串口通信（默认 COM3 ，波特率 1M），连接 Feetech SCS0009 舵机控制器。
   - 启动时开启电机扭矩，并根据配置将电机移动到初始位置。
2. Dora 数据流循环 ：
   - 初始化 Dora 节点，监听输入事件。
   - 接收数据 ：监听 `mj_l_joints_pos` 或 `mj_r_joints_pos` 输入（通常来自仿真节点）。这些数据是归一化的关节角度（Float64Array）。
   - 数据转换 ：将接收到的关节角度加上配置文件中定义的偏移量 ( offset )，并处理反向逻辑 ( invert )，计算出每个舵机的目标位置。
   - 控制执行 ：使用 `sync_write_goal_position` 指令，一次性同步写入所有舵机的目标位置，驱动机械手运动。
3. 退出处理 ：
   - 接收到 Stop 事件时，关闭电机扭矩并退出程序。