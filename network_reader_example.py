from tespy.components import (Sink, Source, CombustionChamber,
                            Compressor, Turbine, SimpleHeatExchanger)
from tespy.connections import Connection, Ref, Bus
from tespy.networks import load_network, Network
import shutil

# 创建一个新的TESPy网络对象，并设置单位为bar（压力）、C（温度）、kJ/kg（比焓）
nw = Network(p_unit='bar', T_unit='C', h_unit='kJ / kg', iterinfo=False)

# 定义各个组件：空气源、燃料源、压缩机、燃烧室、涡轮机和燃油预热器
air = Source('air')
f = Source('fuel')
c = Compressor('compressor')
comb = CombustionChamber('combustion')
t = Turbine('turbine')
p = SimpleHeatExchanger('fuel preheater')
si = Sink('sink')

# 定义连接关系及其属性
# 空气源到压缩机的连接
inc = Connection(air, 'out1', c, 'in1', label='ambient air')
# 压缩机到燃烧室的连接
cc = Connection(c, 'out1', comb, 'in1')
# 燃料源到燃油预热器的连接
fp = Connection(f, 'out1', p, 'in1')
# 燃油预热器到燃烧室的连接
pc = Connection(p, 'out1', comb, 'in2')
# 燃烧室到涡轮机的连接
ct = Connection(comb, 'out1', t, 'in1')
# 涡轮机到汇流点的连接
outg = Connection(t, 'out1', si, 'in1')

# 将所有连接添加到网络中
nw.add_conns(inc, cc, fp, pc, ct, outg)

# 设置压缩机的设计参数和离设计工况下的性能特性
c.set_attr(pr=10, eta_s=0.88, design=['eta_s', 'pr'], offdesign=['char_map_eta_s', 'char_map_pr'])
# 设置涡轮机的设计参数和离设计工况下的性能特性
t.set_attr(eta_s=0.9, design=['eta_s'], offdesign=['eta_s_char', 'cone'])
# 设置燃烧室的过剩空气系数
comb.set_attr(lamb=2)
# 设置进口气体的组成、温度和压力
inc.set_attr(fluid={'N2': 0.7556, 'O2': 0.2315, 'Ar': 0.0129}, T=25, p=1)
# 设置燃料气体的组成、温度和压力
fp.set_attr(fluid={'CH4': 0.96, 'CO2': 0.04}, T=25, p=40)
# 设置燃油预热器出口气体的温度
pc.set_attr(T=25)
# 设置排气气体的压力与进口气体相同
outg.set_attr(p=Ref(inc, 1, 0))

# 创建一个总线来表示总的功率输出
power = Bus('total power output')
# 将压缩机和涡轮机添加到总线上
power.add_comps({"comp": c, "base": "bus"}, {"comp": t})
# 将总线添加到网络中
nw.add_busses(power)

# 设置空气质量流量
inc.set_attr(m=3)
# 解决设计工况
nw.solve('design')

# 移除燃烧室的过剩空气系数限制
comb.set_attr(lamb=None)
# 设置涡轮机出口气体的温度
ct.set_attr(T=1100)
# 移除空气质量流量的固定值
inc.set_attr(m=None)
# 设置总功率输出为目标值
power.set_attr(P=-1e6)
# 再次解决设计工况
nw.solve('design')

# 保存当前的设计状态
nw.save('design_state')
# 导出整个网络结构到文件夹'design_state'
nw.export('exported_nwk')

# 获取空气质量流量并四舍五入到小数点后一位
mass_flow = round(nw.get_conn('ambient air').m.val_SI, 1)

# 设置压缩机进口导向叶片角度为可变参数
c.set_attr(igva='var')
# 解决离设计工况
nw.solve('offdesign', design_path='design_state')

# 获取涡轮机效率并四舍五入到小数点后三位
eta_s_t = round(t.eta_s.val, 3)
# 获取压缩机进口导向叶片角度并四舍五入到小数点后三位
igva = round(c.igva.val, 3)