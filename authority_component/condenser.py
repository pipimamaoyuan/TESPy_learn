# TESPy Condenser 类 ，继承 HeatExchanger base 类。
# Condenser是一种换热器组件，用于冷却流体直到其进入液态状态。冷侧流体 负责冷却 热侧流体。
# 热侧流体必须是纯物质，并且可以选择启用亚冷却功能。

# 必需方程
# 1. 流体平衡：确保流体类型在各端口之间保持一致。
# 2. 质量流量守恒：流入和流出的质量流量相等。
# 3. 能量守恒：通过计算热量传递来平衡输入和输出的能量。
# 4. 冷凝出口状态：
#    - 默认情况下，冷凝出口的状态被假设为饱和液体。
#    - 如果启用了亚冷却（`subcooling=True`），则可以通过手动指定焓值来调整冷凝出口的状态。

# 可选方程 这些方程可以根据需要选择使用，以增强模型的准确性：
# - 热平衡方程（冷侧）
# - 传热系数（kA）计算
# - 传热系数特性曲线
# - 上温差（ttd_u）计算
# - 下温差（ttd_l）计算
# - 最小温差（ttd_min）计算
# - 冷侧效率（eff_cold）计算
# - 热侧效率（eff_hot）计算
# - 最大效率（eff_max）计算
# - 热侧压力比（pr1）
# - 冷侧压力比（pr2）
# - 热侧压降（dp1）
# - 冷侧压降（dp2）
# - 热侧摩擦损失因子（zeta1）
# - 冷侧摩擦损失因子（zeta2）

# 输入/输出端口
# - in1: 热侧入口
# - in2: 冷侧入口
# - out1: 热侧出口
# - out2: 冷侧出口

# 参数说明
# - label: 组件标签
# - design: 设计参数列表
# - offdesign: 非设计参数列表
# - design_path: 设计案例路径
# - local_offdesign: 在设计计算中将此组件视为非设计组件
# - local_desig: 在非设计计算中将此组件视为设计组件
# - char_warnings: 是否忽略默认特征曲线使用警告
# - printout: 包含网络结果打印中的此组件

# 物理参数
# - Q: 热侧流体的热传递量 Q (w)
# self.Q.val = self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)

# - pr1/pr2: 出口到入口的压力比（热侧/冷侧）
# - dp1/dp2: 压力降（热侧/冷侧）
# - zeta1/zeta2: 几何无关摩擦系数（热侧/冷侧）

# - ttd_l/ttd_u/ttd_min: 温差（下限、上限、最小值）
# self.ttd_u.val = self.inl[0].calc_T_sat() - self.outl[1].T.val_SI
# self.ttd_l.val = self.outl[0].T.val_SI - self.inl[1].T.val_SI
# self.ttd_min.val = min(self.ttd_u.val, self.ttd_l.val)

# - eff_cold/eff_hot/eff_max: 效率（冷侧、热侧、最大值）

# - kA: 面积无关传热系数 kA = - Q / 对数平均温差
# self.kA.val = - self.Q.val / self.td_log.val

# - kA_char/kA_char1/kA_char2: 传热系数特征曲线
# - subcooling: 启用/禁用亚冷却，默认为禁用

# 注意：
# - 冷凝出口的状态默认为饱和液体状态。
# - 如果启用了亚冷却，则可以手动指定出口处的焓值。
# - 对于给定的传热系数(kA)和上温差(ttd_u)，这些参数指的是冷凝温度，即使热侧流体进入时处于过热状态也是如此。


from tespy.components import Sink, Source, Condenser  # 导入TESPy组件类：Sink、Source和Condenser
from tespy.connections import Connection  # 导入TESPy连接类：Connection
from tespy.networks import Network  # 导入TESPy网络类：Network
from tespy.tools.fluid_properties import T_sat_p  # 导入TESPy工具中的饱和温度计算函数：T_sat_p
import shutil  # 导入shutil模块，用于删除文件夹

# 创建一个TESPy网络对象，设置单位为摄氏度(C)、巴(bar)和千焦/千克(kJ/kg)，质量流量范围为0.01到1000 kg/s，并关闭迭代信息显示
nw = Network(T_unit='C', p_unit='bar', h_unit='kJ / kg', m_range=[0.01, 1000], iterinfo=False)

# 创建两个源组件：一个是环境空气进口，另一个是废蒸汽进口
amb_in = Source('ambient air inlet')  # 环境空气入口
waste_steam = Source('waste steam')  # 废蒸汽入口

# 创建两个汇组件：一个是空气出口，另一个是冷凝水汇流
amb_out = Sink('air outlet')  # 空气出口
c = Sink('condensate sink')  # 冷凝水汇流

# 创建一个Condenser组件，命名为'condenser'
cond = Condenser('condenser')

# 设置Condenser组件的属性，包括压力比pr1和pr2，上温差ttd_u，并指定设计参数和非设计参数
cond.set_attr(pr1=0.98, pr2=0.999, ttd_u=15, design=['pr2', 'ttd_u'], offdesign=['zeta2', 'kA_char'])

# 创建四个连接对象：
# 1. 环境空气从入口到Condenser的冷侧入口
amb_he = Connection(amb_in, 'out1', cond, 'in2')
# 2. 环境空气从Condenser的冷侧出口到空气出口
he_amb = Connection(cond, 'out2', amb_out, 'in1')
# 3. 废蒸汽从入口到Condenser的热侧入口
ws_he = Connection(waste_steam, 'out1', cond, 'in1')
# 4. 冷却后的蒸汽（冷凝水）从Condenser的热侧出口到冷凝水汇流
he_c = Connection(cond, 'out1', c, 'in1')

# 将这四个连接添加到网络中
nw.add_conns(amb_he, he_amb, ws_he, he_c)

# 设置废蒸汽连接的初始条件：纯水，焓值为2700 kJ/kg，质量流量为1 kg/s
ws_he.set_attr(fluid={'water': 1}, h=2700, m=1)

# 设置环境空气连接的初始条件：纯空气，温度为20°C，并在非设计状态下考虑体积流量的变化
amb_he.set_attr(fluid={'air': 1}, T=20, offdesign=['v'])

# 设置环境空气出口连接的目标温度为40°C，并将其作为设计参数之一
he_amb.set_attr(p=1, T=40, design=['T'])

# 解决网络的设计工况
nw.solve('design')

# 将设计结果保存到临时文件夹'tmp'
nw.save('tmp')

# 计算并四舍五入环境空气连接的体积流量到小数点后两位
round(amb_he.v.val, 2)

# 计算并四舍五入废蒸汽与环境空气之间的温度差到小数点后一位
round(ws_he.T.val - he_amb.T.val, 1)

# 计算并四舍五入废蒸汽的饱和温度与环境空气温度之差到小数点后一位
round(ws_he.calc_T_sat() - 273.15 - he_amb.T.val, 1)

# 修改废蒸汽的质量流量为0.7 kg/s
ws_he.set_attr(m=0.7)

# 修改环境空气的温度为30°C
amb_he.set_attr(T=30)

# 在非设计工况下解决网络，使用之前保存的设计路径'tmp'
nw.solve('offdesign', design_path='tmp')

# 计算并四舍五入废蒸汽与环境空气之间的温度差到小数点后一位
round(ws_he.T.val - he_amb.T.val, 1)

# 计算并四舍五入废蒸汽的饱和温度与环境空气温度之差到小数点后一位
round(ws_he.calc_T_sat() - 273.15 - he_amb.T.val, 1)

# 启用Condenser的亚冷却功能
cond.set_attr(subcooling=True)

# 设置冷凝水出口相对于饱和点的过冷度为-5 K
he_c.set_attr(Td_bp=-5)

# 在非设计工况下再次解决网络，使用之前保存的设计路径'tmp'
nw.solve('offdesign', design_path='tmp')

# 计算并四舍五入废蒸汽与环境空气之间的温度差到小数点后一位
round(ws_he.T.val - he_amb.T.val, 1)

# 计算并四舍五入废蒸汽的饱和温度与环境空气温度之差到小数点后一位
round(ws_he.calc_T_sat() - 273.15 - he_amb.T.val, 1)

# 删除临时文件夹'tmp'及其内容
shutil.rmtree('./tmp', ignore_errors=True)



# 通过计算热侧出口的实际焓值与饱和液体焓值之间的差值来确保在不启用亚冷却的情况下
# 热侧出口流体处于饱和液体状态
# def subcooling_func(self)

# 计算对数平均温差
# def calculate_td_log(self)

# 计算上温差 ttd_u （热侧入口温度与冷侧出口温度之差）
# def ttd_u_func(self)

