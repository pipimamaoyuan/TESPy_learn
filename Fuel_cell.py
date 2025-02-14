# -*- coding: utf-8 -*-
# 使用TESPy库创建 燃料电池模型

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