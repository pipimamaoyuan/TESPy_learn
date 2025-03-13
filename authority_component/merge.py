# TESPy merge类

# Merge类用于表示具有多个入口和一个出口的混合点。
# 这个组件主要用于将多个流合并成一个单一的流出流。

# 必需方程
# 质量流量平衡 (mass_flow_func)
# 这个函数确保所有进入merge组件的质量流量之和等于离开该组件的质量流量。

# 压力相等 (pressure_equality_func):所有进入merge组件的压力必须相同。
# 流体成分一致 (fluid_func):所有进入merge组件的流体成分（即各种组分的比例）必须保持一致。

# 能量守恒 (energy_balance_func):进入merge组件的能量总和应等于离开该组件的能量。
# 所有入口流体的焓值之和 i.m.val_SI * i.h.val_SI = 出口流体焓值 o.m.val_SI * o.h.val_SI

# 接口
# 默认情况下，merge组件有两个入口 (num_in=2)。可以通过设置 num_in 参数来指定更多的入口数量。
# 出口只有一个，标记为 out1。

# 参数说明
# label: 组件的标签字符串，用于标识该组件。
# design: 设计参数列表，列出在设计工况下需要考虑的参数。
# offdesign: 非设计参数列表，在非设计工况下需要调整的参数。
# design_path: 指向组件的设计案例文件路径。
# local_offdesign: 布尔值，指示是否在全局设计计算中将此组件视为非设计状态处理。
# local_design: 布尔值，指示是否在全局非设计计算中将此组件视为设计状态处理。
# char_warnings: 布尔值，忽略默认特性曲线使用时的警告信息。
# printout: 布尔值，指示是否将此组件包含在网络结果打印输出中。

# num_in: 浮点数或字典类型，默认值为2，指定组件的入口数量。

from tespy.components import Sink, Source, Merge  # 导入TESPy中的Sink、Source和Merge组件
from tespy.connections import Connection         # 导入TESPy中的Connection类，用于连接组件
from tespy.networks import Network               # 导入TESPy中的Network类，用于创建和管理网络

# 创建一个网络对象，设置压力单位为bar，并关闭迭代信息输出
nw = Network(p_unit='bar', iterinfo=False)

# 定义三个源组件，分别命名为'source1'、'source2'和'source3'
so1 = Source('source1')
so2 = Source('source2')
so3 = Source('source3')

# 定义一个汇组件，命名为'sink'
si1 = Sink('sink')

# 定义一个合并组件，命名为'merge'，并且指定有3个入口
m = Merge('merge', num_in=3)

# 定义从'source1'到'merge'的第一个入口的连接
inc1 = Connection(so1, 'out1', m, 'in1')

# 定义从'source2'到'merge'的第二个入口的连接
inc2 = Connection(so2, 'out1', m, 'in2')

# 定义从'source3'到'merge'的第三个入口的连接
inc3 = Connection(so3, 'out1', m, 'in3')

# 定义从'merge'的出口到'sink'的连接
outg = Connection(m, 'out1', si1, 'in1')

# 将所有连接添加到网络中
nw.add_conns(inc1, inc2, inc3, outg)

# 设置温度变量T为293.15K
T = 293.15

# 设置第一个连接的流体组成、压力、温度和质量流量
inc1.set_attr(fluid={'O2': 0.23, 'N2': 0.77}, p=1, T=T, m=5)

# 设置第二个连接的流体组成、温度和质量流量
inc2.set_attr(fluid={'O2': 1}, T=T, m=5)

# 设置第三个连接的流体组成和温度
inc3.set_attr(fluid={'N2': 1}, T=T)

# 设置出口气体的氮气摩尔分数
outg.set_attr(fluid={'N2': 0.4})

# 对网络进行设计工况下的求解
nw.solve('design')

# 计算并四舍五入第三个入口的质量流量值到小数点后两位
round(inc3.m.val_SI, 2)

# 检查出口气体的温度是否接近设定的温度T，误差小于0.01%
abs(round((outg.T.val_SI - T) / T, 5)) < 0.01
print(outg.T.val_SI)

# 设置温度变量T为173.15K
T = 173.15

# 更新第一个连接的温度
inc1.set_attr(T=T)

# 更新第二个连接的温度
inc2.set_attr(T=T)

# 更新第三个连接的温度
inc3.set_attr(T=T)

# 再次对网络进行设计工况下的求解
nw.solve('design')

# 再次检查出口气体的温度是否接近设定的温度T，误差小于0.01%
abs(round((outg.T.val_SI - T) / T, 5)) < 0.01
print(outg.T.val_SI)

# 计算不可逆熵平衡
# 出口处的不可逆熵产生量 = 入口处的不可逆熵产生量
# def entropy_balance(self)
