from tespy.networks import Network  # 导入 TESPy 的 Network 类
from tespy.components import Source, Sink, Pipe  # 导入 TESPy 的 Source、Sink 和 Pipe 组件类
from tespy.connections import Connection, Bus  # 导入 TESPy 的 Connection 和 Bus 类

# 创建一个名为 nw 的 Network 实例，并设置温度单位为摄氏度 (C)，压力单位为巴 (bar)，容积流量单位为立方米每秒 (m3 / s)
nw = Network(T_unit='C', p_unit='bar', v_unit='m3 / s')

# 创建一个名为 so 的 Source 组件实例，命名为 'source'
so = Source('source')

# 创建一个名为 si 的 Sink 组件实例，命名为 'sink'
si = Sink('sink')

# 创建一个名为 p 的 Pipe 组件实例，命名为 'pipe'，并设置其热流为 0，压降比率为 0.95，不打印计算信息
p = Pipe('pipe', Q=0, pr=0.95, printout=False)

# 创建一个连接 a，从源组件 so 的输出端 ('out1') 连接到管道 p 的输入端 ('in1')
a = Connection(so, 'out1', p, 'in1')

# 创建一个连接 b，从管道 p 的输出端 ('out1') 连接到汇组件 si 的输入端 ('in1')
b = Connection(p, 'out1', si, 'in1')

# 将连接 a 和 b 添加到网络 nw 中
nw.add_conns(a, b)

# 设置连接 a 的属性：流体组成为 {'CH4': 1}（纯甲烷），温度为 30 摄氏度，压力为 10 巴，质量流量为 10 kg/s，不打印计算信息
a.set_attr(fluid={'CH4': 1}, T=30, p=10, m=10, printout=False)

# 设置连接 b 的属性：不打印计算信息
b.set_attr(printout=False)

# 创建一个名为 b 的 Bus 实例，命名为 'heat bus'
b = Bus('heat bus')

# 将管道 p 添加到总线 b 中
b.add_comps({'comp': p})

# 将总线 b 添加到网络 nw 中
nw.add_busses(b)

# 设置总线 b 的属性：不打印计算信息
b.set_attr(printout=False)

# 设置网络 nw 的属性：不打印迭代信息
nw.set_attr(iterinfo=False)

# 解决网络的设计工况
nw.solve('design')

# 打印网络的结果
nw.print_results()