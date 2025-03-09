# TESPy Valve类 
# 阀门（Valve）组件在TESPy中用于节流流体而不改变其焓值。
# 这意味着通过阀门后，流体的压力会发生变化
# 但其热力学状态（如温度和熵）保持不变

# 方程
# 必需方程
# 1. fluid_func: 该函数确保进出阀门的流体成分一致。
# 2. mass_flow_func: 该函数保证质量流量守恒，即进入阀门的质量流量等于离开阀门的质量流量。

# 可选方程：这些方程可以根据具体的设计需求选择性地启用：
# 1. pr_func: 计算压力比（出口压力与入口压力之比），
# pr = p_out / p_in
# 2. zeta_func: 计算几何无关摩擦系数 ，这是一个与阀门设计相关的参数，通常表示为管道直径的四次幂的倒数乘以某个常数值。
# 3. dp_char_func: 使用特性曲线来描述压降与质量流量之间的关系。

# 接口
# in1: 阀门的一个进口接口。
# out1: 阀门的一个出口接口。

# 参数
# - label: 组件的标签字符串，用于标识特定的阀门实例。
# - design 和 offdesign: 这些列表分别定义了在设计工况和非设计工况下使用的参数集。
# - design_path: 设计案例文件的路径，包含该组件在设计点下的性能数据。
# - local_offdesign 和 local_design: 这两个布尔变量决定了在全局设计计算或非设计计算时如何处理当前组件。
# - char_warnings: 是否忽略默认特性曲线使用时发出的警告信息。
# - printout: 决定是否将此组件的数据包含在网络结果打印输出中。

# 物理参数
# -pr: 出口压力与入口压力的比值。它可以是一个固定值、字典或者一个可变参数。
# -zeta: 几何无关摩擦系数，表示为管道直径的四次幂的倒数乘以某个常数值。它也可以是一个固定值、字典或者一个可变参数。
# -dp_char (Characteristic Line for Pressure Drop): 描述 压降 与 质量流量 之间关系的特性曲线对象。这种曲线可以用来模拟阀门的非线性行为。

from tespy.components import Sink, Source, Valve  # 导入TESPy中的Sink、Source和Valve组件
from tespy.connections import Connection  # 导入TESPy中的Connection类
from tespy.networks import Network  # 导入TESPy中的Network类
import shutil  # 导入shutil模块，用于删除目录

nw = Network(p_unit='bar', T_unit='C', iterinfo=False)  # 创建一个网络对象，设置压力单位为巴（bar），温度单位为摄氏度（C），并且关闭迭代信息显示

so = Source('source')  # 创建一个源组件，并命名为'source'
si = Sink('sink')  # 创建一个汇组件，并命名为'sink'
v = Valve('valve')  # 创建一个阀门组件，并命名为'valve'

so_v = Connection(so, 'out1', v, 'in1')  # 创建从源组件到阀门组件的连接，源组件的出口1连接到阀门组件的入口1
v_si = Connection(v, 'out1', si, 'in1')  # 创建从阀门组件到汇组件的连接，阀门组件的出口1连接到汇组件的入口1

nw.add_conns(so_v, v_si)  # 将上述两个连接添加到网络中

v.set_attr(offdesign=['zeta'])  # 设置阀门组件在非设计工况下的参数为几何无关摩擦系数(zeta)

# 设置源到阀门的连接属性：流体为纯甲烷(CH4)，质量流量为1 kg/s，温度为50°C，压力为80 bar，并将质量流量(m)设为设计参数
so_v.set_attr(fluid={'CH4': 1}, m=1, T=50, p=80, design=['m'])  
v_si.set_attr(p=15)  # 设置阀门到汇的连接属性：出口压力为15 bar

nw.solve('design')  # 解决设计工况下的网络
nw.save('tmp')  # 将当前网络的状态保存到'tmp'文件夹中

round(v_si.T.val, 1)  # 四舍五入输出阀门到汇的连接处的温度值，保留一位小数
round(v.pr.val, 3)  # 四舍五入输出阀门的压力比(pr)，保留三位小数

so_v.set_attr(p=70)  # 修改源到阀门的连接属性：入口压力改为70 bar
nw.solve('offdesign', design_path='tmp')  # 在非设计工况下解决网络，并使用之前保存的设计点数据
round(so_v.m.val, 1)  # 四舍五入输出源到阀门的连接处的质量流量值，保留一位小数
round(v_si.T.val, 1)  # 四舍五入输出阀门到汇的连接处的温度值，保留一位小数

shutil.rmtree('./tmp', ignore_errors=True)  # 删除'tmp'文件夹及其所有内容，如果存在的话

# 压力比 最大 = 1 ，最小值 = 1e-4
# 几何无关摩擦系数 最大 = 1e15 ，最小值 = 0

# 阀门两端 热力学状态（如温度和熵）保持不变

# 压降与质量流量之间的特性曲线方程
# self.inl[0].p.val_SI - self.outl[0].p.val_SI  = self.dp_char.char_func.evaluate(expr)

# 不可逆熵 = 质量流量 * （出口熵 - 入口熵）
# self.S_irr = self.inl[0].m.val_SI * (self.outl[0].s.val_SI - self.inl[0].s.val_SI)