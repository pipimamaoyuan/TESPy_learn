# TESPy Bus 类
# Bus是一个用于连接不同能量流的对象。
# 通过使用Bus，可以汇总和管理多个组件的能量流动，例如功率或热量的总和。
# key: 这对于热力学系统分析非常有用，特别是当你需要平衡整个系统的能量时。
# 通过在设计阶段不显式设置其功率值，系统会在求解过程中自动平衡电力流动。

# 参数说明
# label : str
# 这是为总线指定的一个字符串标签。标签用于标识这个特定的总线对象，
# 在后续的网络计算和结果输出中可以通过该标签来引用和识别。

# P : float
# 这个参数指定了总线上所有能量流的总功率或热量，单位是瓦特（W）。
# 它是对总线上所有连接的能量流进行量化的一种方式，可以用来设定目标值或者查看实际的总能量流。

# printout : boolean
# 这是一个布尔值，默认情况下设置为True。当设置为True时，使用Network.print_results方法打印网络计算结果时，会包含这个总线的相关信息。
# 如果设置为False，则不会在打印结果中显示该总线的信息。

from tespy.components import (Sink, Source, CombustionEngine, HeatExchanger, Merge, Splitter, Pump)
from tespy.connections import Connection, Ref, Bus
from tespy.networks import Network
from tespy.tools import CharLine
import shutil
import numpy as np

# 创建一个TESPy网络实例，设置压力单位为bar，温度单位为摄氏度，压力范围为0.5到10 bar，并关闭迭代信息显示
nw = Network(p_unit='bar', T_unit='C', p_range=[0.5, 10], iterinfo=False)

# 定义各个组件：
# 环境空气源、燃料源、烟气出口汇、冷却水入口源、冷却水出口汇
# 冷却水分流器、冷却水合并器、
# 烟气冷却器、冷却水泵、内燃机

amb = Source('ambient')
sf = Source('fuel')
fg = Sink('flue gas outlet')
cw_in = Source('cooling water inlet')
sp = Splitter('cooling water splitter', num_out=2)
me = Merge('cooling water merge', num_in=2)
cw_out = Sink('cooling water outlet')
fgc = HeatExchanger('flue gas cooler')
pu = Pump('cooling water pump')
chp = CombustionEngine(label='internal combustion engine')

# 定义连接关系：环境空气进入内燃机的第3个进口，燃料进入内燃机的第4个进口
amb_comb = Connection(amb, 'out1', chp, 'in3')
sf_comb = Connection(sf, 'out1', chp, 'in4')

# 内燃机的第3个出口连接到烟气冷却器的第1个进口
comb_fgc = Connection(chp, 'out3', fgc, 'in1')

# 烟气冷却器的第1个出口连接到烟气出口汇
fgc_fg = Connection(fgc, 'out1', fg, 'in1')

# 将上述连接添加到网络中
nw.add_conns(sf_comb, amb_comb, comb_fgc, fgc_fg)

# 定义冷却水路径的连接关系：
# 冷却水入口源连接到冷却水泵的进口
cw_pu = Connection(cw_in, 'out1', pu, 'in1')

# 冷却水泵的出口连接到冷却水分流器的进口
pu_sp = Connection(pu, 'out1', sp, 'in1')

# 冷却水分流器的第一个出口连接到内燃机的第一个进口
sp_chp1 = Connection(sp, 'out1', chp, 'in1')

# 冷却水分流器的第二个出口连接到内燃机的第二个进口
sp_chp2 = Connection(sp, 'out2', chp, 'in2')

# 内燃机的第一个出口连接到冷却水合并器的第一个进口
chp1_me = Connection(chp, 'out1', me, 'in1')

# 内燃机的第二个出口连接到冷却水合并器的第二个进口
chp2_me = Connection(chp, 'out2', me, 'in2')

# 冷却水合并器的出口连接到烟气冷却器的第二个进口
me_fgc = Connection(me, 'out1', fgc, 'in2')

# 烟气冷却器的第二个出口连接到冷却水出口汇
fgc_cw = Connection(fgc, 'out2', cw_out, 'in1')

# 将上述冷却水路径的连接添加到网络中
nw.add_conns(cw_pu, pu_sp, sp_chp1, sp_chp2, chp1_me, chp2_me, me_fgc, fgc_cw)

# 设置内燃机的设计参数和离设计点操作参数
chp.set_attr(pr1=0.99, lamb=1.0, design=['pr1'], offdesign=['zeta1'])

# 设置烟气冷却器的设计参数和离设计点操作参数
fgc.set_attr(pr1=0.999, pr2=0.98, design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2', 'kA_char'])

# 设置冷却水泵的设计参数和离设计点操作参数
pu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# 设置环境空气进入内燃机的条件：压力为5 bar，温度为30°C，组成为空气成分
amb_comb.set_attr(p=5, T=30, fluid={'Ar': 0.0129, 'N2': 0.7553, 'CO2': 0.0004, 'O2': 0.2314})

# 设置燃料进入内燃机的条件：温度为30°C，组成为纯甲烷
sf_comb.set_attr(T=30, fluid={'CH4': 1})

# 设置冷却水入口条件：压力为3 bar，温度为60°C，组成为纯水，质量流量为100 kg/s
cw_pu.set_attr(p=3, T=60, fluid={'H2O': 1}, m=100)

# 设置冷却水分流器的第二个出口的质量流量与第一个出口相同
sp_chp2.set_attr(m=Ref(sp_chp1, 1, 0))

# 设置烟气冷却器冷却水出口的压力与冷却水泵进口相同，温度为90°C
fgc_cw.set_attr(p=Ref(cw_pu, 1, 0), T=90)

# 定义负荷和效率数组，用于生成特性曲线
load = np.array([0.2, 0.4, 0.6, 0.8, 1, 1.2])
eff = np.array([0.9, 0.94, 0.97, 0.99, 1, 0.99]) * 0.98

# 创建发电机和电动机的特性曲线对象
gen = CharLine(x=load, y=eff)
mot = CharLine(x=load, y=eff)

# 创建总线以汇总总功率输出、总热输入和燃料输入
power_bus = Bus('total power output', P=-10e6)
heat_bus = Bus('total heat input')
fuel_bus = Bus('thermal input')

# 检查热输入总线的功率是否已设置，并取消设置
heat_bus.set_attr(P=-1e5)
heat_bus.set_attr(P=None)


# add_comps 方法的输入参数及其可能的配置选项
# comp : 要添加到总线的组件对象

# char : 组件的特性曲线对象, 当char=-1时，表示流入

# param : 如果组件只有一个总线选项（如涡轮机、换热器、燃烧室），则不需要提供此参数。
# 对于有多种选择的情况（如发动机），需要指定具体的参数
# "Q":表示热量传递,表示从一个部件到另一个部件的热量交换。
# 'Q1' 和 'Q2' 在换热器中，'Q1' 可能表示一侧的热量传递，而 'Q2' 表示另一侧的热量传递。
# 'TI':表示燃料输入,在换热器中，'Q1' 可能表示一侧的热量传递，而 'Q2' 表示另一侧的热量传递。
# 'P':表示电功率或机械功率的输入/输出。
# 'Qloss':表示组件的热损失。

# P_ref: 参考情况下的能量流规格，单位为瓦特（W）
# base: 可以是'bus'或者'comp'，指定参考情况下的能量流规格是基于总线还是组件
# 



# 将内燃机和冷却水泵添加到总功率输出总线中，并关联各自的特性曲线和参数
power_bus.add_comps({'comp': chp, 'char': gen, 'param': 'P'}, 
                    {'comp': pu, 'char': mot, 'base': 'bus'})

# 将内燃机和烟气冷却器添加到总热输入总线中，并关联各自的参数和方向（负号表示流入）
heat_bus.add_comps({'comp': chp, 'param': 'Q', 'char': -1},
                   {'comp': fgc, 'char': -1})

# 将内燃机和冷却水泵添加到燃料输入总线中，并关联各自的参数
fuel_bus.add_comps({'comp': chp, 'param': 'TI'}, 
                   {'comp': pu, 'char': mot})

# 将所有总线添加到网络中
nw.add_busses(power_bus, heat_bus, fuel_bus)

# 设定模式为设计工况并求解网络
mode = 'design'
nw.solve(mode=mode)

# 取消设置冷却水入口的质量流量，并设定烟气冷却器烟气出口的温度为120°C，并将其设为设计参数
cw_pu.set_attr(m=None)
fgc_fg.set_attr(T=120, design=['T'])

# 再次求解网络
nw.solve(mode=mode)

# 保存当前网络状态到临时文件夹'tmp'
nw.save('tmp')

# 获取烟气冷却器在热输入总线中的特性曲线数据
heat_bus.comps.loc[fgc]['char'].x
heat_bus.comps.loc[fgc]['char'].y

# 计算并四舍五入内燃机的热输入值
round(chp.ti.val, 0)

# 计算并四舍五入内燃机的热量输出总和
round(chp.Q1.val + chp.Q2.val, 0)

# 计算并四舍五入烟气冷却器释放给冷却水的能量
round(fgc_cw.m.val_SI * (fgc_cw.h.val_SI - pu_sp.h.val_SI), 0)

# 计算并四舍五入热输入总线的功率值
round(heat_bus.P.val, 0)

# 计算并四舍五入冷却水泵在总功率输出总线上的效率
round(pu.calc_bus_efficiency(power_bus), 2)

# 设置总功率输出总线的功率为-7.5 MW
power_bus.set_attr(P=-7.5e6)

# 设定模式为非设计工况并从临时文件夹'tmp'加载设计点和初始点进行求解
mode = 'offdesign'
nw.solve(mode=mode, design_path='tmp', init_path='tmp')

# 计算并四舍五入内燃机的热输入值
round(chp.ti.val, 0)

# 计算并四舍五入内燃机的实际功率与设计功率的比值
round(chp.P.val / chp.P.design, 3)

# 计算并四舍五入冷却水泵在总功率输出总线上的效率
round(pu.calc_bus_efficiency(power_bus), 3)

# 删除临时文件夹'tmp'
shutil.rmtree('./tmp', ignore_errors=True)