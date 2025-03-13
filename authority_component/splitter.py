# TESPy Splitter类 

# Splitter 用于将一个质量流分成多个部分
# 输入的流体仅仅按照指定的质量流量进行分割
# 这些部分的质量流具有相同的焓值和流体组成

# 相同的焓值: 分割后的各个流体部分的能量状态（焓值）与原始流体相同。
# 这意味着温度和压力在分割过程中保持一致

# 相同的流体组成比例: 分割后的各个流体部分的化学成分比例（如氧气、氮气的比例）与原始流体完全相同。

# 方程
# 必需方程：
# 1. 质量流量方程(`mass_flow_func`): 确保从入口流入的质量流量等于所有出口流出的质量流量之和。
# 2. 压力相等性方程(`pressure_equality_func`): 所有出口的压力与入口的压力相同。
# 3. 流体成分方程(`fluid_func`): 所有出口的流体成分与入口的流体成分相同。

# 4. 能量平衡方程(`energy_balance_func`): 所有出口的能量（焓值）与入口的能量相同。
# 入口流体的焓值 self.inl[0].h.val_SI = 所有出口流体的焓值之和 o.h.val_SI

# 接口
# - 入口: 有一个入口 `in1`
# - 出口: 出口的数量可以通过参数 `num_out` 来指定，默认情况下有两个出口。

# 参数
# label: 组件的标签字符串，用于标识该组件。
# design: 设计参数列表，列出在设计工况下需要考虑的参数。
# offdesign: 非设计参数列表，在非设计工况下需要调整的参数。
# design_path: 指向组件的设计案例文件路径。
# local_offdesign: 布尔值，指示是否在全局设计计算中将此组件视为非设计状态处理。
# local_design: 布尔值，指示是否在全局非设计计算中将此组件视为设计状态处理。
# char_warnings: 布尔值，忽略默认特性曲线使用时的警告信息。
# printout: 布尔值，指示是否将此组件包含在网络结果打印输出中。
  
# num_out: 浮点数或字典，表示该组件的出口数量，默认值为 2。

from tespy.components import Sink, Source, Splitter  # 导入TESPy中的Sink、Source和Splitter组件
from tespy.connections import Connection             # 导入TESPy中的Connection类
from tespy.networks import Network                 # 导入TESPy中的Network类

nw = Network(p_unit='bar', T_unit='C', iterinfo=False)  # 创建一个网络对象，设置压力单位为bar，温度单位为摄氏度，并关闭迭代信息显示

so = Source('source')                                 # 创建一个源组件，标签为'source'
si1 = Sink('sink1')                                   # 创建一个汇组件，标签为'sink1'
si2 = Sink('sink2')                                   # 创建一个汇组件，标签为'sink2'
si3 = Sink('sink3')                                   # 创建一个汇组件，标签为'sink3'
s = Splitter('splitter', num_out=3)                   # 创建一个分割器组件，标签为'splitter'，并指定有3个出口

inc = Connection(so, 'out1', s, 'in1')                # 创建从源到分割器的连接，源的出端口为'out1'，分割器的入口为'in1'
outg1 = Connection(s, 'out1', si1, 'in1')              # 创建从分割器的第一个出口到第一个汇的连接，分割器的出口为'out1'，汇的入口为'in1'
outg2 = Connection(s, 'out2', si2, 'in1')              # 创建从分割器的第二个出口到第二个汇的连接，分割器的出口为'out2'，汇的入口为'in1'
outg3 = Connection(s, 'out3', si3, 'in1')              # 创建从分割器的第三个出口到第三个汇的连接，分割器的出口为'out3'，汇的入口为'in1'

nw.add_conns(inc, outg1, outg2, outg3)                  # 将所有连接添加到网络中

inc.set_attr(fluid={'O2': 0.23, 'N2': 0.77}, p=1, T=20, m=5)  # 设置进料连接的属性：氧气含量为23%，氮气含量为77%，压力为1 bar，温度为20°C，质量流量为5 kg/s
outg1.set_attr(m=3)                                     # 设置第一个出口连接的质量流量为3 kg/s
outg2.set_attr(m=1)                                     # 设置第二个出口连接的质量流量为1 kg/s

nw.solve('design')                                      # 解决设计工况下的网络问题

round(outg3.m.val_SI, 1)                                # 四舍五入后得到第三个出口的质量流量（SI单位）
round(inc.T.val, 1)                                     # 四舍五入后得到进料连接的温度
round(outg3.T.val, 1)                                   # 四舍五入后得到第三个出口的温度