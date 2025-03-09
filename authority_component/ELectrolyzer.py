# 使用TESPy库创建 电解槽 模型

from tespy.components import (Sink, Source, Compressor, WaterElectrolyzer)
from tespy.connections import Connection
from tespy.networks import Network
import shutil
import matplotlib.pyplot as plt

# 水电解槽从水中产生氢气和氧气，并消耗电力来完成这一过程
  
# 主要方程
# 必需的：
#1. 流体平衡方程 (`fluid_func`): 确保进水、冷却液以及出气成分满足质量守恒定律。
#2. 质量流量平衡方程 (`mass_flow_func`): 保证所有入口的质量流量之和等于出口处的质量流量总和。
#3. 反应器压力平衡方程 (`reactor_pressure_func`)： 控制反应器内部的压力保持一致。
# p_in2 = p_out2 = p_out3

#4. 能量守恒方程 (`energy_balance_func`): 计算整个系统中的能量变化，包括输入功率与热输出之间的关系。
#5. 气体温度平衡方程 (`gas_temperature_func`): 确定生成的氢气和氧气的温度。

# 可选方程：
# 1. 冷却回路相关方程:
#    - 几何无关摩擦系数 (`zeta_func`)
#    - 压力比 (`pr_func`) = self.in1[0].p.val_SI / self.out1[0].p.val.SI
   
# 2. 效率相关方程:
#    - 效率 (`eta_func`)
#    - 特性曲线下的效率 (`eta_char_func`)
   
# 3. 热量交换方程 (`heat_func`): 描述冷却过程中释放或吸收的热量。
# 4. 特定能量消耗方程 (`specific_energy_consumption_func`): 计算每立方米产物所需的电能。

# 进口/出口端口
# 进口:
#   - `in1`: 冷却介质入口
#   - `in2`: 馈水电解质入口
  
# 出口:
#   - `out1`: 冷却介质出口
#   - `out2`: 氧气出口
#   - `out3`: 氢气出口

# 参数说明
# - label: 字符串类型，用于标识组件。
# - design: 列表类型，包含设计工况参数名称（字符串形式）。
# - offdesign: 列表类型，包含非设计工况参数名称（字符串形式）。
# - design_path: 字符串类型，指向设计工况数据文件路径。
# - local_offdesign: 布尔值，表示在设计计算中是否将此组件视为非设计状态处理。
# - local_design: 布尔值，表示在非设计计算中是否将此组件视为设计状态处理。
# - char_warnings: 布尔值，忽略默认特性曲线使用的警告信息。
# - printout: 布尔值，决定是否在网络结果打印时包含此组件的信息。

# - P: 浮点数或字典类型，单位为瓦特(W)，表示输入功率。可以是一个固定的数值，也可以通过变量进行优化。
# - Q: 浮点数或字典类型，单位为瓦特(W)，表示冷却系统的热输出。
# self.Q.val = -self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)

# - e: 浮点数或字典类型，单位为焦耳每立方米(J/m³)，表示电解的能量消耗。同样支持固定值或变量优化。
# self.e.val = self.P.val / self.outl[2].m.val_SI

# - eta: 浮点数或字典类型，范围0到1，表示电解效率（基于H₂高位发热量）。
# self.eta.val = self.e0 / self.e.val

# - eta_char: 字典类型，包含一个CharLine对象，用于描述电解效率随操作条件的变化特性曲线。
# - pr: 浮点数或字典类型，表示冷却回路的压力比。
# - zeta: 浮点数或字典类型，几何无关摩擦系数，用于计算冷却回路中的压力损失。

# 注意事项
# 与其他组件不同的是，水电解槽在其方程中已经内置了对进水及产气成分的要求，因此用户不需要在此指定具体的流体组成。



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
# 电解效率为80%，压力比为0.99，
# 设计参数：电解效率，压力比
# 非设计参数：电解效率特性曲线，几何无关摩擦系数
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

# self.e0 = self.calc_e0()
# 调用 calc_e0 方法计算标准电解能，标准电解能是电解水生成一立方米氢气所需的理论能量，单位通常为焦耳每立方米 (J/m³)

# 电解槽的电解效率 eta = 氢气出口的质量流量 * 标准电解能 / 输入功率
# self.P.val * self.eta.val - self.outl[2].m.val_SI * self.e0

# 冷却系统的热输出 Q = 冷却水的质量流量 * 比热容 * 温度变化
# self.Q.val - self.inl[0].m.val_SI * (self.inl[0].h.val_SI - self.outl[0].h.val_SI)

# 总线 bus
# 假设有一个总线对象 bus，其参数 bus['param'] 设置为 'P'，那么 bus_func 将计算并返回水电解槽的输入功率 P。
# 如果 bus['param'] 设置为 'Q'，那么 bus_func 将计算并返回冷却系统的热量转移值 -self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI )