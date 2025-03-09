# 使用TESPy库创建 地源热泵 模型

from tespy.components import Compressor  # 导入压缩机组件
from tespy.components import Condenser   # 导入冷凝器组件
from tespy.components import CycleCloser # 导入循环闭合器组件
from tespy.components import HeatExchanger # 导入换热器组件
from tespy.components import Sink         # 导入汇流点组件（用于排出流体）
from tespy.components import Source       # 导入源组件（用于引入流体）
from tespy.components import Valve        # 导入阀门组件
from tespy.components import Pump         # 导入泵组件

from tespy.connections import Connection  # 导入连接类，用于连接组件
from tespy.connections import Bus         # 导入总线类，用于将多个连接组合在一起

from tespy.networks import Network       # 导入网络类，用于定义整个热力系统

from tespy.tools.characteristics import CharLine  # 导入特性曲线类
from tespy.tools.characteristics import load_default_char as ldc  # 导入加载默认特性的函数

from tespy.tools import ExergyAnalysis    # 导入能流分析工具

import numpy as np                        # 导入NumPy库，用于数值计算

from plotly.offline import plot           # 导入Plotly离线绘图功能
import plotly.graph_objects as go         # 导入Plotly图形对象

from fluprodia import FluidPropertyDiagram # 导入Fluprodia库，用于绘制工质性质图表

import pandas as pd                       # 导入Pandas库，用于数据处理和分析

import matplotlib.pyplot as plt           # 导入Matplotlib库，用于绘制静态图表

# %% network
pamb = 1.013  # 环境压力 (bar)
Tamb = 2.8    # 环境温度 (°C)

# 地热平均温度（地热回路进水和回水的平均温度）
Tgeo = 9.5

# 创建网络实例，设置单位制和流体类型
nw = Network(fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s')

# %% components

# 循环闭合器，用于闭合循环路径
cc = CycleCloser('cycle closer')

# 热泵系统组件
cd = Condenser('condenser')      # 冷凝器
va = Valve('valve')              # 阀门
ev = HeatExchanger('evaporator') # 蒸发器
cp = Compressor('compressor')    # 压缩机

# 地热换热器系统组件
gh_in = Source('ground heat feed flow')     # 地热回路进水流入口
gh_out = Sink('ground heat return flow')    # 地热回路过水流出口
ghp = Pump('ground heat loop pump')         # 地热回路泵

# 加热系统组件
hs_feed = Sink('heating system feed flow')   # 加热系统进水流入口
hs_ret = Source('heating system return flow') # 加热系统回水流出口
hsp = Pump('heating system pump')             # 加热系统泵

# %% connections

# 热泵系统连接
cc_cd = Connection(cc, 'out1', cd, 'in1')  # 循环闭合器 -> 冷凝器
cd_va = Connection(cd, 'out1', va, 'in1')  # 冷凝器 -> 阀门
va_ev = Connection(va, 'out1', ev, 'in2')  # 阀门 -> 蒸发器的二次侧入口
ev_cp = Connection(ev, 'out2', cp, 'in1')  # 蒸发器的二次侧出口 -> 压缩机
cp_cc = Connection(cp, 'out1', cc, 'in1')  # 压缩机 -> 循环闭合器
nw.add_conns(cc_cd, cd_va, va_ev, ev_cp, cp_cc)

# 地热换热器系统连接
gh_in_ghp = Connection(gh_in, 'out1', ghp, 'in1')  # 地热回路进水流入口 -> 地热回路泵
ghp_ev = Connection(ghp, 'out1', ev, 'in1')       # 地热回路泵 -> 蒸发器的一次侧入口
ev_gh_out = Connection(ev, 'out1', gh_out, 'in1')   # 蒸发器的一次侧出口 -> 地热回路过水流出口
nw.add_conns(gh_in_ghp, ghp_ev, ev_gh_out)

# 加热系统连接
hs_ret_hsp = Connection(hs_ret, 'out1', hsp, 'in1')  # 加热系统回水流出口 -> 加热系统泵
hsp_cd = Connection(hsp, 'out1', cd, 'in2')          # 加热系统泵 -> 冷凝器的二次侧入口
cd_hs_feed = Connection(cd, 'out2', hs_feed, 'in1')  # 冷凝器的二次侧出口 -> 加热系统进水流入口
nw.add_conns(hs_ret_hsp, hsp_cd, cd_hs_feed)

# %% component parametrization

# 冷凝器参数设置
cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
# 蒸发器参数设置
kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)
ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=5,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
# 压缩机参数设置
cp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
# 加热系统泵参数设置
hsp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])
# 地热回路泵参数设置
ghp.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])

# %% connection parametrization

# 热泵系统连接参数设置
cc_cd.set_attr(fluid={'NH3': 1})  # 循环闭合器到冷凝器的流体为氨
ev_cp.set_attr(Td_bp=3)           # 蒸发器二次侧出口与沸腾点温差为3°C

# 地热换热器系统连接参数设置
gh_in_ghp.set_attr(T=Tgeo + 1.5, p=1.5, fluid={'water': 1})  # 地热回路进水流入口温度和压力
ev_gh_out.set_attr(T=Tgeo - 1.5, p=1.5)                      # 地热回路过水流出口温度和压力

# 加热系统连接参数设置
cd_hs_feed.set_attr(T=40, p=2, fluid={'water': 1})  # 加热系统进水流入口温度和压力
hs_ret_hsp.set_attr(T=35, p=2)                      # 加热系统回水流出口温度和压力

# 初始值设置
ev_cp.set_attr(p0=5)  # 蒸发器二次侧出口初始压力
cc_cd.set_attr(p0=18) # 循环闭合器到冷凝器初始压力

# %% create busses

# 特性函数用于电机效率
x = np.array([0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4])
y = np.array([0, 0.86, 0.9, 0.93, 0.95, 0.96, 0.95, 0.93])

# 功率总线
char = CharLine(x=x, y=y)
power = Bus('power input')
power.add_comps(
    {'comp': cp, 'char': char, 'base': 'bus'},  # 压缩机功率
    {'comp': ghp, 'char': char, 'base': 'bus'}, # 地热回路泵功率
    {'comp': hsp, 'char': char, 'base': 'bus'}  # 加热系统泵功率
)

# 消费热量总线
heat_cons = Bus('heating system')
heat_cons.add_comps({'comp': hs_ret, 'base': 'bus'}, {'comp': hs_feed})

# 地热热量总线
heat_geo = Bus('geothermal heat')
heat_geo.add_comps({'comp': gh_in, 'base': 'bus'}, {'comp': gh_out})

nw.add_busses(power, heat_cons, heat_geo)

# %% key parameter

cd.set_attr(Q=-4e3)  # 冷凝器释放的热量为-4000 kW（负号表示放热）

# %% design calculation

path = 'NH3'
nw.solve('design')
# 或者使用：
# nw.solve('design', init_path=path)
print("\n##### DESIGN CALCULATION #####\n")
nw.print_results()
nw.save(path)

# %% plot h_log(p) diagram

# 生成绘图数据
result_dict = {}
result_dict.update({ev.label: ev.get_plotting_data()[2]})
result_dict.update({cp.label: cp.get_plotting_data()[1]})
result_dict.update({cd.label: cd.get_plotting_data()[1]})
result_dict.update({va.label: va.get_plotting_data()[1]})

# 创建对数焓-压力 (h-log(p)) 图
diagram = FluidPropertyDiagram('NH3')
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

for key, data in result_dict.items():
    result_dict[key]['datapoints'] = diagram.calc_individual_isoline(**data)

diagram.calc_isolines()

fig, ax = plt.subplots(1, figsize=(16, 10))
diagram.draw_isolines(fig, ax, 'logph', x_min=0, x_max=2100, y_min=1e0, y_max=2e2)

for key in result_dict.keys():
    datapoints = result_dict[key]['datapoints']
    ax.plot(datapoints['h'], datapoints['p'], color='#ff0000')
    ax.scatter(datapoints['h'][0], datapoints['p'][0], color='#ff0000')

plt.tight_layout()
plt.show()
#fig.savefig('NH3_logph.svg')

# %% exergy analysis

ean = ExergyAnalysis(network=nw, E_F=[power, heat_geo], E_P=[heat_cons])
ean.analyse(pamb, Tamb)
print("\n##### EXERGY ANALYSIS #####\n")
ean.print_results()

# 创建桑基图
links, nodes = ean.generate_plotly_sankey_input()
fig = go.Figure(go.Sankey(
    arrangement="snap",
    node={
        "label": nodes,
        'pad': 11,
        'color': 'orange'},
    link=links))
plt.show()
#plot(fig, filename='NH3_sankey.html')

# %% plot exergy destruction

# 创建数据用于条形图
comps = ['E_F']
E_F = ean.network_data.E_F
# 最上面的条
E_D = [0]  # 没有在顶部栏的能量破坏
E_P = [E_F]  # 添加E_F作为顶部条
for comp in ean.component_data.index:
    # 只绘制能量破坏大于1 W的组件
    if ean.component_data.E_D[comp] > 1:
        comps.append(comp)
        E_D.append(ean.component_data.E_D[comp])
        E_F = E_F - ean.component_data.E_D[comp]
        E_P.append(E_F)
comps.append("E_P")
E_D.append(0)
E_P.append(E_F)

# 创建数据框并保存数据
df_comps = pd.DataFrame(columns=comps)
df_comps.loc["E_D"] = E_D
df_comps.loc["E_P"] = E_P
df_comps.to_csv('NH3_E_D.csv')

# %% further calculations

print("\n#### FURTHER CALCULATIONS ####\n")
# 关闭迭代信息显示
nw.set_attr(iterinfo=False)
# 进行非设计工况测试
nw.solve('offdesign', design_path=path)

# %% 计算 epsilon 取决于:
#    - 环境温度 Tamb
#    - 地热平均温度 Tgeo

Tamb_design = Tamb  # 设计环境温度
Tgeo_design = Tgeo  # 设计地热平均温度
i = 0  # 案例编号

# 创建数据范围和数据框
Tamb_range = [1, 4, 8, 12, 16, 20]  # 环境温度范围
Tgeo_range = [11.5, 10.5, 9.5, 8.5, 7.5, 6.5]  # 地热平均温度范围
df_eps_Tamb = pd.DataFrame(columns=Tamb_range)  # 存储不同 Tamb 下的 epsilon
df_eps_Tgeo = pd.DataFrame(columns=Tgeo_range)  # 存储不同 Tgeo 下的 epsilon

# 根据 Tamb 计算 epsilon
eps_Tamb = []
print("变化环境温度:\n")
for Tamb in Tamb_range:
    i += 1
    ean.analyse(pamb, Tamb)  # 进行能流分析
    eps_Tamb.append(ean.network_data.epsilon)  # 获取并存储 epsilon
    print("案例 %d: Tamb = %.1f °C" % (i, Tamb))

# 将结果保存到数据框并导出为 CSV 文件
df_eps_Tamb.loc[Tgeo_design] = eps_Tamb
df_eps_Tamb.to_csv('NH3_eps_Tamb.csv')

# 根据 Tgeo 计算 epsilon
eps_Tgeo = []
print("\n变化地热平均温度:\n")
for Tgeo in Tgeo_range:
    i += 1
    # 设置地热回路进水和回水温度
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
    ean.analyse(pamb, Tamb_design)  # 进行能流分析
    eps_Tgeo.append(ean.network_data.epsilon)  # 获取并存储 epsilon
    print("案例 %d: Tgeo = %.1f °C" % (i, Tgeo))

# 将结果保存到数据框并导出为 CSV 文件
df_eps_Tgeo.loc[Tamb_design] = eps_Tgeo
df_eps_Tgeo.to_csv('NH3_eps_Tgeo.csv')

# %% 计算 epsilon 和 COP 取决于:
#     - 地热平均温度 Tgeo
#     - 加热系统温度 Ths

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 地热平均温度范围
Ths_range = [42.5, 37.5, 32.5]  # 加热系统温度范围
df_eps_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 存储不同 Tgeo 和 Ths 下的 epsilon
df_cop_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 存储不同 Tgeo 和 Ths 下的 COP

# 计算 epsilon 和 COP
print("\n变化地热平均温度和加热系统温度:\n")
for Tgeo in Tgeo_range:
    # 设置地热回路进水和回水温度
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    epsilon = []
    cop = []
    for Ths in Ths_range:
        i += 1
        # 设置加热系统进水和回水温度
        cd_hs_feed.set_attr(T=Ths + 2.5)
        hs_ret_hsp.set_attr(T=Ths - 2.5)
        if Ths == Ths_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
        else:
            nw.solve('offdesign', design_path=path)  # 解算网络
        ean.analyse(pamb, Tamb_design)  # 进行能流分析
        epsilon.append(ean.network_data.epsilon)  # 获取并存储 epsilon
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算并存储 COP
        print("案例 %d: Tgeo = %.1f °C, Ths = %.1f °C" % (i, Tgeo, Ths))

    # 将结果保存到数据框并导出为 CSV 文件
    df_eps_Tgeo_Ths.loc[Tgeo] = epsilon
    df_cop_Tgeo_Ths.loc[Tgeo] = cop

df_eps_Tgeo_Ths.to_csv('NH3_eps_Tgeo_Ths.csv')
df_cop_Tgeo_Ths.to_csv('NH3_cop_Tgeo_Ths.csv')

# %% calculate epsilon and COP depending on:
#     - mean geothermal temperature Tgeo
#     - heating load Q_cond

# 重置加热系统温度为设计值
cd_hs_feed.set_attr(T=40)
hs_ret_hsp.set_attr(T=35)

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 地热平均温度范围
Q_range = np.array([4.3e3, 4e3, 3.7e3, 3.4e3, 3.1e3, 2.8e3])  # 加热负荷范围 (kW)
df_cop_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 存储不同 Tgeo 和 Q 下的 COP
df_eps_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 存储不同 Tgeo 和 Q 下的 epsilon

# 计算 epsilon 和 COP
print("\n变化地热平均温度和加热负荷:\n")
for Tgeo in Tgeo_range:
    gh_in_ghp.set_attr(T=Tgeo + 1.5)  # 设置地热回路进水温度
    ev_gh_out.set_attr(T=Tgeo - 1.5)   # 设置地热回路过水温度
    cop = []
    epsilon = []
    for Q in Q_range:
        i += 1
        cd.set_attr(Q=-Q)  # 设置冷凝器的热量（负号表示放热）
        if Q == Q_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
        else:
            nw.solve('offdesign', design_path=path)  # 解算网络
        ean.analyse(pamb, Tamb_design)  # 进行能流分析
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算并存储 COP
        epsilon.append(ean.network_data.epsilon)  # 获取并存储 epsilon
        print("案例 %s: Tgeo = %.1f °C, Q = -%.1f kW" % (i, Tgeo, Q/1000))

    # 将结果保存到数据框并导出为 CSV 文件
    df_cop_Tgeo_Q.loc[Tgeo] = cop
    df_eps_Tgeo_Q.loc[Tgeo] = epsilon

df_cop_Tgeo_Q.to_csv('NH3_cop_Tgeo_Q.csv')
df_eps_Tgeo_Q.to_csv('NH3_eps_Tgeo_Q.csv')


# %% further calculations

print("\n#### FURTHER CALCULATIONS ####\n")
# 关闭迭代信息显示
nw.set_attr(iterinfo=False)
# 进行非设计工况测试
nw.solve('offdesign', design_path=path)

# %% 计算 epsilon 取决于:
#    - 环境温度 Tamb
#    - 地热平均温度 Tgeo

Tamb_design = Tamb  # 设计环境温度
Tgeo_design = Tgeo  # 设计地热平均温度
i = 0  # 案例编号

# 创建数据范围和数据框
Tamb_range = [1, 4, 8, 12, 16, 20]  # 环境温度范围
Tgeo_range = [11.5, 10.5, 9.5, 8.5, 7.5, 6.5]  # 地热平均温度范围
df_eps_Tamb = pd.DataFrame(columns=Tamb_range)  # 存储不同 Tamb 下的 epsilon
df_eps_Tgeo = pd.DataFrame(columns=Tgeo_range)  # 存储不同 Tgeo 下的 epsilon

# 根据 Tamb 计算 epsilon
eps_Tamb = []
print("变化环境温度:\n")
for Tamb in Tamb_range:
    i += 1
    ean.analyse(pamb, Tamb)  # 进行能流分析
    eps_Tamb.append(ean.network_data.epsilon)  # 获取并存储 epsilon
    print("案例 %d: Tamb = %.1f °C" % (i, Tamb))

# 将结果保存到数据框并导出为 CSV 文件
df_eps_Tamb.loc[Tgeo_design] = eps_Tamb
df_eps_Tamb.to_csv('NH3_eps_Tamb.csv')

# 根据 Tgeo 计算 epsilon
eps_Tgeo = []
print("\n变化地热平均温度:\n")
for Tgeo in Tgeo_range:
    i += 1
    # 设置地热回路进水和回水温度
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
    ean.analyse(pamb, Tamb_design)  # 进行能流分析
    eps_Tgeo.append(ean.network_data.epsilon)  # 获取并存储 epsilon
    print("案例 %d: Tgeo = %.1f °C" % (i, Tgeo))

# 将结果保存到数据框并导出为 CSV 文件
df_eps_Tgeo.loc[Tamb_design] = eps_Tgeo
df_eps_Tgeo.to_csv('NH3_eps_Tgeo.csv')

# %% 计算 epsilon 和 COP 取决于:
#     - 地热平均温度 Tgeo
#     - 加热系统温度 Ths

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 地热平均温度范围
Ths_range = [42.5, 37.5, 32.5]  # 加热系统温度范围
df_eps_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 存储不同 Tgeo 和 Ths 下的 epsilon
df_cop_Tgeo_Ths = pd.DataFrame(columns=Ths_range)  # 存储不同 Tgeo 和 Ths 下的 COP

# 计算 epsilon 和 COP
print("\n变化地热平均温度和加热系统温度:\n")
for Tgeo in Tgeo_range:
    # 设置地热回路进水和回水温度
    gh_in_ghp.set_attr(T=Tgeo + 1.5)
    ev_gh_out.set_attr(T=Tgeo - 1.5)
    epsilon = []
    cop = []
    for Ths in Ths_range:
        i += 1
        # 设置加热系统进水和回水温度
        cd_hs_feed.set_attr(T=Ths + 2.5)
        hs_ret_hsp.set_attr(T=Ths - 2.5)
        if Ths == Ths_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
        else:
            nw.solve('offdesign', design_path=path)  # 解算网络
        ean.analyse(pamb, Tamb_design)  # 进行能流分析
        epsilon.append(ean.network_data.epsilon)  # 获取并存储 epsilon
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算并存储 COP
        print("案例 %d: Tgeo = %.1f °C, Ths = %.1f °C" % (i, Tgeo, Ths))

    # 将结果保存到数据框并导出为 CSV 文件
    df_eps_Tgeo_Ths.loc[Tgeo] = epsilon
    df_cop_Tgeo_Ths.loc[Tgeo] = cop

df_eps_Tgeo_Ths.to_csv('NH3_eps_Tgeo_Ths.csv')
df_cop_Tgeo_Ths.to_csv('NH3_cop_Tgeo_Ths.csv')

# %% calculate epsilon and COP depending on:
#     - mean geothermal temperature Tgeo
#     - heating load Q_cond

# 重置加热系统温度为设计值
cd_hs_feed.set_attr(T=40)
hs_ret_hsp.set_attr(T=35)

# 创建数据范围和数据框
Tgeo_range = [10.5, 8.5, 6.5]  # 地热平均温度范围
Q_range = np.array([4.3e3, 4e3, 3.7e3, 3.4e3, 3.1e3, 2.8e3])  # 加热负荷范围 (kW)
df_cop_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 存储不同 Tgeo 和 Q 下的 COP
df_eps_Tgeo_Q = pd.DataFrame(columns=Q_range)  # 存储不同 Tgeo 和 Q 下的 epsilon

# 计算 epsilon 和 COP
print("\n变化地热平均温度和加热负荷:\n")
for Tgeo in Tgeo_range:
    gh_in_ghp.set_attr(T=Tgeo + 1.5)  # 设置地热回路进水温度
    ev_gh_out.set_attr(T=Tgeo - 1.5)   # 设置地热回路过水温度
    cop = []
    epsilon = []
    for Q in Q_range:
        i += 1
        cd.set_attr(Q=-Q)  # 设置冷凝器的热量（负号表示放热）
        if Q == Q_range[0]:
            nw.solve('offdesign', init_path=path, design_path=path)  # 解算网络
        else:
            nw.solve('offdesign', design_path=path)  # 解算网络
        ean.analyse(pamb, Tamb_design)  # 进行能流分析
        cop += [abs(cd.Q.val) / (cp.P.val + ghp.P.val + hsp.P.val)]  # 计算并存储 COP
        epsilon.append(ean.network_data.epsilon)  # 获取并存储 epsilon
        print("案例 %s: Tgeo = %.1f °C, Q = -%.1f kW" % (i, Tgeo, Q/1000))

    # 将结果保存到数据框并导出为 CSV 文件
    df_cop_Tgeo_Q.loc[Tgeo] = cop
    df_eps_Tgeo_Q.loc[Tgeo] = epsilon

df_cop_Tgeo_Q.to_csv('NH3_cop_Tgeo_Q.csv')
df_eps_Tgeo_Q.to_csv('NH3_eps_Tgeo_Q.csv')