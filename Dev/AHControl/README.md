# 电机控制节点

电机配置在 TOML 文件中设置（参见 [r_hand.toml](config/r_hand.toml)）。
在该文件中可以设置电机的 ID，以及每根手指的角度偏移。

# 工具
- **change_id**：帮助你更改电机的 ID。使用 `cargo run --bin=change_id -- -h` 查看参数列表
- **goto**：将单个电机移动到指定位置。使用 `cargo run --bin=goto -- -h` 查看参数列表
- **get_zeros**：帮助设置电机零位，它会将电机置于柔顺模式并把 TOML 配置输出到控制台。使用 `cargo run --bin=get_zeros -- -h` 查看参数列表
get_zeros：帮助设置电机零位，它会将电机置于柔顺模式并把 TOML 配置输出到控制台。使用 `cargo run --bin=get_zeros -- -h` 查看参数列表
- **set_zeros**：根据配置文件将机械手移动到“零位”。使用 `cargo run --bin=set_zeros -- -h` 查看参数列表