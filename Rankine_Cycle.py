from tespy.networks import Network

# 创建一个网络对象，并指定流体为 R134a（实际上这里应该是水蒸汽循环，所以应为 'water'）
my_plant = Network()
my_plant.set_attr(fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg')  # 设置温度单位为摄氏度，压力单位为巴，比焓单位为 kJ/kg

from tespy.components import (
    CycleCloser, Pump, Condenser, Turbine, SimpleHeatExchanger, Source, Sink
)

# 对于封闭热力学循环，我们必须插入一个循环闭止器
cc = CycleCloser('cycle closer')  # 循环闭合器，用于闭合循环
sg = SimpleHeatExchanger('steam generator')  # 蒸汽发生器
mc = Condenser('main condenser')  # 主冷凝器
tu = Turbine('steam turbine')  # 蒸汽涡轮机
fp = Pump('feed pump')  # 给水泵

cwso = Source('cooling water source')  # 冷却水源
cwsi = Sink('cooling water sink')  # 冷却水汇

from tespy.connections import Connection

c1 = Connection(cc, 'out1', tu, 'in1', label='1')  # 连接从循环闭合器到蒸汽涡轮机
c2 = Connection(tu, 'out1', mc, 'in1', label='2')  # 连接从蒸汽涡轮机到主冷凝器
c3 = Connection(mc, 'out1', fp, 'in1', label='3')  # 连接从主冷凝器到给水泵
c4 = Connection(fp, 'out1', sg, 'in1', label='4')  # 连接从给水泵到蒸汽发生器
c0 = Connection(sg, 'out1', cc, 'in1', label='0')  # 连接从蒸汽发生器到循环闭合器

my_plant.add_conns(c1, c2, c3, c4, c0)  # 将这些连接添加到网络中

c11 = Connection(cwso, 'out1', mc, 'in2', label='11')  # 连接从冷却水源到主冷凝器的第二入口
c12 = Connection(mc, 'out2', cwsi, 'in1', label='12')  # 连接从主冷凝器的第二出口到冷却水汇

my_plant.add_conns(c11, c12)  # 将这些连接添加到网络中

mc.set_attr(pr1=1, pr2=0.98)  # 设置主冷凝器的第一和第二压力比
sg.set_attr(pr=0.9)  # 设置蒸汽发生器的压力比
tu.set_attr(eta_s=0.9)  # 设置蒸汽涡轮机的等熵效率
fp.set_attr(eta_s=0.75)  # 设置给水泵的等熵效率

c11.set_attr(T=20, p=1.2, fluid={'water': 1})  # 设置冷却水源的温度、压力和流体类型
c12.set_attr(T=30)  # 设置冷却水汇的温度
c1.set_attr(T=600, p=150, m=10, fluid={'water': 1})  # 设置蒸汽涡轮机入口的温度、压力、质量流量和流体类型
c2.set_attr(p=0.1)  # 设置蒸汽涡轮机出口的压力

my_plant.solve(mode='design')  # 求解设计模式下的网络
my_plant.print_results()  # 打印求解结果

mc.set_attr(ttd_u=4)  # 设置主冷凝器的端差
c2.set_attr(p=None)  # 清除蒸汽涡轮机出口的压力设置

my_plant.solve(mode='design')  # 重新求解设计模式下的网络
my_plant.print_results()  # 打印求解结果

# 添加功能以使用 fluprodia 库绘制 T-s 图
# T-s 曲线，即 温度-熵图 或 T-S 图，是热力学中用来表示流体状态的一种重要图表。
# 它是通过绘制流体的状态参数——温度和熵来展示流体在不同过程中的行为。
# 导入必要的库
import matplotlib.pyplot as plt
import numpy as np
from fluprodia import FluidPropertyDiagram

# 初始设置
diagram = FluidPropertyDiagram('water')  # 创建水的性质图对象
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')  # 设置单位系统：温度为摄氏度，压力为巴，比焓为 kJ/kg

# 将模型结果存储在字典中
result_dict = {}
result_dict.update(
    {cp.label: cp.get_plotting_data()[1] for cp in my_plant.comps['object']
     if cp.get_plotting_data() is not None})  # 获取每个组件的绘图数据

# 遍历从 TESPy 模拟获得的结果
for key, data in result_dict.items():
    # 计算 T-s 图中的个别隔离线
    result_dict[key]['datapoints'] = diagram.calc_individual_isoline(**data)

# 创建一个图形和轴用于绘制 T-s 图
fig, ax = plt.subplots(1, figsize=(20, 10))
isolines = {
    'Q': np.linspace(0, 1, 2),
    'p': np.array([1, 2, 5, 10, 20, 50, 100, 300]),
    'v': np.array([]),
    'h': np.arange(500, 3501, 500)
}

# 设置 T-s 图的隔离线
diagram.set_isolines(**isolines)
diagram.calc_isolines()

# 在 T-s 图上绘制隔离线
diagram.draw_isolines(fig, ax, 'Ts', x_min=0, x_max=7500, y_min=0, y_max=650)

# 调整隔离线标签的字体大小
for text in ax.texts:
    text.set_fontsize(10)

# 绘制每个组件的 T-s 曲线
for key in result_dict.keys():
    datapoints = result_dict[key]['datapoints']
    _ = ax.plot(datapoints['s'], datapoints['T'], color='#ff0000', linewidth=2)  # 绘制曲线
    _ = ax.scatter(datapoints['s'][0], datapoints['T'][0], color='#ff0000')  # 绘制起点标记

# 设置 T-s 图的标签和标题
ax.set_xlabel('Entropy, s in J/kgK', fontsize=16)  # 设置横坐标标签
ax.set_ylabel('Temperature, T in °C', fontsize=16)  # 设置纵坐标标签
ax.set_title('T-s Diagram of Rankine Cycle', fontsize=20)  # 设置图表标题

# 设置横坐标和纵坐标的刻度字体大小
ax.tick_params(axis='x', labelsize=12)
ax.tick_params(axis='y', labelsize=12)
plt.tight_layout()  # 自动调整子图参数，使之填充整个图像区域

# 将 T-s 图保存为 SVG 文件
fig.savefig('rankine_ts_diagram.svg')
plt.close()  # 关闭图形

# 为了评估电力输出，我们希望考虑涡轮机产生的功率以及驱动给水泵所需的功率。
# 可以将这两个组件的功率值包含在单个电气 Bus 中。
from tespy.connections import Bus
# 总线 bus 是一种抽象的概念，用于将多个组件的能量流或功率流组合在一起。常见的总线类型包括：
# 电力总线 (Electrical Bus): 汇总发电机和电动机的功率。
# 热力总线 (Thermal Bus): 汇总加热器和冷却器的热量交换。
# 质量流量总线 (Mass Flow Bus): 汇总不同组件的质量流量。

powergen = Bus("electrical power output")  # 创建一个总线对象来表示电力输出

# 使用 add_comps 方法将组件添加到总线上。每个组件可以通过字典的形式指定其属性。主要参数包括：
# comp: 要添加的组件对象。
# char: 字符化效率，默认为 1.0。
# base: 基准值的选择，可以是 "component" 或 "bus"。
# "component": 以组件的功率作为基准值
# "bus": 效率值是以电能作为参考

powergen.add_comps(
    {"comp": tu, "char": 0.97, "base": "component"},  # 将蒸汽涡轮机添加到总线，字符化效率为 0.97
    {"comp": fp, "char": 0.97, "base": "bus"}  # 将给水泵添加到总线，字符化效率为 0.97
)

# 使用 add_busses 方法将总线对象添加到网络中
my_plant.add_busses(powergen)  # 将总线添加到网络中

my_plant.solve(mode='design')  # 求解设计模式下的网络
my_plant.print_results()  # 打印求解结果

powergen.set_attr(P=-10e6)  # 设置总线的功率输出为 -10 MW
c1.set_attr(m=None)  # 清除蒸汽涡轮机入口的质量流量设置

my_plant.solve(mode='design')  # 重新求解设计模式下的网络
my_plant.print_results()  # 打印求解结果

my_plant.set_attr(iterinfo=False)  # 关闭迭代信息打印
c1.set_attr(m=20)  # 设置蒸汽涡轮机入口的质量流量为 20 kg/s
powergen.set_attr(P=None)  # 清除总线的功率输出设置

# 调整文本大小以使其合理
plt.rc('font', **{'size': 18})

data = {
    'T_livesteam': np.linspace(450, 750, 7),  # 生活蒸汽温度范围
    'T_cooling': np.linspace(15, 45, 7),  # 冷却水温度范围
    'p_livesteam': np.linspace(75, 225, 7)  # 生活蒸汽压力范围
}
eta = {
    'T_livesteam': [],
    'T_cooling': [],
    'p_livesteam': []
}
power = {
    'T_livesteam': [],
    'T_cooling': [],
    'p_livesteam': []
}

for T in data['T_livesteam']:
    c1.set_attr(T=T)  # 设置蒸汽涡轮机入口的温度
    my_plant.solve('design')  # 求解设计模式下的网络
    eta['T_livesteam'] += [abs(powergen.P.val) / sg.Q.val * 100]  # 计算并存储效率
    power['T_livesteam'] += [abs(powergen.P.val) / 1e6]  # 计算并存储功率

# 恢复到基础温度
c1.set_attr(T=600)

for T in data['T_cooling']:
    c12.set_attr(T=T)  # 设置冷却水汇的温度
    c11.set_attr(T=T - 10)  # 设置冷却水源的温度
    my_plant.solve('design')  # 求解设计模式下的网络
    eta['T_cooling'] += [abs(powergen.P.val) / sg.Q.val * 100]  # 计算并存储效率
    power['T_cooling'] += [abs(powergen.P.val) / 1e6]  # 计算并存储功率

# 恢复到基础温度
c12.set_attr(T=30)
c11.set_attr(T=20)

for p in data['p_livesteam']:
    c1.set_attr(p=p)  # 设置蒸汽涡轮机入口的压力
    my_plant.solve('design')  # 求解设计模式下的网络
    eta['p_livesteam'] += [abs(powergen.P.val) / sg.Q.val * 100]  # 计算并存储效率
    power['p_livesteam'] += [abs(powergen.P.val) / 1e6]  # 计算并存储功率

# 恢复到基础压力
c1.set_attr(p=150)

fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex='col', sharey='row')  # 创建子图

ax = ax.flatten()  # 展平子图数组
[a.grid() for a in ax]  # 为每个子图添加网格

i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")  # 绘制效率散点图
    ax[i + 3].scatter(data[key], power[key], s=100, color="#18a999")  # 绘制功率散点图
    i += 1

ax[0].set_ylabel('Efficiency in %')  # 设置第一个子图的纵坐标标签
ax[3].set_ylabel('Power in MW')  # 设置第四个子图的纵坐标标签
ax[3].set_xlabel('Live steam temperature in °C')  # 设置第四个子图的横坐标标签
ax[4].set_xlabel('Feed water temperature in °C')  # 设置第五个子图的横坐标标签
ax[5].set_xlabel('Live steam pressure in bar')  # 设置第六个子图的横坐标标签
plt.tight_layout()  # 自动调整子图参数，使之填充整个图像区域
fig.savefig('rankine_parametric-darkmode.svg')  # 将图形保存为 SVG 文件
plt.close()  # 关闭图形

# 当你使用 my_plant.solve('design') 时，所有设置了 design 的参数都会被固定为设计点的值。
# 当你使用 my_plant.solve('offdesign') 时，设置了 offdesign 的参数会根据新的操作条件重新计算。