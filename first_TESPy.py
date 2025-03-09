from tespy.networks import Network #建立网络模型
from tespy.components import (CycleCloser, Compressor, Valve, SimpleHeatExchanger)#设置组件：包括一个压缩机，两个换热器，一个膨胀阀
from tespy.connections import Connection #建立连接
my_plant = Network() # 建立网络模型

# 1 bar = 100 kPa = 0.1 MPa 压强单位，比焓单位，'kJ / kg' 表示每千克物质的能量，单位为千焦耳（kJ）
my_plant.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg') #指定变量单位，不指定将使用SI单位

# 设置组件：包括一个压缩机，两个换热器，一个膨胀阀

# CycleCloser 是在处理闭式循环时必要的组件，
# 在循环中的某个点指定了质量流量，系统将始终是过确定的。
# 由于所有组件在入口和出口处都有质量流量的相等约束，它将传播到所有组件。

cc = CycleCloser('cycle closer')        # 此组件用来关闭循环过程
co = SimpleHeatExchanger('condenser')   # 冷凝器 SimpleHeatExchanger格式
ev = SimpleHeatExchanger('evaporator')  # 蒸发器 SimpleHeatExchanger格式
va = Valve('expansion valve')           # 膨胀阀
cp = Compressor('compressor')           # 压缩机

# 建立连接，将各个组件通过温度，压力，流量等参数连接在一起
c1 = Connection(cc, 'out1', ev, 'in1', label='1')
c2 = Connection(ev, 'out1', cp, 'in1', label='2') # 将蒸发器和压缩机进行参数化连接
c3 = Connection(cp, 'out1', co, 'in1', label='3')
c4 = Connection(co, 'out1', va, 'in1', label='4')
c0 = Connection(va, 'out1', cc, 'in1', label='0')

# 注意：创建连接后，我们需要将它们添加到网络中
# 由于连接包含信息，即哪些组件以何种方式连接，因此我们不需要将组件传递给网络
my_plant.add_conns(c1, c2, c3, c4, c0) # 将连接点增加到网络中

# 设置各个组件 /各个节点 的参数
# 注意：能量传递组件的符号约定始终以组件的视角为准。
# 进入组件的能量表示正号，离开组件系统边界的能量表示负号。
co.set_attr(pr=0.98, Q=-1e6) # 冷凝器，散热量-1000000W,出口压力/进口压力=0.98
ev.set_attr(pr=0.98)         # 蒸发器,出口压力/进口压力=0.98
cp.set_attr(eta_s=0.85)      # 压缩机 等熵效率0.85

c2.set_attr(T=20, x=1, fluid={'R134a': 1}) # 蒸发器出口温度20℃，干度为1，R134A制冷剂
c4.set_attr(T=60, x=0)       # 冷凝器出口温度80℃
 
 
# design模式：设计模式用于第一次求解一个新的热力系统模型。
# 当你首次构建一个系统并希望找到满足所有给定边界条件的最佳操作点时，使用设计模式。
# offdesign 模式：当你想要在设计条件之外的条件下运行系统时，使用offdesign模式。
# 当你已经有一个经过设计优化的系统，并希望在不同的工况下分析其性能时，使用非设计模式。
my_plant.solve(mode='design') #求解
my_plant.print_results()
 
print(f'COP = {abs(co.Q.val) / cp.P.val}') #输出COP
 
