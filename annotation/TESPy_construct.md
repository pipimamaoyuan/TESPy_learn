```mermaid
graph LR;
    TESPy --> network;
    TESPy --> component;
    TESPy --> connnection;
    component --> basics;
    component --> heat_exchangers;
    component --> piping;
    component --> reactors;
    component --> turbomachinery;


    basics --> cycle_closer;
    basics --> sink;
    basics --> source;

    heat_exchangers --> heat_cexchangers_base;
    heat_cexchangers_base --> condenser;
    heat_cexchangers_base --> desuperheater;

    heat_exchangers --> simple;
    simple --> solar_collector;
    simple --> parabolic_though;

    piping --> pipe;
    piping --> valve;

    turbomachinery --> turbomachinery_base;
    turbomachinery_base --> pump;
    turbomachinery_base --> turbine;
    turbomachinery_base --> compressor;
```

``` mermaid
graph LR;
    TESPy --> network;
    TESPy --> component;
    TESPy --> connnection;
    component --> basics;
    component --> heat_exchangers;
    component --> piping;
    component --> reactors;
    component --> turbomachinery;

    basics --> cycle_closer回路闭合器;
    basics --> sink汇;
    basics --> source源;

    heat_exchangers --> heat_exchangers_base;
    heat_exchangers_base --> condenser冷凝器;
    heat_exchangers_base --> desuperheater过热蒸汽降温器;

    heat_exchangers --> simple;
    simple --> solar_collector太阳能集热器;
    simple --> parabolic_though抛物面集热器;

    piping --> pipe管道;
    piping --> valve阀门;

    turbomachinery --> turbomachinery_base;
    turbomachinery_base --> pump泵;
    turbomachinery_base --> turbine湍轮机;
    turbomachinery_base --> compressor压缩机;
```