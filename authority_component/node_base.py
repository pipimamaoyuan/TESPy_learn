# TESPy node base 类

# node base 类 是所有节点的基类，它包含了节点的基本属性和方法。

# 质量流量平衡 ：
# 进入节点的所有流体的质量流量之和 = 离开节点的所有流体的质量流量之和
# def mass_flow_func(self)

# 压力平衡：
# 节点的所有入口和出口的压力都等于第一个入口的压力
# def pressure_equality_func(self):