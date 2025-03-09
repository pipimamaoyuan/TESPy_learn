# TESPy turbomachine

# turbomachine 是 涡轮机械（compressor, pump and turbine）的父类。

# 方程

# 必需方程
# 流体方程 (fluid_func): 这个方程确保流入和流出组件的流体组成保持一致。
# 质量流量方程 (mass_flow_func): 这个方程确保通过组件的质量流量守恒。

# 可选方程
# 压力比方程 (pr_func): 这个方程用于计算或设定出口相对于入口的压力比。
# 能量平衡方程 (energy_balance_func): 这个方程用于计算或设定通过组件的能量变化。

# 接口
# in1: 组件的一个进口接口。
# out1: 组件的一个出口接口。

# 参数
# label: 组件的标签，通常是一个字符串，用于标识组件。
# design: 设计工况参数列表，包含一些关键参数，这些参数在设计工况下会被固定。
# offdesign: 非设计工况参数列表，包含一些关键参数，在非设计工况下可以调整。
# design_path: 存储设计工况数据文件的路径。
# local_offdesign: 在设计计算中是否将此组件视为非设计状态。
# local_design: 在非设计计算中是否将此组件视为设计状态。
# char_warnings: 是否忽略默认特性曲线使用时发出的警告信息。
# printout: 计算结果输出时是否包含此组件的信息。

# 属性
# P (Power): 功率，单位为瓦特 (W)。
# pr (Pressure Ratio): 出口与入口之间的压力比。