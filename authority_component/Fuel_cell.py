# -*- coding: utf-8 -*-
# 使用TESPy库创建 燃料电池模型

# 燃料电池:通过氢气氧化产生电力。

# 必要方程组
# 1. 流体守恒(`fluid_func`)：确保流经燃料电池的物质种类及其比例满足化学反应的需求。
# 2. 质量守恒 (`mass_flow_func`)：确保进入和离开燃料电池的质量流量一致。

# 3. 压力平衡 (`reactor_pressure_func`)：保持燃料电池内部的压力稳定。
# 氧气入口的压力 = 产水出口的压力 = 氢气入口的压力
# self.outl[1].p.val_SI - self.inl[1].p.val_SI
# self.outl[1].p.val_SI - self.inl[1].p.val_SI

# 4. 能量平衡 (`energy_balance_func`)：确保输入的能量等于输出的能量加上损耗。
# 燃料电池电功率输出P是通过考虑氢气和氧气入口的能量输入、冷却介质的能量消耗以及产水出口的能量损失来计算

# 可选方程组：这些方程可以根据具体应用场景选择性地启用
# 1. 冷却回路：
#    - 压力损失系数 (`zeta_func`)：考虑冷却介质在管道中的摩擦阻力。
#    - 压力比 (`pr_func`)：计算冷却介质进出燃料电池的压力变化比率。
# 2. 效率相关：
#    - 电堆效率 (`eta_func`)：衡量燃料电池将化学能转化为电能的效率。
#    - 冷却热负荷 (`heat_func`)：计算燃料电池产生的废热。
#    - 特定能量消耗 (`specific_energy_func`)：评估单位体积氢气的发电能力
# self.P.val - self.inl[2].m.val_SI * self.e.val

# 接口
# 入口:
#   - `in1`: 冷却介质入口
#   - `in2`: 氧气入口
#   - `in3`: 氢气入口
# 出口:
#   - `out1`: 冷却介质出口
#   - `out2`: 生成水的出口

# 设置参数：
# label: 组件标签名，用于标识该燃料电池组件。
# design/offdesign: 设计工况和偏离设计工况时需要考虑的设计参数列表。
# design_path: 存储设计工况数据的文件路径。
# local_offdesign/local_design: 控制组件在设计/偏离设计工况下的行为。
# char_warnings: 是否忽略默认特性曲线使用的警告信息。
# printout: 在网络结果打印时是否包含此组件的信息。

# 工作参数：
# P: 输出电功率，单位为瓦特 (W)。负数代表输出功率。
# Q: 冷却系统输出热量，单位为瓦特 (W)。
# self.Q.val = -self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)

# e: 燃料电池燃烧每立方米的氢气，所获得的输出电能，单位为焦耳/立方米 (J/m³)。
# self.e.val = self.P.val / self.inl[2].m.val_SI

# eta: 燃料电池效率，表示实际输出电能占理论最大值的比例。
# self.eta.val = self.e.val / self.e0

# pr: 冷却系统的压力比，即冷却介质出口与入口压力之比。
# self.pr.val = self.outl[0].p.val_SI / self.inl[0].p.val_SI

# zeta: 几何无关的压力损失系数，用于计算冷却介质流动过程中的摩擦阻力。

# 注意事项：
# - 燃料电池组件内置了对氢气、氧气进口气体成分以及产水出口气体成分的处理机制
# 因此用户不应手动指定这些接口上的流体组成。


# 从tespy.components导入Sink、Source和FuelCell类
from tespy.components import (Sink, Source, FuelCell)

# 从tespy.connections导入Connection类
from tespy.connections import Connection

# 从tespy.networks导入Network类
from tespy.networks import Network

# 从tespy.tools导入ComponentCharacteristics类，并简写为dc_cc（虽然在这个例子中没有使用）
from tespy.tools import ComponentCharacteristics as dc_cc

# 导入shutil模块（虽然在这个例子中没有使用）
import shutil

# 创建一个网络对象nw，设置温度单位为摄氏度(C)，压力单位为巴(bar)，体积流速单位为升/秒(l/s)，并且不显示迭代信息(iterinfo=False)
nw = Network(T_unit='C', p_unit='bar', v_unit='l / s', iterinfo=False)

# 创建一个燃料电池组件fc，并命名为'fuel cell'
fc = FuelCell('fuel cell')

# 打印燃料电池的名称，验证其正确创建
fc.component()
# 输出: 'fuel cell'

# 创建一个氧气源组件oxygen_source，并命名为'oxygen_source'
oxygen_source = Source('oxygen_source')

# 创建一个氢气源组件hydrogen_source，并命名为'hydrogen_source'
hydrogen_source = Source('hydrogen_source')

# 创建一个冷却水源组件cw_source，并命名为'cw_source'
cw_source = Source('cw_source')

# 创建一个冷却水汇组件cw_sink，并命名为'cw_sink'
cw_sink = Sink('cw_sink')

# 创建一个产物水汇组件water_sink，并命名为'water_sink'
water_sink = Sink('water_sink')

# 创建一个连接cw_in，从冷却水源(cw_source)的出口(out1)连接到燃料电池(fc)的冷却液入口(in1)
cw_in = Connection(cw_source, 'out1', fc, 'in1')

# 创建一个连接cw_out，从燃料电池(fc)的冷却液出口(out1)连接到冷却水汇(cw_sink)的入口(in1)
cw_out = Connection(fc, 'out1', cw_sink, 'in1')

# 创建一个连接oxygen_in，从氧气源(oxygen_source)的出口(out1)连接到燃料电池(fc)的氧气入口(in2)
oxygen_in = Connection(oxygen_source, 'out1', fc, 'in2')

# 创建一个连接hydrogen_in，从氢气源(hydrogen_source)的出口(out1)连接到燃料电池(fc)的氢气入口(in3)
hydrogen_in = Connection(hydrogen_source, 'out1', fc, 'in3')

# 创建一个连接water_out，从燃料电池(fc)的产物水出口(out2)连接到产物水汇(water_sink)的入口(in1)
water_out = Connection(fc, 'out2', water_sink, 'in1')

# 将所有创建的连接添加到网络中
nw.add_conns(cw_in, cw_out, oxygen_in, hydrogen_in, water_out)

# 设置燃料电池的属性
# 效率(eta)为0.45
# 功率输入(P)为-200kW（负值表示输出功率）
# 热输出(Q)为-200kW（负值表示放出热量）
# 冷却回路的压力比(pr)为0.9
fc.set_attr(eta=0.45, P=-200e03, Q=-200e03, pr=0.9)

# 设置冷却水进口(cw_in)的参数
# 温度(T)为25°C
# 压力(p)为1bar
# 质量流量(m)为1kg/s
# 流体(fluid)为纯水({'H2O': 1})
cw_in.set_attr(T=25, p=1, m=1, fluid={'H2O': 1})

# 设置氧气进口(oxygen_in)的参数
# 温度(T)为25°C
# 压力(p)为1bar
oxygen_in.set_attr(T=25, p=1)

# 设置氢气进口(hydrogen_in)的参数
# 温度(T)为25°C
hydrogen_in.set_attr(T=25)

# 解决网络的设计工况
nw.solve('design')

# 获取设计工况下的功率输出，并将其转换为千瓦(kW)
P_design = fc.P.val / 1e3

# 四舍五入设计工况下的功率输出到最接近的整数，并打印结果
round(P_design, 0)
# 输出: -200.0

# 四舍五入设计工况下的效率到小数点后两位，并打印结果
round(fc.eta.val, 2)
# 输出: 0.45


# calc_e0 计算燃料电池每摩尔氢气燃烧，能产生的理论热量。
# 燃料电池的效率 eta = 燃料电池输出电功率 / （氢气入口的质量流量 * 每摩尔氢气燃烧，产生的理论热能 calc_e0）
# self.eta.val = self.e.val / self.e0
