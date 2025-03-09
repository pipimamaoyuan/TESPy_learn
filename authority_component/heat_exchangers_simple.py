# TESPy `SimpleHeatExchanger` 组件
# `SimpleHeatExchanger` 是 TESPy 中的一个基础换热器组件
# 它可以代表一个热源或热汇
# 这个类是其他几个特定换热器组件（solar collector, parabolic trough, pipe）的父类。

# 该组件仅模拟换热器的一侧（通常是主侧），而不模拟另一侧（即二次侧）。
# 相当于 冷端是环境温度，热端是流体流过的管道。
# 环境温度认为是恒定的，因此冷端出口温度和冷端入口温度相等。
# 因此，它适用于那些只需要关注一侧热交换过程的情况。

# 达西-魏斯巴赫方程: 可以使用达西-魏斯巴赫方程来计算压力损失。
# 这通常适用于气体流动。
# 哈根-威廉姆斯方程: 如果处理的是液态水，可以使用哈根-威廉姆斯方程来计算压力损失。
# 这种方法在管道中液态水流动时更为常见

# 注意：SimpleHeatExchanger 可以作为系统的热源（吸收热量）或热汇（释放热量）。
# 这意味着它可以模拟从外部获取热量或将热量排放到外部的过程。

# 环境温度和传热系数: 提供了环境温度和传热系数后，可以预测热量传递。
# 这意味着通过设定环境温度和传热系数，可以计算出实际的热量传递量。

# 必要方程
# - 流体平衡 (`fluid_func`): 确保流入和流出的流体种类一致。
# - 质量守恒 (`mass_flow_func`): 确保流入和流出的质量流量相等。

# 可选方程
# - 压力比(`pr_func`)
# - 几何无关摩擦系数 (`zeta_func`)
# - 能量平衡(`energy_balance_func`)
# - 达西公式计算压降 (`darcy_group_func`)
# - 哈根-威廉姆斯公式计算压降 (`hw_group_func`)
# - 面积无关传热系数计算热量传递 (`kA_group_func`)
# - 通过特性曲线调整传热系数 (`kA_char_group_func`)

# 接口
# - 入口: in1
# - 出口: out1

# 参数说明
# - `label`: 组件的标签字符串。
# - `design`: 设计参数列表。
# - `offdesign`: 非设计参数列表。
# - `design_path`: 设计案例路径。
# - `local_offdesign`: 在设计计算中将此组件视为非设计组件。
# - `local_design`: 在非设计计算中将此组件视为设计组件。
# - `char_warnings`: 是否忽略默认特征线使用的警告信息。
# - `printout`: 是否在结果打印中包含此组件。

# - `Q`: 换热速率，单位为 W。
# self.Q.val = self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)

# - `pr`: 出口到入口的压力比。
# self.pr.val = o.p.val_SI / i.p.val_SI

# - `zeta`: 几何无关摩擦系数，单位为 m^-4。
# self.zeta.val = self.calc_zeta(i, o)
# - `D`: 管道直径，单位为 m。
# - `L`: 管道长度，单位为 m。
# - `ks`: 管道粗糙度，单位为 m。

# 达西公式相关参数组：`darcy_group`: 使用达西-魏斯巴赫方程根据管道尺寸计算压降。
# def darcy_func(self)

# 哈根-威廉姆斯公式相关参数组，用于液态水流动的压降计算。
# def hazen_williams_func(self)
# - `ks_HW`: 管道粗糙度（用于哈根-威廉姆斯方程），无量纲。
# - `hw_group`: 使用哈根-威廉姆斯方程根据管道尺寸计算压降。

# 传热系数相关参数
# - `kA`: 面积无关传热系数，单位为 W/K。
# self.kA.val = abs(self.Q.val / td_log)
# i.m.val_SI * (o.h.val_SI - i.h.val_SI) + self.kA.val * td_log = 0

# - `kA_char`: 传热系数的特性曲线对象。
# def kA_char_group_func(self)
# i.m.val_SI * (o.h.val_SI - i.h.val_SI) + self.kA.design * fkA * td_log = 0


# - `Tamb`: 环境温度，使用网络中的温度单位。
# - `kA_group`: 利用环境温度和面积无关传热系数 kA 计算热量传递。

from tespy.components import Sink, Source, SimpleHeatExchanger  # 导入TESPy中的Sink、Source和SimpleHeatExchanger组件
from tespy.connections import Connection  # 导入TESPy中的Connection类
from tespy.networks import Network  # 导入TESPy中的Network类
import shutil  # 导入shutil模块用于删除文件夹

nw = Network()  # 创建一个网络实例
# 设置网络的基本单位：压力单位为bar，温度单位为摄氏度，比焓单位为kJ/kg，并关闭迭代信息显示
nw.set_attr(p_unit='bar', T_unit='C', h_unit='kJ / kg', iterinfo=False)

so1 = Source('source 1')  # 创建一个名为'source 1'的源组件
si1 = Sink('sink 1')  # 创建一个名为'sink 1'的汇组件
heat_sink = SimpleHeatExchanger('heat sink')  # 创建一个名为'heat sink'的简单换热器组件

# 设置换热器的设计参数和非设计参数
# 设计参数包括出口到入口的压力比(pr)
# 非设计参数包括几何无关摩擦系数(zeta)和传热系数特性曲线(kA_char)
heat_sink.set_attr(Tamb=10, pr=0.95, design=['pr'], offdesign=['zeta', 'kA_char'])

# 创建从源(source 1)到换热器(heat sink)的进气连接
inc = Connection(so1, 'out1', heat_sink, 'in1')
# 创建从换热器(heat sink)到汇(sink 1)的排气连接
outg = Connection(heat_sink, 'out1', si1, 'in1')

# 将两个连接添加到网络中
nw.add_conns(inc, outg)

# 设置进气连接的流体组成、质量流量、温度和压力
# 流体组成为氮气(N2)，质量流量为1 kg/s，温度为200°C，压力为5 bar
inc.set_attr(fluid={'N2': 1}, m=1, T=200, p=5)
# 设置排气连接的设计温度为150°C
outg.set_attr(T=150, design=['T'])

# 进行设计点计算
nw.solve('design')
# 将设计点的结果保存到'tmp'文件夹中
nw.save('tmp')

# 计算并四舍五入换热器在设计点下的热量传递值，保留整数位
round(heat_sink.Q.val, 0)
# 计算并四舍五入换热器在设计点下的面积无关传热系数值，保留整数位
round(heat_sink.kA.val, 0)

# 修改进气连接的质量流量为1.25 kg/s
inc.set_attr(m=1.25)
# 进行非设计点计算，使用之前保存的设计点结果作为参考
nw.solve('offdesign', design_path='tmp')
# 计算并四舍五入换热器在非设计点下的热量传递值，保留整数位
round(heat_sink.Q.val, 0)
# 计算并四舍五入排气连接在非设计点下的温度值，保留一位小数
round(outg.T.val, 1)

# 修改进气连接的质量流量为0.75 kg/s
inc.set_attr(m=0.75)
# 再次进行非设计点计算，使用之前保存的设计点结果作为参考
nw.solve('offdesign', design_path='tmp')
# 计算并四舍五入换热器在新的非设计点下的热量传递值，保留一位小数
round(heat_sink.Q.val, 1)
# 计算并四舍五入排气连接在新的非设计点下的温度值，保留一位小数
round(outg.T.val, 1)

# 删除临时文件夹'tmp'
shutil.rmtree('./tmp', ignore_errors=True)

# 熵平衡
# def entropy_balance(self)

# 可以应用于总线
# def bus_func(self, bus)
# i.m.val_SI * (o.h.val_SI - i.h.val_SI) 当热源比环境温度高时，结果是一个负值，表示热源向外散热