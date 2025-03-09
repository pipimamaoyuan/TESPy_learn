from tespy.networks import Network  # 导入Network类用于创建热力系统网络
working_fluid = "NH3"  # 定义工作流体为氨气

nw = Network(
    T_unit="C", p_unit="bar", h_unit="kJ / kg", m_unit="kg / s"
)
# 创建一个新的热力系统网络实例，并设置温度、压力、比焓和质量流量的单位

from tespy.components import Condenser  # 导入Condenser类用于冷凝器组件
from tespy.components import CycleCloser  # 导入CycleCloser类用于循环闭合组件
from tespy.components import SimpleHeatExchanger  # 导入SimpleHeatExchanger类用于简单的换热器组件
from tespy.components import Pump  # 导入Pump类用于泵组件
from tespy.components import Sink  # 导入Sink类用于汇组件
from tespy.components import Source  # 导入Source类用于源组件

# 源 和 汇
c_in = Source("refrigerant in")  # 创建一个名为“refrigerant in”的源组件
cons_closer = CycleCloser("consumer cycle closer")  # 创建一个名为“consumer cycle closer”的循环闭合组件
va = Sink("valve")  # 创建一个名为“valve”的汇组件

# 冷凝器 和 再循环泵 和 消费者换热器
cd = Condenser("condenser")  # 创建一个名为“condenser”的冷凝器组件
rp = Pump("recirculation pump")  # 创建一个名为“recirculation pump”的泵组件
cons = SimpleHeatExchanger("consumer")  # 创建一个名为“consumer”的简单换热器组件

# 建立 消费者系统
# 从消费者开始，因为该装置将设计为提供特定的热流量。
# 可以确定消费者系统的组件：冷凝器、泵和消费者
from tespy.connections import Connection  # 导入Connection类用于连接组件

c0 = Connection(c_in, "out1", cd, "in1", label="0")  # 连接“refrigerant in”到“condenser”
c1 = Connection(cd, "out1", va, "in1", label="1")  # 连接“condenser”到“valve”
c20 = Connection(cons_closer, "out1", rp, "in1", label="20")  # 连接“consumer cycle closer”到“recirculation pump”
c21 = Connection(rp, "out1", cd, "in2", label="21")  # 连接“recirculation pump”到“condenser”
c22 = Connection(cd, "out2", cons, "in1", label="22")  # 连接“condenser”到“consumer”
c23 = Connection(cons, "out1", cons_closer, "in1", label="23")  # 连接“consumer”到“consumer cycle closer”

nw.add_conns(c0, c1, c20, c21, c22, c23)  # 将所有连接添加到网络中

cd.set_attr(pr1=0.99, pr2=0.99)  # 设置冷凝器的第一和第二出口的压力比
rp.set_attr(eta_s=0.75)  # 设置再循环泵的等熵效率
cons.set_attr(pr=0.99)  # 设置消费者换热器的压力比

# PropsSI函数可以用来查询各种流体的热力学性质，比如压力、温度、比焓等
from CoolProp.CoolProp import PropsSI as PSI  # 导入PropsSI函数用于获取流体性质

# "P" 表示我们要查询的是压力
# "Q", 1 表示我们要查询的是饱和状态下的性质（Q=1表示饱和蒸汽）
# "T", 273.15 + 95 表示我们在273.15 + 95 K（即95°C）的温度下进行查询
# working_fluid 是我们指定的工作流体，这里是氨气（NH3）
# / 1e5 将结果从Pa转换为bar
p_cond = PSI("P", "Q", 1, "T", 273.15 + 95, working_fluid) / 1e5  # 计算冷凝温度对应的饱和压力
c0.set_attr(T=170, p=p_cond, fluid={working_fluid: 1})  # 设置c0连接的温度、压力和流体组分
c20.set_attr(T=60, p=2, fluid={"water": 1})  # 设置c20连接的温度、压力和流体组分
c22.set_attr(T=90)  # 设置c22连接的温度

# key design parameter
cons.set_attr(Q=-230e3)  # 设置消费者换热器的热量传递率

nw.solve("design")  # 执行设计点计算
nw.print_results()  # 打印计算结果

# 建立 阀门和蒸发器系统
from tespy.components import Valve  # 导入Valve类用于阀门组件
from tespy.components import Drum  # 导入Drum类用于集汽器组件
from tespy.components import HeatExchanger  # 导入HeatExchanger类用于换热器组件

# 环境源 和 汇
amb_in = Source("source ambient")  # 创建一个名为“source ambient”的源组件
amb_out = Sink("sink ambient")  # 创建一个名为“sink ambient”的汇组件

# 蒸发系统
va = Valve("valve")  # 创建一个名为“valve”的阀门组件
dr = Drum("drum")  # 创建一个名为“drum”的集汽器组件
ev = HeatExchanger("evaporator")  # 创建一个名为“evaporator”的换热器组件
su = HeatExchanger("superheater")  # 创建一个名为“superheater”的过热器组件

# 虚拟汇
cp1 = Sink("compressor 1")  # 创建一个名为“compressor 1”的虚拟汇组件

nw.del_conns(c1)  # 删除之前的c1连接

# 蒸发系统
c1 = Connection(cd, "out1", va, "in1", label="1")  # 连接“condenser”到“valve”
c2 = Connection(va, "out1", dr, "in1", label="2")  # 连接“valve”到“drum”
c3 = Connection(dr, "out1", ev, "in2", label="3")  # 连接“drum”到“evaporator”
c4 = Connection(ev, "out2", dr, "in2", label="4")  # 连接“evaporator”到“drum”
c5 = Connection(dr, "out2", su, "in2", label="5")  # 连接“drum”到“superheater”
c6 = Connection(su, "out2", cp1, "in1", label="6")  # 连接“superheater”到“compressor 1”

nw.add_conns(c1, c2, c3, c4, c5, c6)  # 将新的连接添加到网络中

c17 = Connection(amb_in, "out1", su, "in1", label="17")  # 连接“source ambient”到“superheater”
c18 = Connection(su, "out1", ev, "in1", label="18")  # 连接“superheater”到“evaporator”
c19 = Connection(ev, "out1", amb_out, "in1", label="19")  # 连接“evaporator”到“sink ambient”

nw.add_conns(c17, c18, c19)  # 将新的连接添加到网络中

ev.set_attr(pr1=0.99)  # 设置蒸发器的第一出口的压力比
su.set_attr(pr1=0.99, pr2=0.99)  # 设置过热器的第一和第二出口的压力比

# 蒸发系统冷端
c4.set_attr(x=0.9, T=5)  # 设置c4连接的质量含汽率和温度

h_sat = PSI("H", "Q", 1, "T", 273.15 + 15, working_fluid) / 1e3  # 计算饱和温度对应的比焓
c6.set_attr(h=h_sat)  # 设置c6连接的比焓

# 蒸发系统热端
c17.set_attr(T=15, fluid={"water": 1})  # 设置c17连接的温度和流体组分
c19.set_attr(T=9, p=1.013)  # 设置c19连接的温度和压力

# 注意：鼓是一个特殊组件，它内置了循环闭合器
# 因此，尽管我们在技术上在鼓的出口 1 到入口 2 处形成一个循环，但我们在这里不需要包括循环闭合器。

nw.solve("design")  # 执行设计点计算
nw.print_results()  # 打印计算结果

# 建立 压缩机系统
from tespy.components import Compressor  # 导入Compressor类用于压缩机组件
from tespy.components import Splitter  # 导入Splitter类用于分流器组件
from tespy.components import Merge  # 导入Merge类用于合并器组件

cp1 = Compressor("compressor 1")  # 创建一个名为“compressor 1”的压缩机组件
cp2 = Compressor("compressor 2")  # 创建一个名为“compressor 2”的压缩机组件

ic = HeatExchanger("intermittent cooling")  # 创建一个名为“intermittent cooling”的间歇冷却器组件
hsp = Pump("heat source pump")  # 创建一个名为“heat source pump”的热源泵组件

sp = Splitter("splitter")  # 创建一个名为“splitter”的分流器组件
me = Merge("merge")  # 创建一个名为“merge”的合并器组件
cv = Valve("control valve")  # 创建一个名为“control valve”的控制阀组件

hs = Source("ambient intake")  # 创建一个名为“ambient intake”的环境入口源组件
cc = CycleCloser("heat pump cycle closer")  # 创建一个名为“heat pump cycle closer”的热泵循环闭合组件

nw.del_conns(c0, c6, c17)  # 删除之前的c0、c6和c17连接

c6 = Connection(su, "out2", cp1, "in1", label="6")  # 连接“superheater”到“compressor 1”
c7 = Connection(cp1, "out1", ic, "in1", label="7")  # 连接“compressor 1”到“intermittent cooling”
c8 = Connection(ic, "out1", cp2, "in1", label="8")  # 连接“intermittent cooling”到“compressor 2”
c9 = Connection(cp2, "out1", cc, "in1", label="9")  # 连接“compressor 2”到“heat pump cycle closer”
c0 = Connection(cc, "out1", cd, "in1", label="0")  # 连接“heat pump cycle closer”到“condenser”

c11 = Connection(hs, "out1", hsp, "in1", label="11")  # 连接“ambient intake”到“heat source pump”
c12 = Connection(hsp, "out1", sp, "in1", label="12")  # 连接“heat source pump”到“splitter”
c13 = Connection(sp, "out1", ic, "in2", label="13")  # 连接“splitter”到“intermittent cooling”
c14 = Connection(ic, "out2", me, "in1", label="14")  # 连接“intermittent cooling”到“merge”
c15 = Connection(sp, "out2", cv, "in1", label="15")  # 连接“splitter”到“control valve”
c16 = Connection(cv, "out1", me, "in2", label="16")  # 连接“control valve”到“merge”
c17 = Connection(me, "out1", su, "in1", label="17")  # 连接“merge”到“superheater”

nw.add_conns(c6, c7, c8, c9, c0, c11, c12, c13, c14, c15, c16, c17)  # 将新的连接添加到网络中

pr = (c1.p.val / c5.p.val) ** 0.5  # 计算压力比
cp1.set_attr(pr=pr)  # 设置压缩机1的压力比
ic.set_attr(pr1=0.99, pr2=0.98)  # 设置间歇冷却器的第一和第二出口的压力比
hsp.set_attr(eta_s=0.75)  # 设置热源泵的等熵效率

c0.set_attr(p=p_cond, fluid={working_fluid: 1})  # 设置c0连接的压力和流体组分

c6.set_attr(h=c5.h.val + 10)  # 设置c6连接的比焓
c8.set_attr(h=c5.h.val + 10)  # 设置c8连接的比焓

c7.set_attr(h=c5.h.val * 1.2)  # 设置c7连接的比焓
c9.set_attr(h=c5.h.val * 1.2)  # 设置c9连接的比焓

c11.set_attr(p=1.013, T=15, fluid={"water": 1})  # 设置c11连接的压力、温度和流体组分
c14.set_attr(T=30)  # 设置c14连接的温度

nw.solve("design")  # 执行设计点计算

c0.set_attr(p=None)  # 清除c0连接的压力设定
cd.set_attr(ttd_u=5)  # 设置冷凝器的上部温差

c4.set_attr(T=None)  # 清除c4连接的温度设定
ev.set_attr(ttd_l=5)  # 设置蒸发器的下部温差

c6.set_attr(h=None)  # 清除c6连接的比焓设定
su.set_attr(ttd_u=5)  # 设置过热器的上部温差

c7.set_attr(h=None)  # 清除c7连接的比焓设定
cp1.set_attr(eta_s=0.8)  # 设置压缩机1的等熵效率

c9.set_attr(h=None)  # 清除c9连接的比焓设定
cp2.set_attr(eta_s=0.8)  # 设置压缩机2的等熵效率

c8.set_attr(h=None, Td_bp=4)  # 清除c8连接的比焓设定并设置与泡点的温差
nw.solve("design")  # 再次执行设计点计算
nw.save("system_design")  # 保存当前的设计点参数

cp1.set_attr(design=["eta_s"], offdesign=["eta_s_char"])  # 设置压缩机1的设计和离设计工况下的特性曲线
cp2.set_attr(design=["eta_s"], offdesign=["eta_s_char"])  # 设置压缩机2的设计和离设计工况下的特性曲线
rp.set_attr(design=["eta_s"], offdesign=["eta_s_char"])  # 设置再循环泵的设计和离设计工况下的特性曲线
hsp.set_attr(design=["eta_s"], offdesign=["eta_s_char"])  # 设置热源泵的设计和离设计工况下的特性曲线

cons.set_attr(design=["pr"], offdesign=["zeta"])  # 设置消费者换热器的设计和离设计工况下的阻力系数

cd.set_attr(
    design=["pr2", "ttd_u"], offdesign=["zeta2", "kA_char"]
)  # 设置冷凝器的设计和离设计工况下的阻力系数和传热系数特性曲线

from tespy.tools.characteristics import CharLine  # 导入CharLine类用于特性曲线
from tespy.tools.characteristics import load_default_char as ldc  # 导入load_default_char函数用于加载默认特性曲线

kA_char1 = ldc("heat exchanger", "kA_char1", "DEFAULT", CharLine)  # 加载默认的传热系数特性曲线
kA_char2 = ldc("heat exchanger", "kA_char2", "EVAPORATING FLUID", CharLine)  # 加载蒸发侧的传热系数特性曲线
ev.set_attr(
    kA_char1=kA_char1, kA_char2=kA_char2,
    design=["pr1", "ttd_l"], offdesign=["zeta1", "kA_char"]
)  # 设置蒸发器的设计和离设计工况下的阻力系数和传热系数特性曲线

su.set_attr(
    design=["pr1", "pr2", "ttd_u"], offdesign=["zeta1", "zeta2", "kA_char"]
)  # 设置过热器的设计和离设计工况下的阻力系数和传热系数特性曲线

ic.set_attr(
    design=["pr1", "pr2"], offdesign=["zeta1", "zeta2", "kA_char"]
)  # 设置间歇冷却器的设计和离设计工况下的阻力系数和传热系数特性曲线
c14.set_attr(design=["T"])  # 设置c14连接的设计温度
nw.solve("offdesign", design_path="system_design")  # 执行离设计工况计算
nw.print_results()  # 打印计算结果

# %% [sec_18]
import numpy as np  # 导入numpy库用于数值计算
nw.set_attr(iterinfo=False)  # 关闭迭代信息输出

for Q in np.linspace(1, 0.6, 5) * cons.Q.val:
    cons.set_attr(Q=Q)  # 设置消费者换热器的热量传递率为原始值的线性变化
    nw.solve("offdesign", design_path="system_design")  # 执行离设计工况计算
    print(
        "COP:", abs(cons.Q.val) / (cp1.P.val + cp2.P.val + hsp.P.val + rp.P.val)
    )  # 计算并打印系统的性能系数（COP）
    
# 设计点（Design Point）： 这是指系统或组件的最佳运行点，通常是根据特定的操作条件（如温度、压力、流量等）优化过的。
# 在这个点上，组件的性能最佳，效率最高。
# 设计点参数（Design Point Parameters）：这些是系统或组件在设计点时的具体参数值，如温度、压力、流量、比焓等。
# 偏离设计点（Off-design Operation）：当系统或组件不在设计点运行时，其性能会有所下降，相关的参数也会发生变化。
# 部分负荷（Part Load）： 指的是系统在低于其设计容量的情况下运行。
# 非设计点参数：在offdesign属性中列出那些在非设计点计算时需要固定的参数。这些参数在非设计点计算时被设置为设计点计算中得出的值。
# 例如，如果一个系统设计容量为100 kW的热量输出，但在实际运行中只需要70 kW，则处于部分负荷状态。


# 设计属性（Design Attribute）： 这是一个列表，列出了在设计点计算时需要考虑的参数。
# 离设计属性（Offdesign Attribute）： 这是一个列表，列出了在非设计点计算时需要考虑的参数。
# 在非设计点计算中，所有在design属性中列出的参数将被取消设置（即不再固定这些参数）
# 在非设计点计算中，所有在offdesign属性中列出的参数将被设置为特定值（即固定这些参数）。

# 如果在规格值没有任何更改的情况下运行非设计模拟，结果必须与相应的设计案例相同！如果它们不相同，很可能是出了些问题。