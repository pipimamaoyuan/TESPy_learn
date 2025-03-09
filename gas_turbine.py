from tespy.networks import Network  # 导入Network类，用于创建和管理热力系统网络
from tespy.components import (  # 导入所需的组件类
    DiabaticCombustionChamber,  # 非绝热燃烧室
    Turbine,  # 涡轮机
    Source,  # 源（空气源、燃料源）
    Sink,  # 汇（烟气汇）
    Compressor  # 压缩机
)
from tespy.connections import Connection, Ref, Bus  # 导入连接类、引用类和总线类

# 定义网络中的流体列表，并设置压力和温度单位
nw = Network(p_unit="bar", T_unit="C")  # 创建一个新的网络对象，设置压力单位为巴，温度单位为摄氏度

cp = Compressor("Compressor")  # 创建一个压缩机组件，命名为"Compressor"
cc = DiabaticCombustionChamber("combustion chamber")  # 创建一个非绝热燃烧室组件，命名为"combustion chamber"
tu = Turbine("turbine")  # 创建一个涡轮机组件，命名为"turbine"
air = Source("air source")  # 创建一个空气源组件，命名为"air source"
fuel = Source("fuel source")  # 创建一个燃料源组件，命名为"fuel source"
fg = Sink("flue gas sink")  # 创建一个烟气汇组件，命名为"flue gas sink"

# 定义连接关系
c2 = Connection(air, "out1", cc, "in1", label="2")  # 连接空气源到燃烧室
c3 = Connection(cc, "out1", fg, "in1", label="3")  # 连接燃烧室到烟气汇
c5 = Connection(fuel, "out1", cc, "in2", label="5")  # 连接燃料源到燃烧室
nw.add_conns(c2, c3, c5)  # 将这些连接添加到网络中

# 设置燃烧室的属性
cc.set_attr(pr=1, eta=1, lamb=1.5, ti=10e6)  # 设置燃烧室的压力比、效率、污染因子和热输入

# 设置空气源到燃烧室连接的初始条件
c2.set_attr(
    p=1, T=20,  # 设置压力为1 bar，温度为20°C
    fluid={"Ar": 0.0129, "N2": 0.7553, "CO2": 0.0004, "O2": 0.2314}  # 设置流体组成
)

# 设置燃料源到燃烧室连接的初始条件
c5.set_attr(p=1, T=20, fluid={"CO2": 0.04, "CH4": 0.96, "H2": 0})  # 设置压力为1 bar，温度为20°C，流体组成

nw.solve(mode="design")  # 解决设计工况下的网络
nw.print_results()  # 打印网络结果

# 修改燃烧室的热输入属性并重新求解
cc.set_attr(ti=None)  # 清除燃烧室的热输入属性
c5.set_attr(m=1)  # 设置燃料的质量流量为1 kg/s
nw.solve(mode="design")  # 再次解决设计工况下的网络

# 修改燃烧室的污染因子属性并重新求解
cc.set_attr(lamb=None)  # 清除燃烧室的污染因子属性
c3.set_attr(T=1400)  # 设置涡轮机入口温度为1400°C
nw.solve(mode="design")  # 再次解决设计工况下的网络

# 修改燃料源的流体组成并重新求解
c5.set_attr(fluid={"CO2": 0.03, "CH4": 0.92, "H2": 0.05})  # 修改燃料的流体组成
nw.solve(mode="design")  # 再次解决设计工况下的网络

# 打印所有连接的结果
print(nw.results["Connection"])

# 删除之前的连接，重新定义新的连接关系
nw.del_conns(c2, c3)  # 删除之前定义的连接
c1 = Connection(air, "out1", cp, "in1", label="1")  # 连接空气源到压缩机
c2 = Connection(cp, "out1", cc, "in1", label="2")  # 连接压缩机到燃烧室
c3 = Connection(cc, "out1", tu, "in1", label="3")  # 连接燃烧室到涡轮机
c4 = Connection(tu, "out1", fg, "in1", label="4")  # 连接涡轮机到烟气汇
nw.add_conns(c1, c2, c3, c4)  # 将新的连接添加到网络中

# 创建发电机总线，并将涡轮机和压缩机加入总线
# 总线：用于将多个组件组合在一起，计算它们之间的能量平衡

# 当设置 base="component" 时，效率系数直接应用于组件的实际输出功率。
# 这意味着组件贡献到总线的能量 = 其实际输出功率 * 这个效率系数。
# 当设置 base="bus" 时，效率系数应用于组件在总线上的份额。
# 这意味着组件贡献到总线的能量 = 其在总线上的份额 * 这个效率系数。

# 虽然最终的结果在这两种情况下看起来相同，
# 但在多组件的情况下，这两种方法的应用场景和影响会有所不同。

generator = Bus("generator")  # 创建一个名为"generator"的总线
generator.add_comps(
    {"comp": tu, "char": 0.98, "base": "component"},  # 将涡轮机加入总线，效率为0.98
    {"comp": cp, "char": 0.98, "base": "bus"}  # 将压缩机加入总线，效率为0.98
)
nw.add_busses(generator)  # 将总线添加到网络中

# 设置压缩机和涡轮机的性能参数
cp.set_attr(eta_s=0.85, pr=15)  # 设置压缩机的等熵效率为0.85，压力比为15
tu.set_attr(eta_s=0.90)  # 设置涡轮机的等熵效率为0.90

# 设置空气源到压缩机连接的初始条件
c1.set_attr(
    p=1, T=20,  # 设置压力为1 bar，温度为20°C
    fluid={"Ar": 0.0129, "N2": 0.7553, "CO2": 0.0004, "O2": 0.2314}  # 设置流体组成
)

# 设置涡轮机入口的质量流量和出口压力
c3.set_attr(m=30)  # 设置涡轮机入口的质量流量为30 kg/s
c4.set_attr(p=Ref(c1, 1, 0))  # 设置烟气汇的压力与空气源相同

nw.solve("design")  # 解决设计工况下的网络
c3.set_attr(m=None, T=1200)  # 清除质量流量设置，设置涡轮机入口温度为1200°C
nw.solve("design")  # 再次解决设计工况下的网络
nw.print_results()  # 打印网络结果

# 使用参考值设置燃料源到燃烧室连接的压力
c5.set_attr(p=None)  # 清除燃料源到燃烧室连接的压力设置
c5.set_attr(p=Ref(c2, 1.05, 0))  # 设置燃料源到燃烧室连接的压力为压缩机出口压力的1.05倍
nw.solve("design")  # 再次解决设计工况下的网络

# 修改燃烧室的压力比和效率，并关闭迭代信息输出
cc.set_attr(pr=0.97, eta=0.98)  # 设置燃烧室的压力比为0.97，效率为0.98
nw.set_attr(iterinfo=False)  # 关闭迭代信息输出

# 导入绘图库
import matplotlib.pyplot as plt
import numpy as np

# 设置字体大小
plt.rc('font', **{'size': 18})

# 定义参数范围
data = {
    'T_3': np.linspace(900, 1400, 11),  # 涡轮机入口温度从900°C到1400°C
    'pr': np.linspace(10, 30, 11)  # 压缩机压力比从10到30
}
power = {
    'T_3': [],
    'pr': []
}
eta = {
    'T_3': [],
    'pr': []
}

# 计算不同涡轮机入口温度下的功率和效率
for T in data['T_3']:
    c3.set_attr(T=T)  # 设置涡轮机入口温度
    nw.solve('design')  # 解决设计工况下的网络
    power['T_3'] += [abs(generator.P.val) / 1e6]  # 记录发电机功率（MW）
    eta['T_3'] += [abs(generator.P.val) / cc.ti.val * 100]  # 记录发电机效率（%）

# 重置涡轮机入口温度
c3.set_attr(T=1200)

# 计算不同压缩机压力比下的功率和效率
for pr in data['pr']:
    cp.set_attr(pr=pr)  # 设置压缩机压力比
    nw.solve('design')  # 解决设计工况下的网络
    power['pr'] += [abs(generator.P.val) / 1e6]  # 记录发电机功率（MW）
    eta['pr'] += [abs(generator.P.val) / cc.ti.val * 100]  # 记录发电机效率（%）

# 重置压缩机压力比
cp.set_attr(pr=15)

# 绘制功率和效率随涡轮机入口温度变化的关系图
fig, ax = plt.subplots(2, 2, figsize=(16, 8), sharex='col', sharey='row')
ax = ax.flatten()
[(a.grid(), a.set_axisbelow(True)) for a in ax]

i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")  # 绘制效率散点图
    ax[i + 2].scatter(data[key], power[key], s=100, color="#18a999")  # 绘制功率散点图
    i += 1

ax[0].set_ylabel('Efficiency in %')  # 设置左上子图的y轴标签
ax[2].set_ylabel('Power in MW')  # 设置左下子图的y轴标签
ax[2].set_xlabel('Turbine inlet temperature °C')  # 设置左下子图的x轴标签
ax[3].set_xlabel('Compressor pressure ratio')  # 设置右下子图的x轴标签

plt.tight_layout()  # 调整子图间距
fig.savefig('gas_turbine_parametric.svg')  # 保存图表
plt.close()  # 关闭图表

# 计算不同氧含量下的涡轮机入口温度
c3.set_attr(T=None)  # 清除涡轮机入口温度设置

data = np.linspace(0.1, 0.2, 6)  # 定义氧含量范围
T3 = []

for oxy in data[::-1]:  # 反向遍历氧含量
    c3.set_attr(fluid={"O2": oxy})  # 设置烟气中的氧含量
    nw.solve('design')  # 解决设计工况下的网络
    T3 += [c3.T.val]  # 记录涡轮机入口温度

T3 = T3[::-1]  # 反转温度数组

# 重置氧含量设置
c3.fluid.is_set.remove("O2")
c3.set_attr(T=1200)

# 绘制涡轮机入口温度随氧含量变化的关系图
fig, ax = plt.subplots(1, figsize=(16, 8))

ax.scatter(data * 100, T3, s=100, color="#1f567d")  # 绘制散点图
ax.grid()  # 显示网格
ax.set_axisbelow(True)  # 网格线位于数据下方

ax.set_ylabel('Turbine inlet temperature in °C')  # 设置y轴标签
ax.set_xlabel('Oxygen mass fraction in flue gas in %')  # 设置x轴标签

plt.tight_layout()  # 调整子图间距
fig.savefig('gas_turbine_oxygen.svg')  # 保存图表
plt.close()  # 关闭图表

# 固定除燃烧气体外的所有潜在流体的质量分数
c5.set_attr(fluid={"CO2": 0.03, "O2": 0, "H2O": 0, "Ar": 0, "N2": 0, "CH4": None, "H2": None})  # 设置固定流体组成
c5.set_attr(fluid_balance=True)  # 启用流体平衡

data = np.linspace(50, 60, 11)  # 定义热输入范围

CH4 = []
H2 = []

# 计算不同热输入下的甲烷和氢气质量分数
for ti in data:
    cc.set_attr(ti=ti * 1e6)  # 设置燃烧室的热输入
    nw.solve('design')  # 解决设计工况下的网络
    CH4 += [c5.fluid.val["CH4"] * 100]  # 记录甲烷质量分数
    H2 += [c5.fluid.val["H2"] * 100]  # 记录氢气质量分数

nw._convergence_check()  # 检查收敛情况

# 绘制甲烷和氢气质量分数随热输入变化的关系图
fig, ax = plt.subplots(1, figsize=(16, 8))

ax.scatter(data, CH4, s=100, color="#1f567d", label="CH4 mass fraction")  # 绘制甲烷质量分数散点图
ax.scatter(data, H2, s=100, color="#18a999", label="H2 mass fraction")  # 绘制氢气质量分数散点图
ax.grid()  # 显示网格
ax.set_axisbelow(True)  # 网格线位于数据下方
ax.legend()  # 显示图例

ax.set_ylabel('Mass fraction of the fuel in %')  # 设置y轴标签
ax.set_xlabel('Thermal input in MW')  # 设置x轴标签
ax.set_ybound([0, 100])  # 设置y轴范围

plt.tight_layout()  # 调整子图间距
fig.savefig('gas_turbine_fuel_composition.svg')  # 保存图表
plt.close()  # 关闭图表