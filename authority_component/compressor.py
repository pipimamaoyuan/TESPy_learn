# TESPy 压缩机compressor

# 轴流式或径流式的压缩机。压缩机是涡轮机械的一种，主要用于提高气体的压力。
# 在TESPy中，压缩机类继承自`Turbomachine`基类，并且包含了特定于压缩机的功能和特性。

# 必要方程，这些方程必须满足，因为它们定义了基本的物理约束条件：
# 1. fluid_func: 定义流体组成。
# 2. mass_flow_func: 定义质量流量守恒。

# 可选方程
# 1. pr_func: 压力比函数，计算出口压力与入口压力之比。
# 2. energy_balance_func: 能量平衡方程，描述能量转换过程中的能量守恒。
# 3. eta_s_func: 等熵效率方程，表示实际效率与理想等熵过程的比率。
# 4. eta_s_char_func: 使用特征曲线来描述等熵效率的变化规律。
# 5. char_map_eta_s_func: 利用特性图谱（CharMap）来确定不同工况下的等熵效率。
# 6. char_map_pr_func: 特性图谱也用来确定不同工况下的压力比。

# 进口/出口
# - in1: 单一进口
# - out1: 单一出口

# 参数

# - label: 组件标签
# - design: 设计参数列表
# - offdesign: 非设计参数列表
# - design_path: 设计案例路径
# - local_offdesign: 在设计计算中将此组件视为非设计组件
# - local_desig: 在非设计计算中将此组件视为设计组件
# - char_warnings: 是否忽略默认特征曲线使用警告
# - printout: 包含网络结果打印中的此组件


# - P: 功率，单位为瓦特(W)。
# - eta_s: 等熵效率，无量纲。
# - pr: 出口与入口的压力比，无量纲。
#   压力比 >= 1
# - eta_s_char: 描述等熵效率随某些操作变量变化的特征曲线。
# - char_map: 包含压力比和等熵效率随无量纲质量流量变化的关系图谱。
# - igva: 入口导向叶片角度，单位为度(°)，可变参数。
#  -90 <= igva <= 90, 默认值为0度


from tespy.components import Sink, Source, Compressor  # 导入TESPy中的Sink、Source和Compressor组件
from tespy.connections import Connection  # 导入TESPy中的Connection类，用于连接组件
from tespy.networks import Network  # 导入TESPy中的Network类，用于创建热力网络
import shutil  # 导入shutil模块，用于删除文件夹

# 创建一个热力网络对象，并设置单位：压力(bar)、温度(摄氏度C)、比焓(kJ/kg)、比体积(l/s)
nw = Network(p_unit='bar', T_unit='C', h_unit='kJ / kg', v_unit='l / s', iterinfo=False)

# 创建一个汇流器（Sink）组件，命名为'sink'
si = Sink('sink')

# 创建一个源（Source）组件，命名为'source'
so = Source('source')

# 创建一个压缩机（Compressor）组件，命名为'compressor'
comp = Compressor('compressor')

# 创建从源到压缩机的进气管道（Connection），命名为'inc'
inc = Connection(so, 'out1', comp, 'in1')

# 创建从压缩机到汇流器的排气管道（Connection），命名为'outg'
outg = Connection(comp, 'out1', si, 'in1')

# 将两个管道添加到热力网络中
nw.add_conns(inc, outg)

# 设置压缩机的设计参数：压力比(pr=5)，等熵效率(eta_s=0.8)，并将等熵效率设为设计参数之一
comp.set_attr(pr=5, eta_s=0.8, design=['eta_s'], offdesign=['char_map_pr', 'char_map_eta_s'])

# 设置进气管道的初始条件：空气作为工作流体，入口压力为1 bar，入口温度为20°C，入口比体积为50 l/s
inc.set_attr(fluid={'air': 1}, p=1, T=20, v=50)

# 解决设计点问题
nw.solve('design')

# 将设计工况保存到'tmp'目录中
nw.save('tmp')

# 计算并输出压缩机在设计点下的功率，四舍五入到整数位
round(comp.P.val, 0)

# 修改进气管道的比体积为45 l/s，模拟非设计工况
inc.set_attr(v=45)

# 将入口导向叶片角度(igva)设为可变参数，参与非设计计算
comp.set_attr(igva='var')

# 解决非设计点问题，使用之前保存的设计工况路径'tmp'
nw.solve('offdesign', design_path='tmp')

# 计算并输出压缩机在非设计点下的等熵效率，保留两位小数
round(comp.eta_s.val, 2)

# 删除'tmp'目录及其所有内容，清理临时文件
shutil.rmtree('./tmp', ignore_errors=True)

# 等熵效率
# i = self.inl[0]
# o = self.outl[0]
# (o.h.val_SI - i.h.val_SI) * self.eta_s.val = isentropic(i.p.val_SI,i.h.val_SI,o.p.val_SI,i.fluid_data,i.mixing_rule,T0=None) - self.inl[0].h.val_SI

# 等熵效率特征曲线
# i = self.inl[0]
# o = self.outl[0]
# (o.h.val_SI - i.h.val_SI) * self.eta_s.design * self.eta_s_char.char_func.evaluate(expr)
#    = isentropic(i.p.val_SI,i.h.val_SI, o.p.val_SI,i.fluid_data, i.mixing_rule, T0=None) - i.h.val_SI

# 使用特性图谱，计算实际压力比
# def char_map_pr_func(self)

# 使用特性图谱，计算实际等熵效率
# def char_map_eta_s_func(self)

# 出口压力 > = 入口压力
# 出口焓值 > = 入口焓值