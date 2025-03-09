from tespy.components.basics.cycle_closer import CycleCloser
from tespy.networks import Network
from tespy.components import (
    CycleCloser, Pipe, Pump, Valve, SimpleHeatExchanger
)
from tespy.connections import Connection

# 创建一个新的网络对象
nw = Network()

# 设置网络的温度、压力和比焓单位
nw.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')

# 中央供暖系统组件
hs = SimpleHeatExchanger('heat source')  # 热源换热器
cc = CycleCloser('cycle closer')         # 循环闭合器
pu = Pump('feed pump')                   # 给水泵

# 消费者端组件
cons = SimpleHeatExchanger('consumer')   # 消费者换热器
val = Valve('control valve')             # 控制阀

# 管道组件
pipe_feed = Pipe('feed pipe')            # 进水管
pipe_return = Pipe('return pipe')        # 回水管

# 定义连接关系
c0 = Connection(cc, "out1", hs, "in1", label="0")  # 循环闭合器到热源换热器
c1 = Connection(hs, "out1", pu, "in1", label="1")  # 热源换热器到给水泵
c2 = Connection(pu, "out1", pipe_feed, "in1", label="2")  # 给水泵到进水管
c3 = Connection(pipe_feed, "out1", cons, "in1", label="3")  # 进水管到消费者换热器
c4 = Connection(cons, "out1", val, "in1", label="4")  # 消费者换热器到控制阀
c5 = Connection(val, "out1", pipe_return, "in1", label="5")  # 控制阀到回水管
c6 = Connection(pipe_return, "out1", cc, "in1", label="6")  # 回水管到循环闭合器

# 将所有连接添加到网络中
nw.add_conns(c0, c1, c2, c3, c4, c5, c6)

# 假设消费者有特定的热需求，管道中的压力和热损失保持恒定
# 设置消费者的属性：传热量为-10000 kW（负值表示放热），压降比率为0.98
cons.set_attr(Q=-10000, pr=0.98)

# 设置热源换热器的压降比率为1
hs.set_attr(pr=1)

# 设置给水泵的效率为75%
pu.set_attr(eta_s=0.75)

# 设置进水管的传热量为-250 kW，压降比率为0.98
pipe_feed.set_attr(Q=-250, pr=0.98)

# 设置回水管的传热量为-200 kW，压降比率为0.98
pipe_return.set_attr(Q=-200, pr=0.98)

# 设置进水管道的初始条件：温度为90°C，压力为10 bar，流体为INCOMP::Water
c1.set_attr(T=90, p=10, fluid={'INCOMP::Water': 1})

# 设置给水泵出口的压力为13 bar
c2.set_attr(p=13)

# 设置消费者入口处的温度为65°C
c4.set_attr(T=65)

# 运行设计点计算
nw.solve(mode="design")

# 打印网络结果
nw.print_results()

# 设置管道的粗糙度、长度和直径
pipe_feed.set_attr(
    ks=0.0005,  # 管道的粗糙度为0.0005米
    L=100,      # 管道长度为100米
    D="var"     # 直径为变量，待求解
)

pipe_return.set_attr(
    ks=0.0005,  # 管道的粗糙度为0.0005米
    L=100,      # 管道长度为100米
    D="var"     # 直径为变量，待求解
)

# 再次运行设计点计算以确定管道直径
nw.solve(mode="design")

# 打印网络结果
nw.print_results()

# 将管道直径固定，并移除压降比率约束
pipe_feed.set_attr(D=pipe_feed.D.val, pr=None)
pipe_return.set_attr(D=pipe_return.D.val, pr=None)

# 设置环境温度和面积无关的传热系数为变量
pipe_feed.set_attr(
    Tamb=0,  # 环境温度为0°C
    kA="var"  # 面积无关的传热系数为变量
)

pipe_return.set_attr(
    Tamb=0,  # 环境温度为0°C
    kA="var"  # 面积无关的传热系数为变量
)

# 再次运行设计点计算以确定传热系数
nw.solve(mode="design")

# 打印网络结果
nw.print_results()

# 关闭迭代信息输出
nw.set_attr(iterinfo=False)

# 固定环境温度和传热系数，移除传热量约束
pipe_feed.set_attr(Tamb=0, kA=pipe_feed.kA.val, Q=None)
pipe_return.set_attr(Tamb=0, kA=pipe_return.kA.val, Q=None)

import matplotlib.pyplot as plt
import numpy as np

# 设置字体大小以便更好地阅读
plt.rc('font', **{'size': 18})

# 接下来，我们想调查如果发生以下情况，会发生什么
# 1. 环境温度从-10°C到20°C变化
# 2. 热负荷从3 kW到12 kW变化
# 3. 供热系统整体温度水平从90°C到60°C变化

# 定义不同参数下的数据范围
data = {
    'T_ambient': np.linspace(-10, 20, 7),  # 环境温度从-10°C到20°C
    'heat_load': np.linspace(3, 12, 10),   # 热负荷从3 kW到12 kW
    'T_level': np.linspace(90, 60, 7)       # 温度水平从90°C到60°C
}

# 初始化性能指标存储列表
eta = {
    'T_ambient': [],
    'heat_load': [],
    'T_level': []
}

heat_loss = {
    'T_ambient': [],
    'heat_load': [],
    'T_level': []
}

# 计算不同环境温度下的性能指标
for T in data['T_ambient']:
    pipe_feed.set_attr(Tamb=T)
    pipe_return.set_attr(Tamb=T)
    nw.solve('design')
    eta['T_ambient'] += [abs(cons.Q.val) / hs.Q.val * 100]  # 计算效率
    heat_loss['T_ambient'] += [abs(pipe_feed.Q.val + pipe_return.Q.val)]  # 计算热损失

# 重置环境温度为基准值
pipe_feed.set_attr(Tamb=0)
pipe_return.set_attr(Tamb=0)

# 计算不同热负荷下的性能指标
for Q in data['heat_load']:
    cons.set_attr(Q=-1e3 * Q)
    nw.solve('design')
    eta['heat_load'] += [abs(cons.Q.val) / hs.Q.val * 100]  # 计算效率
    heat_loss['heat_load'] += [abs(pipe_feed.Q.val + pipe_return.Q.val)]  # 计算热损失

# 重置热负荷为基准值
cons.set_attr(Q=-10e3)

# 计算不同温度水平下的性能指标
for T in data['T_level']:
    c1.set_attr(T=T)
    c4.set_attr(T=T - 20)  # 返回水流温度假设比供给温度低20°C
    nw.solve('design')
    eta['T_level'] += [abs(cons.Q.val) / hs.Q.val * 100]  # 计算效率
    heat_loss['T_level'] += [abs(pipe_feed.Q.val + pipe_return.Q.val)]  # 计算热损失

# 创建子图并设置图形大小
fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex='col', sharey='row')

# 展平轴数组以便于索引
ax = ax.flatten()
[a.grid() for a in ax]

# 绘制散点图
i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")  # 效率图
    ax[i + 3].scatter(data[key], heat_loss[key], s=100, color="#18a999")  # 热损失图
    i += 1

# 设置坐标轴标签
ax[0].set_ylabel('Efficiency in %')  # 效率百分比
ax[3].set_ylabel('Heat losses in W')  # 热损失瓦特数
ax[3].set_xlabel('Ambient temperature in °C')  # 环境温度摄氏度
ax[4].set_xlabel('Consumer heat load in kW')  # 消费者热负荷千瓦
ax[5].set_xlabel('District heating temperature level in °C')  # 区域供热温度水平摄氏度

# 调整子图间距
plt.tight_layout()

# 保存图表为SVG文件
fig.savefig('district_heating_partload.svg')

# 关闭图表
plt.close()