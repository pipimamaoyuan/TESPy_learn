
# TESPy Pipe 类

# `Pipe` 是 TESPy 中的一个子类，继承自 `SimpleHeatExchanger`。
# 它主要用于模拟流体在管道中的流动、压力损失以及热交换情况。

# 方程
# 必需方程
# 1. 流体守恒方程 - `fluid_func`: 确保进出流体成分一致。
# 2. 质量流量守恒方程 - `mass_flow_func`: 保证流入和流出的质量流量相等。

# 可选方程
# 1. 压比方程： `pr_func`: 描述出口与入口的压力比。
# 2. 几何无关摩擦系数方程：`zeta_func`: 定义几何无关的摩擦系数。
# 3. 能量平衡方程：`energy_balance_func`: 计算传热量 Q。
# 4. 达西-魏斯巴赫公式组：`darcy_group_func`: 使用达西-魏斯巴赫方程计算基于管径的压力损失。
# 5. 海泽-威廉姆斯公式组：`hw_group_func`: 使用海泽-威廉姆斯方程计算基于管径的压力损失。
# 6. 面积无关换热系数方程组：`kA_group_func`: 使用面积无关的换热系数 kA 进行热交换计算。
# 7. 面积无关换热系数特性曲线组：`kA_char_group_func`: 利用换热系数的特性曲线进行热交换计算。

# 接口
# - 进接口: `in1`
# - 出接口: `out1`

# 参数
# - label: 字符串类型，用于标识组件。
# - design: 列表类型，包含设计工况参数名称（字符串形式）。
# - offdesign: 列表类型，包含非设计工况参数名称（字符串形式）。
# - design_path: 字符串类型，指向设计工况数据文件路径。
# - local_offdesign: 布尔值，表示在设计计算中是否将此组件视为非设计状态处理。
# - local_design: 布尔值，表示在非设计计算中是否将此组件视为设计状态处理。
# - char_warnings: 布尔值，忽略默认特性曲线使用的警告信息。
# - printout: 布尔值，决定是否在网络结果打印时包含此组件的信息。

# - Q: 热量传递，单位为瓦特（W）。
# - pr: 出口与入口的压力比。
# - zeta: 几何无关的摩擦系数，单位为 m^-4。
# - D: 管道直径，单位为米（m）。
# - L: 管道长度，单位为米（m）。
# - ks: 管壁粗糙度，单位为米（m）。
# - darcy_group:基于达西-魏斯巴赫公式的压力损失计算参数组。
# - ks_HW: 海泽-威廉姆斯公式的管壁相对粗糙度，无量纲。
# - hw_group: 基于海泽-威廉姆斯公式的压力损失计算参数组。
# - kA: 面积无关的换热系数，单位为 W/K。
# - kA_char: 换热系数的特性线对象。
# - Tamb: 环境温度，使用网络设定的温度单位。
# - kA_group: 基于环境温度和面积无关的换热系数 kA 的热交换计算参数组。


from tespy.components import Sink, Source, Pipe  # 导入TESPy中的Sink、Source和Pipe组件
from tespy.connections import Connection       # 导入TESPy中的Connection类
from tespy.networks import Network             # 导入TESPy中的Network类
import shutil                                # 导入shutil模块，用于删除文件夹

nw = Network()  # 创建一个新的网络实例
# 设置网络的基本单位：压力为bar，温度为摄氏度，比焓为kJ/kg，并关闭迭代信息显示
nw.set_attr(p_unit='bar', T_unit='C', h_unit='kJ / kg', iterinfo=False)

so = Source('source 1')  # 创建一个名为'source 1'的源组件
si = Sink('sink 1')      # 创建一个名为'sink 1'的汇组件
pi = Pipe('pipeline')    # 创建一个名为'pipeline'的管道组件


# 设置管道的属性：
# pr=0.975 表示出口压力与入口压力的比值为0.975
# Q=0 表示没有热量传递
# design=['pr'] 表示在设计工况下考虑压比参数
# L=100 表示管道长度为100米
# D='var' 表示直径是一个变量，在求解过程中会被确定
# ks=5e-5 表示管道的粗糙度为5e-5米
pi.set_attr(pr=0.975, Q=0, design=['pr'], L=100, D='var', ks=5e-5)

# 创建从源到管道的连接
inc = Connection(so, 'out1', pi, 'in1')
# 创建从管道到汇的连接
outg = Connection(pi, 'out1', si, 'in1')

# 将两个连接添加到网络中
nw.add_conns(inc, outg)

# 设置进口连接的流体组成、质量流量、温度和压力：
# fluid={'ethanol': 1} 表示流体为纯乙醇
# m=10 表示质量流量为10 kg/s
# T=30 表示温度为30摄氏度
# p=3 表示压力为3 bar
inc.set_attr(fluid={'ethanol': 1}, m=10, T=30, p=3)

# 对网络进行设计工况下的求解
nw.solve('design')

# 将当前的设计工况保存到'tmp'文件夹中
nw.save('tmp')

# 输出管道直径的计算结果，保留三位小数
round(pi.D.val, 3)

# 验证出口压力与入口压力的比值是否等于设置的压比
outg.p.val / inc.p.val == pi.pr.val

# 修改进口连接的质量流量为15 kg/s
inc.set_attr(m=15)

# 将管道的直径固定为之前设计工况下的计算值
pi.set_attr(D=pi.D.val)

# 在偏离设计工况下进行求解，使用之前保存的设计工况数据
nw.solve('offdesign', design_path='tmp')

# 输出偏离设计工况下的压比值，保留两位小数
round(pi.pr.val, 2)

# 删除'tmp'文件夹及其内容
shutil.rmtree('./tmp', ignore_errors=True)
