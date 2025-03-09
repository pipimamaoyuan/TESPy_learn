# TESPy 中 Pump 用于模拟轴流或径流泵的行为。
# 在理想情况下，泵将机械能转化为流体的动能和势能（即压能）

# 必要方程
# `fluid_func`: 确定流体成分。
# `mass_flow_func`: 确定质量流量守恒。

# 可选方程 这些是可选的物理方程，可以根据需要启用：
# `pr_func`: 出口压力与入口压力之比。
# 详情见：`tespy.components.component.Component.pr_func`

# `energy_balance_func`: 能量守恒方程，适用于涡轮机械。
# 详情见：`tespy.components.turbomachinery.base.Turbomachine.energy_balance_func`
# P = 质量流量 * (出口比焓 - 入口比焓)

# `eta_s_func`: 等熵效率计算。
# `eta_s_char_func`: 使用特性曲线来计算等熵效率。
# `flow_char_func`: 根据体积流量计算压升特性。

# 进出口 
# `in1`: 入口。
# `out1`: 出口。

# 参数
# 基本参数:
# `label`: 组件标签，字符串类型。
# `design`: 设计工况参数列表，字符串形式。
# `offdesign`: 非设计工况参数列表，字符串形式。
# `design_path`: 设计案例路径，字符串形式。
# `local_offdesign`: 在设计计算中是否将此组件视为非设计状态。
# `local_design`: 在非设计计算中是否将此组件视为设计状态。
# `char_warnings`: 是否忽略默认特性曲线使用警告。
# `printout`: 是否在网络结果输出中包含此组件。

# 特性参数:
# `P`: 输出机械功率，单位为瓦特(W)
# `eta_s`: 等熵效率，无量纲
# 泵的输入电功率 = 泵的输出机械功率 / 泵的等熵效率

# `pr`: 出口压力与入口压力之比，无量纲。pr >= 1
# `eta_s_char`: 等熵效率特性曲线，提供一个CharLine对象作为函数。
# `flow_char`: 压升 随 体积流量 变化的特性曲线，提供一个CharLine对象表示体积流量(m³/s)和压力(Pa)的关系。

from tespy.components import Sink, Source, Pump  # 导入TESPy组件模块中的Sink、Source和Pump类
from tespy.connections import Connection  # 导入TESPy连接模块中的Connection类
from tespy.networks import Network  # 导入TESPy网络模块中的Network类
from tespy.tools.characteristics import CharLine  # 导入TESPy特性曲线模块中的CharLine类
import shutil  # 导入shutil模块，用于删除目录
import numpy as np  # 导入numpy模块，用于数值计算

# 创建一个TESPy网络对象，设置压力单位为bar，温度单位为摄氏度，比焓单位为kJ/kg，比体积单位为l/s，并关闭迭代信息显示
nw = Network(p_unit='bar', T_unit='C', h_unit='kJ / kg', v_unit='l / s', iterinfo=False)

# 创建一个汇点（Sink）组件，命名为'sink'
si = Sink('sink')

# 创建一个源点（Source）组件，命名为'source'
so = Source('source')

# 创建一个泵（Pump）组件，命名为'pump'
pu = Pump('pump')

# 创建从源点到泵的连接（Connection），命名为'inc'
inc = Connection(so, 'out1', pu, 'in1')

# 创建从泵到汇点的连接（Connection），命名为'outg'
outg = Connection(pu, 'out1', si, 'in1')

# 将两个连接添加到网络中
nw.add_conns(inc, outg)

# 定义体积流量的数据点数组，单位转换为m³/s
v = np.array([0, 0.4, 0.8, 1.2, 1.6, 2]) / 1000

# 定义压升的数据点数组，单位转换为Pa
dp = np.array([15, 14, 12, 9, 5, 0]) * 1e5

# 创建一个特性曲线对象，x轴为体积流量，y轴为压升
char = CharLine(x=v, y=dp)

# 设置泵的等熵效率为0.8，并设置流量特性曲线
pu.set_attr(eta_s=0.8, flow_char={'char_func': char, 'is_set': True},
            design=['eta_s'], offdesign=['eta_s_char'])

# 设置进口气流的边界条件：水作为唯一流体，压力为1 bar，温度为20°C，体积流量为1.5 l/s，
# 并将体积流量设为设计参数
inc.set_attr(fluid={'water': 1}, p=1, T=20, v=1.5, design=['v'])

# 进行设计工况下的求解
nw.solve('design')

# 将当前的设计工况保存到'tmp'文件夹中
nw.save('tmp')

# 计算并四舍五入泵的压力比（出口压力与入口压力之比）
round(pu.pr.val, 0)

# 计算并四舍五入泵的压升值（出口压力减去入口压力）
round(outg.p.val - inc.p.val, 0)

# 计算并四舍五入泵的功率
round(pu.P.val, 0)

# 修改出口气流的压力为12 bar，进入非设计工况
outg.set_attr(p=12)

# 在非设计工况下进行求解，并指定设计工况路径为'tmp'
nw.solve('offdesign', design_path='tmp')

# 计算并四舍五入泵在非设计工况下的等熵效率
round(pu.eta_s.val, 2)

# 计算并四舍五入进口气流在非设计工况下的体积流量
round(inc.v.val, 1)

# 删除'tmp'文件夹及其内容
shutil.rmtree('./tmp', ignore_errors=True)

# 等熵效率 = 理想进出口比焓差 / 实际进出口比焓差
# i = self.inl[0]
# o = self.outl[0]
# (o.h.val_SI - i.h.val_SI) * self.eta_s.val = isentropic(i.p.val_SI,i.h.val_SI,o.p.val_SI,i.fluid_data,i.mixing_rule,T0=None) - self.inl[0].h.val_SI

# 等熵效率特性曲线
# i = self.inl[0]
# o = self.outl[0]
# (o.h.val_SI - i.h.val_SI) * self.eta_s.design * self.eta_s_char.char_func.evaluate(expr) = isentropic(i.p.val_SI,i.h.val_SI,o.p.val_SI,i.fluid_data,i.mixing_rule,T0=None) - i.h.val_SI

# 压升特性曲线
# self.outl[0].p.val_SI - self.inl[0].p.val_SI = self.flow_char.char_func.evaluate(expr))

# 注意：
# 出口压力 要 >= 入口压力
# 出口比焓 要 >= 入口比焓
