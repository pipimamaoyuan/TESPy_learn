# -*- coding: utf-8 -*-

# 导入 TESPy 组件
from tespy.components import Compressor
from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import HeatExchanger
from tespy.components import Sink
from tespy.components import Source
from tespy.components import Valve
from tespy.components import Pump

# 导入 TESPy 连接和总线
from tespy.connections import Connection
from tespy.connections import Bus

# 导入 TESPy 网络类
from tespy.networks import Network

# 导入 TESPy 特征曲线工具
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

# 导入 TESPy 能量分析工具
from tespy.tools import ExergyAnalysis

# 导入其他库
import numpy as np
from plotly.offline import plot
import plotly.graph_objects as go
from fluprodia import FluidPropertyDiagram
import pandas as pd
import matplotlib.pyplot as plt

pamb = 1.013  # 大气压 (bar)
Tamb = 2.8  # 大气温度 (°C)

# 地热平均温度（地热进水和回水的平均值）
Tgeo = 9.5

# 创建网络对象，并设置温度、压力、比焓和质量流量的单位
nw = Network(T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s')

cc = CycleCloser('cycle closer')  # 循环闭合器

# 地源热泵系统
cd = Condenser('condenser')  # 冷凝器
va = Valve('valve')  # 膨胀阀
ev = HeatExchanger('evaporator')  # 蒸发器
cp = Compressor('compressor')  # 压缩机

# 地热集热器
gh_in = Source('ground heat feed flow')  # 地热进水流源
gh_out = Sink('ground heat return flow')  # 地热回流汇
ghp = Pump('ground heat loop pump')  # 地热循环泵

# 加热系统
hs_feed = Sink('heating system feed flow')  # 加热系统进水流汇
hs_ret = Source('heating system return flow')  # 加热系统回水流源
hsp = Pump('heating system pump')  # 加热系统泵

# 地源热泵系统
cc_cd = Connection(cc, 'out1', cd, 'in1')  # 循环闭合器到冷凝器
cd_va = Connection(cd, 'out1', va, 'in1')  # 冷凝器到膨胀阀
va_ev = Connection(va, 'out1', ev, 'in2')  # 膨胀阀到蒸发器
ev_cp = Connection(ev, 'out2', cp, 'in1')  # 蒸发器到压缩机
cp_cc = Connection(cp, 'out1', cc, 'in1')  # 压缩机到循环闭合器
nw.add_conns(cc_cd, cd_va, va_ev, ev_cp, cp_cc)  # 将连接添加到网络中

# 地热集热器
gh_in_ghp = Connection(gh_in, 'out1', ghp, 'in1')  # 地热进水流源到地热循环泵
ghp_ev = Connection(ghp, 'out1', ev, 'in1')  # 地热循环泵到蒸发器
ev_gh_out = Connection(ev, 'out1', gh_out, 'in1')  # 蒸发器到地热回流汇
nw.add_conns(gh_in_ghp, ghp_ev, ev_gh_out)  # 将连接添加到网络中

# 加热系统
hs_ret_hsp = Connection(hs_ret, 'out1', hsp, 'in1')  # 加热系统回水流源到加热系统泵
hsp_cd = Connection(hsp, 'out1', cd, 'in2')  # 加热系统泵到冷凝器
cd_hs_feed = Connection(cd, 'out2', hs_feed, 'in1')  # 冷凝器到加热系统进水流汇
nw.add_conns(hs_ret_hsp, hsp_cd, cd_hs_feed)  # 将连接添加到网络中

# 冷凝器
cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])  # 设置冷凝器参数

# 蒸发器
# ldc 函数：用于加载预定义的特征曲线。
# 第一个参数 'heat exchanger'：指定要加载的特征曲线类型为换热器。
# 第二个参数 'kA_char1' 和 'kA_char2'：分别指定要加载的具体特征曲线名称。
# kA_char1：通常表示冷凝侧的传热系数特征曲线。
# kA_char2：通常表示蒸发侧的传热系数特征曲线。
# 第三个参数 'DEFAULT' 和 'EVAPORATING FLUID'：指定特征曲线的变体或具体应用。
# 'DEFAULT'：使用默认的特征曲线。
# 'EVAPORATING FLUID'：使用适用于蒸发侧的特征曲线。
# 第四个参数 CharLine：指定特征曲线的对象类型。
kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)  # 加载默认特征曲线
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)  # 加载蒸发侧特征曲线
ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=5,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])  # 设置蒸发器参数

# 压缩机
cp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])  # 设置压缩机参数

# 加热系统泵
hsp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])  # 设置加热系统泵参数

# 地热循环泵
ghp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])  # 设置地热循环泵参数

# 连接参数化
# 地源热泵系统
cc_cd.set_attr(fluid={'R410A': 1})  # 设置循环闭合器到冷凝器的流体为 R410A
ev_cp.set_attr(Td_bp=3)  # 设置蒸发器出口与沸腾点的温差

# 地热集热器
gh_in_ghp.set_attr(T=Tgeo + 1.5, p=1.5, fluid={'water': 1})  # 设置地热进水流源的温度、压力和流体
ev_gh_out.set_attr(T=Tgeo - 1.5, p=1.5)  # 设置蒸发器到地热回流汇的温度和压力

# 加热系统
cd_hs_feed.set_attr(T=40, p=2, fluid={'water': 1})  # 设置冷凝器到加热系统进水流汇的温度、压力和流体
hs_ret_hsp.set_attr(T=35, p=2)  # 设置加热系统回水流源到加热系统泵的温度和压力

# 初始值
va_ev.set_attr(h0=275)  # 设置膨胀阀到蒸发器的初始比焓
cc_cd.set_attr(p0=18)  # 设置循环闭合器到冷凝器的初始压力

# 创建总线
# 功率总线的特征函数
x = np.array([0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4])  # 功率总线特征函数的 x 值
y = np.array([0, 0.86, 0.9, 0.93, 0.95, 0.96, 0.95, 0.93])  # 功率总线特征函数的 y 值

char = CharLine(x=x, y=y)  # 创建特征曲线对象
power = Bus('power input')  # 创建功率输入总线
power.add_comps(
    {'comp': cp, 'char': char, 'base': 'bus'},  # 添加压缩机到总线
    {'comp': ghp, 'char': char, 'base': 'bus'},  # 添加地热循环泵到总线
    {'comp': hsp, 'char': char, 'base': 'bus'}  # 添加加热系统泵到总线
)

# 消费者热量总线
heat_cons = Bus('heating system')  # 创建消费者热量总线
heat_cons.add_comps({'comp': hs_ret, 'base': 'bus'}, 
                    {'comp': hs_feed})  # 添加加热系统回流汇和进水流汇到总线

# 地热热量总线
heat_geo = Bus('geothermal heat')  # 创建地热热量总线
heat_geo.add_comps({'comp': gh_in, 'base': 'bus'}, 
                   {'comp': gh_out})  # 添加地热进水流源和回流汇到总线

nw.add_busses(power, heat_cons, heat_geo)  # 将总线添加到网络中

# 关键参数
cd.set_attr(Q=-4e3)  # 设置冷凝器的热量需求

# 设计计算
path = 'R410A'  # 保存设计工况数据的路径
nw.solve('design')  # 求解设计工况
# 或者使用：
# nw.solve('design', init_path=path)  # 使用初始路径求解设计工况
print("\n##### 设计计算 #####\n")
nw.print_results()  # 打印结果
nw.save(path)  # 保存设计工况数据

# 绘制 h_log(p) 图
# 生成绘图数据
result_dict = {}
result_dict.update({ev.label: ev.get_plotting_data()[2]})  # 获取蒸发器的数据
result_dict.update({cp.label: cp.get_plotting_data()[1]})  # 获取压缩机的数据
result_dict.update({cd.label: cd.get_plotting_data()[1]})  # 获取冷凝器的数据
result_dict.update({va.label: va.get_plotting_data()[1]})  # 获取膨胀阀的数据

# 创建图例
diagram = FluidPropertyDiagram('R410A')
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')  # 设置单位系统

for key, data in result_dict.items():
    result_dict[key]['datapoints'] = diagram.calc_individual_isoline(**data)  # 计算孤立线上的数据点

diagram.calc_isolines()  # 计算孤立线

fig, ax = plt.subplots(1, figsize=(16, 10))  # 创建图形和坐标轴
diagram.draw_isolines(fig, ax, 'logph', x_min=200, x_max=500, y_min=0.8e1, y_max=0.8e2)  # 绘制孤立线

for key in result_dict.keys():
    datapoints = result_dict[key]['datapoints']
    ax.plot(datapoints['h'], datapoints['p'], color='#ff0000')  # 绘制孤立线上的数据点
    ax.scatter(datapoints['h'][0], datapoints['p'][0], color='#ff0000')  # 标记起点

plt.tight_layout()
fig.savefig('R410A_logph.svg')  # 保存图形

# 能量分析
ean = ExergyAnalysis(network=nw, E_F=[power, heat_geo], E_P=[heat_cons])  # 创建能量分析对象
ean.analyse(pamb, Tamb)  # 进行情能分析
print("\n##### 能量分析 #####\n")
ean.print_results()  # 打印能量分析结果

# 创建桑基图
links, nodes = ean.generate_plotly_sankey_input()  # 生成桑基图数据
fig = go.Figure(go.Sankey(
    arrangement="snap",
    node={
        "label": nodes,
        'pad': 11,
        'color': 'orange'},
    link=links))
plot(fig, filename='R410A_sankey.html')  # 保存桑基图为 HTML 文件

# 绘制能耗破坏
# 创建柱状图数据
comps = ['E_F']  # 初始化组件列表
E_F = ean.network_data.E_F  # 获取能源流入总量
# 最上层条形
E_D = [0]  # 没有能耗破坏在最上层
E_P = [E_F]  # 添加 E_F 作为最上层条形
for comp in ean.component_data.index:
    # 只绘制能耗破坏大于 1 W 的组件
    if ean.component_data.E_D[comp] > 1:
        comps.append(comp)
        E_D.append(ean.component_data.E_D[comp])
        E_F = E_F - ean.component_data.E_D[comp]
        E_P.append(E_F)
comps.append("E_P")
E_D.append(0)
E_P.append(E_F)

# 创建数据帧并保存数据
df_comps = pd.DataFrame(columns=comps)
df_comps.loc["E_D"] = E_D
df_comps.loc["E_P"] = E_P
df_comps.to_csv('R410A_E_D.csv')  # 保存能耗破坏数据到 CSV 文件

# 进一步计算
print("\n#### 进一步计算 ####\n")
# 关闭迭代信息显示
nw.set_attr(iterinfo=False)
# 非设计工况测试
nw.solve('offdesign', design_path=path)  # 使用设计路径进行非设计工况求解

# 计算效率 epsilon 取决于：
#    - 大气温度 Tamb
#    - 平均地热温度 Tgeo

Tamb_design = Tamb  # 设计大气温度
Tgeo_design = Tgeo  # 设计平均地热温度
i = 0  # 初始化案例编号

# 创建数据范围和数据框
Tamb_range = [1, 4, 8, 12, 16, 20]  # 大气温度范围
Tgeo_range = [11.5, 10.5, 9.5, 8.5, 7.5, 6.5]  # 平均地热温度范围
df_eps_Tamb = pd.DataFrame(columns=Tamb_range)  # 创建 DataFrame 存储不同 Tamb 下的效率
df_eps_Tgeo = pd.DataFrame(columns=Tgeo_range)  # 创建 DataFrame 存储不同 Tgeo 下的效率

# 计算不同 Tamb 下的效率
eps_Tamb = []
print("变化的大气温度:\n")
for Tamb in Tamb_range:
    i += 1
    ean.analyse(pamb, Tamb)  # 进行情能分析
    eps_Tamb.append(ean.network_data.epsilon)  # 获取效率
    print("案例 %d: Tamb = %.1f °C" % (i, Tamb))

# 保存到数据框
df_eps_Tamb.loc[Tgeo_design] = eps_Tamb
df_eps_Tamb.to_csv('R410A_eps_Tamb.csv')  # 保存数据到 CSV 文件

# 计算不同 Tgeo 下的效率
eps_Tgeo = []
print("\n变化的平均地热温度:\n")
for Tgeo in Tgeo_range:
    i += 1
    # 设置地热进水和回水温度围绕平均值 Tgeo
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    nw.solve('offdesign', init_path=path, design_path=path)  # 求解非设计工况
    ean.analyse(pamb, Tamb_design)  # 进行情能分析
    eps_Tgeo.append(ean.network_data.epsilon)  # 获取效率
    print("案例 %d: Tgeo = %.1f °C" % (i, Tgeo))

# 保存到数据框
df_eps_Tgeo.loc[Tamb_design] = eps_Tgeo
df_eps_Tgeo.to_csv('R410A_eps_Tgeo.csv')  # 保存数据到 CSV 文件

# %% 计算效率 epsilon 和 COP 取决于：
#     - 平均地热温度 Tgeo
#     - 加热系统温度 Ths

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 平均地热温度范围
Ths_range = [42.5, 37.5, 32.5]  # 加热系统温度范围
df_eps_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 创建 DataFrame 存储不同 Tgeo 和 Ths 下的效率
df_cop_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 创建 DataFrame 存储不同 Tgeo 和 Ths 下的 COP

# 计算不同 Tgeo 和 Ths 下的效率和 COP
print("\n变化的平均地热温度和加热系统温度:\n")
for Tgeo in Tgeo_range:
    # 设置地热进水和回水温度围绕平均值 Tgeo
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    epsilon = []
    cop = []
    for Ths in Ths_range:
        i += 1
        # 设置加热系统进水和回水温度围绕平均值 Ths
        cd_hs_feed.set_attr(T=Ths + 2.5)
        hs_ret_hsp.set_attr(T=Ths - 2.5)
        if Ths == Ths_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 求解非设计工况
        else:
            nw.solve('offdesign', design_path=path)  # 求解非设计工况
        ean.analyse(pamb, Tamb_design)  # 进行情能分析
        epsilon.append(ean.network_data.epsilon)  # 获取效率
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算 COP
        print("案例 %d: Tgeo = %.1f °C, Ths = %.1f °C" % (i, Tgeo, Ths))

    # 保存到数据框
    df_eps_Tgeo_Ths.loc[Tgeo] = epsilon
    df_cop_Tgeo_Ths.loc[Tgeo] = cop

df_eps_Tgeo_Ths.to_csv('R410A_eps_Tgeo_Ths.csv')  # 保存数据到 CSV 文件
df_cop_Tgeo_Ths.to_csv('R410A_cop_Tgeo_Ths.csv')  # 保存数据到 CSV 文件

# %% 计算效率 epsilon 和 COP 取决于：
#     - 平均地热温度 Tgeo
#     - 加热负荷 Q_cond

# 重置加热系统温度为设计值
cd_hs_feed.set_attr(T=40)
hs_ret_hsp.set_attr(T=35)

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 平均地热温度范围
Q_range = np.array([4.3e3, 4e3, 3.7e3, 3.4e3, 3.1e3, 2.8e3])  # 加热负荷范围
df_cop_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 创建 DataFrame 存储不同 Tgeo 和 Q 下的 COP
df_eps_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 创建 DataFrame 存储不同 Tgeo 和 Q 下的效率

# 计算不同 Tgeo 和 Q 下的效率和 COP
print("\n变化的平均地热温度和加热负荷:\n")
for Tgeo in Tgeo_range:
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    cop = []
    epsilon = []
    for Q in Q_range:
        i += 1
        cd.set_attr(Q=-Q)  # 设置冷凝器的热量需求
        if Q == Q_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 求解非设计工况
        else:
            nw.solve('offdesign', design_path=path)  # 求解非设计工况
        ean.analyse(pamb, Tamb_design)  # 进行情能分析
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算 COP
        epsilon.append(ean.network_data.epsilon)  # 获取效率
        print("案例 %s: Tgeo = %.1f °C, Q = -%.1f kW" % (i, Tgeo, Q/1000))

    # 保存到数据框
    df_cop_Tgeo_Q.loc[Tgeo] = cop
    df_eps_Tgeo_Q.loc[Tgeo] = epsilon

df_cop_Tgeo_Q.to_csv('R410A_cop_Tgeo_Q.csv')  # 保存数据到 CSV 文件
df_eps_Tgeo_Q.to_csv('R410A_eps_Tgeo_Q.csv')  # 保存数据到 CSV 文件