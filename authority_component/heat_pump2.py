# 使用TESPy库创建 热泵 模型

from tespy.networks import Network

# 创建一个网络对象
my_plant = Network()

# 设置温度单位为摄氏度（°C），压力单位为巴（bar），焓值单位为千焦耳每千克（kJ / kg）
my_plant.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')

from tespy.components import (CycleCloser, Compressor, Valve, SimpleHeatExchanger)

# 创建循环闭合器组件
cc = CycleCloser('cycle closer')

# 创建冷凝器组件
co = SimpleHeatExchanger('condenser')
# 创建蒸发器组件
ev = SimpleHeatExchanger('evaporator')

# 创建膨胀阀组件
va = Valve('expansion valve')
# 创建压缩机组件
cp = Compressor('compressor')

from tespy.connections import Connection

# 定义热泵系统的连接
c1 = Connection(cc, 'out1', ev, 'in1', label='1')  # 循环闭合器到蒸发器
c2 = Connection(ev, 'out1', cp, 'in1', label='2')  # 蒸发器到压缩机
c3 = Connection(cp, 'out1', co, 'in1', label='3')  # 压缩机到冷凝器
c4 = Connection(co, 'out1', va, 'in1', label='4')  # 冷凝器到膨胀阀
c0 = Connection(va, 'out1', cc, 'in1', label='0')  # 膨胀阀到循环闭合器

# 将所有连接添加到网络中
my_plant.add_conns(c1, c2, c3, c4, c0)

# 设置冷凝器的压比为0.98，热量传递速率为-1e6 kW
co.set_attr(pr=0.98, Q=-1e6)
# 设置蒸发器的压比为0.98
ev.set_attr(pr=0.98)
# 设置压缩机的等熵效率为0.85
cp.set_attr(eta_s=0.85)

# 设置蒸发器出口的状态：温度为20°C，干度为1（纯蒸汽），流体组成为R134a
c2.set_attr(T=20, x=1, fluid={'R134a': 1})
# 设置冷凝器出口的状态：温度为80°C，干度为0（纯液体）
c4.set_attr(T=80, x=0)

# 求解网络的设计状态
my_plant.solve(mode='design')
# 打印所有的计算结果
my_plant.print_results()

# 计算并打印出系统的性能系数（COP）
print(f'COP = {abs(co.Q.val) / cp.P.val}')

# 将冷凝器的热量传递速率设置为None，表示不再限制热量传递速率
co.set_attr(Q=None)
# 设置进料的质量流量为5 kg/s
c1.set_attr(m=5)

# 再次求解网络并打印结果
my_plant.solve('design')
my_plant.print_results()

# 设置压缩机的压比为4
cp.set_attr(pr=4)
# 将冷凝器出口的温度设置为None
c4.set_attr(T=None)

# 再次求解网络并打印结果
my_plant.solve('design')
my_plant.print_results()

# 将压缩机的压比和等熵效率都设置为None
cp.set_attr(pr=None, eta_s=None)
# 设置中间连接（压缩机出口）的温度为97.3°C
c3.set_attr(T=97.3)
# 将冷凝器出口的温度设置为80°C
c4.set_attr(T=80)

# 再次求解网络并打印结果
my_plant.solve('design')
my_plant.print_results()

# 首先将系统恢复到原始状态
# 设置冷凝器的热量传递速率为-1e6 kW
co.set_attr(Q=-1e6)
# 设置压缩机的压比和等熵效率分别为None和0.85
cp.set_attr(pr=None, eta_s=0.85)
# 设置进料的质量流量为None
c1.set_attr(m=None)
# 设置中间连接（压缩机出口）的温度为None
c3.set_attr(T=None)
# 设置冷凝器出口的温度为80°C
c4.set_attr(T=80)

import matplotlib.pyplot as plt
import numpy as np

# 设置字体大小以便于阅读
plt.rc('font', **{'size': 18})

# 定义一系列的数据范围，包括蒸发温度、冷凝温度和等熵效率
data = {
    'T_source': np.linspace(0, 50, 51),  # 蒸发温度从0°C到40°C，共11个点
    'T_sink': np.linspace(60, 100, 21),  # 冷凝温度从60°C到100°C，共11个点
    'eta_s': np.linspace(0.75, 0.95, 21) * 100  # 等熵效率从75%到95%，共11个点
}
# 初始化存储COP值的字典
COP = {
    'T_source': [],
    'T_sink': [],
    'eta_s': []
}
# 定义每个参数的描述信息
description = {
    'T_source': 'evaporating temperature in °C',
    'T_sink': 'condensing temperature in °C',
    'eta_s': 'isentropic efficiency in %'
}

# 对每个蒸发温度进行遍历
for T in data['T_source']:
    # 设置蒸发器出口的温度
    c2.set_attr(T=T)
    # 求解网络的设计状态
    my_plant.solve('design')
    # 记录当前条件下的COP值
    COP['T_source'] += [abs(co.Q.val) / cp.P.val]

# 将蒸发器出口的温度重置为基准值20°C
c2.set_attr(T=20)

# 对每个冷凝温度进行遍历
for T in data['T_sink']:
    # 设置冷凝器出口的温度
    c4.set_attr(T=T)
    # 求解网络的设计状态
    my_plant.solve('design')
    # 记录当前条件下的COP值
    COP['T_sink'] += [abs(co.Q.val) / cp.P.val]

# 将冷凝器出口的温度重置为基准值80°C
c4.set_attr(T=80)

# 对每个等熵效率进行遍历
for eta_s in data['eta_s']:
    # 设置压缩机的等熵效率
    cp.set_attr(eta_s=eta_s / 100)
    # 求解网络的设计状态
    my_plant.solve('design')
    # 记录当前条件下的COP值
    COP['eta_s'] += [abs(co.Q.val) / cp.P.val]

# 创建三个子图，共享y轴，设置图形大小为16x8英寸
fig, ax = plt.subplots(1, 3, sharey=True, figsize=(16, 8))

# 为每个子图添加网格线
[a.grid() for a in ax]

i = 0
# 对每个参数绘制散点图
for key in data:
    # 绘制散点图，设置点的大小和颜色
    ax[i].scatter(data[key], COP[key], s=100)
    # 设置x轴标签
    ax[i].set_xlabel(description[key])
    i += 1

# 设置第一个子图的y轴标签
ax[0].set_ylabel('heat pump COP')

# 自动调整子图之间的间距
plt.tight_layout()

plt.show()
# 保存生成的图表为SVG文件
#fig.savefig('heat_pump_parametric.svg')