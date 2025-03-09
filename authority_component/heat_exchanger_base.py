# TESPy的`HeatExchanger` base  类。

# `HeatExchanger` base 类是 TESPy 中用于模拟换热器的基本组件类。
# 它有两个子类：
# - `Condenser`: 冷凝器，常用于蒸汽冷凝过程。
# - `Desuperheater`: 减温器，通常用于将过热蒸汽冷却到饱和状态或更低温度。

# 方程
# 必须满足的方程
# 能量守恒方程: 描述了流经换热器的能量平衡关系。
# self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI) + self.inl[1].m.val_SI * (self.outl[1].h.val_SI - self.inl[1].h.val_SI) = 0

# 可选方程
# 这些方程可以用来进一步细化模型的行为:

# - 热传递速率方程 (`kA_func`): 根据传热系数计算热传递速率。
# self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI) + self.kA.val * self.calculate_td_log() = 0
# self.calculate_td_log() 调用前面定义的方法来计算 LMTD。

# - 热传递特性曲线方程 (`kA_char_func`): 使用特性曲线来描述传热系数的变化。
# self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI) + self.kA.design * fkA * td_log


# - 上下端温差方程 (`ttd_u_func`, `ttd_l_func`): 分别表示换热器两端的最大和最小温差。
# - 最小温差方程 (`ttd_min_func`): 确保实际操作中的温差不低于设定值。

# - 效用方程 (`eff_cold_func`, `eff_hot_func`, `eff_max_func`): 评估换热器在冷侧和热侧的效率。
# 最大冷效
# def eff_cold_func(self)  最大理论焓增加量 * 冷侧效用 - 冷侧实际焓增加量 = 0
# self.eff_cold.val * self.calc_dh_max_cold() - (self.outl[1].h.val_SI - self.inl[1].h.val_SI)

# 最大热效
# def eff_hot_func(self)  最大理论焓减少量 * 热侧效用 - 热侧实际焓减少量 = 0
# self.eff_hot.val * self.calc_dh_max_hot() - (self.outl[0].h.val_SI - self.inl[0].h.val_SI)

# 最大效用
# def eff_max_func(self)  
# max(self.eff_cold.val, self.eff_hot.val) = self.eff_max.val 

# - 压降方程 (`pr_func` 和 `dp_func`): 计算通过换热器的压力变化。
# - 摩擦损失方程 (`zeta_func`): 考虑流动阻力对系统的影响。

# 进出口定义
# - `in1` 表示热侧入口。
# - `in2` 表示冷侧入口。
# - `out1` 表示热侧出口。
# - `out2` 表示冷侧出口。

# 参数
# - label: 组件标签
# - design: 设计参数列表
# - offdesign: 非设计参数列表
# - design_path: 设计案例路径
# - local_offdesign: 在设计计算中将此组件视为非设计组件
# - local_desig: 在非设计计算中将此组件视为设计组件
# - char_warnings: 是否忽略默认特征曲线使用警告
# - printout: 包含网络结果打印中的此组件

# - Q: 热交换量，单位为瓦特 (W)
# self.Q.val = self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)  

# - pr1, pr2: 热侧和冷侧进出口压力比。
# - dp1, dp2: 热侧和冷侧进出口压力差。
# - zeta1, zeta2: 热侧和冷侧的几何无关摩擦系数。

# - ttd_l: 下游温差，单位为开尔文 (K)
# 热侧出口与冷端入口之间的温差
# self.ttd_l.val = self.outl[0].T.val_SI - self.inl[1].T.val_SI

# - ttd_u: 上游温差，单位为开尔文 (K)
# 热侧入口与冷侧出口之间的温差 
# self.ttd_u.val = self.inl[0].T.val_SI - self.outl[1].T.val_SI

# - ttd_min: 最小允许温差，单位为开尔文 (K)
# min(ttd_l, ttd_u) = ttd_min
# self.ttd_min.val = min(self.ttd_u.val, self.ttd_l.val)

# - eff_cold, eff_hot: 冷侧和热侧的换热器效用。
# - eff_max: 冷侧和热侧效用的最大值。

# - kA: 面积无关的热传递系数，单位为 W/K。
# 传热系数 = - 热交换量 / 对数温差
# self.kA.val = -self.Q.val / self.td_log.val

# - kA_char: 包含热传递系数特性的字典。
# - kA_char1: 热侧热传递系数的特性线对象。
# - kA_char2: 冷侧热传递系数的特性线对象。

# 注意事项
# - `HeatExchanger` base 类及其子类适用于逆流换热器（countercurrent heat exchangers）。
# - 对于并流、错流或其他组合类型，上述某些方程（如 `kA`, `ttd_u`, `ttd_l`）可能不适用。


from tespy.components import Sink, Source, HeatExchanger  # 导入TESPy中的Sink、Source和HeatExchanger组件
from tespy.connections import Connection  # 导入TESPy中的Connection类，用于连接组件
from tespy.networks import Network  # 导入TESPy中的Network类，用于创建网络
from tespy.tools import document_model  # 导入document_model函数，用于生成模型文档
import shutil  # 导入shutil模块，用于文件和目录操作

# 创建一个TESPy网络实例，设置温度单位为摄氏度，压力单位为巴，比焓单位为kJ/kg，并关闭迭代信息显示
nw = Network(T_unit='C', p_unit='bar', h_unit='kJ / kg', iterinfo=False)

# 定义排气空气出口（热侧入口）
exhaust_hot = Source('Exhaust air outlet')
# 定义排气空气入口（热侧出口）
exhaust_cold = Sink('Exhaust air inlet')
# 定义冷却水入口（冷侧入口）
cw_cold = Source('cooling water inlet')
# 定义冷却水出口（冷侧出口）
cw_hot = Sink('cooling water outlet')

# 定义废热换热器组件
he = HeatExchanger('waste heat exchanger')

# 将换热器作为组件添加到网络中（这行代码在原代码中有误，应删除）
# he.component()

# 创建从排气空气出口到换热器热侧入口的连接
ex_he = Connection(exhaust_hot, 'out1', he, 'in1')
# 创建从换热器热侧出口到排气空气入口的连接
he_ex = Connection(he, 'out1', exhaust_cold, 'in1')
# 创建从冷却水入口到换热器冷侧入口的连接
cw_he = Connection(cw_cold, 'out1', he, 'in2')
# 创建从换热器冷侧出口到冷却水出口的连接
he_cw = Connection(he, 'out2', cw_hot, 'in1')

# 将所有连接添加到网络中
nw.add_conns(ex_he, he_ex, cw_he, he_cw)

# 设置换热器的设计参数：热侧和冷侧的压力比均为0.98，上游最高温差为5K
he.set_attr(pr1=0.98, pr2=0.98, ttd_u=5,
            # 设计工况下的参数列表
            design=['pr1', 'pr2', 'ttd_u'],
            # 偏离设计工况下的参数列表
            offdesign=['zeta1', 'zeta2', 'kA_char'])

# 设置冷却水进口的流体成分、温度和压力，并指定质量流量作为偏离设计工况下的参数
cw_he.set_attr(fluid={'water': 1}, T=10, p=3, offdesign=['m'])

# 设置排气空气出口的流体成分、体积流量和温度
ex_he.set_attr(fluid={'air': 1}, v=0.1, T=35)

# 设置排气空气入口的设计温度和压力，并指定温度作为设计工况下的参数
he_ex.set_attr(T=17.5, p=1, design=['T'])

# 解决设计工况下的网络
nw.solve('design')

# 保存当前的设计点数据到'tmp'目录
nw.save('tmp')

# 计算并四舍五入排气空气出口与冷却水出口之间的温度差，保留整数位
round(ex_he.T.val - he_cw.T.val, 0)

# 修改排气空气出口的体积流量为0.075 m³/s
ex_he.set_attr(v=0.075)

# 在偏离设计工况下解决网络，并使用之前保存的设计点数据
nw.solve('offdesign', design_path='tmp')

# 四舍五入冷却水出口的温度，保留一位小数
round(he_cw.T.val, 1)

# 四舍五入排气空气入口的温度，保留一位小数
round(he_ex.T.val, 1)

# 修改排气空气出口的体积流量为0.1 m³/s，温度为40°C
ex_he.set_attr(v=0.1, T=40)

# 在偏离设计工况下再次解决网络，并使用之前保存的设计点数据
nw.solve('offdesign', design_path='tmp')

# 生成模型文档，保存到'report'目录
document_model(nw)

# 四舍五入冷却水出口的温度，保留一位小数
round(he_cw.T.val, 1)

# 四舍五入排气空气入口的温度，保留一位小数
round(he_ex.T.val, 1)

# 删除'tmp'目录及其内容，忽略错误
shutil.rmtree('./tmp', ignore_errors=True)
# 删除'report'目录及其内容，忽略错误
shutil.rmtree('./report', ignore_errors=True)

# 通过虚拟过程分解热量传递和不可逆性引起的熵变化，
# 并计算各种熵相关的参数：
# def entropy_balance(self)

# 计算冷侧的最大理论焓增加量
# def calc_dh_max_cold(self)
# 通过在冷侧出口的压力下将冷侧入口的温度提升到热侧入口的温度来计算最大焓增加量。
# o2 = self.outl[1]
# T_in_hot = self.inl[0].calc_T()
# h_at_T_in_hot = h_mix_pT(o2.p.val_SI, T_in_hot, o2.fluid_data, o2.mixing_rule)
# return h_at_T_in_hot - self.inl[1].h.val_SI

# 计算热侧的最大理论焓减少量
# def calc_dh_max_hot(self)
# 通过在热侧出口的压力下将热侧入口的温度降低到冷侧入口的温度来计算最大焓减少量。
# o1 = self.outl[0]
# T_in_cold = self.inl[1].calc_T()
# h_at_T_in_cold = h_mix_pT(o1.p.val_SI, T_in_cold, o1.fluid_data, o1.mixing_rule)
# return h_at_T_in_cold - self.inl[0].h.val_SI

# 计算 单位时间内, 通过换热器的能量传递量
# def bus_func(self, bus)
# self.inl[0].m.val_SI * (self.outl[0].h.val_SI - self.inl[0].h.val_SI)
