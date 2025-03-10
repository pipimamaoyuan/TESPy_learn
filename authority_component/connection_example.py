# TESPy 中 Connection

# `Connection` 类是 TESPy 库中用于表示组件之间流体属性的数据容器。
# 通过 `Connection` 对象，可以定义和管理两个组件之间的流体状态信息，
# 包括质量流量、压力、焓值、温度等。

# 参数
# 基本参数:
# `label`: 组件标签，字符串类型。
# `design`: 设计工况参数列表，字符串形式。
# `offdesign`: 非设计工况参数列表，字符串形式。
# `design_path`: 设计案例路径，字符串形式。
# `local_offdesign`: 在设计计算中是否将此组件视为非设计状态。
# `local_design`: 在非设计计算中是否将此组件视为设计状态。
# `char_warnings`: 是否忽略默认特性曲线使用警告。
# `printout`: 是否在网络结果输出中包含此组件。

# - m: 流量（质量流量）规格，单位为 kg/s。它可以是一个浮点数或一个引用对象 (`Ref`)。
# - m0: 质量流量的初始猜测值，单位为 kg/s。
# - p: 压力规格，单位为 Pa。同样可以是一个浮点数或一个引用对象 (`Ref`)。
# - p0: 初始压力猜测值，单位为 Pa。
# - h: 焓值规格，单位为 J/kg。也可以是一个引用对象 (`Ref`)。
# - h0: 初始焓值猜测值，单位为 J/kg。
# - fluid: 流体成分规格，格式为字典，键为流体名称，值为其在总流体中的比例（0~1）。例如：`{'water': 0.8, 'air': 0.2}`。
# - fluid0: 初始流体成分猜测值，格式同上。
# - fluid_balance: 是否启用流体平衡方程。如果设置为 `True`，则会对指定连接上的流体向量进行归一化处理，使其总和等于 100%。
# - x: 气相质量分数规格，范围为 0 到 1。
# - T: 温度规格，单位为 K。同样可以是一个引用对象 (`Ref`)。
# - Td_bp: 在给定压力下相对于沸腾点的温差，单位为 K。
# - v: 体积流量规格，单位为 m³/s。
# - state: 对于纯流体，在该连接上的状态。可以是液态 ('l') 或气态 ('g')。

# 注意
# 1. 流体平衡参数：当 `fluid_balance` 设置为 `True` 时，会自动对指定连接上的流体向量进行归一化处理，使得所有流体成分的比例之和等于 100%。
# 这有助于确保流体组成在整个系统中的守恒。

# 2. 设计与非设计参数：
# `design` 列表中的参数会在非设计计算中被取消设置，而 `offdesign` 列表中的参数则会在非设计计算中被设置。
# 这种机制允许 TESPy 自动从设计工况切换到非设计工况，反之亦然。


from tespy.components import Sink, Source, Valve  # 导入TESPy库中的Sink、Source和Valve组件
from tespy.connections import Connection         # 导入TESPy库中的Connection类
from tespy.networks import Network               # 导入TESPy库中的Network类
import shutil                                   # 导入shutil模块，用于删除文件夹

# 创建一个网络对象，设置压力单位为bar，温度单位为摄氏度，并关闭迭代信息显示
nw = Network(p_unit='bar', T_unit='C', iterinfo=False)

# 创建一个源组件（Source），命名为'source'
so = Source('source')

# 创建一个汇组件（Sink），命名为'sink'
si = Sink('sink')

# 创建一个阀门组件（Valve），命名为'valve'
v = Valve('valve')

# 创建从源组件到阀门组件的连接，连接名为'so_v'
so_v = Connection(so, 'out1', v, 'in1')

# 创建从阀门组件到汇组件的连接，连接名为'v_si'
v_si = Connection(v, 'out1', si, 'in1')

# 将两个连接添加到网络中
nw.add_conns(so_v, v_si)

# 设置阀门组件在非设计工况下的参数，这里只考虑流动阻力系数zeta的变化
v.set_attr(offdesign=['zeta'])

# 设置源到阀门连接的流体组成为甲烷(CH4)，质量流量为1 kg/s，温度为50°C，压力为80 bar
# 并将其质量流量设为设计参数
so_v.set_attr(fluid={'CH4': 1}, m=1, T=50, p=80, design=['m'])

# 设置阀门到汇连接的压力为15 bar
v_si.set_attr(p=15)

# 解决设计工况
nw.solve('design')
nw.print_results()

# 将当前的设计工况保存到'tmp'目录下
nw.save('tmp')

# 计算并四舍五入输出阀门到汇连接的出口温度，保留一位小数
round(v_si.T.val, 1)

# 计算并四舍五入输出阀门的压力损失比(pr)，保留三位小数
round(v.pr.val, 3)

# 修改源到阀门连接的压力为70 bar
so_v.set_attr(p=70)

# 根据之前保存的设计工况解决非设计工况
nw.solve('offdesign', design_path='tmp')
nw.print_results()

# 计算并四舍五入输出源到阀门连接的质量流量，保留一位小数
round(so_v.m.val, 1)

# 计算并四舍五入输出阀门到汇连接的出口温度，保留一位小数
round(v_si.T.val, 1)

# 删除'tmp'目录及其内容，忽略错误
shutil.rmtree('./tmp', ignore_errors=True)