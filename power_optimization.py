# -*- coding: utf-8 -*-

# 使用TESPy 和 pygmo 进行 热电厂效率优化

import numpy as np
import pygmo as pg

from tespy.components import CycleCloser, Sink, Source, Condenser, Desuperheater, SimpleHeatExchanger, Merge, Splitter, Pump, Turbine
from tespy.connections import Bus, Connection
from tespy.networks import Network
from tespy.tools.optimization import OptimizationProblem

class SamplePlant:
    """Class template for TESPy model usage in optimization module."""
    def __init__(self):
        # 创建一个新的网络实例，并设置单位为巴(bar)、摄氏度(Celsius)、千焦耳每千克(kJ/kg)，关闭迭代信息显示
        self.nw = Network()
        self.nw.set_attr(
            p_unit="bar", T_unit="C", h_unit="kJ / kg", iterinfo=False
        )
        
        # 定义组件
        # 主循环
        sg = SimpleHeatExchanger("steam generator")  # 蒸汽发生器
        cc = CycleCloser("cycle closer")              # 循环闭合器
        hpt = Turbine("high pressure turbine")       # 高压涡轮机
        sp1 = Splitter("splitter 1", num_out=2)      # 分流器1，有两个出口
        mpt = Turbine("mid pressure turbine")        # 中压涡轮机
        sp2 = Splitter("splitter 2", num_out=2)      # 分流器2，有两个出口
        lpt = Turbine("low pressure turbine")        # 低压涡轮机
        con = Condenser("condenser")                 # 冷凝器
        pu1 = Pump("feed water pump")                # 给水泵1
        fwh1 = Condenser("feed water preheater 1")   # 给水预热器1
        fwh2 = Condenser("feed water preheater 2")   # 给水预热器2
        dsh = Desuperheater("desuperheater")           # 减温器
        me2 = Merge("merge2", num_in=2)              # 合并器2，有两个入口
        pu2 = Pump("feed water pump 2")              # 给水泵2
        pu3 = Pump("feed water pump 3")              # 给水泵3
        me = Merge("merge", num_in=2)                # 合并器，有两个入口
        
        # 冷却水
        cwi = Source("cooling water source")         # 冷却水源
        cwo = Sink("cooling water sink")             # 冷却水汇
        
        # 定义连接
        # 主循环
        c0 = Connection(sg, "out1", cc, "in1", label="0")
        c1 = Connection(cc, "out1", hpt, "in1", label="1")
        c2 = Connection(hpt, "out1", sp1, "in1", label="2")
        c3 = Connection(sp1, "out1", mpt, "in1", label="3", state="g")
        c4 = Connection(mpt, "out1", sp2, "in1", label="4")
        c5 = Connection(sp2, "out1", lpt, "in1", label="5")
        c6 = Connection(lpt, "out1", con, "in1", label="6")
        c7 = Connection(con, "out1", pu1, "in1", label="7", state="l")
        c8 = Connection(pu1, "out1", fwh1, "in2", label="8", state="l")
        c9 = Connection(fwh1, "out2", me, "in1", label="9", state="l")
        c10 = Connection(me, "out1", fwh2, "in2", label="10", state="l")
        c11 = Connection(fwh2, "out2", dsh, "in2", label="11", state="l")
        c12 = Connection(dsh, "out2", me2, "in1", label="12", state="l")
        c13 = Connection(me2, "out1", sg, "in1", label="13", state="l")

        self.nw.add_conns(
            c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13
        )

        # 预热部分
        c21 = Connection(sp1, "out2", dsh, "in1", label="21")
        c22 = Connection(dsh, "out1", fwh2, "in1", label="22")
        c23 = Connection(fwh2, "out1", pu2, "in1", label="23")
        c24 = Connection(pu2, "out1", me2, "in2", label="24")

        c31 = Connection(sp2, "out2", fwh1, "in1", label="31")
        c32 = Connection(fwh1, "out1", pu3, "in1", label="32")
        c33 = Connection(pu3, "out1", me, "in2", label="33")

        self.nw.add_conns(c21, c22, c23, c24, c31, c32, c33)

        # 冷却水部分
        c41 = Connection(cwi, "out1", con, "in2", label="41")
        c42 = Connection(con, "out2", cwo, "in1", label="42")

        self.nw.add_conns(c41, c42)

        # 总线（bus）
        # 功率总线
        self.power = Bus("power")
        self.power.add_comps(
            {"comp": hpt, "char": -1}, {"comp": mpt, "char": -1},
            {"comp": lpt, "char": -1}, {"comp": pu1, "char": -1},
            {"comp": pu2, "char": -1}, {"comp": pu3, "char": -1}
        )

        # 加热总线
        self.heat = Bus("heat")
        self.heat.add_comps({"comp": sg, "char": 1})

        self.nw.add_busses(self.power, self.heat)

        # 设置组件效率和其他属性
        hpt.set_attr(eta_s=0.9)
        mpt.set_attr(eta_s=0.9)
        lpt.set_attr(eta_s=0.9)

        pu1.set_attr(eta_s=0.8)
        pu2.set_attr(eta_s=0.8)
        pu3.set_attr(eta_s=0.8)

        sg.set_attr(pr=0.92)

        con.set_attr(pr1=1, pr2=0.99, ttd_u=5)
        fwh1.set_attr(pr1=1, pr2=0.99, ttd_u=5)
        fwh2.set_attr(pr1=1, pr2=0.99, ttd_u=5)
        dsh.set_attr(pr1=0.99, pr2=0.99)

        # 设置初始条件
        c1.set_attr(m=200, T=650, p=100, fluid={"water": 1})  # 流量200kg/s，温度650°C，压力100bar，纯水
        c2.set_attr(p=20)                                     # 压力20bar
        c4.set_attr(p=3)                                      # 压力3bar

        c41.set_attr(T=20, p=3, fluid={"INCOMP::Water": 1})     # 温度20°C，压力3bar，不可压缩水
        c42.set_attr(T=28, p0=3, h0=100)                     # 温度28°C，初始压力3bar，初始比焓100kJ/kg

        # 参数化
        # 解决设计点
        self.nw.solve("design")
        self.stable = "_stable"
        self.nw.save(self.stable)
        self.solved = True
        self.nw.print_results()

    def get_param(self, obj, label, parameter):
        """获取网络中指定对象（组件或连接）的参数值
    
        Parameters
        ----------
        obj : str
            要获取参数的对象类型（Components/Connections）。
    
        label : str
            TESPy模型中对象的标签。
    
        parameter : str
            对象的参数名称。
    
        Returns
        -------
        value : float
            参数的值。
        """
        if obj == "Components":
            return self.nw.get_comp(label).get_attr(parameter).val
        elif obj == "Connections":
            return self.nw.get_conn(label).get_attr(parameter).val


    def set_params(self, **kwargs):
        """设置网络中组件或连接的参数
    
        Parameters
        ----------
        kwargs : dict
            包含要设置的参数的字典，键为"Components"或"Connections"，
            值为另一个字典，键为对象标签，值为参数字典。
        """
        if "Connections" in kwargs:
            for c, params in kwargs["Connections"].items():
                self.nw.get_conn(c).set_attr(**params)
    
        if "Components" in kwargs:
            for c, params in kwargs["Components"].items():
                self.nw.get_comp(c).set_attr(**params)


    def solve_model(self, **kwargs):
        """求解TESPy模型给定输入参数
    
        Parameters
        ----------
        kwargs : dict
            包含要设置的参数的字典，键为"Components"或"Connections"，
            值为另一个字典，键为对象标签，值为参数字典。
        """
        self.set_params(**kwargs)
    
        self.solved = False
        try:
            self.nw.solve("design")
            if not self.nw.converged:
                self.nw.solve("design", init_only=True, init_path=self.stable)
            else:
                # 可能需要更多的检查！
                if (
                        any(self.nw.results["Condenser"]["Q"] > 0)
                        or any(self.nw.results["Desuperheater"]["Q"] > 0)
                        or any(self.nw.results["Turbine"]["P"] > 0)
                        or any(self.nw.results["Pump"]["P"] < 0)
                    ):
                    self.solved = False
                else:
                    self.solved = True
        except ValueError as e:
            self.nw.lin_dep = True
            self.nw.solve("design", init_only=True, init_path=self.stable)

    def get_objective(self, objective=None):
        """获取当前目标函数的评估值
    
        Parameters
        ----------
        objective : str
            目标函数的名称。
    
        Returns
        -------
        objective_value : float
            目标函数的评估值。
        """
        if self.solved:
            if objective == "efficiency":
                return 1 / (
                    self.nw.busses["power"].P.val /
                    self.nw.busses["heat"].P.val
                )
            else:
                msg = f"Objective {objective} not implemented."
                raise NotImplementedError(msg)
        else:
            return np.nan

# %%[sec_3]

plant = SamplePlant()
plant.get_objective("efficiency")
variables = {
    "Connections": {
        "2": {"p": {"min": 1, "max": 40}},  # 连接2的压力范围：1到40 bar
        "4": {"p": {"min": 1, "max": 40}}   # 连接4的压力范围：1到40 bar
    }
}
constraints = {
    "lower limits": {
        "Connections": {
            "2": {"p": "ref1"}  # 连接2的压力不低于引用值 ref1
        },
    },
    "ref1": ["Connections", "4", "p"]     # 引用值 ref1 是连接4的压力
}

optimize = OptimizationProblem(
    plant, variables, constraints, objective="efficiency"
)

# %%[sec_4]
num_ind = 10  # 种群大小
num_gen = 100 # 每种群的进化代数

# 选择算法并进行参数设置，请参考 pygmo 文档！
# 算法中的 gen 参数表示每次进化过程中使用的代数数量
algo = pg.algorithm(pg.ihs(gen=3, seed=42))
# 创建初始种群
pop = pg.population(pg.problem(optimize), size=num_ind, seed=42)

optimize.run(algo, pop, num_ind, num_gen)

# %%[sec_5]
# 访问结果
print(optimize.individuals)
# 查看 pygmo 文档以了解可以从种群中获取的信息
pop

# 绘制结果
import matplotlib.pyplot as plt

# 设置字体大小
plt.rc("font", **{"size": 18})

fig, ax = plt.subplots(1, figsize=(16, 8))

# 过滤有效的约束条件和结果
filter_valid_constraint = optimize.individuals["valid"].values
filter_valid_result = ~np.isnan(optimize.individuals["efficiency"].values)
data = optimize.individuals.loc[filter_valid_constraint & filter_valid_result]

# 绘制散点图
sc = ax.scatter(
    data["Connections-2-p"],  # 连接2的压力
    data["Connections-4-p"],  # 连接4的压力
    c=1 / data["efficiency"] * 100,  # 效率的倒数乘以100作为颜色映射
    s=100  # 散点大小
)
cbar = plt.colorbar(sc)
cbar.set_label("Thermal efficiency in %")  # 色条标签

ax.set_axisbelow(True)
ax.set_xlabel("Pressure at connection 2 in bar")  # x轴标签
ax.set_ylabel("Pressure at connection 4 in bar")  # y轴标签
plt.tight_layout()

plt.show()
#fig.savefig("pygmo_optimization.svg")  # 保存图表为SVG文件
print(data.loc[data["efficiency"].values == data["efficiency"].min()])  # 打印最低效率的结果



