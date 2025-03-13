# TESPy Separator 类
# Separator 类 用法与merge相反，用于将一个质量流量，分为多个流体组分输出。
# 分离器用于在相同的压力和温度下，将单一质量流分成特定数量的不同部分，但流体成分不同。
# 液体可以相互分离。

# 必需方程
# mass_flow_func: 质量流量平衡方程。
# pressure_equality_func: 压力相等性方程（所有进出端口的压力相同）。

# fluid_func: 流体成分守恒方程。（质量守恒）
# def fluid_func(self)
# 入口处特定流体的质量流量 = 所有出口处，该流体的质量流量之和。
# i.fluid.val[fluid] * i.m.val_SI = o.fluid.val[fluid] * o.m.val_SI

# energy_balance_func: 能量守恒方程。
# def energy_balance_func(self)
# 确保入口的温度等于所有出口的温度。
# 这样可以保证在分离过程中，没有能量损失或增益，即温度守恒

# 进出口
# 入口: 1个 (in1)
# 出口: 数量由参数 num_out 指定，默认值为2。

# 注意事项
# 目前尚未实现流体分离所需的功率和冷却的相关方程。

# 参数
# label: 组件的标签字符串，用于标识该组件。
# design: 设计参数列表，列出在设计工况下需要考虑的参数。
# offdesign: 非设计参数列表，在非设计工况下需要调整的参数。
# design_path: 指向组件的设计案例文件路径。
# local_offdesign: 布尔值，指示是否在全局设计计算中将此组件视为非设计状态处理。
# local_design: 布尔值，指示是否在全局非设计计算中将此组件视为设计状态处理。
# char_warnings: 布尔值，忽略默认特性曲线使用时的警告信息。
# printout: 布尔值，指示是否将此组件包含在网络结果打印输出中。

# num_out: 此组件的出口数量，默认值: 2

from tespy.components import Sink, Source, Separator  # 导入TESPy组件类：Sink（汇）、Source（源）、Separator（分离器）
from tespy.connections import Connection  # 导入TESPy连接类
from tespy.networks import Network  # 导入TESPy网络类

# 创建一个网络实例，设置压力单位为bar，温度单位为摄氏度，并关闭迭代信息输出
nw = Network(p_unit='bar', T_unit='C', iterinfo=False)

# 创建一个源组件，标签为'source'
so = Source('source')

# 创建两个汇组件，标签分别为'sink1'和'sink2'
si1 = Sink('sink1')
si2 = Sink('sink2')

# 创建一个分离器组件，标签为'separator'，并指定有两个出口
s = Separator('separator', num_out=2)

# 创建从源到分离器的进气连接
inc = Connection(so, 'out1', s, 'in1')

# 创建从分离器的第一个出口到第一个汇的出气连接
outg1 = Connection(s, 'out1', si1, 'in1')

# 创建从分离器的第二个出口到第二个汇的出气连接
outg2 = Connection(s, 'out2', si2, 'in1')

# 将所有连接添加到网络中
nw.add_conns(inc, outg1, outg2)

# 设置进气连接的属性：气体组成（O2: 23%, N2: 77%），压力1 bar，温度20°C，质量流量5 kg/s
inc.set_attr(fluid={'O2': 0.23, 'N2': 0.77}, p=1, T=20, m=5)

# 设置第一个出气连接的属性：气体组成（O2: 10%, N2: 90%），质量流量1 kg/s
outg1.set_attr(fluid={'O2': 0.1, 'N2': 0.9}, m=1)

# 设置第二个出气连接的初始气体组成（O2: 50%, N2: 50%）
# 注意：在TESPy中，fluid0属性用于设置初始猜测值
# 而实际求解过程会根据网络的物理方程调整这些初始值以满足平衡条件。
# 即使你设置了outg2.fluid0={'O2': 0.5, 'N2': 0.5}，最终的结果可能会因为能量守恒、质量守恒和其他约束条件而与初始猜测值不同。
outg2.set_attr(fluid0={'O2': 0.5, 'N2': 0.5})

# 解决网络的设计工况
nw.solve('design')

# 获取第二个出气连接中氧气的质量分数
outg2.fluid.val['O2']
print(outg2.fluid.val['O2'])

# 清除第一个出气连接的质量流量设定
outg1.set_attr(m=None)

# 设置第二个出气连接的气体组成（O2: 30%）
outg2.set_attr(fluid={'O2': 0.3})

# 再次解决网络的设计工况
nw.solve('design')

# 获取第二个出气连接中氧气的质量分数
outg2.fluid.val['O2']
print(outg2.fluid.val['O2'])

# 计算并四舍五入得到第二个出气连接的质量流量占总进气连接质量流量的比例，保留两位小数
round(outg2.m.val_SI / inc.m.val_SI, 2)