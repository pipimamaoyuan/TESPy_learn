# -*- coding: utf-8 -*-
# 使用TESPy库创建 电解槽 模型

from tespy.components import (Sink, Source, Compressor, WaterElectrolyzer)
from tespy.connections import Connection
from tespy.networks import Network
import shutil
import matplotlib.pyplot as plt

# 创建一个网络对象，设置温度单位为摄氏度，压力单位为巴，体积流量单位为升/秒，并关闭迭代信息显示
nw = Network(T_unit='C', p_unit='bar', v_unit='l / s', iterinfo=False)

# 创建源组件：进水、氧气汇流点、氢气汇流点、冷却水源和冷却水汇流点
fw = Source('feed water')          # 进水源
oxy = Sink('oxygen sink')           # 氧气汇流点
hydro = Sink('hydrogen sink')       # 氢气汇流点
cw_cold = Source('cooling water source')  # 冷却水源
cw_hot = Sink('cooling water sink')     # 冷却水汇流点

# 创建压缩机组件，设置等熵效率为0.9
comp = Compressor('compressor', eta_s=0.9)

# 创建水电解槽组件
el = WaterElectrolyzer('electrolyzer')


# 创建连接：
# 进水 -> 水电解槽（进水口2）
fw_el = Connection(fw, 'out1', el, 'in2')
# 水电解槽（出水口2）-> 氧气汇流点
el_o = Connection(el, 'out2', oxy, 'in1')
# 水电解槽（出水口3）-> 压缩机（入口）
el_cmp = Connection(el, 'out3', comp, 'in1')
# 压缩机（出口）-> 氢气汇流点
cmp_h = Connection(comp, 'out1', hydro, 'in1')
# 冷却水源 -> 水电解槽（进水口1）
cw_el = Connection(cw_cold, 'out1', el, 'in1')
# 水电解槽（出水口1）-> 冷却水汇流点
el_cw = Connection(el, 'out1', cw_hot, 'in1')

# 将所有连接添加到网络中
nw.add_conns(fw_el, el_o, el_cmp, cmp_h, cw_el, el_cw)

# 设置连接的参数：
# 进水 -> 水电解槽（进水口2），压力为10 bar，温度为15°C
fw_el.set_attr(p=10, T=15)
# 冷却水源 -> 水电解槽（进水口1），压力为5 bar，温度为15°C，流体组成为纯水
cw_el.set_attr(p=5, T=15, fluid={'H2O': 1})
# 水电解槽（出水口1）-> 冷却水汇流点，温度为45°C
el_cw.set_attr(T=45)
# 压缩机（出口）-> 氢气汇流点，压力为25 bar
cmp_h.set_attr(p=25)
# 水电解槽（出水口3）-> 压缩机（入口），体积流量为100 l/s，温度为50°C
el_cmp.set_attr(v=100, T=50)

# 设置水电解槽的参数：
# 电解效率为80%，压力比为0.99，设计参数包括电解效率和压力比，
# 非设计参数包括电解效率特性曲线和几何无关摩擦系数
el.set_attr(eta=0.8, pr=0.99, design=['eta', 'pr'], offdesign=['eta_char', 'zeta'])

# 设置压缩机的等熵效率为85%
comp.set_attr(eta_s=0.85)

# 设计网络，求解设计工况
nw.solve('design')

# 保存设计工况的结果到临时文件夹'tmp'
nw.save('tmp')

# 计算并打印特定能量消耗与实际功率之比，预期值约为0.8
print(round(el.e0 / el.P.val * el_cmp.m.val_SI, 1))  # 输出: 0.8

# 获取设计工况下的功率，并转换为兆瓦（MW）
P_design = el.P.val / 1e6
print(round(P_design, 1))  # 输出: 13.2

# 在非设计工况下求解网络，使用之前保存的设计工况结果
nw.solve('offdesign', design_path='tmp')

# 打印电解槽在非设计工况下的电解效率，预期值约为0.8
print(round(el.eta.val, 1))  # 输出: 0.8

# 清除压缩机的体积流量设定，改为根据其他条件自动计算
el_cmp.set_attr(v=None)

# 设置新的功率值为设计功率的20%
el.set_attr(P=P_design * 1e6 * 0.2)

# 再次在非设计工况下求解网络
nw.solve('offdesign', design_path='tmp')

# 打印电解槽在新功率下的电解效率，预期值约为0.84
print(round(el.eta.val, 2))  # 输出: 0.84

# 删除临时文件夹'tmp'及其内容
shutil.rmtree('./tmp', ignore_errors=True)

# 可视化部分
fig, axs = plt.subplots(3, 1, figsize=(10, 15))

# 绘制电解槽的电解效率
axs[0].plot([el.eta.design], [el.eta.val], marker='o', linestyle='-')
axs[0].set_title('Electrolysis Efficiency')
axs[0].set_xlabel('Design Efficiency')
axs[0].set_ylabel('Actual Efficiency')
axs[0].grid(True)

# 绘制压缩机的压力比
axs[1].plot([comp.pr.design], [comp.pr.val], marker='o', linestyle='-')
axs[1].set_title('Compressor Pressure Ratio')
axs[1].set_xlabel('Design Pressure Ratio')
axs[1].set_ylabel('Actual Pressure Ratio')
axs[1].grid(True)

# 绘制冷却水的温度变化
axs[2].plot([cw_el.T.design], [el_cw.T.val], marker='o', linestyle='-')
axs[2].set_title('Cooling Water Temperature Change')
axs[2].set_xlabel('Inlet Temperature (°C)')
axs[2].set_ylabel('Outlet Temperature (°C)')
axs[2].grid(True)

plt.tight_layout()
plt.show()