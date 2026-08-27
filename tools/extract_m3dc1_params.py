#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import re
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DOCUMENTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DOCUMENTS_ROOT.parent
ROOT = REPO_ROOT / "M3DC1"
INPUT_F90 = ROOT / "unstructured/input.f90"
DOC_INPUTS = ROOT / "doc/inputs.tex"
OLD_DOC = DOCUMENTS_ROOT / "tools/reference_old_doc.txt"
OUTDIR = DOCUMENTS_ROOT / "docs-data"
DOC_AUDIT_MD = OUTDIR / "M3DC1_official_doc_vs_source_audit.md"
USAGE_MD = OUTDIR / "M3DC1_parameter_source_usage.md"
USAGE_CSV = OUTDIR / "m3dc1_parameter_source_usage.csv"
HTML_GUIDE = OUTDIR / "M3DC1_C1input_reader_guide.html"
SIMPLIFIED_MD = OUTDIR / "M3DC1_C1input_parameters_simplified.md"
SIMPLIFIED_CSV = OUTDIR / "m3dc1_c1input_parameters_simplified.csv"
SIMPLIFIED_HTML = OUTDIR / "M3DC1_C1input_simplified_guide.html"
PUBLISHED_HTML = DOCUMENTS_ROOT / "index.html"


CONSTANTS = {
    "maxcoils": "2000",
    "imax_wall_breaks": "20",
    "imax_wall_regions": "20",
    "max_zones": "100",
    "max_bounds": "1000",
    "imag_probes_max": "100",
    "iflux_loops_max": "100",
    "maxqs": "32",
    "imode_filter_max": "100",
    "BOUND_UNKNOWN": "0",
    "ZONE_UNKNOWN": "0",
}


GROUP_TRANSLATIONS = {
    "Model Options": "模型选项",
    "Equilibrium": "平衡与初始条件",
    "Grad-Shafranov Solver": "Grad-Shafranov 求解器",
    "Transport Coefficients": "输运系数",
    "Hyper Diffusivity": "超扩散",
    "Normalizations": "归一化",
    "Boundary Conditions": "边界条件",
    "Time Step": "时间推进",
    "Mesh": "网格",
    "Solver": "线性求解器",
    "Mesh Adaptation": "网格自适应",
    "Numerical Options": "数值选项",
    "Input": "输入文件/剖面读入",
    "Output": "输出与重启",
    "Diagnostics": "诊断",
    "Sources/Sinks": "源项/汇项",
    "Resistive Wall": "电阻壁/真空/导体区",
    "Miscellaneous": "杂项物理参数",
    "Deprecated": "已废弃兼容参数",
    "Trilinos Options": "Trilinos 选项",
    "PRAD Options": "PRAD 简单辐射模型",
    "KPRAD Options": "KPRAD 辐射/杂质模型",
    "Particle Simulation Options": "粒子模拟选项",
}


GROUP_NOTES = {
    "Normalizations": "这些量定义 M3D-C1 默认归一化：B0_norm=10^4 G、n0_norm=10^14 cm^-3、L0_norm=100 cm；多数物理输入/输出使用归一化单位。",
    "Input": "控制是否从 geqdsk/dskbal/jsolver 及 profile_* 文件读入平衡、剖面、源项等。实际文件名多为固定约定，例如 geqdsk、profile_ne、profile_te、profile_p、profile_f、profile_j。",
    "Model Options": "控制求解的 MHD 方程组、线性/非线性、two-fluid、bootstrap、runaway、温度/压力模型等。",
    "Equilibrium": "选择/缩放初始平衡、外场、RMP、stellarator 场、basicj 模型以及初始扰动。",
    "Grad-Shafranov Solver": "控制 GS 迭代、轴/限制器/X 点、压力/电流/旋转/密度剖面及反馈参数。",
    "Transport Coefficients": "粘性、电阻率、热导、粒子扩散等输运模型参数；若使用函数型模型，开关参数决定下面系数的解释。",
    "Hyper Diffusivity": "磁场、压力和速度方程中的超扩散/平滑系数及其缩放方式。",
    "Boundary Conditions": "场、压力/温度/密度、速度和电流在计算边界上的约束。",
    "Time Step": "时间积分、分裂/非分裂推进、可变时间步、矩阵/预条件器重算及线性增长率停止条件。",
    "Numerical Options": "积分点数、守恒/规整化、物理量 floor、线性模拟重标定等数值控制。",
    "Mesh": "主程序读取已有 mesh/model 文件；mesh 生成工具的 input 文件格式另见附录。",
    "Solver": "M3D-C1 内部线性求解器通用控制。",
    "Mesh Adaptation": "SCOREC/SPR 网格自适应控制；部分参数仅在启用对应库/流程时有效。",
    "Output": "HDF5/标量/辅助变量输出、重启读写、调试打印和 Slurm 超时写时间片。",
    "Diagnostics": "X-ray、磁探针、磁通环等诊断的几何参数。",
    "Sources/Sinks": "回路电压/电流控制、pellet、束源、电流驱动、高斯热源、粒子源/汇、ionization 等。",
    "Resistive Wall": "真空、导体壁、多区域、wall break、RE killer coil 等电阻参数。",
    "Trilinos Options": "Trilinos 编译/运行路径下的 Krylov 与预条件器选项。",
    "PRAD Options": "简单单杂质辐射模型。",
    "KPRAD Options": "KPRAD 杂质电离/复合/辐射与中性粒子演化控制。",
    "Particle Simulation Options": "仅在 USEPARTICLES 编译时注册。",
    "Deprecated": "仍可被解析以兼容旧输入，但新算例不建议使用。",
}

LOGICAL_GROUP_ORDER = [
    "Normalizations",
    "Mesh",
    "Input",
    "Equilibrium",
    "Grad-Shafranov Solver",
    "Model Options",
    "Transport Coefficients",
    "Hyper Diffusivity",
    "Boundary Conditions",
    "Resistive Wall",
    "Time Step",
    "Numerical Options",
    "Solver",
    "Trilinos Options",
    "Mesh Adaptation",
    "Sources/Sinks",
    "PRAD Options",
    "KPRAD Options",
    "Particle Simulation Options",
    "Diagnostics",
    "Output",
    "Miscellaneous",
    "Deprecated",
]


MANUAL_USAGE = {
    "iread_eqdsk": "托卡马克：轴对称 g-file 平衡入口。1 直接投影 `geqdsk`；2 读入 gfile 后在 GS 中改用默认压力/F；3 不使用 `psirz`，只取磁轴、电流和剖面重新求解 GS。仿星器：必须为 0；非零值的执行优先级高于 `itaylor=40/41`。",
    "iread_dskbal": "托卡马克：旧 BAL 平衡入口。1 使用文件 psi、F、FF′、ne 并由 ne(Te+Ti) 计算压力；2 压力/F 改用默认剖面；两者都调用 GS。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化。",
    "iread_jsolver": "托卡马克：旧 Jsolver 平衡入口，读取 `fixed`；`igs>0` 时 1 使用文件 p/F、2 改用默认 p/F，`igs=0` 时直接投影。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化。",
    "iread_omega": "托卡马克：仅 GS 且 `irot!=0` 时读取，模式 1/2/3/4/5/20 分别对应 `profile_omega`、`dtrot.xy`、`profile_vphi`、rho 文件、带表头文件和 `iterdb`，之后乘 `vscale`。仿星器：VMEC 与 `itaylor=41` 路径均不读取。",
    "iread_omega_e": "托卡马克：文件模式同 `iread_omega`，随后扣除完整抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_ExB` 严格互斥。",
    "iread_omega_ExB": "托卡马克：文件模式同 `iread_omega`，随后扣除离子抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_e` 严格互斥。",
    "iread_ne": "托卡马克：GS 使用 1/2/4/10/20 读取 psi、rho、Corsica 或 iterdb 密度。仿星器：固定边界 VMEC 用 21 读取 `n_profile(s)`；21 不用于 `itaylor=41`，该路径可用 22 的 `n_profile(s)` 或 23 的 `n_profile_vs_p` 在平衡后重写密度。两种装置中 `den_edge>0` 均与非零值冲突。",
    "iread_te": "托卡马克：GS 使用 1/2/4/10/20 读取不同坐标和单位的 Te。仿星器：仅固定边界 VMEC 的 21 读取 `te_profile(s)`；自由边界路径不读取。两种装置中 `tedge>0` 均与非零值冲突。",
    "iread_p": "托卡马克：GS 中 1 读取 `profile_p(psi_N,p)`，替换 gfile/旧平衡或默认压力剖面。仿星器：固定边界 VMEC 中 21 读取 `p_profile(s,p)` 并替换 wout 的 `presf` 压力场，但不改变几何和磁场；自由边界路径不读取。",
    "iread_f": "托卡马克：GS 中 1 读取 `profile_f(psi_N,F)`，其中 F 满足 \\(F=R B_\\phi\\)；该文件替换 F，并按最外点重设 `bzero`。仿星器：不读取，VMEC 磁场仍来自 wout，`itaylor=41` 磁场来自外场文件。",
    "iread_j": "托卡马克：常规轴对称 GS 不使用；仅非托卡马克圆柱测试路径 `itor=0,itaylor=33` 读取 `profile_j(r,J_phi)`。仿星器：不使用。",
    "iread_heatsource": "托卡马克：1 读取 `profile_heatsource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘 `ghs_rate` 并与其他热源相加，且只在非线性压力/温度方程中生效。",
    "iread_particlesource": "托卡马克：1 读取 `profile_particlesource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘输入参数 `pellet_rate` 并与其他密度源相加，且要求 `idens=1,linear=0`。",
    "iread_neo": "托卡马克：1 读取三类 NEO 输出和 GYRO `input.profiles`；环向速度叠加到已有 `vz`，极向速度重写 `u/chi`，非 plasma 磁区置零。仿星器：没有与 VMEC 逻辑坐标配套的专用实现，建议保持 0。",
    "ineo_subtract_diamag": "托卡马克：仅 `iread_neo=1,db!=0` 时从 NEO 环向速度扣除离子抗磁贡献。仿星器：随 `iread_neo` 保持 0。",
    "numvar": "1: 2-field；2: 4-field/reduced MHD；3: 6-field/compressible MHD。",
    "linear": "0 非线性；1 线性化方程。2D 非线性通常需 RL=1；线性/complex 需 COM=1 且 `nplanes=1`。",
    "eqsubtract": "线性模拟会在校验阶段强制置 1；非线性时设 1 表示从方程中扣除平衡场。",
    "ipressplit": "仅 `isplitstep=1` 且 `numvar=3` 时允许；把压力/温度求解从场求解分离。",
    "itemp": "1 时推进温度而不是压力；要求 `ipressplit=1`，且 `z_ion` 必须为 1。",
    "kinetic": "1: kinetic PIC hot ion pressure；2: incompressible CGL；3: full CGL。2/3 要求 linear=1,isplitstep=0,ipres=1,itemp=0,ipressplit=0。",
    "irestart": "0 从头启动；1 从 HDF5 restart；2 用 restart 初始化 GS；3 用 2D real restart 初始化 2D complex。",
    "irestart_slice": "-1 使用最后一个 time slice；否则从指定 `time_nnn.h5` restart。",
    "nplanes": "托卡马克：2D/complex 线性取 1，真实三维非线性取大于 1 的环向平面数。仿星器：表示所选环向计算域内的平面数，通常必须大于 1；需足以解析 VMEC/外场的最高环向模。3D+PETSc 当前要求 MPI 进程数等于 `nplanes`。",
    "nperiods": "托卡马克：通常取 1。仿星器：表示整环面被划分的周期数；当 `ifull_torus=0` 时实际只计算 `1/nperiods` 环面，且 VMEC 的 `nfp` 必须能被它整除。",
    "ifull_torus": "托卡马克：通常取 1；取 0 只有在明确采用周期扇区时才有意义。仿星器：0 计算一个由 `nperiods` 定义的周期扇区，1 计算完整环面；它控制环向域长度，不改变 VMEC 几何本身。",
    "iread_vmec": "托卡马克：保持 0，gfile 不通过该参数读取。仿星器：1 时从 `vmec_filename` 读取 VMEC 几何，并在固定边界初始化中同时提供平衡磁场和压力；通常与 `igeometry=1` 配合。",
    "vmec_filename": "托卡马克：不使用。仿星器：`iread_vmec=1` 时的 VMEC NetCDF 文件名；几何映射读取 R/Z 傅里叶系数、场周期和磁场系数，固定边界还使用其中的压力和磁场。",
    "igeometry": "托卡马克：标准物理 R-Z 网格取 0，网格坐标不再映射。仿星器：取 1，先把二维 mesh 坐标解释为逻辑圆盘，再由 VMEC/边界傅里叶数据映射为物理 R-Z；取 2 是求解 Laplace 几何的内部路径，不是常规 VMEC 设置。",
    "xcenter": "托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 x 坐标，逻辑 rho 由 `sqrt((x-xcenter)^2+(z-zcenter)^2)` 计算；必须与生成逻辑 mesh 时采用的圆心一致。",
    "zcenter": "托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 z 坐标，与 `xcenter` 共同定义 rho 和 theta；必须与逻辑 mesh 圆心一致。",
    "bloat_factor": "托卡马克：不使用。仿星器：把 VMEC 几何径向外推到放大的计算边界；0 不按比例扩展。固定边界 `itaylor=40` 的检查要求它为 0；自由边界/外场域可非零。若同时给 `bloat_distance`，后者优先并把本参数置 0。",
    "bloat_distance": "托卡马克：不使用。仿星器：沿 VMEC 磁面外法向按距离扩展计算边界，并覆盖 `bloat_factor` 的作用。固定边界 case 建议保持 0；外扩域不会自动生成真空、壁或 LCFS 的 zone 标签。",
    "nzer_factor": "托卡马克：不使用。仿星器：控制 VMEC R/Z 几何转为 Zernike 径向表示的阶数；非负时取 `n_zer=mpol*nzer_factor`，但仅在 `nzer_manual<0` 时使用。-1 采用程序默认。",
    "nzer_manual": "托卡马克：不使用。仿星器：手动指定 VMEC 几何的 Zernike 径向阶数；只有不低于程序默认阶数时才覆盖默认值，且优先于 `nzer_factor`。主要用于分辨率测试。",
    "iread_planes": "托卡马克：3D 时 1 从 `plane_positions` 读取每个环向平面角度；否则均匀或按 toroidal packing 生成。仿星器：用法相同，但每个角度必须位于当前完整环面或周期扇区的范围内，文件行数必须等于 `nplanes`。",
    "xzero": "托卡马克：某些解析初值、诊断和参考轴使用的 R 参考位置；不会移动 `mesh_filename` 中的节点，也不能用来使 mesh 对齐 gfile。仿星器：逻辑映射中心应使用 `xcenter`，本参数通常保持默认，仅少数测试/诊断使用。",
    "zzero": "托卡马克：某些解析初值、诊断和参考轴使用的 Z 参考位置；不会平移已读入 mesh。仿星器：逻辑映射中心应使用 `zcenter`，本参数通常保持默认。",
    "tiltangled": "托卡马克：给矩形测试网格的边界法向加入旋转角，不会旋转任意外部 mesh 的节点。仿星器：VMEC 曲边界使用映射几何法向，通常保持 0。",
    "mesh_filename": "托卡马克：二维物理 R-Z 有限元 mesh 文件；几何范围应覆盖目标等离子体、真空和壁区域并落在所需平衡数据范围内。仿星器：二维逻辑圆盘 mesh 文件，通常外边界 rho=1，随后映射为三维物理几何。",
    "mesh_model": "托卡马克：与 `mesh_filename` 配套的几何模型，保存边界实体和 zone 拓扑。仿星器：与逻辑 mesh 配套的模型；模型标签定义逻辑分区，不会根据 VMEC 自动改成物理 plasma/vacuum/conductor 分区。",
    "model_info": "托卡马克：仅 `USECADMODEL` 编译路径加载的额外 CAD model-info 文件，普通 `.dmg/.txt` 工作流不设置。仿星器：条件和用途相同，不参与 VMEC 几何映射。",
    "ipartitioned": "托卡马克：当前主源码只注册和保存该值，活动的 SCOREC `load_mesh` 没有按它分支。仿星器：行为相同，也不能用它切换逻辑 mesh 的装载方式；两者都应直接提供与运行方式匹配的 mesh 文件。",
    "imatassemble": "托卡马克：0 使用 SCOREC、1 使用 PETSc 进行并行矩阵装配，不改变物理 R-Z mesh。仿星器：后端选择相同，不改变逻辑到物理的几何映射、区域或平衡场。",
    "is1_agg_blks": "托卡马克：仅 `REORDERED` 编译时注册，设置 S1 矩阵每节点自由度聚合块数。仿星器：用法相同；只影响求解性能，不改变物理网格或 VMEC 映射。",
    "is1_agg_scp": "托卡马克：仅 `REORDERED` 编译时注册；0 每 MPI rank、1 每环向平面、2 全局聚合。仿星器：取值相同，按所选周期域的平面组织聚合；不改变几何。",
    "imulti_region": "托卡马克：0 时全部单元自动视为 plasma；1 时必须用 `boundary_type/zone_type` 明确等离子体、真空和导体区，适合第一壁/电阻壁计算。仿星器：语法相同，但标签只分类逻辑 mesh 的既有单元，程序不会根据 VMEC LCFS 或外场自动判定区域；必须先保证映射后的物理位置合理。",
    "toroidal_pack_factor": "托卡马克：3D 且 `iread_planes=0` 时，>1 在 `toroidal_pack_angle` 附近加密环向平面；1 均匀。仿星器：作用相同，但需在所选周期域内兼顾 VMEC/外场模数解析；不改变二维截面网格。",
    "toroidal_pack_angle": "托卡马克：`toroidal_pack_factor>1` 且未读 `plane_positions` 时的最大环向加密角，必须位于托卡马克计算域内。仿星器：定义相同，但角度必须位于当前完整环面或场周期扇区内。",
    "boundary_type": "托卡马克：`imulti_region=1` 时按几何边编号标记 1=第一壁、2=计算域外边界；它决定边界条件作用位置。仿星器：取值相同，但标记的是逻辑模型边，映射后才成为物理边界；不会自动等于 VMEC LCFS。",
    "zone_type": "托卡马克：`imulti_region=1` 时按 zone 编号标记 1=plasma、2=conductor、3=vacuum。仿星器：取值相同，但必须由用户确认逻辑 zone 经 VMEC/bloat 映射后确实落在相应物理区域；程序只检查标签是否存在，不检查与平衡的一致性。",
    "ntor": "2D/complex 线性模拟的环向模数；RMP 等也会使用。",
    "mpol": "若干测试/外场/REKC 设置中使用的极向模数。",
    "jadv": "1 使用环向电流密度方程代替极向磁通方程；默认值为 1。",
    "imp_mod": "源码当前默认 1。0: standard/theta implicit；1: Caramana split-step 形式。",
    "pskip": "控制预条件器重算与复用周期；默认值为 0。",
    "ntimers": "0 表示校验后取 `ntimepr`；否则为 restart 输出周期。",
    "ifout": "-1 表示校验后按编译维度默认：3D 输出 f，2D 不输出；也可显式 0/1。",
    "ifbound": "-1 表示校验后按编译版本设置：complex 为 2，real 为 1。",
    "rzero": "-1 表示校验后自动设置：toroidal 几何取 `xzero`，否则取 1。",
    "eta_wallRZ": "-1 表示校验后取 `eta_wall`。",
    "wall_region_etaRZ": "-1 表示校验后逐区域取对应 `wall_region_eta(i)`。",
    "eta_max": "若 <=0，校验阶段置为 `eta_vac`。",
    "eta_min": "若 <=0，校验阶段置为 0。",
    "kappa_max": "若 <=0，校验阶段置为 `kappar`。",
    "kappar_max": "若 <=0，校验阶段置为 `kappar`。",
    "kappar_min": "若 <=0，校验阶段置为 `kappar`。",
    "db": "源码默认 -1，表示按物理归一化自动计算 ion skin depth 并乘以 `db_fac`；若显式给非负值则覆盖。",
    "db_fac": "`db<0` 时乘在物理 ion skin depth 上；默认 0 等价于关闭 two-fluid skin-depth 贡献。",
    "control_type": "-1 不启用电流控制；0 旧算法；1 标准 PID，配合 `control_p/i/d`。",
    "n_control_type": "-1 不启用密度控制；0 旧算法；1 标准 PID，配合 `n_control_p/i/d`。",
    "iread_pellet": "0 用标量 pellet_* 定义单 pellet；1 读 `pellet.dat`，每行一个 pellet，列为 r,phi,z,rate,var,var_tor,velr,velphi,velz,r_p,cloud_pel,pellet_mix,cauchy_fraction。",
    "irestart_pellet": "restart 时仍从 C1input 覆盖部分 pellet 参数，如 pellet_rate、pellet_var_tor、pellet_var、cloud_pel、pellet_mix、cauchy_fraction。",
    "ikprad": "0 关闭；1 使用 KPRAD；-1 需 USEADAS 编译，使用 ADAS 数据。",
    "ikprad_max_dt": "0 用 MHD dt；1 推荐用 dt/(kprad_z+1)；也可配合 `kprad_max_dt` 显式限制。",
    "ikprad_min_option": "1 低 ne/Te 时无辐射/电离/复合；2 推荐：允许复合但无辐射/电离；3 按 subcycling 中 ne/Te 判断无辐射/电离/复合。",
    "ikprad_evolve_neutrals": "0 中性粒子不对流不扩散；1 推荐：同其它电荷态对流扩散；2 只扩散不对流。",
    "iprad": "1 启用 Teng PRAD 单杂质辐射模型；当前 PRAD 表中 C/Ar/Fe 常用。",
    "prad_z": "PRAD 杂质电荷数；源码警告只实现 6、18、26。",
    "itaylor": "选择预置初始条件/平衡：toroidal 几何中 1 常用于 GS，40/41 为 stellarator；slab/cylindrical 下有 Taylor、GEM、wave、RWM、basicJ 等测试平衡。",
    "idevice": "-1 读 coil.dat/current.dat；0 generic；1 CDX-U；2 NSTX；3 ITER；4 DIII-D（按文档）。",
    "irmp": "1 在等离子体内应用非轴对称 RMP/error field；2 仅边界应用真空 mpol/ntor 场。常配合 `type_ext_field`、RMP 文件和 `ntor`。",
    "type_ext_field": "-1 默认；0 tokamak RMP/error field；1 free-boundary stellarator FIELDLINES/MGRID total field；2 stellarator total+external subtraction。",
    "file_ext_field": "stellarator/free-boundary 场文件名，默认 `error_field`；支持 fieldlines/mgrid 前缀。",
    "file_total_field": "stellarator total field 文件名，默认 `total_field`；支持 fieldlines/mgrid 前缀。",
    "eta_zone": "托卡马克：为 `zone_type(i)=2` 的导体 zone 指定标量电阻率，正值优先于全局 `eta_wall`；适合显式第一壁/导体区域。仿星器：数值优先级相同，但只有用户事先设计了与 VMEC/bloat 映射后物理位置一致的导体 zone 才有物理意义。",
    "etaRZ_zone": "托卡马克：为导体 zone 指定极向电阻率，正值优先于 `eta_zone`，否则回退到全局 `eta_wallRZ`。仿星器：用法相同，但程序不会检查该 zone 是否真的对应物理导体壁。",
    "wall_region_filename": "字符数组；每个 wall region 轮廓点文件名。",
    "imag_probes": "磁探针数量；对应数组用 `mag_probe_x(i)` 等一基索引给出。",
    "iflux_loops": "磁通环数量；对应数组用 `flux_loop_x(i)`、`flux_loop_z(i)` 一基索引给出。",
}

# Equilibrium is the bridge between the already-loaded input/mesh and the
# evolved MHD state. Keep device-specific behavior explicit in every card.
MANUAL_USAGE.update({
    "itaylor": "托卡马克：当三个外部平衡入口均为 0 时选择内置初始化；`itaylor=1` 进入 GS，19 为 Solovev，24 为 RWM，29/31 为 basicJ，-1 为常量场。仿星器：40 直接投影固定边界 VMEC 平衡；41 从三维 total/external field 初始化，程序不求解 VMEC 自由边界平衡。",
    "iupstream": "托卡马克与仿星器：环向数值上风/稳定化开关，不选择平衡。0 关闭；1 把 `magus` 给出的人工环向二阶项加到已有系数；2 用该人工项替代相应系数。它在时间演化算子中生效。",
    "magus": "托卡马克与仿星器：`iupstream=1/2` 时人工环向二阶稳定项的无量纲强度；常与局部场或速度绝对值相乘。0 不一定关闭，关闭应设 `iupstream=0`。",
    "iflip": "托卡马克与仿星器：新启动时把坐标系手性翻转，统一反号 psi、环向场、速度势和环向速度，并反号 `vloop/tcur`；这是整体坐标约定变换，不等同于单独反转 B、J 或 V。restart 路径不再次调用该初始翻转。",
    "iflip_b": "托卡马克：平衡和已构造外场的环向磁场反号。仿星器：固定 VMEC 或外场初始化后同样反转环向场分量；必须确保输入场、诊断和模数符号约定一致。",
    "iflip_j": "托卡马克：反转平衡极向磁通，从而反转环向电流；`icsubtract=1` 时线圈磁通也反号。gfile 负电流已自动处理，`iflip_j=1` 会中止并提示用 2 强制覆盖。仿星器：同样反转 psi 表示，通常不应把它当作重新求解电流剖面。",
    "iflip_v": "托卡马克与仿星器：1 反转平衡环向速度；-1 把平衡环向速度清零；0 保持初始化结果。它在平衡与 NEO 速度处理完成后执行。",
    "iflip_z": "托卡马克：当前源码只在 gfile 初始化中令 `zmaxis=-zmaxis`，并未同时镜像 `psirz`、mesh 或其它场，不能视为完整的上下翻转。仿星器：VMEC/外场路径没有活动使用。",
    "icsym": "托卡马克：控制 `eps` 初始扰动的上下对称性，0 无约束，1 仅给 U 加奇对称扰动，2 仅给 U 加偶对称扰动，3 使用确定性的 (1,1) 型扰动。仿星器：取值相同，但随机形状在逻辑网格坐标中构造后映射到物理空间。",
    "bzero": "托卡马克：解析/GS 初始化的参考环向场，通常表示 `rzero` 处 Bphi；gfile 会以最外层 `fpol/rmaxis` 覆盖它，`profile_f` 与 GS 磁场缩放还可再次改写。仿星器：固定 VMEC 的 B 直接来自 wout，三维外场来自场文件，本参数不替代这些数据；TF 倾斜/平移解析误差场仍会用到它。",
    "bx0": "托卡马克：仅 wave、3D diffusion 等内置测试平衡的初始 x 向磁场幅值，gfile/GS 生产路径不使用。仿星器：`itaylor=40/41` 不使用。",
    "vzero": "托卡马克：若干解析初始化的环向/轴向速度标度；basicJ 用作核心平坦转动值，`itaylor=-1` 直接作为均匀环向速度。gfile/GS 的文件旋转由 Input 组控制。仿星器：VMEC/外场路径不从本参数建立旋转。",
    "phizero": "托卡马克：FRS、FTZ、eigen 等测试初始化中速度流函数 U 的扰动幅值；常规 gfile/GS 不使用。仿星器：`itaylor=40/41` 不使用。",
    "verzero": "托卡马克与仿星器：在 `init_perturbations` 中向 plasma zone 的扰动速度势加入 `R*verzero`，用于给定初始竖直速度；它是扰动层，不会改变读入平衡或 LCFS。",
    "v0_cyl": "托卡马克：只在 fixed-q/cylindrical 测试剖面中作为中心轴向速度常数项；gfile/GS 不使用。仿星器：`itaylor=40/41` 不使用。",
    "v1_cyl": "托卡马克：只在 fixed-q/cylindrical 测试剖面中作为随归一化磁通变化的速度幅值，形式为 `v0_cyl+v1_cyl*psi^beta`。仿星器：`itaylor=40/41` 不使用。",
    "idevice": "托卡马克：只服务 GS/PF 线圈场。当前源码实际实现 -1 读取 `coil.dat/current.dat`，0 使用 generic dipole；其它值进入无 PF 线圈的默认分支。仿星器：VMEC/三维场初始化不使用该设备选择。",
    "iwave": "托卡马克与仿星器生产平衡均不使用；只为 wave 测试初始化选择波支，具体可用取值随二维/三维测试例程而异。",
    "eps": "托卡马克：初始随机/确定性扰动幅度；`itor=0,irmp=2` 时还作为解析 m/n 真空场幅度。仿星器：固定 VMEC 和 total-field 路径也可用它给 plasma zone 添加初始流扰动，但不改变 wout/外场基态。",
    "maxn": "托卡马克与仿星器：`icsym=0/1/2` 随机初始扰动的模循环上限，值越大包含的平面波越多、初始化代价越高；不控制 M3D-C1 实际环向网格分辨率。",
    "irmp": "托卡马克：1 读取/计算 RMP 与 error field 并投影到整个计算域；2 仅 `itor=0` 可用，在整个域评价解析 mpol/ntor 真空场。仿星器：`itaylor=41,type_ext_field=1,extsubtract=0` 已装入 total field 后会跳过第二次 RMP；固定 VMEC 或 subtraction 路径可另行调用外场处理。",
    "rmp_atten": "托卡马克与仿星器环形生产路径不使用；只在 `itor=0,irmp=2` 中控制解析真空扰动从 r=1 起的指数因子。0 表示不加该衰减/增长因子。",
    "tf_tilt": "托卡马克：TF 线圈相对竖直方向的小倾斜角，单位度；源码据此构造非轴对称误差场并在基态后加入，不移动 mesh。仿星器：不是 VMEC 场线圈几何参数，通常保持 0。",
    "tf_tilt_angle": "托卡马克：`tf_tilt` 的旋转轴环向方位，单位度，只在 `tf_tilt!=0` 时生效。仿星器：通常不使用。",
    "tf_shift": "托卡马克：TF 线圈水平平移幅度，用解析式生成误差场，不改变 mesh 或 GS 线圈坐标。仿星器：通常不使用。",
    "tf_shift_angle": "托卡马克：`tf_shift` 的平移方向方位角，单位度，只在 `tf_shift!=0` 时生效。仿星器：通常不使用。",
    "pf_tilt": "托卡马克：PF 线圈逐线圈倾斜角数组，单位度；只有已经由 GS/`idevice=-1` 装载到 PF 线圈表的线圈才会产生误差场。仿星器：VMEC/外场路径没有 PF 线圈表，通常不使用。",
    "pf_tilt_angle": "托卡马克：每个 `pf_tilt(i)` 的旋转轴方位角数组，单位度，索引对应线圈组标签。仿星器：通常不使用。",
    "pf_shift": "托卡马克：PF 线圈逐线圈水平平移数组；基于已加载线圈场导数构造非轴对称误差场，不修改轴对称 GS 线圈位置。仿星器：通常不使用。",
    "pf_shift_angle": "托卡马克：每个 `pf_shift(i)` 的平移方向方位角数组，单位度。仿星器：通常不使用。",
    "iread_ext_field": "托卡马克：对 `type_ext_field<=0` 表示要读的 error-field 数据组数；1 读 `error_field`，大于 1 读 `error_field01...`。仿星器：`itaylor=41` 必须非零，当前读取器实际只装载索引 `iread_ext_field`，常规用法应取 1。",
    "isample_ext_field": "托卡马克：Schaffer error-field 数据的环向降采样因子。仿星器：仅场文件回退到 Schaffer 格式时使用；FIELDLINES/MGRID/HINT/MIPS 专用读取器不使用该因子。",
    "isample_ext_field_pol": "托卡马克：Schaffer error-field 数据的极向降采样因子。仿星器：仅 Schaffer 回退格式使用，专用三维场读取器不使用。",
    "scale_ext_field": "托卡马克与仿星器：投影已读场数据时统一乘的幅值因子；会作用于该读取器装入的 `file_total_field/file_ext_field/error_field`，但不缩放 gfile 或 `itaylor=40` 直接读取的 wout 基态，也不重新求解平衡。",
    "shift_ext_field": "托卡马克与仿星器：各外场数据组的环向相位平移数组，单位度；3D 中通过改变取样角实现，complex 中转化为所选 `ntor` 的相位因子。",
    "type_ext_field": "托卡马克：<=0 走 RMP/error-field；3 可从 `external_j` 电流数据求外场。仿星器：1 在 `itaylor=41` 中直接把 `file_total_field` 作为 total field；2 要求 `extsubtract=1`，先装 total field、再读 `file_ext_field` 并保存/扣除外场。",
    "file_ext_field": "托卡马克：`type_ext_field<=0` 时此名称被忽略，文件名固定为 `error_field` 或 `error_fieldNN`。仿星器：`type_ext_field=2` 的真空/外部场文件；文件名前缀选择 FIELDLINES、MIPS、HINT、MGRID 读取器，其它名称按 Schaffer 格式。",
    "file_total_field": "托卡马克：常规 RMP/GS 不使用。仿星器：`itaylor=41,type_ext_field=1/2` 的总磁场文件；1 直接作为基态，2 与 `file_ext_field` 组成 total-minus-external 的演化场分解。",
    "beta": "托卡马克：仅 tilting/fixed-q 等模型平衡或测试问题中的无量纲形状/速度幂参数，不是由 gfile 得到的等离子体 beta，也不会覆盖压力。仿星器：`itaylor=40/41` 不使用。",
    "ln": "托卡马克：多个解析/测试平衡的特征径向尺度；basicJ 中是电流剖面半径，Solovev 中控制横向尺寸。它不是自然对数。仿星器：VMEC/外场平衡不使用，但 `icsym=3` 扰动包络仍可能引用。",
    "elongation": "托卡马克：仅 `itaylor=19` Solovev 解析平衡的伸长率。仿星器：VMEC 几何由傅里叶系数给出，本参数不使用。",
    "basicj_nu": "托卡马克：`itaylor=29/31` 电流剖面指数；若 `basicj_qa!=0` 会由 q0/qa 关系覆盖。仿星器：`itaylor=40/41` 不使用。",
    "basicj_j0": "托卡马克：basicJ 轴上电流密度幅值；若 `basicj_q0!=0`，源码用 `2*bzero/(rzero*q0)` 覆盖本值。仿星器：不使用。",
    "basicj_q0": "托卡马克：basicJ 轴上安全因子；非零时优先于 `basicj_j0` 并反算轴上电流。0 表示由 `basicj_j0` 反算 q0。仿星器：不使用。",
    "basicj_qa": "托卡马克：basicJ 目标边缘安全因子；非零时覆盖 `basicj_nu`。`itaylor=31` 且显式给 `xlim!=0` 时源码会报错。仿星器：不使用。",
    "basicj_voff": "托卡马克：basicJ 核心平坦环向速度区的径向范围；范围内速度基值为 `vzero`。仿星器：不使用。",
    "basicj_vdelt": "托卡马克：basicJ 平坦转动区外速度衰减宽度相对 `ln` 的系数，进入高斯型衰减分母。仿星器：不使用。",
    "basicj_dexp": "托卡马克：basicJ 专用输运系数径向缩放函数的幂指数，配合 `basicj_dvac` 使黏性/热传导向外变化；不改变初始密度场本身。仿星器：不使用。",
    "basicj_dvac": "托卡马克：basicJ 专用输运系数缩放函数在 `r=ln` 处的目标倍率，影响相关黏性与热传导系数，不是外部真空区密度。仿星器：不使用。",
    "ibasicj_solvep": "托卡马克：仅 `itaylor=29/31`。0 使用解析压力并由给定 J 求 F；1 令 F 均匀并由 J 求压力。`itaylor=29` 的解析压力为常数，`itaylor=31` 的解析压力随半径衰减。仿星器：不使用。",
    "igs": "托卡马克：大于 0 时给出 GS 最大迭代次数，收敛误差达到 `tol_gs` 可提前退出；0 不求解 GS。它与 Input 的平衡入口、Boundary 的 `ifixedb`、Mesh 的 zone 共同决定初始平衡。仿星器：`itaylor=40/41` 不调用 GS。",
    "ifixedb": "托卡马克：GS 外边界开关；大于等于 1 时把计算域外边界磁通置 0，0 时使用已建立的 plasma/PF 线圈真空场边界值并允许 LCFS 在域内更新。仿星器：VMEC/外场初始化不通过它选择固定或自由边界。",
    "eqsubtract": "托卡马克与仿星器：在时间演化方程中扣除已初始化的平衡场，使 0 层作为参考基态；线性模拟会在校验阶段强制为 1。它不改变平衡读取和投影结果。",
    "extsubtract": "托卡马克：1 把 RMP/error field 保存为独立外场，而不是直接写入扰动场。仿星器：`itaylor=41,type_ext_field=2` 必须为 1，程序先读 total field，再读 external field，并把 total-external 作为动态场。",
    "icsubtract": "托卡马克：1 把 PF 线圈磁通与等离子体磁通分开保存；求总磁场/磁区时仍会重新相加。0 直接把线圈磁通加入 `psi_field(0)`。仿星器：没有对应的 VMEC 线圈分解路径，通常保持 0。",
    "ibootstrap": "托卡马克：0 关闭；1 按 psi 读取 bootstrap 系数，2 按 Te，3 按 `1-Te/Temax` 并使用扩展系数文件。它在平衡完成后的磁通/环向场演化方程中加入 bootstrap 项，不覆盖初始电流。仿星器：没有专用 VMEC/ST bootstrap 初始化，除非已验证模型与系数，否则保持 0。",
    "ibootstrap_model": "托卡马克：1/3 选 Sauter-Angioni，2/4 选 Redl，3/4 为简化方程实现，5 为 constant-Lambda；应与非零 `ibootstrap` 配套。`ibootstrap=3` 配模型 1/3 当前会停止。仿星器：没有专用三维 bootstrap 平衡闭合。",
    "bootstrap_alpha": "托卡马克：bootstrap 项的统一幅值乘子，默认 0；打开 `ibootstrap/model` 后仍需给非零值才有驱动。仿星器：仅在自行验证并启用同一演化闭合时有意义。",
    "ibootstrap_regular": "托卡马克：bootstrap 计算中小 Bp、温度梯度和归一化温度的正则化尺度，默认 `1e-8`，不表示电流比例。仿星器：只有启用并验证 bootstrap 路径时使用。",
})

# The Grad-Shafranov implementation is an axisymmetric tokamak initializer.
# Stellarator initialization (itaylor=40/41) bypasses this module entirely.
MANUAL_USAGE.update({
    "inumgs": "托卡马克：0 使用源码内置解析 p、p'、F、FF' 形状；1 从固定文件 `profiles-p` 与 `profiles-g` 读取完整剖面并约束 GS。若 gfile 或 `iread_p/f` 已建立剖面，本开关不会再生效。仿星器：`itaylor=40/41` 不调用 GS，不使用。",
    "igs": "托卡马克：GS 最大 Picard 迭代次数；必须取正整数才会执行当前源码的 `1...igs` 循环，0 表示不求解。达到 `tol_gs` 可提前结束；负值在当前实现中不会产生迭代。仿星器：`itaylor=40/41` 不调用 GS，不使用。",
    "igs_pp_ffp_rescale": "托卡马克：1 仅在由 gfile 的 p、p'、F、FF' 建立约束剖面时，把 p' 与 FF' 的积分分别重标度到给定 p 与 F；同时改变 `batemanscale` 的应用顺序。0 保留文件导数。仿星器：不使用。",
    "igs_extend_p": "托卡马克：非零时，若 ne 或 Te 剖面延伸到压力剖面末端之外，就用电子压力加保持末端 Ti 不变的离子压力延伸总压力，并重新计算 p'。0 不延伸。仿星器：不使用。",
    "igs_extend_diamag": "托卡马克：读取电子或 E×B 转动并换算离子转动时，0 在归一化磁通大于等于 1 处停止加入抗磁修正；非零则继续到转动样条末端。仿星器：不使用。",
    "igs_start_xpoint_search": "托卡马克：前 N 次 GS 迭代只在给定 `xnull/znull` 位置评价磁通，从第 N 次起在其附近搜索鞍点；0 表示初始化 LCFS 时即搜索。仿星器：不使用。",
    "igs_forcefree_lcfs": "托卡马克：控制 LCFS 外剖面处理。0 允许剖面按样条继续；1 在非 plasma magnetic region 令 p'、FF'、转动均为 0；2 令 p'、FF' 为 0，并把外侧转动保持为 LCFS 值。-1 会在校验时自动选 0 或 2。仿星器：不使用。",
    "nv1equ": "托卡马克：1 使非约束解析 GS 路径把 `gamma2/gamma3/gamma4` 全部置 0，跳过 q0、dJ/dpsi 和总电流约束；0 正常计算这些约束。名称中的 numvar 说明已不能完整代表当前行为。仿星器：不使用。",
    "igs_feedfac": "托卡马克：只按是否等于 1 作为 generic `idevice=0` 双 limiter 外场反馈开关；1 在第二轮以后根据两 limiter 的磁通差修正外边界场，其他值关闭。它不是连续比例系数。仿星器：不使用。",
    "eta_gs": "托卡马克：仅 USE3D 编译中给 GS 矩阵加入环向导数惩罚，平滑 psi 的非轴对称分量；常规轴对称二维求解中无作用。仿星器：不使用。",
    "tcuro": "托卡马克：无 gfile 时是初始电流丝/高斯电流的总电流，也是非约束解析 GS 用 `gamma4` 保持的目标总等离子体电流；gfile 路径会用文件总电流覆盖。完整 p/F 约束路径不再用它重调总电流。仿星器：不使用。",
    "xmag": "托卡马克：初始电流丝的 R 位置及磁轴搜索初猜；每次 LCFS 搜索后会更新为求得的磁轴 R。gfile 会先用 `rmaxis` 覆盖。仿星器：不使用。",
    "zmag": "托卡马克：初始电流丝的 Z 位置及磁轴搜索初猜；迭代中更新为求得的磁轴 Z，gfile 会先用 `zmaxis` 覆盖。仿星器：不使用。",
    "xmag0": "托卡马克：`idevice=-1` 线圈反馈的目标磁轴 R；磁轴反馈数组非零而本值为 0 时，自动取初始 `xmag`。还可被部分诊断参数引用。仿星器：不使用 GS 线圈反馈。",
    "zmag0": "托卡马克：`idevice=-1` 线圈反馈的目标磁轴 Z；与 `xmag0` 配套，反馈是否启用由反馈数组决定。仿星器：不使用 GS 线圈反馈。",
    "xlim": "托卡马克：内部 limiter #1 的物理 R 坐标；LCFS 候选取该点磁通。0 表示不设内部 limiter，并沿用第一壁/X 点给出的当前边界磁通。generic PF 场还用它估计小半径。仿星器：不使用。",
    "zlim": "托卡马克：内部 limiter #1 的物理 Z 坐标，仅在 `xlim!=0` 时与之配套评价磁通。仿星器：不使用。",
    "xlim2": "托卡马克：内部 limiter #2 的物理 R 坐标；大于 0 时作为第二个 LCFS 候选。`idevice=0,igs_feedfac=1` 时还与 limiter #1 的磁通差构成外场反馈。仿星器：不使用。",
    "zlim2": "托卡马克：内部 limiter #2 的物理 Z 坐标，仅在 `xlim2>0` 时使用。仿星器：不使用。",
    "rzero": "托卡马克：参考大半径，进入 F=R Bphi、旋转平衡指数和归一化；读入默认 -1，校验时环形几何改取 `xzero`，gfile 又会用 `rmaxis` 覆盖。仿星器：VMEC/外场基态不由它定义。",
    "psifrac": "托卡马克：把实际归一化磁通乘以该因子后再查询所有剖面，即 `psi_profile=(psi-psiaxis)/(psiLCFS-psiaxis)*psifrac`。小于 1 会让 LCFS 只用到剖面表的内侧部分，并非裁剪 mesh。仿星器：不使用 GS 剖面坐标。",
    "libetap": "托卡马克：只在 `idevice=0` generic 自由边界初值中，作为 Shafranov 竖直场估算的 `li/2+beta_p`；不会由一般 `idevice=-1` 线圈求解自动满足。仿星器：不使用。",
    "p0": "托卡马克：内置解析压力剖面的轴上总压力幅值，也是密度幂律归一化和电子/离子压力分配的参考；gfile 或 `profile_p` 建立完整剖面后，其形状不再由本值控制，但直接 gfile 投影仍以它归一化解析密度。仿星器：GS 不使用；其它解析测试平衡可能复用该全局量。",
    "pi0": "托卡马克：轴上离子压力参考值；校验阶段以 `(p0-pi0)/p0` 计算电子压力份额 `pefac`，压力外延没有 Te 文件时也用它。它不直接进入 GS 磁通源。仿星器：VMEC 初始化会从总压和 `pefac` 重设该量，GS 不使用。",
    "p1": "托卡马克：内置解析压力关于归一化磁通的轴上一次形状系数；实际 `p'(0)=p0*p1`，并参与 q0 约束系数。完整 p/F 剖面约束时不控制压力。仿星器：不使用 GS。",
    "p2": "托卡马克：内置解析压力的轴上二次形状系数；实际 `p''(0)=2*p0*p2`，并参与轴上电流梯度约束。完整 p/F 剖面约束时不生效。仿星器：不使用 GS。",
    "pedge": "托卡马克：GS 路径中大于 0 时平移整个压力样条，使最外剖面点等于该总压力；直接 gfile 且不求 GS 时，非负值则作为常数直接加到投影压力。它不是给真空 zone 单独增加一条压力方程；`tiedge` 可随后覆盖，`tedge` 也可据密度推算。仿星器：不通过 GS 使用。",
    "tedge": "托卡马克：大于 0 时设置最外电子温度；不能同时读取 Te。源码会平移 Te，并在 `pedge<=0` 时试图相应平移总压力以保持离子温度，当前实现该压力修正含明显索引/数值问题，使用前应验证。仿星器：不通过 GS 使用。",
    "tiedge": "托卡马克：大于 0 时按最外密度和 Te 重新计算 `pedge`，因此覆盖用户给定的 `pedge`，再平移总压力使最外离子温度达到目标。仿星器：不使用 GS。",
    "expn": "托卡马克：未读入 ne 时密度随压力的幂指数；0 给常密度，非零构造近似 `n∝p^expn`，可叠加 `den_edge`。直接 gfile 投影也用它从投影压力构造初始密度；它不进入静态无旋转 GS 方程。仿星器：GS 不使用。",
    "q0": "托卡马克：非约束解析 GS 中目标轴上安全因子，用于计算 `gamma2`；完整 gfile/profile p-F 约束或 `nv1equ=1` 时不再用它调解。仿星器：不使用。",
    "sigma0": "托卡马克：初始等离子体电流猜测的物理 R-Z 高斯宽度；0 使用位于 `xmag,zmag` 的 delta 电流，非零使用高斯。它只影响 GS 初猜，不是最终电流剖面宽度。仿星器：不使用。",
    "djdpsi": "托卡马克：非约束解析 GS 的目标轴上环向电流对实际磁通的导数，通过 `gamma3` 调节额外 FF' 基函数；完整剖面约束或 `nv1equ=1` 时不生效。仿星器：不使用。",
    "th_gs": "托卡马克：从第二个已求解迭代起的 Picard 松弛权重，`psi_new=th_gs*psi_solved+(1-th_gs)*psi_old`；通常应在 0 到 1 之间。仿星器：不使用。",
    "tol_gs": "托卡马克：第二轮以后 GS 解变化误差 `error2` 的提前停止阈值；约束剖面的残差另用于输出/诊断，但退出判断仍看 `error2`。仿星器：不使用。",
    "psiscale": "托卡马克：当前源码只检查大于 1 时把它重置为 1，之后没有活动计算使用；不能依靠它缩放或截取磁通剖面，相关用户作用实际由 `psifrac` 完成。仿星器：不使用。",
    "pscale": "托卡马克：在剖面来源确定后统一乘 p 与 p'；随后 `profile_pscale`、边缘压力/温度设置仍可进一步修改。仿星器：不经过 GS；固定 VMEC 压力覆盖不使用本开关。",
    "bscale": "托卡马克：统一缩放 F=R Bphi 的幅值；内部对 g=(F^2-Fedge^2)/2 与 FF' 乘 `bscale^2`，对 `bzero` 乘 `bscale`，随后仍可应用 `bpscale/profile_bscale`。仿星器：不使用。",
    "batemanscale": "托卡马克：gfile 路径的 Bateman 环向场缩放，目标是在改变 F/Bphi 时保持给定 FF' 或电流源关系；与 `igs_pp_ffp_rescale` 的组合决定是在读入时重构 F，还是在 GS 后缩放 `bzero`。仿星器：不使用。",
    "bpscale": "托卡马克：在保持边缘 `F0=bzero*rzero` 不变的条件下缩放 F 的偏离量，从而一致更新 g 与 FF'；不是简单给整个 Bphi 乘常数。仿星器：不使用。",
    "iread_bscale": "托卡马克：1 读取两列 `profile_bscale(psi_N,scale)`，逐点乘 F 后重新计算 g 与 FF'；它在常数 `bscale/bpscale` 之后执行。仿星器：不使用。",
    "iread_pscale": "托卡马克：1 读取两列 `profile_pscale(psi_N,scale)`，令 p→pS，并按乘积法则令 p'→p'S+pS'；在常数 `pscale` 之后执行。仿星器：不使用。",
    "vscale": "托卡马克：`irot!=0` 时统一乘读入或解析的基础环向角频率，之后才加入可选电子/E×B 抗磁换算。仿星器：VMEC/外场初始化不读取 GS 转动剖面。",
    "gs_vertical_feedback": "托卡马克：`idevice=-1` 时按线圈组给出的磁轴 Z 误差比例反馈系数数组；索引对应 `coil.dat` 的 coil group，电流在每轮 GS 后更新。仿星器：不使用。",
    "gs_radial_feedback": "托卡马克：`idevice=-1` 时按线圈组给出的磁轴 R 误差比例反馈系数数组，与 `xmag-xmag0` 相乘。仿星器：不使用。",
    "gs_vertical_feedback_i": "托卡马克：磁轴 Z 误差的积分反馈系数数组；误差逐 GS 迭代累加，不含时间步长。仿星器：不使用。",
    "gs_radial_feedback_i": "托卡马克：磁轴 R 误差的积分反馈系数数组；误差逐 GS 迭代累加，不含时间步长。仿星器：不使用。",
    "gs_vertical_feedback_x": "托卡马克：X 点 Z 误差的比例线圈反馈系数数组；仅 `idevice=-1`、X 点反馈数组非零且迭代次数大于 10 时生效。仿星器：不使用。",
    "gs_radial_feedback_x": "托卡马克：X 点 R 误差的比例线圈反馈系数数组；与 `xnull-xnull0` 相乘，迭代次数必须大于 10。仿星器：不使用。",
    "gs_vertical_feedback_x_i": "托卡马克：X 点 Z 误差的积分反馈系数数组；从第 11 次迭代起累计。仿星器：不使用。",
    "gs_radial_feedback_x_i": "托卡马克：X 点 R 误差的积分反馈系数数组；从第 11 次迭代起累计。仿星器：不使用。",
    "irot": "托卡马克：0 不把环向旋转纳入平衡；1 采用 `p(R,psi)=p0(psi) exp[alpha(psi)(R^2-rzero^2)/rzero^2]` 修改 GS 压力源并输出转动场。其它非零值会建立转动场，但只有等于 1 才进入该旋转 GS 公式。仿星器：不使用 GS 转动平衡。",
    "iscale_rot_by_p": "托卡马克：只在未读入转动文件时选择解析转动参数化。0 先令 alpha 多项式乘 n/p；1 直接用多项式并把边缘 omega 减到 0；2 使用高斯 alpha 后乘 n/p。仿星器：不使用。",
    "alpha0": "托卡马克：解析 alpha 剖面的常数项；`iscale_rot_by_p=2` 时为高斯背景项。只有 `irot!=0` 且未读转动文件时使用。仿星器：GS 不使用；其它测试平衡可能复用该全局量。",
    "alpha1": "托卡马克：解析 alpha 剖面的一次项；模式 2 时为高斯幅值。仿星器：GS 不使用。",
    "alpha2": "托卡马克：解析 alpha 剖面的二次项；模式 2 时为高斯中心 `psi_N`。仿星器：GS 不使用。",
    "alpha3": "托卡马克：解析 alpha 剖面的三次项；模式 2 时为高斯宽度且不可为 0。仿星器：GS 不使用。",
    "idenfunc": "托卡马克：选择 GS 后的平衡密度重写方式。0/4 保留 GS/profile 建立的密度；1 用磁通外侧 tanh 台阶，2 在 `den0` 与 `den_edge` 间作 tanh 过渡，3 在场评价中按磁通与梯度方向区分核心/外侧；源码还实现 20 及专用 21。它不改变无旋转 GS 磁通。仿星器：VMEC/外场可经过通用密度重写，但 1-3 的磁通判据面向托卡马克，不建议直接套用。",
    "den_edge": "托卡马克：未读取 ne 时的外侧密度；大于 0 可加到压力幂律剖面或作为 `idenfunc=2/3` 的外侧值。与非零 `iread_ne` 冲突；与 `pedge`、`tedge` 三者不能同时显式设置。仿星器：通用密度/输运代码可能复用，但不属于 VMEC 平衡求解。",
    "den0": "托卡马克：解析密度的核心幅值；`expn=0` 时 GS 剖面为常数 den0，`idenfunc` 1/2/3 又把它作为核心/台阶幅值。仿星器：可能用于固定 VMEC 无外部密度文件时的默认密度，但不进入 GS。",
    "dendelt": "托卡马克：`idenfunc=1/2` 的归一化磁通 tanh 过渡宽度；越小过渡越尖，需要相应网格分辨率。仿星器：不建议用于 VMEC 逻辑域的物理壁定义。",
    "denoff": "托卡马克：`idenfunc=1/2/3` 的归一化磁通偏移位置；1/2 决定 tanh 中心，3 决定核心判据阈值。仿星器：不建议作为 VMEC 边界定义。",
    "divertors": "托卡马克：generic/线圈真空场中额外电流丝数；0 无，1 在 `xdiv,zdiv`，2 再在 `xdiv,-zdiv` 放置对称电流丝。它不是 X 点数量开关。仿星器：不使用。",
    "xdiv": "托卡马克：附加 divertor 电流丝的物理 R 坐标，仅 `divertors>=1` 使用。仿星器：不使用。",
    "zdiv": "托卡马克：第一附加 divertor 电流丝的物理 Z 坐标；`divertors=2` 时第二根位于其相反 Z。仿星器：不使用。",
    "divcur": "托卡马克：每根附加 divertor 电流丝相对 `tcuro` 的电流比例，实际线圈源用 `tcuro/(2pi)*divcur`。仿星器：不使用。",
    "xnull": "托卡马克：X 点 #1 的物理 R 初猜；大于 0 才启用。搜索前可只在该点取磁通，搜索启动后在附近找鞍点，并把所得磁通作为 LCFS 候选。仿星器：不使用。",
    "znull": "托卡马克：X 点 #1 的物理 Z 初猜，与 `xnull>0` 配套。仿星器：不使用。",
    "mod_null_rs": "托卡马克 restart：0 用 restart 文件保存的 X 点 #1 坐标覆盖 C1input；1 保留本次 C1input 中的 `xnull/znull`。新启动 GS 不受此开关影响。仿星器：通常不使用。",
    "xnull2": "托卡马克：X 点 #2 的物理 R 初猜；大于 0 时与第一个 X 点同样搜索并参与 LCFS 候选比较，源码不会强制它保持 inactive。仿星器：不使用。",
    "znull2": "托卡马克：X 点 #2 的物理 Z 初猜，与 `xnull2>0` 配套。仿星器：不使用。",
    "mod_null_rs2": "托卡马克 restart：0 用 restart 文件坐标覆盖 X 点 #2 输入；1 保留本次 C1input 的 `xnull2/znull2`。仿星器：通常不使用。",
    "gs_pf_psi_width": "托卡马克：私有磁通区把归一化磁通镜像到 LCFS 外侧时的 tanh 平滑宽度；0 使用尖锐镜像，正值使转接平滑。只影响 private-flux 剖面取样。仿星器：不使用。",
    "xnull0": "托卡马克：`idevice=-1` X 点线圈反馈的目标 R；X 点反馈数组非零而本值为 0 时自动取初始 `xnull`，实际反馈从第 11 轮开始。仿星器：不使用。",
    "znull0": "托卡马克：X 点线圈反馈的目标 Z，与 `xnull0` 配套。仿星器：不使用。",
    "adapt_qs": "托卡马克：尽管源码把它注册在 GS 参数组，实际属于 Mesh Adaptation；给出要加密的安全因子 q 值数组，需启用自适应及 q 打包逻辑。仿星器：没有由 GS 生成的轴对称 q 面，通常不使用。",
    "adapt_zlow": "托卡马克：实际属于 Mesh Adaptation；非零时把 Z 小于该值的 SOL 区域标为粗化候选，不参与 GS 方程。仿星器：逻辑/物理坐标适用性需单独验证。",
    "adapt_zup": "托卡马克：实际属于 Mesh Adaptation；非零时把 Z 大于该值的 SOL 区域标为粗化候选，不参与 GS 方程。仿星器：逻辑/物理坐标适用性需单独验证。",
})

DOC_ALIASES = {
    "bound_type": "boundary_type",
    "ikprad_z": "kprad_z",
    "iread_partilesource": "iread_particlesource",
    "iwall_break": "iwall_breaks",
    "iwrite_transport_coefs": "iwrite_transport_coeffs",
    "pellet_R": "pellet_r",
    "temin_q0": "temin_qd",
    "igs_extend_diagmag": "igs_extend_diamag",
}

DOC_DEFAULT_MISMATCHES = {
    "idens": ("1", "源码默认 0；官方文档旧表写 1。"),
    "bootstrap_alpha": ("1", "源码默认 0；官方文档旧表写 1。"),
    "eta_fac": ("0", "源码默认 1；官方文档输运表写 0。"),
    "ikappar_ni": ("0", "源码默认 1；官方文档表写 0。"),
    "ihypdx": ("2", "源码默认 0；官方文档表写 2。"),
    "nonrect": ("0", "源码默认 1；官方文档表写 0。"),
    "inoslip_pol": ("0", "源码默认 1；官方文档表写 0。"),
    "iconst_bz": ("1", "源码默认 0；官方文档表写 1。"),
    "iconst_n": ("0", "源码默认 1；官方文档表写 0。"),
    "iconst_t": ("0", "源码默认 1；官方文档表写 0。"),
    "imp_mod": ("0", "源码默认 1；官方文档表写 0。"),
    "pskip": ("1", "源码默认 0；官方文档表写 1。"),
    "max_repeat": ("3", "源码默认 1；官方文档表写 3。"),
    "ksp_min": ("1200", "源码默认 500；官方文档表写 1200。"),
    "ksp_warn": ("1600", "源码默认 1000；官方文档表写 1600。"),
    "jadv": ("0", "源码默认 1；官方文档表写 0。"),
    "ntimepr": ("5", "源码默认 1；官方文档表写 5。"),
    "ifull_torus": ("0", "源码默认 1；官方文档 mesh/stellarator 小节写 0。"),
    "rzero": ("1", "源码读入默认 -1，`validate_input` 中若为 -1 则 toroidal 几何取 `xzero`，否则取 1；官方文档直接写 1。"),
    "db": ("0", "源码默认 -1，表示按物理归一化自动计算 ion skin depth 后乘 `db_fac`；官方文档写 0。"),
    "ghs_var": ("0", "源码默认 1；官方文档 Gaussian heat source 表写 0。"),
    "eta_wallRZ": (".001", "源码读入默认 -1，`validate_input` 中若 <0 则取 `eta_wall`；官方文档直接写 .001。"),
    "wall_region_etaRZ": ("1.e-3", "源码读入默认 -1，`validate_input` 中若 <0 则逐区取 `wall_region_eta(i)`；官方文档直接写 1.e-3。"),
}

DOC_USAGE_MISMATCHES = {
    "idevice": "官方文档列出 1=CDX-U、2=NSTX、3=ITER、4=DIII-D；当前 `gradshafranov.f90` 的活动 `select case` 只实现 -1（读 `coil.dat/current.dat`）和 0（generic dipole），其它值进入无 PF 线圈的默认分支。",
    "irmp": "官方文档写 1 只在 plasma、2 只在 boundary 施加；当前 `rmp.f90` 对所有计算单元评价并投影该场，且 2 仅允许 `itor=0`，不是环形托卡马克的边界条件。",
    "icsym": "官方文档只列 0-2；当前源码还实现 3，使用确定性的 (1,1) 型初始扰动而不是随机噪声。",
    "iflip_z": "官方文档称其翻转整个平衡；当前活动使用点只在 gfile 初始化中反号 `zmaxis`，没有同时镜像 `psirz`、mesh 节点或其它平衡场。",
    "iread_ext_field": "官方文档只说明 1=读取外场；tokamak 源码把它作为数据组数量，1 读 `error_field`，大于 1 读 `error_fieldNN`。stellarator 读取器则只装载数组索引 `iread_ext_field`，常规可靠用法是 1。",
    "ibasicj_solvep": "官方文档把 0 概括为 uniform p；源码中 `itaylor=29` 的解析压力确为常数，但 `itaylor=31` 使用随半径衰减的解析压力，因此 0 的准确含义是使用所选 basicJ 解析压力并求 F。",
    "ibootstrap_model": "官方文档列出 1-4；源码 `bootstrap.f90` 还显式实现 `ibootstrap_model=5` 的 constant-Lambda 分支。源码 `input.f90` 内联说明仍是旧的一行模型说明，使用时以 `bootstrap.f90` 为准。",
    "iread_te": "官方文档主要写 `1: profile_te`；源码 GS 路径还支持 2(eV vs Psi)、4(keV vs rho)、10(Corsica)、20(iterdb)，VMEC 路径支持 21(`te_profile`)。",
    "iread_ne": "官方文档主要写 `1: profile_ne`；源码 GS 路径还支持 2、4、10、20，VMEC/ST 相关路径支持 21、22、23 等专用剖面读入方式。",
    "iread_omega": "官方文档主要写 `1: profile_omega`；源码还支持 2(`dtrot.xy`)、3(`profile_vphi`)、4(`profile_omega_rho_0`)、5(J. Menard profile_omega 格式)、20(iterdb)。",
    "iread_p": "官方文档写 `1: profile_p`；源码 VMEC 路径还测试 `iread_p=21` 并读 `p_profile`。",
    "ikprad": "官方文档只说明 `ikprad=1` 的 KPRAD 模型；源码还允许 `ikprad=-1`，在 `USEADAS` 编译时走 ADAS ADF11 数据路径，否则校验报错。",
    "type_ext_field": "官方文档列出 tokamak/stellarator 主要取值；源码 `rmp.f90` 中 `type_ext_field<=0` 走 RMP/error-field 分支，`=1/2` 走 stellarator/free-boundary 分支，另有 `=3` 从电流计算外场的分支。",
    "ipellet": "官方文档列到 15；源码 `pellet.f90` 还支持 `abs(ipellet)=16`，即 toroidal von-Mises 分布并带 1/R 权重。双位数取值在归一化时还会除以 `Lor_vol`。",
    "pellet_var_tor": "官方文档写 0 时取 `pellet_var`；源码中若 `ipellet=15` 且 `pellet_var_tor<=0`，实际设为 `pellet_var/pellet_r`，其它 pellet 分支才取 `pellet_var`。",
    "ipellet_abl": "官方文档列出 1、2、3；源码另有 `ipellet_abl=43` 的 Sergeev06 carbon ablation 分支，并且 `ipellet_z=0` 时会按 ablation 模型推断默认 Z。",
    "itaylor": "官方文档列出常用初始条件；源码 `init_conds.f90` 还包含 -1、24、25、26、28、30、31、32、33、34 等分支，实际可用性取决于编译宏和对应初始化例程。",
    "inumgs": "官方文档写读取 `profile-p` 与 `profile-g`；当前源码固定打开的文件名实际是复数 `profiles-p` 与 `profiles-g`，并按固定宽度格式读取 p/p' 和 g/FF'。",
    "igs": "官方文档只称其为最大 Picard 迭代次数；当前活动循环是 `do itnum=1,igs`。源码旁仍保留关于 `abs(igs)`/负值继续运行的旧注释，但负 `igs` 在当前实现中不会执行 GS 迭代。",
    "igs_feedfac": "官方文档称其为 external-field feedback 的 proportionality factor；当前源码只检查 `igs_feedfac.eq.1`，实际是 0/1 型开关，反馈幅值由固定公式计算。",
    "igs_forcefree_lcfs": "官方文档主要说明取 1 时使 LCFS force-free；当前源码还区分 0、1、2，并把读入默认 -1 自动改为 0 或 2。1 令 LCFS 外转动为 0，2 则保持 LCFS 转动值。",
    "psiscale": "源码声明注释称小于 1 可丢弃边缘剖面点，但当前活动代码只把大于 1 的值重置为 1，之后没有任何计算读取 `psiscale`；实际剖面磁通范围缩放使用的是 `psifrac`。",
    "p1": "官方文档把它写成轴上 p'(Psi)；内置解析式使用归一化磁通，实际轴上导数系数为 `p0*p1`，不是参数值本身。",
    "p2": "官方文档把它写成轴上 p''(Psi)；内置解析式的实际轴上二阶导数系数为 `2*p0*p2`，且自变量是归一化磁通。",
    "xnull2": "官方文档称第二 X 点为 inactive；当前 `lcfs` 对两个 X 点使用同样的搜索和 LCFS 候选比较，第二点若更靠近磁轴磁通会成为活动 LCFS 限制点。",
    "idenfunc": "官方文档把 0-3 都列为平衡密度函数；当前初始化流程中 0/4 直接保留 GS/profile 密度，1/2 在 `den_eq` 中重写，3 主要在场评价算子中按磁通梯度重写，源码还实现文档未列出的 20 与专用 21。",
    "tedge": "官方文档把它概括为真空区电子温度并给出边界关系；当前 GS 源码先平移 Te 样条，随后在 `pedge<=0` 时用 `n0_spline%n`（样条点数）而非边缘密度修正压力，行为与文档公式不一致，使用该组合前应验证或修正源码。",
    "adapt_qs": "官方输入表把它放在 GS 小节，且源码也误用 `gs_grp` 注册；实际唯一活动使用位于 `adapt.f90`，用于按 q 面打包自适应网格，不参与 GS 求解。",
    "adapt_zlow": "官方输入表和源码注册把它归入 GS；实际只在 `adapt.f90` 中控制 SOL 粗化区域，不参与 GS 方程。",
    "adapt_zup": "官方输入表和源码注册把它归入 GS；实际只在 `adapt.f90` 中控制 SOL 粗化区域，不参与 GS 方程。",
    "ivisfunc": "官方文档只说明 0-3；当前源码还实现 4、10/11（读取 `profile_amu`）、12（basicJ 专用）以及 USEST 条件下的 21（逻辑 rho）。",
    "iresfunc": "官方文档把 2/3/4 分别描述为解析台阶/Spitzer 等模型；当前 `resistivity_func` 中 2、3、4 都直接使用预先构造的 `eta_field`。源码还实现 10/11 的 `profile_eta` 和 USEST 模式 21。",
    "ikappafunc": "官方文档列到 12；当前源码还在 USEST 条件下实现 21，按逻辑 rho 构造 tanh 热导。",
    "ikapparfunc": "官方文档只列 0/1；当前源码还实现 2，使用按 Te^(5/2) 构造并由 `kappar_min/max` 截断的场。",
    "kappag": "官方文档称其按压力梯度阈值启用。CPU 弱式的热流项确含压力梯度平方范数，但当前 mask 实际比较 `p**2` 与 `gradp_crit**2`；GPU 对应实现被注释。",
    "kappax": "官方文档把它列为 B×grad(T) 交叉热输运。当前普通 CPU、非 USEPARTICLES 路径有耦合项；GPU 版本的对应块被注释，USEPARTICLES 编译也排除该项。",
    "ifixedb": "官方边界表把它概括为运行时 `psi=0` 边界；当前活动用途集中在 gfile/GS 初始化和 LCFS 诊断。时间演化磁边界由 `iconst_bn`、`inocurrent_*`、`ifbound` 与多区域模型决定。",
    "jper": "官方文档表写 `2: Top/bottom boundaries periodic`；当前网格与边界源码实际测试 `jper.eq.1`。",
    "imp_mod": "官方文档称模式 1 为 implicit leapfrog；当前输入注册和活动分支将其称为 Caramana split-step，并由 `caramana_fac` 控制显式部分。",
    "mass_ratio": "官方文档列出该输入但没有说明；当前源码除注册/存储外没有活动计算引用，电子质量仍使用内部常数。",
    "lambdae": "官方文档只写 `lambdae`；当前源码除注册/存储外没有活动计算引用，非零值不会打开电子惯性。",
    "imode_filter": "输入注册说明称其为要过滤的环向模数量；当前实现中负值只保留所列模，而正值只从各场减去所列模重构幅值的 0.1，并非完全删除。",
}

RUNTIME_DEFAULT_NOTES = {
    "ifout": "`ifout=-1` 在 `validate_input` 中改为 `i3d`：3D 默认输出 f 场，2D 默认不输出。",
    "ntimers": "`ntimers<=0` 时源码把它设为 `ntimepr`。",
    "rzero": "`rzero=-1` 时，toroidal 几何取 `xzero`，其它几何取 1；若最终 `rzero<=0` 只给 warning。",
    "ifbound": "`ifbound=-1` 时，complex 版本默认 2，real 版本默认 1。",
    "eta_wallRZ": "`eta_wallRZ<0` 时改为 `eta_wall`。",
    "wall_region_etaRZ": "每个 `wall_region_etaRZ(i)<0` 时改为对应 `wall_region_eta(i)`。",
    "eta_max": "`eta_max<=0` 时改为 `eta_vac`。",
    "eta_min": "`eta_min<=0` 时改为 0。",
    "kappa_max": "`kappa_max<=0` 时改为 `kappar`。",
    "kappar_max": "`kappar_max<=0` 时改为 `kappar`。",
    "kappar_min": "`kappar_min<=0` 时改为 `kappar`。",
    "db": "`db<0` 时源码按 `b0_norm/n0_norm/l0_norm/ion_mass` 计算物理 ion skin depth，再乘 `db_fac`；显式给非负 `db` 会覆盖该自动计算。",
    "particle_linear": "`particle_linear=-1` 时改为当前 `linear`。",
    "imp_mod": "`isplitstep=0` 时校验阶段强制 `imp_mod=0`。",
    "iread_omega": "`iread_omega_e` 或 `iread_omega_ExB` 非零时会写入同一个内部 `iread_omega`，且与已有 `iread_omega` 互斥。",
}

SOURCE_USAGE_OVERRIDES = {
    "ibootstrap_model": "在 `bootstrap.f90` 中选择 bootstrap closure：1/3 为 Sauter & Angioni，2/4 为 Redl，5 为 constant-Lambda 分支。",
    "iread_te": "GS 路径的 1/2/4/10/20 分别采用 psi、rho、Corsica 或 iterdb 坐标；VMEC 的 21 采用逻辑 `s=rho^2`。",
    "iread_ne": "GS 路径的 1/2/4/10/20 建立磁通函数；VMEC/ST 的 21/22/23 分别在 VMEC 投影中或后续 `den_eq` 中写入密度。",
    "iread_omega": "`iread_omega_e` 与 `iread_omega_ExB` 会在校验阶段映射到同一个内部选择量；`irot=0` 时不会读取文件。",
    "iread_p": "GS 外部压力剖面会替换 gfile/dskbal/jsolver 或默认剖面；VMEC 外部压力只替换压力场，不改变 wout 的几何和磁场。",
    "ikprad": "0 关闭；1 使用内置 KPRAD polynomial fit；-1 在 `USEADAS` 编译时读 ADAS ADF11，否则报错。",
    "type_ext_field": "`<=0` 用 tokamak RMP/error-field 分支，`=1/2` 用 stellarator/free-boundary 场文件，`=3` 从电流计算外场。",
    "ipellet": "在 `pellet.f90` 中选择密度源分布；正值为持续源，负值用于初始扰动；双位数分布按 `Lor_vol` 数值归一化。",
    "pellet_var_tor": "读入后若 <=0 会自动补值：`ipellet=15` 用 `pellet_var/pellet_r`，其它分支用 `pellet_var`。",
    "ipellet_abl": "选择 pellet ablation 模型；1/2 lithium，3 neon，43 carbon/Sergeev06。`ipellet_z=0` 时会由模型推断默认 Z。",
    "itaylor": "主初始化分发开关；不同几何下选择 tilting cylinder、GS、VMEC/stellarator、fixed-q、basicJ、RWM、wave/diffusion tests 等分支。",
}


# Parameters whose registration strings are empty or too terse need an explicit
# user-facing meaning.  Keep these descriptions about the mathematical/numerical
# role; source locations belong in the audit artifacts, not in the reader guide.
MANUAL_USAGE.update({
    "igauge": "选择矢势规范相关的数值处理。当前活动方程只在非零时加入规范约束/稳定项；常规算例保持 0。托卡马克与仿星器使用同一场表示。",
    "irunaway": "非零时增加 runaway-electron 密度场及其电流耦合；需要同时设置 `cre/radiff/rjra` 等参数。两种装置使用同一演化方程，但初始场和磁场几何来自各自平衡。",
    "cre": "runaway-electron 沿磁场特征线的传播速度输入，读入后按速度归一化换算；仅 `irunaway!=0` 使用。",
    "ra_cyc": "每个 MHD 时间步内 runaway 特征线/粒子推进的子循环次数；增大它可缩短 runaway 子步而不改变 MHD 的 `dt`。",
    "radiff": "runaway-electron 密度方程的扩散系数，进入 `div(radiff grad(n_RE))`；仅 `irunaway!=0` 使用。",
    "rjra": "runaway 电流反馈到广义 Ohm 定律/总电流时的幅值系数；1 使用模型电流，0 去掉该反馈。",
    "bzsign": "runaway 平行传播方向所用的背景环向磁场符号；0 时由初始磁场自动判断，显式正负值用于覆盖自动结果。",
    "nosig": "非零时抑制密度源 `sigma` 对部分动量/温度方程的伴随项；用于源项模型诊断，不会关闭密度方程中的粒子源本身。",
    "gravr": "R 方向的恒定体加速度，作为密度乘以加速度的动量源；0 表示无该外力。托卡马克和映射后的仿星器均使用物理柱坐标 R。",
    "gravz": "Z 方向的恒定体加速度，作为密度乘以加速度的动量源；0 表示无该外力。",
    "chiiner": "六场模型中压缩速度势 `chi` 的惯性项乘子；1 为完整项，减小它可改变压缩分量的数值时间尺度。",
    "ieq_bdotgradt": "决定温度方程平行导热是否保留平衡场的 `B dot grad(T)` 贡献；用于平衡减除/线性化时控制平衡项。",

    "ivisfunc": "选择各向同性粘性空间模型：0 常数；1/2 磁通 tanh 边缘层；3/4 预计算场；10/11 读 `profile_amu`；12 专用 basicJ；21 为 USEST 逻辑 rho 模型。",
    "amuoff": "`ivisfunc=1/2/21` 的粘性过渡位置；1/2 使用归一化磁通坐标，21 使用逻辑 rho。",
    "amuoff2": "`ivisfunc=2` 第二个 tanh 过渡中心；只有它与 `amudelt2` 都非零时才加入第二层。",
    "amue": "电子/自举电流闭合使用的粘性系数；不代替流体动量方程的 `amu`。",
    "amu_edge": "粘性边缘增量或外侧幅值，配合 `ivisfunc=1/2/21`；最终各向同性粘性还包含基值 `amu`。",
    "amu_wall": "靠近 wall-distance 场时附加的粘性幅值；按 `amu_wall_off/amu_wall_delt` 的 tanh 层叠加到其它粘性模型。",
    "amu_wall_off": "壁面附加粘性层在 wall-distance 坐标中的中心位置。",
    "iresfunc": "选择 plasma zone 电阻率模型：0 Spitzer 型；1 磁通 tanh；2-4 预计算场；5 简化新古典；10/11 读 `profile_eta`；21 为 USEST 逻辑 rho 模型。conductor/vacuum zone 不用此开关。",
    "etaoff": "电阻率 tanh 过渡位置；`iresfunc=1` 使用磁通，`iresfunc=21` 使用逻辑 rho。",
    "eta0": "温度依赖或 tanh 电阻率的幅值；`iresfunc=0` 中形成 `eta0(Te-eta_te_offset)^(-3/2)`。",
    "ikappafunc": "选择各向同性热输运模型：0 温度依赖；1/2 磁通 tanh；3 反比于 `sqrt(p n)`；4 梯度依赖；5 预计算场；10/11 读 `profile_kappa`；12 专用模型；21 为 USEST 逻辑 rho。",
    "ikapparfunc": "选择平行热导：0 常数 `kappar`；1 用 `tcrit` 低温抑制；2 使用按 `Te^(5/2)` 计算并受上下限约束的预计算场。",
    "ikapscale": "1 时令平行热导场按局部各向同性 `kappa` 缩放，即使用 `kappar*kappa(x)`；0 时按 `ikapparfunc` 单独构造。",
    "kappaoff": "`ikappafunc=1/2/21` 的热导 tanh 过渡中心；坐标分别为磁通或 USEST 逻辑 rho。",
    "kappa0": "所选各向同性热导函数的可变部分幅值；最终系数通常还加常数 `kappat`。",
    "tcrit": "`ikapparfunc=1` 的低温转折温度，平行热导为 `kappar/[1+(tcrit/Te)^(5/2)]`。",
    "kappax": "交叉场热输运系数；普通 CPU、非 USEPARTICLES 方程中耦合压力与环向磁场，GPU 对应块被注释，USEPARTICLES 路径也排除该项。",
    "kappag": "CPU 压力方程中的非线性梯度热流系数，形式含 `-kappag*|grad(p)|^2 grad(p)` 与阈值补偿项；GPU 对应块被注释。当前阈值掩码实际比较 `p^2` 与 `gradp_crit^2`。",
    "kappah": "在各向同性热导上附加边界层 `kappah*tanh^2[(psi_N-1)/0.2]`；`ikappafunc=5` 时不加。",
    "idenmfunc": "选择主离子密度扩散：0 常数 `denm`；1 使用预计算温度依赖场并限幅；10/11 从 `profile_denm` 读 SI/归一化剖面。",

    "deex": "超扩散的参考长度/网格尺度；当 `ihypdx!=0` 时所有 hyper 输入乘 `deex^ihypdx`。",
    "hyper": "磁通/极向磁场方程的超电阻率系数，抑制高波数电流结构；0 关闭该项。",
    "hyperc": "压缩/极向速度势方程的超粘性系数；只在相应速度未知量存在时生效。",
    "hyperi": "环向磁场未知量的超扩散系数；`numvar>=2` 才有对应场。",
    "hyperp": "压力或温度方程的超扩散系数；需要实际推进压力/温度未知量。",
    "hyperv": "环向速度方程的超粘性系数；`numvar>=2` 且速度未冻结时使用。",
    "ihypdx": "hyper 系数的长度缩放指数：0 不缩放，非零时 `lambda_eff=lambda_input*deex^ihypdx`。当前默认 0。",
    "ihypeta": "磁超扩散的空间乘子：0 常数；1 乘电阻率；2 乘压力；大于 2 使用压力与指定磁扰动谐波构造乘子，并要求不超过 `ibh_harmonics`。",
    "ihypkappa": "1 时压力/温度 hyper 系数乘局部热导率，0 时保持输入常数。",

    "isurface": "控制分部积分后 Galerkin 弱式中的外边界表面积分；1 保留，0 去掉。它不选择边界位置，位置来自 mesh/model 分类。",
    "icurv": "边界几何曲率处理阶数/开关；大于 0 时使用曲边几何信息，常规高阶曲边网格保持默认 2。",
    "nonrect": "1 表示非矩形/一般边界并关闭矩形快捷假设；0 仅适合边界拓扑确为规则矩形的测试网格。",
    "com_bc": "1 时给压缩速度势 `chi` 增加 `nabla^2 chi=0` 的边界约束。",
    "vor_bc": "1 时给极向速度势 `U` 增加 `Delta* U=0` 的涡量边界约束。",
    "inograd_p": "1 对压力施加零法向梯度 Neumann 条件；不要与同一压力场的固定值条件重复指定。",
    "inograd_t": "1 对温度施加零法向梯度 Neumann 条件。",
    "inograd_n": "1 对主离子密度施加零法向梯度 Neumann 条件。",
    "inostress_tor": "1 对环向速度施加零法向导数/无切向应力条件；与 `inoslip_tor=1` 是不同选择。",
    "inocurrent_pol": "1 通过环向磁场变量的法向导数约束使边界极向电流为零。",
    "inocurrent_tor": "1 通过 `Delta*psi=0` 型边界约束使环向电流为零。",
    "inocurrent_norm": "1 对三维磁场变量施加组合边界条件，使法向电流为零；会改变 `psi/bz` 的边界掩码组合。",
    "iconstflux": "非线性推进中重新缩放环向磁场以保持总环向磁通；0 不做该全局修正。",
    "tebound": "大于 0 时，在标记为 first-wall 的边界把电子温度固定为该归一化值；负值保留初始边界值。",
    "tibound": "大于 0 时，在 first-wall 边界把离子温度固定为该归一化值；仅双温模型有独立作用。",

    "integrator": "时间离散选择：0 为 theta/Crank-Nicolson 家族；1 为 BDF2，且程序把 `thimp` 强制为 1，首步使用一阶隐式启动。",
    "iteratephi": "分裂推进中，更新密度/输运后再重算一次磁场推进；只用于非线性分裂步，线性模式禁止。",
    "irecalc_eta": "分裂步密度求解后重新计算输运系数，使电阻率等使用更新后的密度/温度。",
    "iconst_eta": "1 时冻结初始电阻率场，不随温度/密度演化重新构造。",
    "itime_independent": "线性模式下去掉普通时间导数并求频域/稳态响应；程序同时令 `thimp=1`，`frequency` 给出复频率。",
    "thimpsm": "平滑器/辅助隐式项使用的 theta 权重，与主时间离散的 `thimp` 分开。",
    "harned_mikic": "二场模型的 Harned-Mikic 数值稳定项系数；0 关闭，非零时抑制特定高速/高频耦合。",
    "isources": "1 时把粒子注入等源项导致的动量修正放入速度推进；要求计算标量诊断以取得所需全局量。",
    "nskip": "有限元系统矩阵重建的时间步间隔；1 每步重建，较大值在系数变化慢时复用矩阵。",
    "iskippc": "后端线性求解中预条件器可复用的调用次数/周期控制；与分裂步层面的 `pskip` 分开。",

    "int_pts_main": "主演化弱式在每个二维三角形上的 Gaussian 积分点数；必须是程序已实现的 Dunavant 阶数。",
    "int_pts_aux": "辅助场投影/构造所用的二维积分点数；提高它增加后处理与系数构造成本。",
    "int_pts_diag": "标量和诊断积分使用的二维积分点数。",
    "int_pts_tor": "三维棱柱在环向 Hermite 方向的积分点数；非 3D 编译会强制为 1，且与二维点数乘积不能超过内部上限。",
    "regular": "小分母/坐标奇点的正则化尺度；USEST 逻辑 rho 模型使用 `sqrt(rho^2+regular^2)`，压缩势方程也复用该量。",

    "iadapt": "SCOREC 网格自适应总模式：0 关闭；1 初始化按磁通；2 推进中按误差；3 两者结合；4 初始化和推进均可按误差。",
    "ispradapt": "1 启用 SPR 梯度恢复自适应，并在推进阶段替代普通 residual/error 路径。",
    "isprntime": "SPR 自适应的时间步调用周期。",
    "isprweight": "SPR 恢复误差转换为目标尺寸时的权重，控制细化强度。",
    "isprmaxsize": "SPR 目标尺寸场允许的最大单元尺寸。",
    "isprrefinelevel": "一次 SPR 调用允许的最大细化层级。",
    "isprcoarsenlevel": "一次 SPR 调用允许的粗化层级；负值表示使用实现的默认/不强制粗化。",
    "iadapt_writevtk": "1 在自适应阶段写出 VTK 调试网格/尺寸场。",
    "iadapt_writesmb": "1 写出 SCOREC `.smb` 自适应网格快照，便于重启或检查。",
    "iadapt_useH1": "1 用 H1 型误差度量替代默认高阶度量构造目标尺寸。",
    "iadapt_removeEquiv": "1 在误差估计前去掉环向等价节点/重复贡献，供周期网格的专用适配路径使用。",
    "adapt_target_error": "普通误差自适应的目标/触发误差；估计误差未超过它时不换网格。",
    "adapt_ke": "线性计算中触发动态自适应的动能阈值；0 不使用该触发条件。",
    "iadapt_ntime": "普通动态自适应检查的时间步周期；非线性且为 0 时当前流程可每步检查。",
    "iadapt_max_node": "自适应后允许的节点数上限，用于限制内存和网格增长。",
    "adapt_control": "误差到目标尺寸的控制模式/方向参数；常规保持默认 1。",
    "iadapt_order_p": "误差随网格尺寸收敛的假定阶数，用于由目标误差反算目标尺寸。",
    "iadaptFaceNumber": "只适配指定几何模型 face 的编号；-1 表示不按单一 face 限制。",
    "iadapt_snap": "1 时把新边界节点投影/贴合回既有几何模型边界；不会创建新的壁面或 LCFS。",
    "adapt_factor": "保留的自适应缩放输入；当前活动源码未读取其值，修改它不会改变网格。",
    "adapt_hmin": "磁通/误差尺寸场允许的绝对最小单元尺度。",
    "adapt_hmax": "磁通/误差尺寸场允许的绝对最大单元尺度。",
    "adapt_hmin_rel": "相对当前单元尺寸的一次最小缩放比，限制单次细化幅度。",
    "adapt_hmax_rel": "相对当前单元尺寸的一次最大缩放比，限制单次粗化幅度。",
    "adapt_smooth": "保留的尺寸场平滑输入；当前活动源码未读取其值。",
    "adapt_psin_vacuum": "按磁通适配时 vacuum 区的归一化磁通阈值/目标范围；负值关闭该专用阈值。",
    "adapt_psin_wall": "按磁通适配时 wall 区的归一化磁通阈值/目标范围；负值关闭该专用阈值。",

    "iheat_sink": "1 启用 `itaylor=27` 专用热沉；其它平衡类型下不产生通用热沉。",
    "vloop": "施加在环向 Ohm/磁通方程中的回路电压幅值；无电流反馈时按 `vloop*cos(2*pi*vloop_freq*t)` 使用。",
    "vloopRZ": "R-Z/极向磁场方程使用的回路电压分量，独立于主环向 `vloop`。",
    "tcur": "电流反馈的目标总等离子体电流；若给定 `tcuri/tcurf`，运行时目标可被时间 ramp 覆盖。",
    "tcuri": "电流反馈 tanh ramp 的初始目标电流。",
    "tcurf": "电流反馈 tanh ramp 的最终目标电流。",
    "tcur_t0": "目标电流 tanh ramp 的中心时间。",
    "tcur_tw": "目标电流 tanh ramp 的时间宽度；用于从 `tcuri` 平滑过渡到 `tcurf`。",
    "control_p": "`control_type=1` 电流 PID 的比例增益 P。",
    "control_i": "`control_type=1` 电流 PID 的积分增益 I。",
    "control_d": "`control_type=1` 电流 PID 的微分增益 D。",
    "r_p": "pellet 实体半径，供 ablation 模型计算剩余粒子数和烧蚀率；不是沉积 Gaussian 宽度。",
    "cloud_pel": "pellet ablation 云团/沉积宽度的乘性系数，控制烧蚀物质相对 pellet 的扩散尺度。",
    "ionization": "1 在主离子密度方程加入温度门控的电离粒子源，并可用 `coolrate` 从热方程扣除能量。",
    "ionization_temp": "电离源中的特征温度，同时出现在 Arrhenius 型 `exp(-Tion/T)` 因子和高温衰减门控中。",
    "ionization_depth": "温度高于 `ionization_temp` 后电离源指数衰减的温度宽度。",
    "isink": "启用局部 Gaussian 粒子汇的数量：1 使用 sink1，2 同时使用 sink1 和 sink2。",
    "iarc_source": "1 启用与壁面法向电流和 wall-distance 相关的 arc 粒子源。",
    "arc_source_alpha": "arc 粒子源的总幅值系数，乘正向法向电流。",
    "arc_source_eta": "arc 源随 wall-distance 的尺度长度，形状含 `(w/eta)*exp(-w/eta)`。",
    "idenfloor": "1 在外侧非 plasma magnetic region 加入恢复型密度源，把密度拉向 `den_edge`；它不是逐节点硬截断。",
    "alphadenfloor": "密度恢复源 `alphadenfloor*(den_edge-n)` 的速率系数。",
    "n_target": "pellet 密度反馈所追踪的目标全局粒子数/密度诊断量。",
    "n_control_p": "`n_control_type=1` pellet-rate PID 的比例增益。",
    "n_control_i": "pellet-rate PID 的积分增益。",
    "n_control_d": "pellet-rate PID 的微分增益。",

    "iprint": "终端日志详细度：0 最少；1 打印主要步骤/迭代；2 及以上打印更多矩阵、系数和输出阶段信息。它不控制 HDF5 字段内容。",
    "irestart_slice": "-1 从 HDF5 中最后一个已保存时间片重启；非负值选择指定时间片索引，并在同一输出文件中删除其后的时间片组后续写。",
    "mass_ratio": "已注册但当前活动计算未读取的兼容参数；电子/离子质量比由内部常数和 `ion_mass` 形成，用户不应依赖此值。",
    "lambdae": "已注册但当前活动计算未读取的兼容参数；不会单独打开电子惯性或改变广义 Ohm 定律。",
    "ibform": "旧磁场形式开关的占位参数，读入后写入 dummy 变量；当前方程形式不会随它改变。",
    "igs_method": "旧 GS 算法选择的占位参数，当前 GS 求解器不读取其值。",
})


ARRAY_USAGE = "数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。"


@dataclass
class Param:
    order: int
    name: str
    internal_var: str
    namelist: str
    group: str
    group_cn: str
    dtype: str
    default: str
    size: str
    description: str
    usage: str
    condition: str
    source: str
    line: int
    source_use_count: int = 0
    source_use_files: str = ""
    source_usage_summary: str = ""
    source_use_examples: str = ""


def strip_comment(line: str) -> str:
    in_s = False
    in_d = False
    out = []
    i = 0
    while i < len(line):
        c = line[i]
        if c == "'" and not in_d:
            in_s = not in_s
        elif c == '"' and not in_s:
            in_d = not in_d
        if c == "!" and not in_s and not in_d:
            break
        out.append(c)
        i += 1
    return "".join(out)


def normalize_fortran_call(text: str) -> str:
    # Remove Fortran continuation markers that are outside strings.
    lines = []
    for raw in text.splitlines():
        s = strip_comment(raw).strip()
        if not s:
            continue
        if s.endswith(";"):
            s = s[:-1]
        if s.endswith("&"):
            s = s[:-1].rstrip()
        if s.startswith("&"):
            s = s[1:].lstrip()
        lines.append(s)
    return " ".join(lines)


def split_args(arg_text: str) -> list[str]:
    args = []
    buf = []
    depth = 0
    in_s = False
    in_d = False
    for c in arg_text:
        if c == "'" and not in_d:
            in_s = not in_s
        elif c == '"' and not in_s:
            in_d = not in_d
        elif not in_s and not in_d:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "," and depth == 0:
                args.append("".join(buf).strip())
                buf = []
                continue
        buf.append(c)
    if buf:
        args.append("".join(buf).strip())
    return args


def unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0]:
        return s[1:-1]
    return s


def resolve_expr(s: str) -> str:
    s = s.strip()
    s = CONSTANTS.get(s, s)
    # keep exact Fortran-ish expression, but make a few obvious forms clearer
    replacements = {
        "5./3.": "5./3. (约 1.6667)",
        "2./3.": "2./3. (约 0.6667)",
        "0.000000001": "1e-9",
    }
    return replacements.get(s, s)


def iter_calls(path: Path) -> Iterable[tuple[int, str, str]]:
    condition_stack: list[str] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped.startswith("#ifdef") or stripped.startswith("#if defined"):
            condition_stack.append(stripped.lstrip("#").strip())
        elif stripped.startswith("#ifndef"):
            condition_stack.append(stripped.lstrip("#").strip())
        elif stripped.startswith("#else"):
            if condition_stack:
                condition_stack[-1] = "else of " + condition_stack[-1]
        elif stripped.startswith("#endif"):
            if condition_stack:
                condition_stack.pop()

        if re.search(r"\bcall\s+add_(group|var_)", raw, flags=re.I):
            start = i + 1
            acc = [raw]
            # Accumulate until parentheses balance.
            joined = normalize_fortran_call("\n".join(acc))
            while joined.count("(") > joined.count(")") and i + 1 < len(lines):
                i += 1
                acc.append(lines[i])
                joined = normalize_fortran_call("\n".join(acc))
            yield start, joined, " && ".join(condition_stack)
        i += 1


def parse_params() -> list[Param]:
    groups: dict[str, str] = {}
    group_order: list[str] = []
    params: list[Param] = []

    for line_no, call, cond in iter_calls(INPUT_F90):
        m_group = re.match(r"call\s+add_group\s*\((.*)\)\s*$", call, flags=re.I)
        if m_group:
            args = split_args(m_group.group(1))
            if len(args) >= 2:
                label = unquote(args[0])
                var = args[1].strip()
                groups[var] = label
                group_order.append(var)
            continue

        m = re.match(r"call\s+(add_var_(?:double|double_array|int|int_array|string|string_array))\s*\((.*)\)\s*$", call, flags=re.I)
        if not m:
            continue

        func = m.group(1).lower()
        args = split_args(m.group(2))
        if not args:
            continue
        name = unquote(args[0])
        internal_var = args[1].strip()
        dtype = {
            "add_var_double": "real",
            "add_var_double_array": "real array",
            "add_var_int": "integer",
            "add_var_int_array": "integer array",
            "add_var_string": "character",
            "add_var_string_array": "character array",
        }[func]
        if func == "add_var_double":
            default, desc, grp = args[2], args[3], args[4]
            size = "1"
        elif func == "add_var_int":
            default, desc, grp = args[2], args[3], args[4]
            size = "1"
        elif func == "add_var_double_array":
            size, default, desc, grp = args[2], args[3], args[4], args[5]
        elif func == "add_var_int_array":
            size, default, desc, grp = args[2], args[3], args[4], args[5]
        elif func == "add_var_string":
            size, default, desc, grp = args[2], args[3], args[4], args[5]
            dtype = f"character(len={resolve_expr(size)})"
            size = "1"
        elif func == "add_var_string_array":
            strlen, size, default, desc, grp = args[2], args[3], args[4], args[5], args[6]
            dtype = f"character(len={resolve_expr(strlen)}) array"
        else:
            continue

        group = groups.get(grp.strip(), grp.strip())
        desc_clean = unquote(desc).replace("|", "；").strip()
        default_clean = unquote(default)
        default_clean = resolve_expr(default_clean)
        size_clean = resolve_expr(size)

        usage = MANUAL_USAGE.get(name, "")
        if "array" in dtype:
            usage = (usage + " " + ARRAY_USAGE).strip()
        if dtype.startswith("character"):
            usage = (usage + " 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。").strip()

        params.append(
            Param(
                order=len(params) + 1,
                name=name,
                internal_var=internal_var,
                namelist="&inputnl",
                group=group,
                group_cn=GROUP_TRANSLATIONS.get(group, group),
                dtype=dtype,
                default=default_clean if default_clean != "" else '""',
                size=size_clean,
                description=desc_clean,
                usage=usage,
                condition=cond,
                source="unstructured/input.f90",
                line=line_no,
            )
        )
    return params


def parse_doc_option_names(text: str) -> set[str]:
    return set(re.findall(r"\\texttt\{([A-Za-z0-9_\\]+)\}", text.replace("\\_", "_")))


def all_official_doc_text() -> str:
    chunks = []
    for path in sorted((ROOT / "doc").glob("*.tex")):
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def mentioned_in_official_docs(name: str, doc_text: str) -> bool:
    plain_text = doc_text.replace(r"\_", "_")
    return name in plain_text


def parse_old_doc_names(text: str) -> set[str]:
    return set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=", text, flags=re.M))


def parse_old_doc_entries(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^|\n]+)\|\s*([A-Za-z0-9_ ()]+)", line)
        if m:
            if current:
                entries[current] = " ".join(buf).strip()
            current = m.group(1)
            buf = []
        elif current and line:
            if line.startswith("【") and "】" in line:
                continue
            if line.startswith(">"):
                continue
            if line in {'""', "''"}:
                continue
            buf.append(line)
    if current:
        entries[current] = " ".join(buf).strip()
    return entries


def enrich_params(params: list[Param]) -> None:
    for p in params:
        if p.name in SOURCE_USAGE_OVERRIDES:
            p.usage = (p.usage + " 源码用法：" + SOURCE_USAGE_OVERRIDES[p.name]).strip()
        if p.name in RUNTIME_DEFAULT_NOTES:
            p.usage = (p.usage + " 运行时默认：" + RUNTIME_DEFAULT_NOTES[p.name]).strip()
        if not p.description:
            p.description = "源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。"


def sorted_params(params: list[Param]) -> list[Param]:
    group_rank = {g: i for i, g in enumerate(LOGICAL_GROUP_ORDER)}
    return sorted(params, key=lambda p: (group_rank.get(p.group, 999), p.order))


SOURCE_SUFFIXES = {".f90", ".F90", ".F", ".f", ".fh", ".c", ".cc", ".cpp", ".h", ".hpp"}
SOURCE_EXCLUDE_PARTS = {
    ".git",
    "doc",
    "regtest",
    "templates",
    "tutorials",
    "idl",
    "python",
    "spack",
    "cmake",
    "device_data",
    "README",
}


def iter_source_files() -> Iterable[Path]:
    for root in [ROOT / "unstructured", ROOT / "m3dc1_scorec"]:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            rel_parts = path.relative_to(ROOT).parts
            if any(part in SOURCE_EXCLUDE_PARTS for part in rel_parts):
                continue
            yield path


def is_declaration_line(code: str) -> bool:
    low = code.strip().lower()
    if "::" not in low:
        return False
    return bool(
        re.match(
            r"(integer|real|logical|character|complex|type|class|procedure)\b",
            low,
        )
    )


def truncate_context(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def scan_source_usage(params: list[Param]) -> None:
    source_files = list(iter_source_files())

    def usage_terms(p: Param) -> list[str]:
        terms = [p.internal_var.lower()]
        if p.internal_var.lower().endswith("_scl"):
            terms.append(p.internal_var[:-4].lower())
        if p.name.lower() not in terms:
            terms.append(p.name.lower())
        out = []
        for term in terms:
            if term not in out:
                out.append(term)
        return out

    by_var: dict[str, list[Param]] = {}
    for p in params:
        for term in usage_terms(p):
            by_var.setdefault(term, []).append(p)

    patterns = {
        var: re.compile(rf"(?<![A-Za-z0-9_]){re.escape(var)}(?![A-Za-z0-9_])", re.I)
        for var in by_var
        if var not in {"idum", "dum"}
    }
    hits: dict[str, list[tuple[str, int, str]]] = {p.name: [] for p in params}
    hit_seen: dict[str, set[tuple[str, int, str]]] = {p.name: set() for p in params}

    for path in source_files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, raw in enumerate(lines, start=1):
            code = strip_comment(raw).strip()
            raw_stripped = raw.strip()
            if not raw_stripped or not code:
                continue
            if re.search(r"\bcall\s+add_var_", code, flags=re.I):
                continue
            if is_declaration_line(code):
                continue
            for var, pat in patterns.items():
                if pat.search(code):
                    hit = (rel, lineno, truncate_context(raw_stripped))
                    for param in by_var[var]:
                        if hit not in hit_seen[param.name]:
                            hits[param.name].append(hit)
                            hit_seen[param.name].add(hit)

    for p in params:
        key = p.internal_var.lower()
        if key in {"idum", "dum"}:
            p.source_use_count = 0
            p.source_use_files = ""
            p.source_usage_summary = f"兼容旧输入：读入到 dummy 变量 `{p.internal_var}`，未见模型计算使用。"
            p.source_use_examples = ""
            continue
        phits = hits.get(p.name, [])
        p.source_use_count = len(phits)
        if not phits:
            p.source_use_files = ""
            p.source_usage_summary = "未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。"
            p.source_use_examples = ""
            continue
        file_counter = Counter(rel for rel, _, _ in phits)
        p.source_use_files = "; ".join(f"{rel}({count})" for rel, count in file_counter.most_common(8))
        top_files = ", ".join(f"`{Path(rel).name}` {count}处" for rel, count in file_counter.most_common(4))
        p.source_usage_summary = f"源码引用 {len(phits)} 处；主要在 {top_files}。"
        examples = []
        for rel, lineno, text in phits[:10]:
            examples.append(f"{rel}:{lineno}: {text}")
        p.source_use_examples = "\n".join(examples)


def write_csv(params: list[Param], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(params[0]).keys()), lineterminator="\n")
        w.writeheader()
        for p in sorted_params(params):
            w.writerow(asdict(p))


def audit_notes_for_params(params: list[Param]) -> dict[str, list[str]]:
    by_name = {p.name: p for p in params}
    notes: dict[str, list[str]] = {}
    for alias, real in DOC_ALIASES.items():
        if real in by_name:
            notes.setdefault(real, []).append(f"官方文档名称 `{alias}` 应改用源码名称 `{real}`。")
    for name, (doc_default, note) in DOC_DEFAULT_MISMATCHES.items():
        if name in by_name:
            notes.setdefault(name, []).append(f"默认值不一致：官方 `{doc_default}`；源码 `{by_name[name].default}`。{note}")
    for name, note in DOC_USAGE_MISMATCHES.items():
        if name in by_name:
            notes.setdefault(name, []).append("语义/取值范围： " + note)
    for name, note in RUNTIME_DEFAULT_NOTES.items():
        if name in by_name:
            notes.setdefault(name, []).append("运行时行为： " + note)
    return notes


def write_usage_files(params: list[Param], md_path: Path, csv_path: Path) -> None:
    fields = [
        "name",
        "internal_var",
        "namelist",
        "group",
        "dtype",
        "default",
        "source_use_count",
        "source_use_files",
        "source_usage_summary",
        "source_use_examples",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for p in sorted_params(params):
            row = asdict(p)
            w.writerow({k: row[k] for k in fields})

    lines: list[str] = []
    lines.append("# M3D-C1 `C1input` 参数源码使用位置索引")
    lines.append("")
    lines.append("本文件由源码自动扫描生成，用于辅助核查每个输入参数读入后的使用场合。扫描范围为程序源码目录，排除了 `doc/`、`templates/`、`tutorials/`、`regtest/` 等文档和示例目录；同时跳过 `add_var_*` 注册行和声明行。")
    lines.append("")
    lines.append("| 参数 | 内部变量 | 逻辑组 | 引用数 | 主要文件 | 源码使用摘要 | 示例引用 |")
    lines.append("|---|---|---|---:|---|---|---|")
    for p in sorted_params(params):
        examples = "<br>".join(html.escape(x) for x in p.source_use_examples.splitlines()[:5]) or "-"
        cells = [
            f"`{p.name}`",
            f"`{p.internal_var}`",
            p.group,
            str(p.source_use_count),
            p.source_use_files or "-",
            p.source_usage_summary,
            examples,
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


KNOWN_INLINE_LATEX = (
    ("`sqrt((x-xcenter)^2+(z-zcenter)^2)`", r"\(\rho=\sqrt{(x-x_{\mathrm{center}})^2+(z-z_{\mathrm{center}})^2}\)"),
    ("`s=xl^2+zl^2`", r"\(s=x_l^2+z_l^2\)"),
    ("`s=xl²+zl²`", r"\(s=x_l^2+z_l^2\)"),
    ("`s=rho^2`", r"\(s=\rho^2\)"),
    ("`n=Te/p`", r"\(n=T_e/p\)"),
    ("`n_zer=mpol*nzer_factor`", r"\(n_{\mathrm{zer}}=m_{\mathrm{pol}}\,\mathrm{nzer\_factor}\)"),
    ("`1/nperiods`", r"\(1/n_{\mathrm{periods}}\)"),
    ("B0_norm=10^4 G", r"\(B_{0,\mathrm{norm}}=10^4\,\mathrm{G}\)"),
    ("n0_norm=10^14 cm^-3", r"\(n_{0,\mathrm{norm}}=10^{14}\,\mathrm{cm}^{-3}\)"),
    ("L0_norm=100 cm", r"\(L_{0,\mathrm{norm}}=100\,\mathrm{cm}\)"),
    ("ne(Te+Ti)", r"\(p=n_e(T_e+T_i)\)"),
    ("F=R*B_phi", r"\(F=R B_\phi\)"),
)


def latexize_known_formulas(text: str) -> str:
    for plain, latex in KNOWN_INLINE_LATEX:
        text = text.replace(plain, latex)
    return text


def paragraph(text: str) -> str:
    escaped = h(latexize_known_formulas(text))
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)
    return escaped.replace("\n", "<br>")


def write_html_guide(params: list[Param], path: Path) -> None:
    by_group: dict[str, list[Param]] = {}
    for p in params:
        by_group.setdefault(p.group, []).append(p)
    group_order = [g for g in LOGICAL_GROUP_ORDER if g in by_group]
    group_order.extend(g for g in by_group if g not in group_order)
    audit_notes = audit_notes_for_params(params)

    no_source_use = sum(1 for p in params if p.source_use_count == 0 and p.internal_var.lower() not in {"idum", "dum"})
    dummy_count = sum(1 for p in params if p.internal_var.lower() in {"idum", "dum"})
    conditional_count = sum(1 for p in params if p.condition)
    audit_param_count = len(audit_notes)

    css = """
:root {
  color-scheme: light;
  --bg: #f7f7f4;
  --panel: #ffffff;
  --ink: #1f2528;
  --muted: #5f696d;
  --line: #d9ddd8;
  --accent: #1f6f8b;
  --accent-2: #2f7d54;
  --warn: #a35d00;
  --bad: #9c2f2f;
  --soft: #eef5f7;
  --soft-2: #eef6ef;
  --code: #f1f3f2;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.58;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  background: var(--code);
  padding: 0.08rem 0.28rem;
  border-radius: 4px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 0.92em;
}
.layout {
  display: grid;
  grid-template-columns: 290px minmax(0, 1fr);
  min-height: 100vh;
}
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  padding: 22px 18px;
  border-right: 1px solid var(--line);
  background: #fbfbf8;
}
.sidebar h1 {
  font-size: 1.08rem;
  margin: 0 0 12px;
  line-height: 1.35;
}
.sidebar .small { color: var(--muted); font-size: 0.86rem; margin-bottom: 14px; }
.search {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 10px;
  font-size: 0.95rem;
  background: white;
}
.nav { margin-top: 16px; display: grid; gap: 5px; }
.nav a {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 6px;
  color: var(--ink);
}
.nav a:hover { background: var(--soft); text-decoration: none; }
.nav span:last-child { color: var(--muted); }
.content { padding: 28px min(5vw, 58px) 64px; }
.hero {
  border-bottom: 1px solid var(--line);
  padding-bottom: 22px;
  margin-bottom: 22px;
}
.hero h2 { font-size: clamp(1.55rem, 2.4vw, 2.35rem); margin: 0 0 8px; letter-spacing: 0; }
.hero p { color: var(--muted); margin: 7px 0; max-width: 980px; }
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(130px, 1fr));
  gap: 10px;
  margin-top: 18px;
}
.stat {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 11px 12px;
}
.stat b { display: block; font-size: 1.35rem; }
.stat span { color: var(--muted); font-size: 0.86rem; }
.notice {
  background: #fff8ea;
  border: 1px solid #e5cf9a;
  border-left: 4px solid var(--warn);
  border-radius: 6px;
  padding: 12px 14px;
  margin: 18px 0 24px;
}
.section {
  margin: 34px 0 42px;
}
.section-title {
  display: flex;
  align-items: baseline;
  gap: 10px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 8px;
  margin-bottom: 10px;
}
.section-title h2 { margin: 0; font-size: 1.35rem; }
.section-title span { color: var(--muted); }
.group-note { color: var(--muted); margin: 0 0 14px; max-width: 980px; }
.param-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 14px 15px 12px;
  margin: 10px 0;
}
.param-card.no-use { border-left-color: var(--warn); }
.param-card.deprecated { border-left-color: #777; }
.param-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.param-title {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-weight: 700;
  font-size: 1rem;
  overflow-wrap: anywhere;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.75rem;
  border: 1px solid var(--line);
  background: #f9faf8;
  color: var(--muted);
}
.chip.audit { color: var(--bad); border-color: #e1b3b3; background: #fff4f4; }
.chip.runtime { color: var(--warn); border-color: #dfc18b; background: #fff8ea; }
.chip.source { color: var(--accent-2); border-color: #b8d5c2; background: var(--soft-2); }
.meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 8px;
  margin: 8px 0 10px;
}
.meta div {
  background: #fafbf9;
  border: 1px solid #e7e9e5;
  border-radius: 6px;
  padding: 7px 8px;
  min-width: 0;
}
.meta dt { color: var(--muted); font-size: 0.78rem; margin-bottom: 2px; }
.meta dd { margin: 0; overflow-wrap: anywhere; }
.field { margin: 8px 0; }
.field b { color: #333; }
details {
  border-top: 1px dashed var(--line);
  margin-top: 10px;
  padding-top: 8px;
}
summary { cursor: pointer; color: var(--accent); font-weight: 600; }
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #f5f6f4;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px;
  font-size: 0.82rem;
}
.audit-list { margin: 8px 0 0; padding-left: 18px; }
.hidden { display: none !important; }
.empty {
  padding: 18px;
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 8px;
  background: var(--panel);
}
@media (max-width: 920px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }
  .stats { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
  .meta { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
}
@media (max-width: 560px) {
  .content { padding: 22px 16px 42px; }
  .stats, .meta { grid-template-columns: 1fr; }
}
"""

    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append('<html lang="zh-CN">')
    lines.append("<head>")
    lines.append('<meta charset="utf-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    lines.append("<title>M3D-C1 C1input 参数读者手册</title>")
    lines.append(f"<style>{css}</style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append('<div class="layout">')
    lines.append('<aside class="sidebar">')
    lines.append("<h1>M3D-C1 C1input 参数读者手册</h1>")
    lines.append('<div class="small">基于当前 master 源码生成；官方文档只作对照。</div>')
    lines.append('<input id="search" class="search" type="search" placeholder="搜索参数、默认值、文件名、说明...">')
    lines.append('<div class="small" id="result-count"></div>')
    lines.append('<nav class="nav">')
    for group in group_order:
        plist = by_group[group]
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        lines.append(f'<a href="#{h(anchor)}"><span>{h(GROUP_TRANSLATIONS.get(group, group))}</span><span>{len(plist)}</span></a>')
    lines.append("</nav>")
    lines.append("</aside>")
    lines.append('<main class="content">')
    lines.append('<section class="hero">')
    lines.append("<h2>M3D-C1 主程序输入参数总览</h2>")
    lines.append("<p>所有主程序输入均由 `unstructured/input.f90` 的 `set_defaults` 注册，并由 `read_namelist.cpp` 从固定文件名 `C1input` 读取。惯例写作 `&inputnl ... /`；源码实际按 `name = value` 逐行解析。</p>")
    lines.append("<p>本手册按逻辑组重排参数，默认值以源码为准；每个参数都列出内部变量、数据类型、默认值、使用说明和源码引用摘要。完整逐行引用可查 CSV/Markdown 索引。</p>")
    lines.append('<div class="stats">')
    stats = [
        (len(params), "源码注册参数"),
        (len(group_order), "逻辑分组"),
        (conditional_count, "条件编译参数"),
        (audit_param_count, "含文档差异/运行时提示"),
        (no_source_use, "未见直接源码引用"),
        (dummy_count, "废弃 dummy 参数"),
        (len(DOC_USAGE_MISMATCHES), "语义/取值差异项"),
        (len(DOC_DEFAULT_MISMATCHES), "默认值差异项"),
    ]
    for num, label in stats:
        lines.append(f'<div class="stat"><b>{h(num)}</b><span>{h(label)}</span></div>')
    lines.append("</div>")
    lines.append("</section>")
    lines.append('<div class="notice">读者提示：搜索框可以搜参数名、内部变量名、默认值、源码文件名或差异说明。数组参数按 Fortran 一基索引写入，例如 <code>boundary_type(1)=2</code>。</div>')

    for group in group_order:
        plist = sorted(by_group[group], key=lambda p: p.order)
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        lines.append(f'<section class="section" id="{h(anchor)}" data-section>')
        lines.append('<div class="section-title">')
        lines.append(f"<h2>【{h(GROUP_TRANSLATIONS.get(group, group))}】</h2><span>{h(group)} · {len(plist)} 个参数</span>")
        lines.append("</div>")
        if group in GROUP_NOTES:
            lines.append(f'<p class="group-note">{paragraph(GROUP_NOTES[group])}</p>')
        for p in plist:
            notes = audit_notes.get(p.name, [])
            no_use_cls = " no-use" if p.source_use_count == 0 and p.internal_var.lower() not in {"idum", "dum"} else ""
            dep_cls = " deprecated" if group == "Deprecated" else ""
            search_blob = " ".join([
                p.name,
                p.internal_var,
                p.group,
                p.group_cn,
                p.dtype,
                p.default,
                p.description,
                p.usage,
                p.source_usage_summary,
                p.source_use_files,
                " ".join(notes),
            ])
            lines.append(f'<article class="param-card{no_use_cls}{dep_cls}" data-param data-search="{h(search_blob.lower())}">')
            lines.append('<div class="param-head">')
            lines.append(f'<div class="param-title">{h(p.name)} = {h(p.default)} | {h(p.dtype)}</div>')
            lines.append('<div class="chips">')
            if "array" in p.dtype:
                lines.append('<span class="chip">array</span>')
            if p.condition:
                lines.append('<span class="chip">conditional</span>')
            if p.source_use_count > 0:
                lines.append(f'<span class="chip source">源码 {p.source_use_count} 处</span>')
            else:
                lines.append('<span class="chip runtime">未见直接引用</span>')
            if p.name in RUNTIME_DEFAULT_NOTES:
                lines.append('<span class="chip runtime">运行时改写</span>')
            if notes:
                lines.append('<span class="chip audit">文档差异</span>')
            lines.append("</div></div>")
            lines.append('<dl class="meta">')
            meta = [
                ("namelist", p.namelist),
                ("内部变量", p.internal_var),
                ("数组长度/上限", p.size),
                ("注册位置", f"{p.source}:{p.line}"),
            ]
            for k, v in meta:
                lines.append(f"<div><dt>{h(k)}</dt><dd>{h(v)}</dd></div>")
            lines.append("</dl>")
            lines.append(f'<div class="field"><b>含义：</b>{paragraph(p.description)}</div>')
            usage_text = p.usage or "按需在 C1input 中写 `name = value`；未设置则使用默认值。"
            if p.condition:
                usage_text += f" 条件编译：{p.condition}。"
            if p.size != "1":
                usage_text += f" 数组长度/上限：{p.size}。"
            lines.append(f'<div class="field"><b>使用：</b>{paragraph(usage_text)}</div>')
            lines.append(f'<div class="field"><b>源码使用：</b>{paragraph(p.source_usage_summary)}</div>')
            if p.source_use_files:
                lines.append(f'<div class="field"><b>主要文件：</b>{paragraph(p.source_use_files)}</div>')
            if p.source_use_examples:
                lines.append("<details><summary>源码引用示例</summary>")
                lines.append(f"<pre>{h(p.source_use_examples)}</pre>")
                lines.append("</details>")
            if notes:
                lines.append("<details open><summary>官方文档差异 / 运行时提示</summary>")
                lines.append('<ul class="audit-list">')
                for note in notes:
                    lines.append(f"<li>{paragraph(note)}</li>")
                lines.append("</ul></details>")
            lines.append("</article>")
        lines.append("</section>")

    lines.append('<div id="empty" class="empty hidden">没有匹配的参数。请换一个关键词试试。</div>')
    lines.append("</main></div>")
    lines.append(
        """
<script>
const search = document.getElementById('search');
const cards = Array.from(document.querySelectorAll('[data-param]'));
const sections = Array.from(document.querySelectorAll('[data-section]'));
const count = document.getElementById('result-count');
const empty = document.getElementById('empty');
function update() {
  const q = search.value.trim().toLowerCase();
  let visible = 0;
  for (const card of cards) {
    const ok = !q || card.dataset.search.includes(q);
    card.classList.toggle('hidden', !ok);
    if (ok) visible++;
  }
  for (const section of sections) {
    const any = Array.from(section.querySelectorAll('[data-param]')).some(card => !card.classList.contains('hidden'));
    section.classList.toggle('hidden', !any);
  }
  count.textContent = q ? `匹配 ${visible} / ${cards.length} 个参数` : `共 ${cards.length} 个参数`;
  empty.classList.toggle('hidden', visible !== 0);
}
search.addEventListener('input', update);
update();
</script>
"""
    )
    lines.append("</body></html>")
    path.write_text("\n".join(lines), encoding="utf-8")


def strip_audit_language(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    replacements = {
        "源码用法：": "",
        "运行时默认：": "有效行为：",
        "源码当前默认": "当前默认",
        "源码默认": "默认",
        "源码读入默认": "读入默认",
        "源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。": "",
        "按需在 `C1input` 中写 `name = value`；未设置则使用默认值。": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Drop comparison/audit wording from the user-facing meaning column.
    text = re.sub(r"官方文档[^。；]*[。；]", "", text)
    text = re.sub(r"在\s*`[^`]*\.(?:f90|F90|F|f|c|cc|cpp|h|hpp)`\s*中", "", text, flags=re.I)
    text = re.sub(r"`[^`]*\.(?:f90|F90|F|f|c|cc|cpp|h|hpp)`", "程序内部", text, flags=re.I)
    text = text.replace("应以源码为准。", "")
    text = text.replace("旧表写 0，但", "")
    text = text.replace("旧表写 1，但", "")
    text = text.replace("源码", "程序")
    text = re.sub(r"\s+", " ", text).strip(" ；。")
    return text


def inferred_meaning(p: Param) -> str:
    name = p.name.lower()
    group_cn = GROUP_TRANSLATIONS.get(p.group, p.group)
    if "array" in p.dtype:
        return f"{group_cn}相关数组参数，用一基索引给出多组同类数值；未指定的元素保持默认值。"
    if p.dtype.startswith("character"):
        if "filename" in name or "file" in name:
            return f"{group_cn}相关文件名参数，用于指定外部输入或输出文件。"
        return f"{group_cn}相关字符串参数，用于选择名称、文件前缀或外部资源。"
    if name.startswith("i") and p.dtype == "integer":
        return f"{group_cn}相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法。"
    if name.endswith("_fac") or name.endswith("fac") or "scale" in name:
        return f"{group_cn}相关乘性系数，用于缩放对应物理量、剖面、源项或数值模型强度。"
    if name.endswith("_max") or name.startswith("max"):
        return f"{group_cn}相关上限参数，用于限制迭代、场量、系数或网格/时间步控制范围。"
    if name.endswith("_min") or name.startswith("min"):
        return f"{group_cn}相关下限参数，用于限制场量、系数、时间步或模型适用范围。"
    if name.endswith("_rate") or "rate" in name:
        return f"{group_cn}相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度。"
    if name.endswith("_var") or "delt" in name or "width" in name:
        return f"{group_cn}相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度。"
    if name.endswith("_x") or name.endswith("_z") or name.endswith("_r") or name.endswith("_phi"):
        return f"{group_cn}相关几何位置参数，用于给定 R/Z/phi 等空间坐标。"
    if name in {"dt", "dtmin", "dtmax", "ddt"}:
        return "时间推进参数，用于设置时间步长及其允许变化范围。"
    return f"{group_cn}相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置。"


def simplified_meaning_components(p: Param) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    desc = strip_audit_language(p.description)
    if desc and "注册说明为空" not in desc:
        parts.append(("description", desc))
    manual = strip_audit_language(MANUAL_USAGE.get(p.name, ""))
    if manual and manual not in [text for _, text in parts]:
        parts.append(("usage", manual))
    source_override = strip_audit_language(SOURCE_USAGE_OVERRIDES.get(p.name, ""))
    if source_override and source_override not in [text for _, text in parts]:
        parts.append(("rule", source_override))
    runtime = strip_audit_language(RUNTIME_DEFAULT_NOTES.get(p.name, ""))
    if runtime and runtime not in [text for _, text in parts]:
        parts.append(("runtime", runtime))
    if p.condition:
        parts.append(("condition", f"仅在满足条件编译 `{p.condition}` 时可用。"))
    if p.size != "1" and "array" in p.dtype:
        parts.append(("array", f"数组长度/上限：{p.size}。"))
    if not parts:
        parts.append(("description", inferred_meaning(p)))
    return parts


def simplified_meaning(p: Param) -> str:
    parts = simplified_meaning_components(p)
    meaning = "；".join(text.rstrip("；。") for _, text in parts)
    meaning = re.sub(r"\s+", " ", meaning).strip()
    return meaning or inferred_meaning(p)


def split_device_usage(text: str) -> list[tuple[str, str, str]]:
    tokamak_marker = "托卡马克："
    stellarator_marker = "仿星器："
    tokamak_at = text.find(tokamak_marker)
    stellarator_at = text.find(stellarator_marker)
    if tokamak_at < 0 or stellarator_at < tokamak_at:
        return [("usage", "使用方法", text)]

    items: list[tuple[str, str, str]] = []
    prefix = text[:tokamak_at].strip(" ；。")
    if prefix:
        items.append(("usage", "使用方法", prefix))
    tokamak = text[tokamak_at + len(tokamak_marker):stellarator_at].strip(" ；。")
    stellarator = text[stellarator_at + len(stellarator_marker):].strip(" ；。")

    common = ""
    common_match = re.search(r"(?<=[。；])((?:两种装置|两者|两边|二者|三者|与\s*`).*)$", stellarator)
    if common_match:
        common = common_match.group(1).strip(" ；。")
        stellarator = stellarator[:common_match.start()].strip(" ；。")

    if tokamak:
        items.append(("tokamak", "托卡马克", tokamak))
    if stellarator:
        items.append(("stellarator", "仿星器", stellarator))
    if common:
        items.append(("common", "共同条件", common))
    return items


MEANING_LABELS = {
    "description": "基本含义",
    "usage": "使用方法",
    "rule": "覆盖与生效规则",
    "runtime": "运行时默认",
    "condition": "编译条件",
    "array": "数组范围",
}


def render_simplified_meaning(p: Param) -> str:
    display_parts: list[tuple[str, str, str]] = []
    for kind, text in simplified_meaning_components(p):
        if kind == "usage":
            display_parts.extend(split_device_usage(text))
        else:
            display_parts.append((kind, MEANING_LABELS[kind], text))

    if len(display_parts) == 1 and display_parts[0][0] == "description":
        return f'<p class="meaning-summary">{paragraph(display_parts[0][2])}</p>'

    lines = ['<div class="meaning-parts">']
    for kind, label, text in display_parts:
        lines.append(f'<div class="meaning-part meaning-{h(kind)}">')
        lines.append(f'<div class="meaning-label">{h(label)}</div>')
        lines.append(f'<div class="meaning-text">{paragraph(text)}</div>')
        lines.append('</div>')
    lines.append('</div>')
    return "".join(lines)


def write_simplified_csv(params: list[Param], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["参数名", "数据类型", "默认值", "含义"], lineterminator="\n")
        w.writeheader()
        for p in sorted_params(params):
            w.writerow({
                "参数名": p.name,
                "数据类型": p.dtype,
                "默认值": p.default,
                "含义": simplified_meaning(p),
            })


def write_simplified_markdown(params: list[Param], path: Path) -> None:
    by_group: dict[str, list[Param]] = {}
    for p in params:
        by_group.setdefault(p.group, []).append(p)
    group_order = [g for g in LOGICAL_GROUP_ORDER if g in by_group]
    group_order.extend(g for g in by_group if g not in group_order)

    lines: list[str] = []
    lines.append("# M3D-C1 `C1input` 参数使用手册")
    lines.append("")
    lines.append("本文是面向 M3D-C1 算例配置的独立发布版本，逐项给出参数名、数据类型、默认值和含义。所有条目均为主程序 `C1input` 可读参数，属于 `&inputnl`；逻辑分组用于组织阅读顺序。")
    lines.append("")
    lines.append(f"参数总数：{len(params)}。默认值以当前程序注册值为准。")
    lines.append("")
    for group in group_order:
        plist = sorted(by_group[group], key=lambda p: p.order)
        lines.append(f"## {GROUP_TRANSLATIONS.get(group, group)} / {group}")
        lines.append("")
        note = GROUP_NOTES.get(group)
        if note:
            lines.append(strip_audit_language(note))
            lines.append("")
        lines.append("| 参数名 | 数据类型 | 默认值 | 含义 |")
        lines.append("|---|---|---:|---|")
        for p in plist:
            row = [
                f"`{p.name}`",
                p.dtype,
                f"`{p.default}`",
                simplified_meaning(p),
            ]
            lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def remaining_module_supplement(group: str) -> str:
    if group == "Normalizations":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Normalizations：先把所有物理输入放到同一单位系统</h3><p>这三个参数在 mesh 和平衡读入之后用于建立全程序的归一化尺度；<code>ion_mass</code> 也参与 Alfvén 速度和时间尺度。除明确标有 SI/cgs 单位并由读取器转换的文件外，C1input 中的演化系数通常应给归一化值。</p></div><span class="guide-kicker">CASE 第 1 层</span></div>
<div class="formula">\[v_0=\frac{B_0}{\sqrt{4\pi m_i n_0}},\qquad \tau_0=\frac{L_0}{v_0}=\frac{L_0\sqrt{4\pi m_i n_0}}{B_0}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>量</th><th>归一化单位</th><th>用户含义</th></tr></thead><tbody>
<tr><td>压力/能量密度</td><td>\(p_0=B_0^2/(4\pi)\)</td><td>压力、电子/离子温度方程中的能量尺度。</td></tr>
<tr><td>温度</td><td>\(T_0=B_0^2/(4\pi n_0)\)</td><td>程序温度以能量表示；读取器注明 keV/eV 时会转换。</td></tr>
<tr><td>扩散率</td><td>\(D_0=L_0^2/\tau_0\)</td><td><code>denm</code> 等粒子扩散系数的单位。</td></tr>
<tr><td>电阻率</td><td>\(\eta_0=4\pi L_0^2/(c^2\tau_0)\)</td><td>plasma、vacuum 和 conductor 的电阻率统一使用此尺度。</td></tr>
<tr><td>热导率</td><td>\(\kappa_0=n_0L_0^2/\tau_0\)</td><td><code>kappa/kappar</code> 的单位；profile 模式可显式从 SI 转换。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>物理 R-Z mesh 和 gfile 量先按各自声明单位读入</h4></div><p>归一化不改变 mesh 几何或 LCFS，只改变场、时间和输运系数进入方程时的数值尺度。改变三项后必须同步重算所有手工给定的归一化系数。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>VMEC 映射后的物理场使用同一归一化</h4></div><p>逻辑坐标映射本身是几何过程；wout/外场被投影后仍按同一 \(B_0,n_0,L_0\) 标度进入 MHD 方程。两种装置没有第二套单位系统。</p></section>
</div>"""

    if group == "Model Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Model Options：决定实际求解哪一组 extended-MHD 方程</h3><p>本组承接 Mesh/Input/Equilibrium 的初始场。先选未知量数和线性化方式，再打开密度、压力/温度、two-fluid、bootstrap、runaway 或 kinetic 闭合；未被选择的场即使在平衡文件中存在，也不会成为独立演化未知量。</p></div><span class="guide-kicker">CASE 物理核心</span></div>
<div class="formula">\[\frac{\partial n_i}{\partial t}+\nabla\!\cdot(n_i\mathbf v)=\nabla\!\cdot(D\nabla n_i)+\sigma_i\]</div>
<div class="formula">\[\rho\left(\frac{\partial\mathbf v}{\partial t}+\mathbf v\!\cdot\nabla\mathbf v\right)=\mathbf J\!\times\mathbf B-\nabla p-\nabla\!\cdot\Pi-\varpi\mathbf v\]</div>
<div class="formula">\[\frac{\partial\mathbf B}{\partial t}=-\nabla\times\mathbf E,\qquad \mathbf E=-\mathbf v\times\mathbf B+\eta(\mathbf J-\mathbf J_x)+\frac{d_i}{n_e}(\mathbf J\times\mathbf B-\nabla p_e).\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>设置层</th><th>主要参数</th><th>实际作用</th></tr></thead><tbody>
<tr><td>场数</td><td><code>numvar</code>, <code>idens</code>, <code>ipres</code></td><td>1 为 \(U,\psi\) 二场；2 再加环向速度和环向磁场；3 再加压缩势与压力槽。密度和附加热力学场由独立开关加入。</td></tr>
<tr><td>热力学</td><td><code>ipressplit</code>, <code>itemp</code>, <code>iadiabat</code>, <code>imp_temp</code></td><td>选择总压/电子压或电子/离子温度表示及分裂求解。<code>itemp=1</code> 要求 <code>numvar=3,ipressplit=1,z_ion=1</code>。</td></tr>
<tr><td>线性化</td><td><code>linear</code>, <code>eqsubtract</code>, <code>extsubtract</code>, <code>icsubtract</code></td><td>线性模式强制减去轴对称平衡；外场和 PF 场是否从演化量中扣除由另外两个开关决定。</td></tr>
<tr><td>非理想闭合</td><td><code>itwofluid</code>, <code>gyro</code>, <code>inertia</code>, <code>iohmic_heating</code>, <code>irad_heating</code></td><td>控制 Hall/电子压强、gyroviscosity、非线性惯性和热方程源项。two-fluid 的实际幅值还取决于 <code>db</code>。</td></tr>
<tr><td>专用模型</td><td><code>ibootstrap*</code>, <code>irunaway*</code>, <code>kinetic</code></td><td>在基本 MHD 上加入 bootstrap 电流闭合、runaway 密度/电流或 PIC/CGL 模型；这些开关不重做初始平衡。</td></tr>
<tr><td>冻结/调试</td><td><code>istatic</code>, <code>iestatic</code>, <code>no_vdg_T</code>, <code>nosig</code></td><td>冻结速度或磁场，或移除特定热力学项；主要用于响应、验证和模型拆分。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>可从轴对称平衡进入 2D、单 n complex 或真实 3D 演化</h4></div><p><code>ntor</code> 定义 complex 线性模；真实三维使用 <code>nplanes&gt;1</code>。bootstrap、runaway 和若干径向闭合使用磁通面/轴对称几何量，托卡马克是其主要使用路径。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>映射完成后求解同一套三维弱式</h4></div><p>没有另一套“stellarator MHD 方程”；差别来自三维几何和平衡场。完整 3D 模型可用，但依赖轴对称 \(\psi,q,R_0\) 的 bootstrap/runaway/剖面闭合不能因语法可读就视为已对仿星器验证。</p></section>
<div class="callout"><strong>合法组合：</strong><code>linear=1</code> 禁止 <code>iteratephi=1</code>；<code>kinetic=2/3</code> 要求 <code>linear=1,isplitstep=0,ipres=1,itemp=0,ipressplit=0</code>；<code>kinetic=1</code> 还要求 USEPARTICLES 编译。</div>
</div>"""

    if group == "Transport Coefficients":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Transport：构造各积分点上的耗散系数</h3><p>Model Options 决定参与演化的方程，本组为动量、Ohm、温度和密度方程构造粘性、电阻率、热导率与粒子扩散率。函数型参数仅修改 plasma zone；conductor 和 vacuum 的电阻率由 Resistive Wall 组控制。</p></div><span class="guide-kicker">CASE 耗散层</span></div>
<div class="formula">\[\mathbf q_s=-\kappa_s\nabla T_s-\kappa_{\parallel s}\frac{\mathbf B\mathbf B}{B^2}\!\cdot\nabla T_s,\qquad \partial_t n_i\supset\nabla\!\cdot(D\nabla n_i).\]</div>
<div class="formula">\[\eta_{\mathrm{Sp}}=\eta_{fac}\!\left[\eta_r+\eta_0(T_e-T_{off})^{-3/2}\right],\quad \eta_{min}\le\eta\le\eta_{max}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>系数</th><th>模式选择</th><th>用户设置逻辑</th></tr></thead><tbody>
<tr><td>粘性</td><td><code>ivisfunc=0,1,2,3,4,10,11,12,21</code></td><td>先给基值 <code>amu</code>，再由边缘层、预计算场或 <code>profile_amu</code> 加空间变化；<code>amu_wall</code> 是独立叠加层。<code>amuc=0</code> 会取 <code>amu</code>。</td></tr>
<tr><td>plasma 电阻率</td><td><code>iresfunc=0,1,2,3,4,5,10,11,21</code></td><td>0 为 Spitzer 型；1 为磁通 tanh；2-4 使用先前构造的电阻率场；5 为简化新古典；10/11 读 SI/归一化剖面；21 只在 USEST+逻辑几何。</td></tr>
<tr><td>垂直热导</td><td><code>ikappafunc=0..5,10,11,12,21</code></td><td><code>kappat</code> 是常数底值，<code>kappa0</code> 是函数幅值；<code>kappaf/kappah</code> 可再按压强梯度或边界层修改。</td></tr>
<tr><td>平行热导</td><td><code>ikapparfunc=0,1,2</code></td><td>0 常数；1 在低温按 \([1+(T_{crit}/T_e)^{5/2}]^{-1}\) 抑制；2 使用 \(T_e^{5/2}\) 场并按 <code>kappar_min/max</code> 截断。</td></tr>
<tr><td>密度扩散</td><td><code>idenmfunc=0,1,10,11</code></td><td>0 常数；1 用温度依赖预计算场并限幅；10/11 读 <code>profile_denm</code>。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>磁通剖面模式按 \(\psi_N\) 取样</h4></div><p>模式 1/2 和 profile 10/11 依赖磁轴、LCFS 与 private-flux 判定；用户应保证当前平衡能稳定定义这些量。真空和壁区不会沿用 plasma 的 <code>iresfunc</code>。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>优先使用常数、物理场或 USEST 逻辑 rho 模型</h4></div><p>通用三维弱式使用相同系数，但普通 \(\psi_N\) profile 分支面向轴对称磁区。USEST 编译下的模式 21 明确使用映射前逻辑 \(\rho\)，要求 <code>igeometry=1</code>；它仍不会自动识别真实 LCFS/壁。</p></section>
<div class="callout"><strong>编译路径限制：</strong><code>kappag</code> 和 <code>kappax</code> 仅在普通 CPU 弱式中启用；GPU 路径不启用这两项，USEPARTICLES 路径也不启用 <code>kappax</code>。<code>kappag</code> 的阈值掩码比较 \(p^2\) 与 <code>gradp_crit^2</code>。</div>
</div>"""

    if group == "Hyper Diffusivity":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Hyper Diffusivity：针对有限元高波数结构的高阶耗散</h3><p>它位于常规 Transport 之后，不改变平衡或低阶输运模型；只有对应未知量存在且系数非零时才加入弱式。使用时应先做网格收敛性比较，因为 hyper 项会直接改变小尺度增长率。</p></div><span class="guide-kicker">数值稳定层</span></div>
<div class="formula">\[\lambda_{eff}=\lambda_{input}\,\mathtt{deex}^{\mathtt{ihypdx}},\qquad \mathbf E_H\sim-\nabla\times(\lambda_H\nabla\times\mathbf J).\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数族</th><th>作用场</th><th>控制</th></tr></thead><tbody>
<tr><td><code>hyper</code>, <code>hyperi</code></td><td>极向磁通/环向磁场</td><td><code>imp_hyper=0</code> 显式 psi 形式；1 隐式 \(\nabla^2\mathbf J\)；2 隐式场对齐 \(\sigma=\mathbf J\cdot\mathbf B/B^2\) 形式。</td></tr>
<tr><td><code>hyperc</code>, <code>hyperv</code></td><td>压缩/极向与环向速度</td><td>作为超粘性抑制网格尺度速度振荡。</td></tr>
<tr><td><code>hyperp</code></td><td>压力/温度</td><td><code>ihypkappa=1</code> 时再乘局部热导。</td></tr>
<tr><td><code>ihypeta</code></td><td>磁 hyper 空间权重</td><td>0 常数，1 乘 \(\eta\)，2 乘 \(p\)，大于 2 依赖已输出的磁扰动谐波。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>同一系数可用于 2D、complex 与真实 3D</h4></div><p>complex/谐波加权模式需令 <code>ibh_harmonics</code> 覆盖 <code>ihypeta</code> 所需模数；它不会只在 LCFS 内自动生效。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>作用在映射后的物理三维场</h4></div><p>公式相同，几何导数由 VMEC 映射后的 metric 给出。不要把 <code>deex</code> 当成 bloat 或逻辑 rho 尺度。</p></section>
<div class="callout"><strong>参数约束：</strong>速度 hyper 由 <code>hyperc</code> 和 <code>hyperv</code> 控制；<code>ihypdx</code> 的默认值为 0。</div>
</div>"""

    if group == "Boundary Conditions":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Boundary Conditions：把弱式自由度约束到 mesh 的物理外边界</h3><p>本组不创建边界。Mesh 的 model 分类和 <code>boundary_type</code> 先确定 first wall/domain boundary，随后这些开关为已经存在的场选择 Dirichlet、Neumann 或组合条件；内部 plasma-vacuum-conductor 界面仍由多区域方程耦合。</p></div><span class="guide-kicker">CASE 边界层</span></div>
<div class="formula">\[\int_\Omega \mu\,\nabla\!\cdot(\eta\nabla q)\,dV=-\int_\Omega\eta\nabla\mu\!\cdot\nabla q\,dV+\oint_{\partial\Omega}\mu\eta\,\hat n\!\cdot\nabla q\,dS.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>物理量</th><th>固定值</th><th>零法向梯度/导出量</th></tr></thead><tbody>
<tr><td>压力、温度、密度</td><td><code>iconst_p/t/n</code></td><td><code>inograd_p/t/n</code>；<code>tebound/tibound&gt;0</code> 只覆盖 first-wall 温度值。</td></tr>
<tr><td>磁场/电流</td><td><code>iconst_bn</code>, <code>iconst_bz</code>, <code>ifbound</code></td><td><code>inocurrent_tor/pol/norm</code> 通过 psi、F/f 的导数约束相应电流分量。</td></tr>
<tr><td>速度</td><td><code>inonormalflow</code>, <code>inoslip_pol</code>, <code>inoslip_tor</code></td><td><code>inostress_tor</code>, <code>vor_bc</code>, <code>com_bc</code> 给导数/涡量/压缩边界条件。</td></tr>
<tr><td>数值几何</td><td><code>iper</code>, <code>jper</code>, <code>nonrect</code></td><td>规则矩形测试可把相对边配成周期；一般托卡马克/仿星器外边界不使用此方式。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>运行时外边界条件与 GS 的 <code>ifixedb</code> 要分开理解</h4></div><p><code>ifixedb</code> 用于 GS 初始化阶段是否令外边界 \(\psi=0\)；它不是演化阶段的一整套壁模型。运行时磁边界由 <code>iconst_bn</code>、电流条件及是否显式包含真空/导体 zone 共同决定。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>逻辑外边界映射后才成为物理边界</h4></div><p>同样的掩码作用于映射后的三维曲面。固定边界 VMEC 的最外面常是 LCFS；bloat/multi-region case 的最外面可能是计算域或壁，必须由用户保证边界标签与物理面一致。</p></section>
<div class="callout"><strong>避免过约束：</strong>同一场通常在固定值和零法向梯度中选一种。多区域 case 的内部界面不是把所有 <code>inocurrent_*</code> 全部打开即可得到理想壁。</div>
</div>"""

    if group == "Resistive Wall":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Resistive Wall：为已有 conductor/vacuum zone 分配电阻率</h3><p>前置条件是 <code>imulti_region=1</code> 且 Mesh 已含 <code>zone_type=2</code> 导体和/或 <code>zone_type=3</code> 真空。该模块不生成有限厚度壁，也不按 LCFS 或第一壁坐标自动分类单元。</p></div><span class="guide-kicker">多区域材料层</span></div>
<div class="formula">\[\partial_t\mathbf B=-\nabla\times(\eta\mathbf J),\qquad \mathbf J=\nabla\times\mathbf B\quad (\mathbf v=0\text{ 的被动导体/真空区}).\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>优先级（低→高）</th><th>参数</th><th>含义</th></tr></thead><tbody>
<tr><td>区域类型基值</td><td><code>eta_wall</code>, <code>eta_vac</code>, <code>eta_wallRZ</code></td><td>导体/真空默认值；RZ 值负数时取对应标量值。</td></tr>
<tr><td>mesh zone 覆盖</td><td><code>eta_zone(i)</code>, <code>etaRZ_zone(i)</code></td><td>按 zone 编号指定材料；正值优先于全局壁值。</td></tr>
<tr><td>几何 region 覆盖</td><td><code>iwall_regions</code>, <code>wall_region_*</code></td><td>从文件读空间 region；后定义的匹配 region 优先。</td></tr>
<tr><td>wall break</td><td><code>iwall_breaks</code>, <code>wall_break_*</code>, <code>eta_break</code></td><td>矩形 R-Z-phi 范围内覆盖为缝隙电阻率；3D 才使用 phi 范围。</td></tr>
<tr><td>REKC</td><td><code>eta_rekc</code>, <code>ntor/mpol/sigma/phi/theta_rekc</code></td><td>以螺旋相位构造平滑局部电阻率；这是材料分布，不是外加线圈磁场。</td></tr>
</tbody></table></div>
<div class="formula">\[\Theta=\tan^{-1}\!\frac{Z-Z_0}{R-R_0},\quad \alpha=n(\phi-\phi_0)\frac{2\pi}{N_{period}}-m(\Theta-\Theta_0),\quad w=e^{(\cos\alpha-1)/\sigma^2}.\]</div>
<div class="formula">\[\eta=10^{(1-w)\log_{10}\eta_{base}+w\log_{10}\eta_{REKC}}.\]</div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>典型用途是 plasma-vacuum-finite-thickness-wall 网格</h4></div><p>物理 R-Z mesh 可直接把第一壁外的有限厚度单元标为 conductor，再按 zone、region、break 设置材料。自由边界演化来自等离子体与外部磁场/导体的耦合，不来自把 plasma zone 单纯画大。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>导体壁必须对应映射后的实际几何区域</h4></div><p>固定边界 VMEC 通常将计算域截断在最外磁面，因此没有 conductor zone 可供本组使用。外扩逻辑 multi-region mesh 可以使用同一电阻壁方程，但必须确认映射后的 zone 位于预定的真空或导体壁区域。</p></section>
</div>"""

    if group == "Time Step":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Time Step：把已选物理方程变成逐步线性系统</h3><p>这一步位于模型、输运、边界之后。先选 split/unsplit 和积分器，再决定矩阵与预条件器复用，最后才启用基于动能/KSP 迭代数的自适应时间步。</p></div><span class="guide-kicker">CASE 推进层</span></div>
<div class="formula">\[\frac{q^{n+1}-q^n}{\Delta t}=F\!\left(q^n+\theta(q^{n+1}-q^n)\right),\qquad \theta=\mathtt{thimp}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>阶段</th><th>参数</th><th>使用逻辑</th></tr></thead><tbody>
<tr><td>积分公式</td><td><code>integrator</code>, <code>thimp</code>, <code>dt</code>, <code>ddt</code></td><td>0 为 theta 法（0.5 为 CN）；1 为 BDF2 并强制 theta=1。<code>ddt</code> 是每步时间步增量。</td></tr>
<tr><td>方程拆分</td><td><code>isplitstep</code>, <code>imp_mod</code>, <code>caramana_fac</code>, <code>ipressplit</code></td><td>split 按磁场、速度、密度、热力学分块；unsplit 组装整体系统并强制 <code>imp_mod=0</code>。</td></tr>
<tr><td>系数更新</td><td><code>iteratephi</code>, <code>irecalc_eta</code>, <code>iconst_eta</code></td><td>决定在分块之间是否用新密度/温度重算输运及磁场。</td></tr>
<tr><td>矩阵复用</td><td><code>nskip</code>, <code>pskip</code>, <code>iskippc</code></td><td>分别控制矩阵和不同层次预条件器的更新/复用；系数变化快时应缩短周期。</td></tr>
<tr><td>可变步长</td><td><code>dtkecrit</code>, <code>dtmin/max</code>, <code>dtfrac</code>, <code>ksp_min/warn/max</code>, <code>max_repeat</code></td><td>只有 <code>dtkecrit&gt;0</code> 才进入此控制；步长每次乘/除 \(1+dtfrac\)，并限制在 min/max。3D 迭代超限可重做当前步。</td></tr>
<tr><td>停止条件</td><td><code>gamma_gr_stop</code>, <code>nt_gamma_gr</code>, <code>gamma_gr_stop_std</code></td><td>线性计算用动能增长率滑动标准差判断收敛，写出时间片后停止。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>2D/complex 与真实 3D 的代价控制不同</h4></div><p>复杂线性响应可用 <code>itime_independent=1</code> 与 <code>frequency</code>；真实 3D 才使用全局最大 KSP 迭代数触发重复/调步。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>通常是完整三维 split/unsplit 推进</h4></div><p>时间算法相同，但强三维几何常使矩阵与预条件器复用更敏感。VMEC 固定/自由边界的选择在初始化完成，此组不会改变计算域边界类型。</p></section>
<div class="callout"><strong>生效条件：</strong><code>dtmin/dtmax/ksp_*</code> 不会仅因被设置而自动生效；变量步长控制由 <code>dtkecrit&gt;0</code> 启用。<code>pskip</code> 的默认值为 0。</div>
</div>"""

    if group == "Numerical Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Numerical Options：控制弱式积分、变量形式和物理量保护</h3><p>这些参数不改变初始平衡来源，但会改变离散方程、积分精度和推进后场值。先保持默认建立基准，再针对收敛、负温度/密度或矩阵代价逐项调整。</p></div><span class="guide-kicker">离散细节</span></div>
<div class="formula">\[q(\mathbf x)=\sum_j\nu_j(\mathbf x)q_j,\qquad M_{ij}\dot q_j=S_{ij}q_j,\qquad \int_K f\,dV\approx\sum_{a=1}^{N_q}w_af(\mathbf x_a).\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数族</th><th>数值作用</th><th>注意</th></tr></thead><tbody>
<tr><td><code>jadv</code></td><td>1 推进环向电流/\(\Delta^*\psi\) 形式，0 推进磁通 \(\psi\) 形式。</td><td>这是离散未知量选择，不是电流源开关；当前默认 1。</td></tr>
<tr><td><code>int_pts_main/aux/diag/tor</code></td><td>主演化、辅助场、诊断和环向方向的 Gaussian 积分点数。</td><td>只能选实现支持的阶数，且二维点数与环向点数乘积受内部最大点数限制。</td></tr>
<tr><td><code>max_ke</code></td><td>线性扰动动能超过阈值时整体缩放扰动，避免数值溢出。</td><td>0 关闭；不代表物理饱和机制。</td></tr>
<tr><td><code>equilibrate</code></td><td>对线性系统行/列或未知量做尺度平衡以改善条件数。</td><td>只影响求解数值尺度，不应改变收敛后的物理解。</td></tr>
<tr><td><code>iset_*_floor</code>, <code>*_floor</code></td><td>时间推进后把相应 p/n/T 的低值截到下限。</td><td>在 <code>eqsubtract=1</code> 时修正扰动，使“平衡+扰动”满足 floor；不是连续方程中的源项。</td></tr>
<tr><td><code>iprecompute_metric</code></td><td>预计算完整几何 metric，换内存为重复积分速度。</td><td>USEST 几何会强制使用；不改变几何映射本身。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>轴对称 mesh 仍需要柱坐标 metric 与足够积分阶数</h4></div><p>2D 令 <code>int_pts_tor=1</code>；complex/3D 项再增加环向积分。floor 常用于边缘低温/低压区，但会破坏严格守恒，应记录敏感性。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>VMEC 映射使 metric 变化更强</h4></div><p>应优先检查 <code>int_pts_main/tor</code> 和 <code>iprecompute_metric</code> 的收敛/内存；逻辑网格圆滑不代表物理单元 metric 简单。</p></section>
</div>"""

    if group == "Solver":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Solver：求解每个时间块形成的线性系统</h3><p>Time Step 组决定何时组装矩阵，本组给通用容差、直接/迭代选择、最大迭代数和初猜策略。具体后端还受编译选项以及 PETSc 命令行/选项文件控制。</p></div><span class="guide-kicker">线性代数层</span></div>
<div class="formula">\[A\,\delta q=b,\qquad \frac{\|b-A\delta q\|}{\|b\|}\lesssim\mathtt{solver\_tol}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数</th><th>作用</th><th>用户判断</th></tr></thead><tbody>
<tr><td><code>solver_type</code></td><td>SCOREC/PETSc 通用接口中 0 直接、1 迭代；Trilinos/Aztec 路径本质上走迭代配置。</td><td>最终算法可能被后端选项覆盖，应以运行日志为准。</td></tr>
<tr><td><code>solver_tol</code></td><td>线性残差收敛容差。</td><td>必须明显小于时间离散/非线性误差；过松会污染增长率与守恒。</td></tr>
<tr><td><code>num_iter</code></td><td>通用/Trilinos 最大迭代数。</td><td>PETSc 常由命令行 KSP 最大迭代数进一步控制。</td></tr>
<tr><td><code>isolve_with_guess</code></td><td>用已有场/上一次解作为非零初猜。</td><td>连续时间步常有利，重建矩阵或突变源项后需观察迭代数。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>按 2D、complex、3D 和 wall 模型选择求解规模</h4></div><p>装置类型不改变参数语义；多区域电阻壁、六场和真实 3D 会显著增大系统并更依赖预条件器。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>三维映射几何通常更依赖可扩展迭代求解</h4></div><p>同样使用本组容差，但 PETSc/Trilinos 的实际预条件配置应结合映射 metric、平面数和 MPI 分解调节。</p></section>
</div>"""

    if group == "Trilinos Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Trilinos Options：只配置 Aztec/Trilinos 编译路径</h3><p>这些字符串不会配置现代 PETSc 路径。先从编译和启动日志确认正在使用 Trilinos/Aztec，再设置 Krylov、预条件器、子域求解器及 ILU 参数。</p></div><span class="guide-kicker">条件后端</span></div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>层次</th><th>有效字符串或参数</th><th>作用</th></tr></thead><tbody>
<tr><td>Krylov</td><td><code>cg</code>, <code>cg_condnum</code>, <code>gmres</code>, <code>gmres_condnum</code>, <code>cgs</code>, <code>tfqmr</code></td><td><code>krylov_solver</code> 选择外迭代算法。</td></tr>
<tr><td>预条件器</td><td><code>none</code>, <code>Jacobi</code>, <code>Neumann</code>, <code>ls</code>, <code>sym_GS</code>, <code>dom_decomp</code></td><td><code>preconditioner</code> 字符串区分大小写。</td></tr>
<tr><td>子域</td><td><code>ilu</code>, <code>lu</code>, <code>ilut</code>, <code>rilu</code>, <code>bilu</code>, <code>icc</code></td><td><code>sub_dom_solver</code> 与 <code>subdomain_overlap/graph_fill</code> 控制 domain decomposition。</td></tr>
<tr><td>ILU/多项式</td><td><code>drop_tolerance</code>, <code>ilu_fill_level</code>, <code>ilu_omega</code>, <code>poly_ord</code></td><td>控制填充、丢弃、松弛及多项式阶数，只有相应预条件器读取。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>参数语义与装置无关</h4></div><p>场数、多区域 wall 和三维平面数决定矩阵难度；这些选项不改变平衡或物理模型。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>参数语义与装置无关</h4></div><p>映射 metric 会改变矩阵条件数，但同一 Aztec 选项集适用。若运行的是 PETSc，应改 PETSc options，而不是本组字符串。</p></section>
</div>"""

    if group == "Sources/Sinks":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Sources/Sinks：在已建立的演化方程上加入外部驱动和反馈</h3><p>本组不负责初始平衡。只有 Model Options 中对应方程存在、计算为非线性且源项门控满足时，粒子、动量、热和电流源才进入时间推进；多个同类源会相加。</p></div><span class="guide-kicker">CASE 驱动层</span></div>
<div class="formula">\[\partial_t n_i+\nabla\!\cdot(n_i\mathbf v)=\nabla\!\cdot(D\nabla n_i)+\sigma_{pel}+\sigma_{beam}+\sigma_{ion}-\sigma_{sink}+\sigma_{arc}.\]</div>
<div class="formula">\[S_G(R,Z)=\frac{A}{2\pi\sigma^2R}\exp\!\left[-\frac{(R-R_0)^2+(Z-Z_0)^2}{2\sigma^2}\right].\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>源族</th><th>主要参数</th><th>生效条件与覆盖</th></tr></thead><tbody>
<tr><td>回路电压/电流控制</td><td><code>vloop*</code>, <code>tcur*</code>, <code>control_*</code></td><td>只在非线性且未减去平衡电流的反馈路径工作。无反馈时回路电压可按 <code>cos(2*pi*vloop_freq*t)</code> 振荡；PID 会更新控制量。</td></tr>
<tr><td>pellet</td><td><code>ipellet</code>, <code>pellet_*</code>, <code>iread_pellet</code>, <code>ipellet_abl</code></td><td>持续粒子源或初始扰动；可由标量定义一个 pellet，或从 <code>pellet.dat</code> 定义多个。ablation 会随局部等离子体状态更新速率/宽度。</td></tr>
<tr><td>neutral beam</td><td><code>ibeam</code>, <code>beam_*</code></td><td>模式 1-5 选择向密度、动量和热方程加入哪些沉积项；沉积为 R-Z Gaussian，强度由 ions/s 与束能换算。</td></tr>
<tr><td>电流/极向动量</td><td><code>icd_source</code>, <code>J_0cd/R_0cd/...</code>, <code>ipforce</code>, <code>*force</code></td><td>current-drive 模式 1 为物理 R-Z Gaussian，2/3 是 USEST 逻辑 rho/profile 路径；极向力按磁通坐标构造。</td></tr>
<tr><td>热源</td><td><code>igaussian_heat_source</code>, <code>ghs_*</code>, <code>iread_heatsource</code></td><td>需要非线性压力/温度方程；Gaussian 与文件剖面相加。<code>iheat_sink=1</code> 只实现于专用 <code>itaylor=27</code>。</td></tr>
<tr><td>粒子化学/汇</td><td><code>ionization*</code>, <code>isink/sink*</code>, <code>iarc_source*</code>, <code>idenfloor*</code></td><td>需要 <code>idens=1,linear=0</code>。ionization 有温度门控；sink 是最多两个局部 Gaussian；density floor 是恢复源而非硬截断。</td></tr>
<tr><td>密度反馈</td><td><code>n_target</code>, <code>n_control_*</code></td><td>用全局密度误差调节每个 pellet 的 <code>pellet_rate</code>。</td></tr>
</tbody></table></div>
<div class="formula">\[I_{target}(t)=I_i+\frac{I_f-I_i}{2}\left[1+\tanh\frac{t-t_0}{t_w}\right],\qquad u_{PID}=-(K_Pe+K_I\!\int e\,dt+K_D\dot e).\]</div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>磁通剖面源与回路电压/总电流反馈是主要路径</h4></div><p><code>profile_particlesource/profile_heatsource</code> 以 \(\psi_N\) 为横坐标；<code>ipforce</code> 和大部分 current-drive 模式也依赖轴对称磁区。物理 R-Z-phi Gaussian 坐标必须落在 mesh 内。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>先区分逻辑径向源与物理空间源</h4></div><p>Input 读入的粒子/热源剖面以逻辑 \(s=x_l^2+z_l^2\) 取样；物理 Gaussian/pellet 坐标则在映射后的柱坐标域中运动。轴对称总电流、\(\psi_N\) 极向力和 loop-voltage 控制不应未经验证直接移植。</p></section>
<div class="callout"><strong>总门控：</strong>density source 要求 <code>idens=1,linear=0</code>；momentum source 要求非线性并选择相应 beam；heat source 要求非线性且 <code>numvar&gt;=3</code> 或 <code>ipres=1</code>。仅设置幅值而未满足这些条件不会创建方程。</div>
</div>"""

    if group == "PRAD Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>PRAD：不演化电荷态的单杂质瞬时辐射模型</h3><p>PRAD 在现有电子密度和温度上计算单一杂质的辐射冷却，不增加每个电荷态的连续方程。它需要非线性压力/温度方程，且 Model Options 中 <code>irad_heating=1</code> 才把损失写入热方程。</p></div><span class="guide-kicker">简单辐射</span></div>
<div class="formula">\[P_{rad}=n_e n_Z L_Z(T_e),\qquad n_Z=\mathtt{prad\_fz}\,n_e\ \text{或由 profile\_nz 给定}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数</th><th>用法</th></tr></thead><tbody>
<tr><td><code>iprad</code></td><td>1 开启；0 不计算 PRAD。</td></tr>
<tr><td><code>prad_z</code></td><td>选择辐射表的原子序数；当前活动表面向 C=6、Ar=18、Fe=26，其它值只给警告，不能视为有可靠数据。</td></tr>
<tr><td><code>prad_fz</code></td><td>未读文件时的杂质总密度/电子密度比例。</td></tr>
<tr><td><code>iread_prad</code></td><td>1 读 <code>profile_nz</code>：第一列 \(\psi_N\)，第二列为 \(10^{20}\,m^{-3}\) 杂质密度，并覆盖比例模型。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>文件剖面按归一化磁通使用</h4></div><p>PRAD 本身只读局部 \(n_e,T_e,n_Z\)，但 <code>profile_nz</code> 的空间映射依赖轴对称磁通坐标。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>局部比例模型可工作，普通 psi 剖面不具有明确三维映射</h4></div><p><code>prad_fz</code> 的局部比例公式不区分装置；若要给三维仿星器杂质分布，应确认当前版本的 profile 映射，不要默认它等于 VMEC 的 s。</p></section>
</div>"""

    if group == "KPRAD Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>KPRAD：逐电荷态演化、准中性和辐射能量耦合</h3><p>KPRAD 在主离子 MHD 上增加一个杂质元素的中性态与所有离化态密度；电离/复合在每个 MHD 步内自适应子循环，随后更新电子密度、质量密度和热损失。</p></div><span class="guide-kicker">多电荷态杂质</span></div>
<div class="formula">\[\partial_t n_Z^{(j)}+\nabla\!\cdot(n_Z^{(j)}\mathbf v)=\nabla\!\cdot(D_j\nabla n_Z^{(j)})+\sigma_Z^{(j)},\qquad n_e=Z_i n_i+\sum_{j=1}^{Z}j\,n_Z^{(j)}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>步骤</th><th>参数</th><th>作用</th></tr></thead><tbody>
<tr><td>原子数据</td><td><code>ikprad</code>, <code>kprad_z</code>, <code>adas_adf11</code></td><td>1 用内置拟合（支持 Z=1,2,4,5,6,10,18）；-1 仅在 USEADAS 编译下读 ADF11 路径。</td></tr>
<tr><td>初始中性杂质</td><td><code>kprad_nz</code>, <code>kprad_fz</code>, <code>iread_lp_source</code></td><td>初始中性密度为常数项加电子密度比例；Lagrangian-particle 源读取 <code>cloud.txt</code>，属于专用 pellet 工作流。</td></tr>
<tr><td>空间输运</td><td><code>ikprad_evolve_neutrals</code>, <code>kprad_n0_denm_fac</code></td><td>0 中性不对流/扩散；1 对流并扩散；2 只扩散。离化态随主流体并使用密度扩散。</td></tr>
<tr><td>低值处理</td><td><code>kprad_nemin</code>, <code>kprad_temin</code>, <code>ikprad_min_option</code></td><td>选项 1 使用默认全反应；2 低值处禁电离/辐射但允许受限复合；3 在子循环中低于阈值时关闭电离、复合和辐射。</td></tr>
<tr><td>子步</td><td><code>ikprad_max_dt</code>, <code>kprad_max_dt</code></td><td>选项 1 令上限为 \(dt/(Z+1)\)，显式正值可进一步限制；算法在电子密度变化超过 20% 时回退减半，小于 2% 时增大子步。</td></tr>
<tr><td>内部热反馈</td><td><code>ikprad_evolve_internal</code></td><td>1 在每个 KPRAD 子步内更新局部 \(n_e,T_e\) 和反应率；0 在整 MHD 步内冻结输入反应率。</td></tr>
</tbody></table></div>
<div class="formula">\[Q_e\supset-\left(P_{line}+P_{brem}+P_{ion}+P_{rec,kin}\right).\]</div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>电荷态方程作用于 plasma zone 并随 MHD 流演化</h4></div><p>可与 pellet/杂质注入联合使用。KPRAD 不重新求 GS，也不会覆盖初始主离子剖面；它在时间推进中通过准中性和质量项反馈。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>同一局部反应与三维输运方程作用于映射域</h4></div><p>原子率只依赖局部 \(n_e,T_e\)，装置无关；中性/杂质源的空间位置和逻辑/物理坐标仍需与 VMEC 映射及 zone 对齐。</p></section>
<div class="callout"><strong>能量含义：</strong>程序计算复合释放的动能与势能，但热方程只扣除 kinetic recombination 项；势能释放不再次从电子流体动能中扣除。</div>
</div>"""

    if group == "Particle Simulation Options":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Particle Simulation：USEPARTICLES 下的混合 MHD-PIC 闭合</h3><p>这些参数只有编译了 USEPARTICLES 才能读入，并且 Model Options 的 <code>kinetic=1</code> 才启动 PIC。<code>kinetic=2/3</code> 是 CGL 流体模型，不使用本组粒子参数。</p></div><span class="guide-kicker">条件物理模块</span></div>
<div class="formula">\[\dot{\mathbf x}=\mathbf v,\qquad m_s\dot{\mathbf v}=q_s(\mathbf E+\mathbf v\times\mathbf B),\qquad \Delta t_p=\frac{\Delta t_{MHD}}{N_{substep}N_{subcycle}}.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数族</th><th>选择</th><th>作用</th></tr></thead><tbody>
<tr><td>物种</td><td><code>kinetic_fast_ion</code>, <code>kinetic_thermal_ion</code>, <code>fast_ion_mass/z</code></td><td>打开快离子和/或热离子 PIC；质量/电荷为 0 时分别继承 <code>ion_mass/z_ion</code>。</td></tr>
<tr><td>分布</td><td><code>fast_ion_dist=0/1/2</code>, <code>fast_ion_max_energy</code></td><td>0 读三维分布；1 Maxwellian；2 slowing-down，并用最大能量截断采样。</td></tr>
<tr><td>表示与耦合</td><td><code>particle_linear</code>, <code>ifullf</code>, <code>iconst_f0</code>, <code>particle_couple</code></td><td>选择 delta-f/full-f、背景分布及 -1 test-particle、0 压力耦合、1 电流耦合。<code>eqsubtract=0</code> 会强制 full-f。</td></tr>
<tr><td>时间与容量</td><td><code>particle_substeps/subcycles</code>, <code>num_par_max</code>, <code>num_par_scale</code></td><td>控制粒子子步和最多粒子数；未启用 thermal-ion PIC 时 subcycles 被强制为 1。</td></tr>
<tr><td>平滑/同步</td><td><code>igyroaverage</code>, <code>smooth_par</code>, <code>smooth_dens_parallel</code>, <code>ikinetic_vpar</code>, <code>vpar_reduce</code></td><td>控制 gyro-average、PIC 矩到 FE 场的平滑及平行流同步/衰减。</td></tr>
<tr><td>径向/模过滤</td><td><code>kinetic_rhomax</code>, <code>imode_filter</code>, <code>mode_filter_ntor</code></td><td>限制粒子权重范围并筛选环向模。负 <code>imode_filter</code> 只保留所列模；正值当前仅从各场减去所列模幅值的 0.1，不能理解为完全删除。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>快离子分布和 rho 截断通常按轴对称平衡构造</h4></div><p>物理 pusher 使用有限元三维 E/B；初始分布、磁通半径和 mode filter 应与所选 2D/3D 表示一致。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>pusher 可使用映射后的三维场，初始化假设需另行验证</h4></div><p>本组没有 stellarator 专用开关。使用读取分布、<code>kinetic_rhomax</code> 或轴对称构造的 Maxwellian/slowing-down 前，应确认其坐标和权重定义与 VMEC/外场域一致。</p></section>
</div>"""

    if group == "Diagnostics":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Diagnostics：在映射后的物理场上布置合成测量</h3><p>诊断不参与求解，但依赖 Mesh/Equilibrium 已经建立的物理坐标。数组长度上限为 100；先给数量，再按一基索引填写位置和方向。</p></div><span class="guide-kicker">合成诊断</span></div>
<div class="formula">\[B_{probe}=\hat{\mathbf n}\cdot\mathbf B(R,\phi,Z),\qquad \Phi_{loop}(R,Z)=\int_{\phi\ domain}\psi(R,\phi,Z)\,d\phi.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>诊断</th><th>参数</th><th>输出含义</th></tr></thead><tbody>
<tr><td>X-ray chord</td><td><code>xray_detector_enabled</code>, <code>xray_r0/phi0/z0</code>, <code>xray_theta/sigma</code></td><td>从给定探测器点、弦方向和角扩展构造 chord mask；phi/theta/sigma 输入为度并在内部转弧度。</td></tr>
<tr><td>磁探针</td><td><code>imag_probes</code>, <code>mag_probe_x/phi/z</code>, <code>mag_probe_nx/nphi/nz</code></td><td>在探针点评价 B 并投影到给定法向。法向分量由用户给出，程序不替你归一化或检查传感器是否在域内。</td></tr>
<tr><td>磁通环</td><td><code>iflux_loops</code>, <code>flux_loop_x/z</code></td><td>在固定 R-Z 位置沿当前环向计算域积分磁通场；点不在域内时输出 0。</td></tr>
<tr><td>固定温度诊断点</td><td><code>ifixed_temax</code></td><td>非零时不搜索温度最大值，而在平衡磁轴参考点 <code>xmag0,zmag0</code> 评价温度。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>位置使用物理柱坐标 R-phi-Z</h4></div><p>二维探针常令 phi=0；三维/complex 信号需按实际环向相位布置。磁通环本质上是固定 R-Z 的环向积分。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>必须填写 VMEC 映射后的物理位置</h4></div><p>不能把逻辑圆盘的 x,z 直接写入探针参数。若只计算一个 field-period 扇区，环向积分和可布置的 phi 范围也只覆盖该计算域。</p></section>
</div>"""

    if group == "Output":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Output：决定何时保存场、标量、辅助量和可重启状态</h3><p>输出在每步求解和诊断之后执行。标量通常每步写，完整场按 <code>ntimepr</code>；timeout 或线性增长率收敛会强制写一个时间片后安全停止。</p></div><span class="guide-kicker">CASE 结果层</span></div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>目标</th><th>参数</th><th>实际行为</th></tr></thead><tbody>
<tr><td>日志/计时</td><td><code>iprint</code>, <code>itimer</code></td><td>控制终端详细度及内部阶段计时输出，不改变物理字段。</td></tr>
<tr><td>场时间片</td><td><code>ntimepr</code>, <code>iwrite_aux_vars</code>, <code>iwrite_transport_coeffs</code></td><td>每 <code>ntimepr</code> 步计算可选辅助场并写 HDF5；关闭辅助量可明显减少计算和文件体积。</td></tr>
<tr><td>标量/谐波</td><td><code>icalc_scalars</code>, <code>ike_only</code>, <code>ike_harmonics</code>, <code>ibh_harmonics</code></td><td>选择全局标量以及 3D 动能/磁扰动谐波；某些控制和 hyper 模式依赖这些诊断，不能为省时随意关闭。</td></tr>
<tr><td>文件结构</td><td><code>ifout</code>, <code>iwrite_adjacency</code>, <code>iwrite_quad_points</code>, <code>idouble_out</code></td><td>控制 f 场、网格邻接、积分点和浮点精度；<code>ifout=-1</code> 运行时取 3D=1、2D=0。</td></tr>
<tr><td>温度/电场调试</td><td><code>itemp_plot</code>, <code>ibdgp</code>, <code>iveldif</code></td><td>额外写热源/导热/Ohmic 或电场分解；非零 partial 模式只输出所选贡献，不能当作完整物理量。</td></tr>
<tr><td>重启</td><td><code>irestart</code>, <code>irestart_slice</code>, <code>ntimers</code></td><td>0 新启动；1 普通 HDF5 restart；2 用 restart 场初始化 GS；3 用 2D real restart 启动 complex。slice=-1 取最后时间片，否则选指定索引并丢弃其后的输出组。</td></tr>
<tr><td>调度保护</td><td><code>write_ts_on_job_timeout</code></td><td>1 安装作业超时/抢占信号处理，收到信号后强制写时间片再停止。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>2D、complex、3D restart 的维度转换有专用入口</h4></div><p>从 2D 扩展到 3D、从 real 2D 转 complex 或改变环向周期时，程序把它视为新算例，重置步数/时间并重新初始化扰动。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>restart 必须保持映射几何和场周期相容</h4></div><p>输出保存的是物理 mesh/场及参数属性；改变 VMEC 文件、逻辑 mesh、周期或平面数并非普通续算，应按新初始化路径验证。</p></section>
<div class="callout"><strong>运行时默认：</strong><code>ntimepr&lt;1</code> 被改为 1；<code>ntimers&lt;=0</code> 被改为 <code>ntimepr</code>。旧参数 <code>iwrite_restart</code> 已废弃，不能代替当前 HDF5 输出流程。</div>
</div>"""

    if group == "Miscellaneous":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Miscellaneous：物种常数、two-fluid 尺度与环向模数</h3><p>这些量被多个前述模块共享，应在选择模型之前确定。<code>ion_mass</code> 会改变整个时间/速度归一化；<code>z_ion</code> 同时进入准中性、电阻率、skin depth 和剖面换算。</p></div><span class="guide-kicker">共享物理常数</span></div>
<div class="formula">\[d_i=\frac{c}{L_0\sqrt{4\pi n_0(Z_ie)^2/m_i}}\,\mathtt{db\_fac},\qquad n_e=Z_i n_i.\]</div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>参数</th><th>物理/数值作用</th></tr></thead><tbody>
<tr><td><code>gam</code></td><td>比热比 \(\Gamma\)，进入压缩功、温度方程和热通量系数；默认 5/3。</td></tr>
<tr><td><code>ion_mass</code>, <code>z_ion</code></td><td>主离子质量（质子质量单位）和电荷态；决定 \(m_i,n_e\)、归一化、束流/粒子及 KPRAD 耦合。</td></tr>
<tr><td><code>db</code>, <code>db_fac</code></td><td><code>db&gt;=0</code> 直接覆盖；<code>db&lt;0</code> 时由物理尺度计算再乘 factor。默认 factor=0，因此自动计算后仍关闭 two-fluid 幅值。</td></tr>
<tr><td><code>lambda_coulomb</code></td><td>Coulomb 对数，进入碰撞频率、Spitzer 电阻率和能量均分系数。</td></tr>
<tr><td><code>thermal_force_coeff</code></td><td>旋转/抗磁换算中的电子温度梯度热力系数。</td></tr>
<tr><td><code>mass_ratio</code>, <code>lambdae</code></td><td>当前仅注册，无活动计算读取；不能用它们打开电子惯性。</td></tr>
<tr><td><code>ntor</code>, <code>mpol</code></td><td>环向/极向模数；<code>ntor</code> 主要用于 complex 线性模，二者也被若干解析扰动、外场和 REKC 设置复用。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>complex 单 n 模和轴对称 two-fluid 闭合最常使用本组</h4></div><p><code>ntor</code> 不等于真实 3D 的平面数；真实 3D 由 <code>nplanes</code> 表示并可同时含多个环向模。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>物种常数相同，单 n 解释通常不适用于三维平衡</h4></div><p>完整仿星器场通过平面和场周期表示；<code>ntor/mpol</code> 只在明确的专用扰动/REKC 分支使用，不描述 VMEC 的全部傅里叶谱。</p></section>
</div>"""

    if group == "Deprecated":
        return r"""
<div class="guide" data-guide>
<div class="guide-title"><div><h3>Deprecated：只为旧 C1input 保持可解析</h3><p>这些名字仍可读入，目的是让旧模板不因未知参数立即失败；它们写入 dummy 变量或已被当前 HDF5/场表示取代。新 case 不应设置。</p></div><span class="guide-kicker">兼容层</span></div>
<div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>旧参数</th><th>当前替代/行为</th></tr></thead><tbody>
<tr><td><code>ibform</code>, <code>igs_method</code></td><td>dummy 占位；当前磁场形式和 GS 算法不随其值改变。</td></tr>
<tr><td><code>zeff</code></td><td>改用 <code>z_ion</code>；旧值不会作为主离子电荷进入当前模型。</td></tr>
<tr><td><code>ivform</code></td><td>只实现当前固定的 velocity form；旧选择值不再提供其它形式。</td></tr>
<tr><td><code>iwrite_restart</code></td><td>重启时间片由当前 HDF5 输出流程、<code>ntimepr/ntimers</code> 和 <code>irestart</code> 管理。</td></tr>
<tr><td><code>iwrite_adios</code>, <code>iread_adios</code>, <code>iglobalout</code>, <code>iglobalin</code>, <code>iread_hdf5</code></td><td>旧 I/O 后端/全局文件开关；当前代码使用 HDF5 初始化与 restart 路径。</td></tr>
</tbody></table></div>
<section class="device-band tokamak-band"><div class="device-heading"><span>托卡马克</span><h4>不用于新 case</h4></div><p>若旧托卡马克模板含这些名字，可删除并按替代参数重新确认行为。</p></section>
<section class="device-band stellarator-band"><div class="device-heading"><span>仿星器</span><h4>不用于新 case</h4></div><p>它们同样不会选择 VMEC/外场、几何映射或三维输出格式。</p></section>
</div>"""

    return ""


def simplified_html_supplement(group: str) -> str:
    remaining = remaining_module_supplement(group)
    if remaining:
        return remaining
    if group == "Mesh":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Mesh：从平衡方案到有限元计算域</h3>
<p>设置 case 时应先决定装置类型和平衡来源，再设计二维网格、区域标签和环向计算域。程序内部的读取顺序与用户的设计顺序不同：托卡马克直接使用物理 R-Z 网格；仿星器先读取 VMEC 几何并把逻辑网格映射到物理空间，随后才初始化平衡场。</p>
</div>
<span class="guide-kicker">CASE 设置链条</span>
</div>

<div class="sequence-pair">
<div><strong>用户设计顺序</strong><span>装置与平衡模式 → 物理计算域 → 二维 mesh/model → boundary/zone → 环向域 → 分辨率检查</span></div>
<div><strong>程序运行顺序</strong><span>读取几何设置 → 装载二维 mesh/model → 建立物理坐标 → 生成环向三维域 → 投影平衡和初始场</span></div>
</div>

<section class="device-band tokamak-band">
<div class="device-heading"><span>托卡马克</span><h4>mesh 坐标就是物理柱坐标 (R,Z)</h4></div>
<ol class="case-steps">
<li><strong>先选平衡入口。</strong>直接使用 gfile 时选择 <code>iread_eqdsk=1, igs=0</code>；需要 M3D-C1 求解 GS 时使用 gfile 作为初值，或完全由解析/输入剖面建立初值。此选择决定 mesh 需要覆盖的物理区域和可用的外部数据范围。</li>
<li><strong>在物理 R-Z 平面生成网格。</strong>标准设置为 <code>igeometry=0</code>、<code>iread_vmec=0</code>。<code>mesh_filename</code> 中每个节点的坐标就是实际 R 和 Z；读取 gfile 不会移动节点，也不会把圆形 mesh 变成等离子体形状。</li>
<li><strong>按希望演化的区域确定外边界。</strong>只算等离子体可把域截断在目标边界；要计算等离子体外真空、第一壁或电阻壁，原始 mesh/model 必须已经包含这些实体。扩大 plasma zone 本身不会把固定边界平衡变成自由边界平衡。</li>
<li><strong>给现有单元赋予物理标签。</strong><code>imulti_region=0</code> 会把全部单元强制视为 plasma；<code>imulti_region=1</code> 时用 <code>zone_type</code> 标记 plasma/conductor/vacuum，用 <code>boundary_type</code> 标记 first wall/domain boundary。标签只分类，不改变几何。</li>
<li><strong>再选择二维或三维环向域。</strong>二维及 complex 线性计算使用 <code>nplanes=1</code>；真实三维计算使用 <code>nplanes&gt;1</code>。托卡马克通常取 <code>nperiods=1, ifull_torus=1</code>；只有明确利用环向周期性时才截取扇区。</li>
<li><strong>最后检查平衡与网格的相容性。</strong>gfile 数据按 R-Z 坐标插值到所有 mesh 单元，并不限于 plasma zone。用户需保证节点位于所需 gfile 数据框内，并保证 LCFS、真空、壁和计算域外边界在物理上合理；程序不做这项一致性认证。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>设置层次</th><th>主要参数</th><th>托卡马克用法</th></tr></thead>
<tbody>
<tr><td>坐标与几何</td><td><code>igeometry</code>, <code>iread_vmec</code>, <code>xcenter/zcenter</code>, <code>bloat_*</code>, <code>nzer_*</code></td><td>常规物理 R-Z mesh 取 <code>igeometry=0, iread_vmec=0</code>；VMEC 映射、bloat 和 Zernike 阶数均不参与。<code>xzero/zzero</code> 也不能用于平移外部 mesh。</td></tr>
<tr><td>二维文件</td><td><code>mesh_filename</code>, <code>mesh_model</code>, <code>model_info</code></td><td>mesh 保存节点和单元，model 保存边界/zone 拓扑；二者编号必须一致。<code>model_info</code> 仅专用 CAD 编译路径使用。</td></tr>
<tr><td>区域</td><td><code>imulti_region</code>, <code>boundary_type(i)</code>, <code>zone_type(i)</code></td><td>单区时自动全 plasma；多区时必须逐编号给出有效类型。导体 zone 的材料参数另在 Resistive Wall 组中用 <code>eta_zone/etaRZ_zone</code> 等设置。</td></tr>
<tr><td>环向离散</td><td><code>nplanes</code>, <code>nperiods</code>, <code>ifull_torus</code>, <code>iread_planes</code>, <code>toroidal_pack_*</code></td><td>未读 <code>plane_positions</code> 时默认均匀分布；packing 只调整平面角度，不改变二维截面。3D+PETSc 当前要求 MPI rank 数等于 <code>nplanes</code>。</td></tr>
<tr><td>数值后端</td><td><code>imatassemble</code>, <code>is1_agg_blks</code>, <code>is1_agg_scp</code>, <code>ipartitioned</code></td><td>仅影响矩阵装配、聚合或保留的兼容选项，不改变几何、zone 或平衡映射。</td></tr>
</tbody>
</table>
</div>
</section>

<section class="device-band stellarator-band">
<div class="device-heading"><span>仿星器</span><h4>二维 mesh 是逻辑圆盘，VMEC 决定物理几何</h4></div>
<ol class="case-steps">
<li><strong>先选固定边界或外场/自由边界初始化。</strong>固定边界通常为 <code>itaylor=40</code>，直接使用 wout 中的几何、磁场和压力；外场/自由边界路径通常为 <code>itaylor=41</code>，磁场由外场/总场文件初始化。两种路径都应先决定物理计算域是否只到 VMEC 边界，还是需要向外 bloat。</li>
<li><strong>生成二维逻辑圆盘 mesh。</strong>常用 <code>igeometry=1, iread_vmec=1</code>。mesh 文件的 x、z 不是最终物理 R、Z，而用于构造 \\(\\rho=\\sqrt{(x-x_{\\mathrm{center}})^2+(z-z_{\\mathrm{center}})^2}\\) 和逻辑极角；因此 <code>xcenter/zcenter</code> 必须与生成圆盘时使用的圆心一致。</li>
<li><strong>用 VMEC 几何完成坐标映射。</strong><code>vmec_filename</code> 提供 R/Z 傅里叶系数和场周期。逻辑 <code>(rho,theta,phi)</code> 被映射为物理 <code>(R,Z,phi)</code>；逻辑圆形单元在物理空间通常成为非圆、随环向扭转的棱柱单元。</li>
<li><strong>决定逻辑外边界对应哪里。</strong>无 bloat 时，逻辑 <code>rho=1</code> 通常映射到 VMEC 最外磁面。<code>bloat_factor</code> 或 <code>bloat_distance</code> 可把计算边界向外扩展；距离参数优先。外扩区域不会自动获得 vacuum、first wall 或 conductor 的标签。</li>
<li><strong>谨慎设计多区域。</strong><code>boundary_type/zone_type</code> 标记的是映射前逻辑 mesh 中已经存在的边和 zone。程序只验证类型值和编号，不根据 wout 的 LCFS、mgrid 范围或真实壁面检查标签位置。语法合法的 conductor zone 仍可能映射到真实等离子体内部。</li>
<li><strong>按场周期生成三维域。</strong><code>nperiods</code> 定义环面周期分割；<code>ifull_torus=0</code> 只计算一个相应扇区，此时 VMEC <code>nfp</code> 必须能被 <code>nperiods</code> 整除。<code>nplanes</code> 是所选域内的环向平面数，应解析几何和磁场中的最高相关环向模。</li>
<li><strong>映射完成后再写入平衡场。</strong>固定边界路径把 wout 的 B、压力等投影到物理有限元域；外场路径写入外部/总磁场。mesh 的 zone 标签不会选择 VMEC 数据的读取范围，也不会替代平衡边界。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>目标</th><th>推荐组合</th><th>用户需要确认</th></tr></thead>
<tbody>
<tr><td>固定边界 VMEC</td><td><code>itaylor=40</code>, <code>igeometry=1</code>, <code>iread_vmec=1</code>, <code>bloat_factor=0</code>, <code>bloat_distance=0</code></td><td>逻辑外边界与 wout 最外磁面对应；通常使用单一 plasma zone。程序显式要求 <code>bloat_factor=0</code>，同时应关闭距离外扩。</td></tr>
<tr><td>外扩计算域</td><td><code>igeometry=1</code>, <code>iread_vmec=1</code>，并选择一种 <code>bloat_*</code></td><td>外扩只改变几何映射；真空、壁和材料区域仍须在 mesh/model 与 zone 参数中显式设计。</td></tr>
<tr><td>周期扇区</td><td><code>ifull_torus=0</code>, 合理的 <code>nperiods</code> 和 <code>nplanes</code></td><td>需满足 \\(n_{\\mathrm{fp}}\\bmod n_{\\mathrm{periods}}=0\\)，且所有自定义 <code>plane_positions</code> 均位于当前扇区角度范围内。</td></tr>
<tr><td>几何阶数调节</td><td><code>nzer_manual</code> 优先；否则使用非负 <code>nzer_factor</code></td><td>只在 VMEC 到 Zernike 几何表示的精度测试中调整；默认值通常更稳妥。</td></tr>
</tbody>
</table>
</div>
</section>

<div class="callout"><strong>共同原则：</strong>mesh 是有限元几何和拓扑的地基，平衡数据负责定义初始物理场。区域标签、坐标映射和平衡边界是三件独立的事；M3D-C1 会按输入执行，但不会证明三者在物理上彼此一致。</div>
</div>
"""
    if group == "Input":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Input：按跑一个 case 的顺序选择初始数据</h3>
<p>先判断是直接读取已有平衡结果，还是让 M3D-C1 根据文件/解析参数继续求解；随后再准备与平衡相容的 mesh，最后才选择可覆盖的剖面、旋转、NEO 数据和运行时源项。下列两条路径分别适用于托卡马克与仿星器。</p>
</div>
<span class="guide-kicker">CASE 设置链条</span>
</div>

<div class="callout"><strong>唯一平衡入口：</strong>初始化分支的优先级为 <code>iread_eqdsk</code> → <code>iread_dskbal</code> → <code>iread_jsolver</code> → <code>itaylor</code>。排序靠前的非零参数会使后续入口失效，且程序不报告参数冲突。因此，一个 case 只能配置一个平衡入口；仿星器使用 <code>itaylor=40/41</code> 时，三个托卡马克平衡读取参数必须全部为 0。</div>

<section class="device-band tokamak-band">
<div class="device-heading"><span>托卡马克</span><h4>先决定直接投影 gfile，还是重新求解 Grad-Shafranov 方程</h4></div>
<ol class="case-steps">
<li><strong>选择平衡策略。</strong>已有平衡且只需作为初值时直接投影 gfile；需要改变剖面、边界条件或重新取得自洽轴对称平衡时启用 GS。<code>dskbal</code> 和 Jsolver 是保留的旧入口。</li>
<li><strong>按所选平衡准备物理 R-Z mesh。</strong>Input 参数不生成网格，也不按 LCFS 裁切数据。gfile 的 <code>psirz</code> 等量会插值到所有单元，用户需先保证 mesh 与 gfile 数据框、壁和 zone 的几何关系合理。</li>
<li><strong>仅在 GS 路径选择剖面覆盖。</strong><code>iread_p/f/ne/te/omega*</code> 位于 GS 的剖面构造流程中。直接导入而不调用 GS 时，这些常规文件不会替换已经投影的平衡。</li>
<li><strong>最后加载独立后处理输入。</strong>NEO 速度在平衡之后施加；粒子源和热源在时间推进时按当前磁通坐标取样。它们不改变初始 mesh 或 GS 边界。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>用户目标</th><th>平衡设置</th><th>程序实际做法</th><th>剖面文件是否可覆盖</th></tr></thead>
<tbody>
<tr><td>直接使用 gfile 结果</td><td><code>iread_eqdsk=1, igs=0</code></td><td>读取并投影 <code>psirz</code>、p、F 等；不求解 GS。</td><td>常规 <code>iread_p/f/ne/te/omega*</code> 不读取。后续独立 NEO/源项仍可使用。</td></tr>
<tr><td>以完整 gfile 为初值继续 GS</td><td><code>iread_eqdsk=1, igs&gt;0</code></td><td>第一轮保留读入 psi，后续 GS 轮次可更新；初始 p/F 来自 gfile。</td><td>是。<code>iread_p=1</code>、<code>iread_f=1</code> 可先替换 p/F，再进入缩放与边缘处理。</td></tr>
<tr><td>使用 gfile 几何信息但重建剖面</td><td><code>iread_eqdsk=2, igs&gt;0</code></td><td>先投影 gfile，再改用默认 p/F，并从第一轮开始重新求解 psi。</td><td>是。外部 p/F 可替换默认剖面。</td></tr>
<tr><td>不采用 gfile 的 psirz，重新构造 GS</td><td><code>iread_eqdsk=3, igs&gt;0</code></td><td>取磁轴、总电流、p/F/q 等信息，建立初始电流并求解 GS；不使用文件 <code>psirz</code>。</td><td>是。输入 p/F 及 GS 缩放设置优先。</td></tr>
<tr><td>无平衡文件，由输入参数求 GS</td><td>三个 <code>iread_*</code> 平衡入口均为 0，常用 <code>itaylor=1, igs&gt;0</code></td><td>由解析初值、设备/线圈及剖面参数构造并迭代 GS。</td><td>是。标准剖面文件在 GS 中读取。</td></tr>
<tr><td>旧 BAL/Jsolver 工作流</td><td><code>iread_dskbal</code> 或 <code>iread_jsolver</code></td><td>按各自模式直接映射或调用 GS；BAL 在 GS 后会用文件 ne 重写密度。</td><td>只有实际进入 GS 时才读取标准覆盖文件。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4>gfile 中实际使用的数据</h4>
<p>使用 R-Z 数据框与分辨率、磁轴 <code>rmaxis/zmaxis</code>、<code>simag/sibry</code>、总电流、<code>fpol</code>、<code>press</code>、<code>ffprim</code>、<code>pprime</code>、<code>psirz</code> 和 <code>qpsi</code>。<code>bzero</code> 按最外点 <code>fpol/rmaxis</code> 设置，不采用文件 <code>bcentr</code>。</p>
</div>
<div class="guide-block">
<h4>gfile 不替代几何模型</h4>
<p>读取器不使用文件末尾显式 LCFS 点和 limiter 点来生成 mesh 或壁面；<code>sibry</code> 只给出边界磁通值。第一壁、真空区、导体区和计算域外边界仍来自 mesh/model 与区域参数。</p>
</div>
</div>

<div class="flow" aria-label="托卡马克 GS 剖面覆盖顺序">
<span>gfile/旧平衡或默认剖面</span><b>→</b><span><code>iread_p/f</code> 替换</span><b>→</b><span><code>pscale/bscale</code></span><b>→</b><span>径向 scale 文件</span><b>→</b><span><code>bpscale</code></span><b>→</b><span>边缘值</span>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>Input 参数</th><th>托卡马克用法</th><th>生效条件与覆盖关系</th></tr></thead>
<tbody>
<tr><td><code>iread_p</code></td><td><code>1</code> 读取 <code>profile_p(psi_N,p)</code>。</td><td>只在 GS 构造剖面时替换平衡/默认压力；之后仍受压力缩放和边缘值修改。</td></tr>
<tr><td><code>iread_f</code></td><td><code>1</code> 读取 <code>profile_f(psi_N,F=RBphi)</code>。</td><td>只在 GS 中替换 F，并按文件最外点重设 <code>bzero</code>；之后仍受磁场缩放。</td></tr>
<tr><td><code>iread_ne</code></td><td>1/2/4/10/20 分别读 psi、专用 xy、rho、Corsica 或 iterdb 密度。</td><td>只在 GS 剖面流程使用；<code>den_edge&gt;0</code> 与非零模式冲突。BAL 路径稍后可再次覆盖密度。</td></tr>
<tr><td><code>iread_te</code></td><td>1/2/4/10/20 读取相应坐标/格式的电子温度。</td><td>只在 GS 中参与电子压力/密度构造；<code>tedge&gt;0</code> 与非零模式冲突。</td></tr>
<tr><td><code>iread_omega</code></td><td>1/2/3/4/5/20 读取不同格式的角频率或环向速度。</td><td>要求 GS 且 <code>irot!=0</code>，读入后乘 <code>vscale</code>；NEO 环向速度可在之后叠加。</td></tr>
<tr><td><code>iread_omega_e</code></td><td>输入电子角频率，再扣除完整抗磁项换算为离子角频率。</td><td>与另外两个旋转入口互斥；<code>db=0</code> 时不执行抗磁换算。</td></tr>
<tr><td><code>iread_omega_ExB</code></td><td>输入 E×B 角频率，再扣除离子抗磁项换算为离子角频率。</td><td>与另外两个旋转入口互斥；其余格式与 <code>iread_omega</code> 相同。</td></tr>
<tr><td><code>iread_j</code></td><td>普通托卡马克 GS 不使用；仅 <code>itor=0,itaylor=33</code> 圆柱测试读 <code>profile_j</code>。</td><td>不要把它当作 gfile 电流剖面覆盖入口。</td></tr>
<tr><td><code>iread_neo</code>, <code>ineo_subtract_diamag</code></td><td>读取 NEO/GYRO 输出；环向速度叠加到 <code>vz</code>，极向速度重写 <code>u/chi</code>。可选扣除离子抗磁贡献。</td><td>在平衡后施加；扣除要求 <code>db!=0</code>。非 plasma 磁区速度置零。</td></tr>
<tr><td><code>iread_particlesource</code></td><td><code>1</code> 按归一化 psi 读取 <code>profile_particlesource</code>。</td><td>第二列乘 <code>pellet_rate</code> 并与其他密度源相加；要求 <code>idens=1, linear=0</code>。</td></tr>
<tr><td><code>iread_heatsource</code></td><td><code>1</code> 按归一化 psi 读取 <code>profile_heatsource</code>。</td><td>第二列乘 <code>ghs_rate</code> 并与其他热源相加；要求非线性压力/温度方程。</td></tr>
</tbody>
</table>
</div>
</section>

<section class="device-band stellarator-band">
<div class="device-heading"><span>仿星器</span><h4>固定边界读取 VMEC 结果；外场路径读取三维磁场数据</h4></div>
<ol class="case-steps">
<li><strong>首先关闭托卡马克平衡入口。</strong><code>iread_eqdsk=iread_dskbal=iread_jsolver=0</code>；任一参数非零时，程序优先进入轴对称分支，不执行 <code>itaylor=40/41</code>。</li>
<li><strong>选择固定边界 VMEC 或外场/自由边界路径。</strong><code>itaylor=40</code> 直接读取 wout 的既有平衡结果，M3D-C1 不在此路径求解 VMEC 平衡；<code>itaylor=41</code> 使用外部/总磁场文件初始化三维场，相关文件与类型参数位于 Equilibrium 组。</li>
<li><strong>先完成逻辑 mesh 与物理几何映射。</strong>通常用 <code>igeometry=1, iread_vmec=1</code>。固定边界关闭 bloat；外场路径可按计算域需要外扩。Input 参数不负责识别 LCFS、壁或真空 zone。</li>
<li><strong>随后选择该路径支持的剖面。</strong>固定 VMEC 使用 21 模式覆盖 p/ne/Te；外场路径不读取 21 模式，可用密度 22/23 在初始场完成后重写密度。旋转、F 和普通 GS 剖面均不进入这些仿星器分支。</li>
<li><strong>最后配置源项。</strong>热源和粒子源文件的横坐标解释为逻辑 \\(s=x_l^2+z_l^2\\)，不是物理 R、Z 距离；因此源剖面与 VMEC/逻辑 mesh 的径向定义必须一致。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>用户目标</th><th>核心设置</th><th>直接读取的数据</th><th>Input 组可追加的数据</th></tr></thead>
<tbody>
<tr><td>固定边界 VMEC</td><td><code>itaylor=40</code>, <code>iread_vmec=1</code>, <code>igeometry=1</code>, 两种 bloat 均为 0</td><td>wout 的物理几何、磁场和平衡压力 <code>presf</code>。</td><td><code>iread_p=21</code> 可替换压力；<code>iread_ne=21</code>、<code>iread_te=21</code> 提供密度/温度。它们不改变几何和 B。</td></tr>
<tr><td>外场/自由边界初始化</td><td><code>itaylor=41</code>，并设置 <code>iread_ext_field</code>、<code>type_ext_field</code> 及场文件</td><td>外部磁场或 total/external 组合；VMEC 文件仍可用于计算域几何映射。</td><td><code>iread_ne=22/23</code> 在平衡后重写密度；21 模式、p/F/Te/旋转输入不读取。热源和粒子源仍可独立使用。</td></tr>
</tbody>
</table>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>Input 参数</th><th>固定边界 VMEC</th><th>外场/自由边界</th><th>使用注意</th></tr></thead>
<tbody>
<tr><td><code>iread_eqdsk</code>, <code>iread_dskbal</code>, <code>iread_jsolver</code></td><td colspan="2">必须为 0。</td><td>任一非零值均优先于 <code>itaylor=40/41</code>。</td></tr>
<tr><td><code>iread_p</code></td><td><code>21</code> 读取 <code>p_profile(s,p)</code>，替换 wout <code>presf</code>。</td><td>不读取。</td><td>只改压力场，不重新计算 VMEC 几何或磁场。</td></tr>
<tr><td><code>iread_ne</code></td><td><code>21</code> 读取 <code>n_profile(s,ne)</code>。</td><td><code>22</code> 读 <code>n_profile(s)</code>；<code>23</code> 读 <code>n_profile_vs_p</code>。</td><td>22/23 在平衡与 NEO 应用之后重写密度；不得同时设置 <code>den_edge&gt;0</code>。</td></tr>
<tr><td><code>iread_te</code></td><td><code>21</code> 读取 <code>te_profile(s,Te)</code>。</td><td>不读取。</td><td><code>tedge&gt;0</code> 与非零模式冲突。</td></tr>
<tr><td><code>iread_f</code>, <code>iread_j</code></td><td colspan="2">不读取。</td><td>磁场分别来自 wout 或外场数据；<code>iread_j</code> 只属于特殊圆柱测试。</td></tr>
<tr><td><code>iread_omega</code>, <code>iread_omega_e</code>, <code>iread_omega_ExB</code></td><td colspan="2">不读取。</td><td>这些实现位于托卡马克 GS 剖面路径。</td></tr>
<tr><td><code>iread_neo</code>, <code>ineo_subtract_diamag</code></td><td colspan="2">没有与 VMEC 逻辑坐标配套的专用实现，建议均为 0。</td><td>当前坐标和磁区处理面向托卡马克。</td></tr>
<tr><td><code>iread_particlesource</code></td><td colspan="2"><code>1</code> 读 <code>profile_particlesource(s)</code>，其中 \\(s=x_l^2+z_l^2\\)。</td><td>乘 <code>pellet_rate</code>，要求 <code>idens=1, linear=0</code>。</td></tr>
<tr><td><code>iread_heatsource</code></td><td colspan="2"><code>1</code> 读 <code>profile_heatsource(s)</code>，其中 \\(s=x_l^2+z_l^2\\)。</td><td>乘 <code>ghs_rate</code>，要求非线性压力/温度方程。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>适用限制：</strong>仿星器或圆柱的 Te-only 单压力分支按 \\(n=T_e/p\\) 计算密度。固定边界 VMEC 不应同时设置 <code>iread_ne=21</code> 与 <code>iread_te=21</code>，因为该组合存在温度输出变量未赋值的执行路径。</div>
</section>

<div class="callout"><strong>共同的文件覆盖原则：</strong>平衡入口决定初始几何和主场；剖面读取只在所属初始化分支中生效；NEO 与 22/23 密度属于平衡后的重写；热源和粒子源属于时间推进中的附加项。参数非零并不保证文件一定会被读到，必须同时满足装置路径和方程开关。</div>
</div>
"""
    if group == "Equilibrium":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Equilibrium：把输入数据和网格变成可演化的 MHD 基态</h3>
<p>本模块承接 Input 与 Mesh：Input 已决定平衡数据从哪里来，Mesh 已决定计算域、边界和 zone；Equilibrium 再选择直接投影、重新求解或解析初始化，建立基态磁场与热力学场，并叠加外场和初始扰动。之后 Model Options、Transport 与 Boundary Conditions 才决定这些场怎样演化。</p>
</div>
<span class="guide-kicker">模块递进</span>
</div>

<div class="sequence-pair">
<div><strong>前置模块提供</strong><span>Input：gfile / wout / profile / restart 的读取入口与覆盖顺序<br>Mesh：物理或逻辑坐标、计算域、zone 与 boundary 标签</span></div>
<div><strong>本模块输出</strong><span>平衡场 0 层：\(\psi_0,F_0,p_0,n_0,\mathbf V_0\)<br>扰动场 1 层与可选外场：\(\delta\psi,\delta F,\mathbf B_{ext}\)</span></div>
</div>

<div class="flow" aria-label="从输入到时间演化的完整顺序">
<span>Input 选择数据源</span><b>→</b><span>Mesh 建立计算域与 zone</span><b>→</b><span>读入或求解基态</span><b>→</b><span>外场分解</span><b>→</b><span>初始扰动与符号约定</span><b>→</b><span>Model/Transport 时间演化</span>
</div>

<div class="callout"><strong>固定边界/自由边界不是一个孤立开关：</strong>必须同时看平衡来源、<code>ifixedb</code>、mesh 外边界、PF 线圈、<code>imulti_region/zone_type</code> 和 GS 是否启用。无论哪种 GS 设置，有限元计算域的最外边界始终存在；“自由”指等离子体 LCFS 可在更大的固定计算域内由电流与线圈场共同决定。</div>

<section class="device-band tokamak-band">
<div class="device-heading"><span>托卡马克</span><h4>从 gfile / GS 选择开始，再决定 LCFS 外是否进入计算域</h4></div>
<ol class="case-steps">
<li><strong>先由 Input 选择基态来源。</strong><code>iread_eqdsk=1,igs=0</code> 直接投影 gfile；<code>igs&gt;0</code> 才重新求解 GS；三个读取入口均为 0 时可用 <code>itaylor=1</code> 从解析初值和剖面求 GS，或选择其它测试平衡。</li>
<li><strong>再由 Mesh 决定物理计算域。</strong>托卡马克 mesh 节点就是 R-Z 坐标。若只覆盖 gfile LCFS 内部，模型天然接近固定等离子体边界；若覆盖 LCFS 外真空和导体，则必须用 <code>imulti_region=1</code> 及 <code>zone_type</code> 给这些单元明确物理意义。</li>
<li><strong>选择 GS 的外边界方式。</strong><code>ifixedb&gt;=1</code> 在计算域外边界强制 \(\psi=0\)；<code>ifixedb=0</code> 先建立等离子体电流和 PF 线圈真空场，再把该场值作为 GS 外边界，LCFS 在域内重新寻找。</li>
<li><strong>建立等离子体源与真空场。</strong>GS 的 \(p'(\psi)\) 与 \(FF'(\psi)\) 源只放在 plasma zone 且被判为 plasma magnetic region 的位置；外部 vacuum/conductor zone 仍参与磁场椭圆方程，但不承载等离子体 GS 源。</li>
<li><strong>最后叠加独立磁场。</strong>RMP、error field、TF/PF 线圈误差在基态之后投影，不会再次求解 GS，也不会重写 gfile/GS 压力或电流剖面。<code>extsubtract/icsubtract</code> 决定这些场并入基态还是单独保存。</li>
<li><strong>进入时间演化。</strong>Model Options 决定是否扣除平衡场、是否加入 bootstrap closure；Transport 根据 zone 选择 plasma、vacuum 或 conductor 的电阻率和输运系数。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>初始平衡目标</th><th>关键设置</th><th>LCFS 与最外边界</th><th>是否重新求解</th></tr></thead>
<tbody>
<tr><td>直接使用 gfile 基态</td><td><code>iread_eqdsk=1, igs=0</code></td><td>gfile 给出磁通与 <code>sibry</code>；mesh 外边界独立存在，程序不按 LCFS 裁网格。</td><td>不求 GS；后续线圈、RMP 或 error field 仍可叠加。</td></tr>
<tr><td>固定计算边界 GS</td><td><code>igs&gt;0, ifixedb&gt;=1</code></td><td>最外边界强制 \(\psi=0\)。若它就是目标 plasma boundary，才构成通常所说的固定 LCFS 求解。</td><td>是。</td></tr>
<tr><td>较大域内的自由 LCFS GS</td><td><code>igs&gt;0, ifixedb=0</code>，常配 <code>idevice=-1</code></td><td>最外边界取已建立的参考磁通；默认 <code>icsubtract=0</code> 时其中包含 PF 线圈真空场。LCFS 每轮在域内更新，外边界本身仍固定。</td><td>是，可带 PF 反馈。</td></tr>
<tr><td>解析/测试平衡</td><td>读取入口全 0，选择 <code>itaylor</code></td><td>由所选解析模型及 mesh 外边界决定。</td><td><code>itaylor=1</code> 求 GS；19、24、29/31 等走各自初始化。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4>直接投影与 zone</h4>
<p>gfile 的 \(\psi,p,F\) 会在读取路径中插值到 mesh 单元，不只写 plasma zone。zone 标签不会裁剪输入数据；它主要决定随后哪些方程、材料系数和源项生效。</p>
</div>
<div class="guide-block">
<h4>GS 求解与 zone</h4>
<p>GS 矩阵覆盖整个计算域，但 plasma 电流源只在 <code>ZONE_PLASMA</code> 内。非 plasma zone 的压力取边缘值、环向真空场取 <code>bzero*rzero</code>；vacuum 与 conductor 的差异主要在后续电阻率和壁电流演化。</p>
</div>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>跨模块参数</th><th>所属模块</th><th>与 Equilibrium 的接口</th></tr></thead>
<tbody>
<tr><td><code>iread_eqdsk</code>, <code>iread_p/f/ne/te</code></td><td>Input</td><td>决定基态数据源以及 GS 前的剖面覆盖；直接投影路径不会读取普通 GS profile 覆盖文件。</td></tr>
<tr><td><code>mesh_filename</code>, <code>imulti_region</code>, <code>zone_type</code></td><td>Mesh</td><td>给出真实 R-Z 域及 plasma/conductor/vacuum 分类；程序不检查这些标签与 gfile LCFS 是否几何一致。</td></tr>
<tr><td><code>igs</code>, GS profile/feedback 参数</td><td>Grad-Shafranov</td><td>决定是否迭代、剖面约束、LCFS/X 点搜索和 PF 电流反馈。</td></tr>
<tr><td><code>ifixedb</code></td><td>Boundary Conditions</td><td>控制 GS 计算域外边界是强制零磁通，还是沿用已建立的线圈/真空磁通。</td></tr>
<tr><td><code>eqsubtract</code>, <code>extsubtract</code>, <code>icsubtract</code></td><td>Model Options</td><td>分别控制演化方程中的平衡扣除、非轴对称外场分离、PF 线圈场分离；不改变 mesh。</td></tr>
</tbody>
</table>
</div>

<h4>RMP、线圈误差与外场：作用在基态之后</h4>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>功能</th><th>设置</th><th>实际作用</th><th>不会做的事</th></tr></thead>
<tbody>
<tr><td>窗口线圈 RMP</td><td><code>irmp=1, type_ext_field&lt;=0</code></td><td>读取 <code>rmp_coil.dat/rmp_current.dat</code>，并可叠加 <code>error_field</code> 数据；场投影到整个计算域。</td><td>不重算 GS，不只限于 plasma zone。</td></tr>
<tr><td>解析 m/n 真空场</td><td><code>irmp=2</code></td><td>用 <code>mpol/ntor/eps/rmp_atten</code> 构造场；仅 <code>itor=0</code> 可用。</td><td>不是环形托卡马克的边界 RMP 设置。</td></tr>
<tr><td>误差场文件</td><td><code>iread_ext_field&gt;0, type_ext_field&lt;=0</code></td><td>1 组读 <code>error_field</code>，多组读 <code>error_fieldNN</code>，再应用采样、缩放和相位平移。</td><td><code>file_ext_field</code> 在此分支不会改文件名。</td></tr>
<tr><td>TF/PF 倾斜和平移</td><td><code>tf_*</code>, <code>pf_*</code></td><td>由理想线圈场的一阶变化构造非轴对称误差场；PF 项要求先有线圈表。</td><td>不移动有限元节点，也不修改轴对称 GS 线圈几何。</td></tr>
</tbody>
</table>
</div>

<h4>自举电流：属于 Equilibrium 之后的演化闭合</h4>
<div class="flow" aria-label="自举电流与初始电流关系">
<span>gfile / GS / basicJ 给出初始 J</span><b>→</b><span>计算 ne、Te、Ti 与 bootstrap 系数</span><b>→</b><span>bootstrap 项进入磁通和环向场方程</span><b>→</b><span>J 随时间演化</span>
</div>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>参数</th><th>程序行为</th><th>生效与覆盖关系</th></tr></thead>
<tbody>
<tr><td><code>ibootstrap=0/1/2/3</code></td><td>0 关闭；1 用 \(\psi\) 作系数坐标；2 用 \(T_e\)；3 用 \(1-T_e/T_{e,max}\)，并从专用文件读取/计算更多几何系数。</td><td>不会覆盖初始 J；它选择演化阶段 bootstrap 系数的坐标和计算路径。</td></tr>
<tr><td><code>ibootstrap_model</code></td><td>1/3 为 Sauter-Angioni，2/4 为 Redl，3/4 是简化方程实现，5 为 constant-Lambda 分支。</td><td>必须与 <code>ibootstrap</code> 及系数文件配套；<code>ibootstrap=3</code> 的模型 1/3 当前会停止运行。</td></tr>
<tr><td><code>bootstrap_alpha</code></td><td>统一乘在计算得到的 bootstrap 项上，默认 0。</td><td>即使打开模型，保持 0 也会把 bootstrap 驱动缩放为零。</td></tr>
<tr><td><code>ibootstrap_regular</code></td><td>正则化小磁场、温度梯度和归一化温度计算，默认 \(10^{-8}\)。</td><td>它是数值保护尺度，不是 bootstrap 电流比例。</td></tr>
</tbody>
</table>
</div>
<div class="guide-grid compact">
<div class="guide-block">
<h4>ibootstrap=1/2 的系数文件</h4>
<p>分别读取 <code>ProfileJBSCoeff_Psi_L31_32_34_alpha_B2_dtedpsit_G</code> 或 <code>ProfileJBSCoeff_Te_L31_32_34_alpha_B2_dtedpsit_G</code>。横坐标分别为归一化磁通或电子温度；后续列提供 L31、L32、L34、alpha、\\(1/\\langle B^2\\rangle\\)、\\(dT_e/d\\psi_t\\) 与 G。</p>
</div>
<div class="guide-block">
<h4>ibootstrap=3 的系数文件</h4>
<p>读取 <code>ProfileJBSCoeff_Tenorm_L31_32_34_alpha_B2_dtedpsit_G_ft_qR_e_temax</code>，以 \\(1-T_e/T_{e,max}\\) 为坐标，并额外提供 trapped fraction、qR、逆长宽比和初始最大电子温度。</p>
</div>
</div>
<div class="callout"><strong>初始电流不会被自动替换：</strong>若希望初始平衡已经包含自举电流，必须让输入 gfile/VMEC/GS 剖面本身包含相应总电流并保持力平衡。只设置 <code>ibootstrap</code> 会在时间推进时驱动电流变化，可能产生初始调整过程，但不会返回 GS 或 VMEC 重求一个自洽平衡。</div>
</section>

<section class="device-band stellarator-band">
<div class="device-heading"><span>仿星器</span><h4>区分固定边界 VMEC 投影与三维 total/external-field 初始化</h4></div>
<ol class="case-steps">
<li><strong>首先由 Input 关闭托卡马克入口。</strong><code>iread_eqdsk=iread_dskbal=iread_jsolver=0</code>；否则程序会优先执行轴对称初始化，不进入 <code>itaylor=40/41</code>。</li>
<li><strong>由 Mesh 建立逻辑域并映射。</strong>通常 <code>igeometry=1,iread_vmec=1</code>；逻辑 \\((\\rho,\\theta,\\phi)\\) mesh 先映射到物理 R-Z-phi，zone 与 boundary 标签随映射带入，但不会由 wout 或场文件自动重分类。</li>
<li><strong>选择固定边界。</strong><code>itaylor=40</code> 读取 wout 的几何、磁场和压力并进行投影；M3D-C1 不求解 VMEC。此模式要求 <code>bloat_factor=0</code>，同时应设置 <code>bloat_distance=0</code>，使外边界对应 VMEC 最外磁面。</li>
<li><strong>或选择三维外场初始化。</strong><code>itaylor=41</code> 要求 <code>iread_ext_field!=0</code>，从 total field 或 total/external 组合建立磁场。该路径不求解 VMEC 自由边界方程，也不根据第一壁位置重新求解 LCFS。</li>
<li><strong>检查计算域物理意义。</strong>bloat 只扩展几何映射；扩展区是 plasma、vacuum 还是 conductor 仍完全由 <code>zone_type</code> 决定。程序允许但不会识别“导体 zone 实际落在 wout plasma 内”等物理冲突。</li>
<li><strong>再进入演化模型。</strong>RMP/外场分解、bootstrap、transport 和壁电阻依次作用；这些模型不会回头改变 VMEC 映射或重求平衡边界。</li>
</ol>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>仿星器模式</th><th>核心设置</th><th>读取/构造内容</th><th>边界含义</th></tr></thead>
<tbody>
<tr><td>固定边界 VMEC</td><td><code>itaylor=40, igeometry=1, iread_vmec=1</code></td><td>wout 几何、B 和 <code>presf</code>；Input 的 21 模式可替换 p/ne/Te，但不改 B 和几何。</td><td>逻辑 mesh 最外边界映射到 VMEC 最外磁面；不包含显式外真空/壁域。</td></tr>
<tr><td>total field 直接初始化</td><td><code>itaylor=41, type_ext_field=1, iread_ext_field=1, extsubtract=0</code></td><td><code>file_total_field</code> 作为初始总 B；若格式携带压力，也可一并投影。</td><td>计算域由 mesh/VMEC 几何决定；场文件不会自动给 zone 贴标签。</td></tr>
<tr><td>total/external 分解</td><td><code>itaylor=41, type_ext_field=2, iread_ext_field=1, extsubtract=1</code></td><td>先装 <code>file_total_field</code>，再装 <code>file_ext_field</code>；演化场保存 total-external，外场单独保存。</td><td>适合把固定真空线圈场从动态等离子体场中分离，但不是自由边界平衡求解器。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4>plasma 与外部区</h4>
<p><code>itaylor=40</code> 的 wout 平衡定义到最外磁面。若通过 bloat 或多区域逻辑 mesh 建立外区，程序不会依据 wout 判断该区属于真空、导体壁或等离子体；必须在 Mesh 阶段定义 zone，并在 Transport/Boundary 模块设置材料参数。</p>
</div>
<div class="guide-block">
<h4><code>itaylor=41</code> 的自由边界含义</h4>
<p><code>itaylor=41</code> 读取三维 total/external field 并初始化 MHD 场。该模式允许 LCFS 在后续 MHD 演化中变化，但不执行基于 mgrid 背景场求解 LCFS 的 VMEC 自由边界平衡迭代。</p>
</div>
</div>

<div class="callout"><strong>固定边界 VMEC 的几何约束：</strong>初始化显式检查 <code>bloat_factor==0</code>。为保证 mesh 外边界与 wout 最外磁面严格对应，还应显式设置 <code>bloat_distance=0</code>。</div>
</section>

<h4>共同的后处理顺序：后面的步骤可以改符号或叠加场，但不回写平衡来源</h4>
<div class="flow" aria-label="平衡完成后的共同后处理">
<span>基态初始化</span><b>→</b><span>NEO 与密度初始化</span><b>→</b><span>RMP/外场/线圈误差</span><b>→</b><span>ne/Te/Ti 派生</span><b>→</b><span><code>iflip_b/j/v</code></span><b>→</b><span><code>iflip</code> 手性变换</span><b>→</b><span>时间推进</span>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>参数族</th><th>生产 case 中的角色</th><th>主要限制</th></tr></thead>
<tbody>
<tr><td><code>eps/maxn/icsym/verzero</code></td><td>构造初始扰动层；扰动只在 plasma zone 生成，并可按压力/磁区掩膜衰减。</td><td>不改变基态边界；仿星器在逻辑坐标中构造随机形状。</td></tr>
<tr><td><code>iflip_b/j/v</code></td><td>分别改变已初始化 B、J 表示和环向速度的符号。</td><td>必须同步核对输入文件、<code>ntor</code>、线圈电流和诊断符号。</td></tr>
<tr><td><code>iflip</code></td><td>整体坐标手性变换，同时反号多种场及 <code>vloop/tcur</code>。</td><td>只在非 restart 的初始化后执行；不要与单项翻转混为一谈。</td></tr>
<tr><td><code>iupstream/magus</code></td><td>时间演化的环向人工二阶稳定化。</td><td>虽归在 Equilibrium 组，但不参与平衡读取或求解。</td></tr>
<tr><td><code>bx0/v0_cyl/v1_cyl/iwave/beta/ln/elongation/basicj_*</code></td><td>解析和回归测试平衡参数；其中 Solovev/basicJ 可用于受控验证。</td><td>不会覆盖 gfile、wout 或三维场文件；只在对应 <code>itaylor</code> 分支有意义。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>几何与物理一致性：</strong>程序会检查部分文件和开关组合，但不会验证 mesh zone、gfile/VMEC LCFS、第一壁、线圈域和外场数据范围之间的物理一致性。通过语法和分支检查的输入组合仍可能不符合预定的物理区域划分。</div>
</div>
"""
    if group == "Grad-Shafranov Solver":
        return r"""
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Grad-Shafranov Solver：托卡马克轴对称基态求解</h3>
<p>本模块只处理托卡马克的轴对称 Grad-Shafranov 平衡。它承接 Input 选定的 gfile/剖面与 Mesh/Equilibrium 建立的物理 R-Z 计算域，在固定的有限元外边界内迭代求解磁通、寻找磁轴与 LCFS，再把压力、环向场、密度和转动投影为可演化的 MHD 基态。</p>
</div>
<span class="guide-kicker">TOKAMAK ONLY</span>
</div>

<div class="sequence-pair">
<div><strong>进入 GS 之前</strong><span>Input：选择 gfile、解析初值与 profile 覆盖<br>Mesh：给出真实 R-Z 域、plasma/vacuum/conductor zone<br>Equilibrium/Boundary：建立初始 psi、PF 场及计算域外边界</span></div>
<div><strong>GS 完成之后</strong><span>得到磁轴、LCFS/X 点与自洽 psi<br>投影 p、F=RBphi、n、omega、Te/Ti 到有限元场<br>再进入扰动、RMP、Model、Transport 和时间推进</span></div>
</div>

<div class="callout"><strong>仿星器不使用本模块：</strong><code>itaylor=40</code> 直接读取固定边界 VMEC 平衡，<code>itaylor=41</code> 读取三维 total/external field；两者均不求解轴对称 GS。本组参数不用于确定仿星器的 LCFS、自由边界、壁或线圈响应。<code>adapt_qs/adapt_zlow/adapt_zup</code> 用于 Mesh Adaptation。</div>

<div class="flow" aria-label="托卡马克 Grad-Shafranov 求解链条">
<span>选择 psi 初值</span><b>→</b><span>建立 p 与 F 剖面</span><b>→</b><span>形成全域 GS 矩阵</span><b>→</b><span>Picard 求解 psi</span><b>→</b><span>搜索磁轴/LCFS</span><b>→</b><span>更新源项与约束</span><b>→</b><span>线圈反馈</span><b>→</b><span>投影平衡场</span>
</div>

<section class="device-band tokamak-band">
<div class="device-heading"><span>托卡马克</span><h4>第一步：先确定 GS 接收到什么初值</h4></div>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>用户设置</th><th>psi 初值</th><th>p/F 初值</th><th>第一轮行为</th></tr></thead>
<tbody>
<tr><td><code>iread_eqdsk=1, igs=0</code></td><td>直接投影 gfile <code>psirz</code></td><td>直接投影 gfile</td><td>不进入 GS；本组大多数参数不生效。</td></tr>
<tr><td><code>iread_eqdsk=1, igs&gt;0</code></td><td>gfile <code>psirz</code></td><td>gfile p/F，可被 <code>iread_p/f</code> 替换</td><td>第一轮保留文件 psi，只更新 LCFS 与源；第二轮起才解线性 GS。</td></tr>
<tr><td><code>iread_eqdsk=2, igs&gt;0</code></td><td>先投影 gfile，并从第一轮开始重新求解</td><td>不采用 gfile p/F，改用内置解析剖面，并允许外部文件覆盖</td><td>使用 gfile 几何、磁轴和电流信息重新构造自洽平衡。</td></tr>
<tr><td><code>iread_eqdsk=3, igs&gt;0</code></td><td>不使用 <code>psirz</code>；在文件磁轴处放置电流丝或高斯电流</td><td>gfile p/F/q 仍可用于约束，随后允许文件覆盖</td><td>从构造的电流初猜求解。</td></tr>
<tr><td>无平衡文件，<code>itaylor=1, igs&gt;0</code></td><td>由 <code>tcuro,xmag,zmag,sigma0</code> 建立电流初猜</td><td><code>inumgs=0</code> 用解析剖面，1 读固定剖面文件</td><td>从第一轮解 GS。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong><code>igs</code> 的有效范围：</strong>迭代循环按 <code>1...igs</code> 执行。需要求解 GS 时应使用 <code>igs&gt;0</code>；<code>igs=0</code> 表示跳过，负值不执行迭代。</div>

<h4>第二步：明确固定的是计算域外边界，不一定是 LCFS</h4>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>边界模式</th><th>GS 外边界条件</th><th>LCFS 如何得到</th><th>物理解释</th></tr></thead>
<tbody>
<tr><td><code>ifixedb&gt;=1</code></td><td>计算域最外边界强制 <code>psi=0</code>。</td><td><code>ifixedb=1</code> 新启动时直接把边界磁通设为 0；其它取值仍可运行 LCFS 判定。</td><td>只有 mesh 外边界本身就是目标等离子体边界时，才等价于通常的固定 LCFS GS。</td></tr>
<tr><td><code>ifixedb=0</code></td><td>使用初始化阶段建立的等离子体电流丝与 PF 线圈真空场在外边界上的 psi。</td><td>每轮在更大 R-Z 域内由第一壁、X 点和 limiter 候选重新确定。</td><td>LCFS 可移动的自由边界平衡；有限元计算域外边界仍然固定并施加 Dirichlet 值。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4>PF 场来源</h4>
<p><code>idevice=-1</code> 读取 <code>coil.dat/current.dat</code>；<code>idevice=0</code> 使用 generic dipole 近似，并用 <code>libetap</code> 估计竖直场。其它 <code>idevice</code> 值不建立 PF 线圈。</p>
</div>
<div class="guide-block">
<h4>线圈场是否分离</h4>
<p><code>icsubtract=0</code> 把 PF psi 加入平衡 psi；<code>icsubtract=1</code> 单独保存线圈场，但 LCFS、剖面坐标和总磁场评价时仍重新相加。它改变场的存储分解，不改变物理总场。</p>
</div>
</div>

<h4>第三步：建立进入 GS 方程的剖面</h4>
<p>求解方程可写为</p>
<div class="formula">\[\Delta^{*}\psi + R^{2}\frac{dp}{d\psi} + F\frac{dF}{d\psi}=0,\qquad F(\psi)=R B_{\phi}.\]</div>
<p>剖面查询坐标不是 mesh 的径向坐标，而是每轮由磁轴与 LCFS 更新的磁通坐标：</p>
<div class="formula">\[s_{\psi}=\frac{\psi-\psi_{\mathrm{axis}}}{\psi_{\mathrm{LCFS}}-\psi_{\mathrm{axis}}}\,\mathtt{psifrac}.\]</div>

<div class="flow" aria-label="GS 剖面覆盖顺序">
<span>gfile / <code>profiles-p,g</code> / 内置解析剖面</span><b>→</b><span><code>iread_p/f</code> 完整替换</span><b>→</b><span><code>pscale/bscale</code></span><b>→</b><span><code>profile_pscale</code></span><b>→</b><span><code>bpscale</code></span><b>→</b><span><code>profile_bscale</code></span><b>→</b><span>edge 与延伸处理</span>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>剖面来源/修改</th><th>读入或计算内容</th><th>覆盖关系</th></tr></thead>
<tbody>
<tr><td>gfile 约束剖面</td><td>p、p'、F、FF'；可选 q 用于 rho 到 psi 换算。</td><td><code>iread_eqdsk=1/3,igs&gt;0</code> 时建立完整约束；此后 <code>q0/djdpsi/tcuro</code> 不再重调其形状或总电流。</td></tr>
<tr><td><code>inumgs=1</code></td><td><code>profiles-p</code> 给 p/p'，<code>profiles-g</code> 给 g/FF'。</td><td>只有此前未建立 p 剖面时读取，并将求解设为完整剖面约束。</td></tr>
<tr><td><code>inumgs=0</code></td><td>由 <code>p0,p1,p2</code> 建 p/p'，由内置 g 基函数建 F/FF'。</td><td>允许 <code>q0,djdpsi,tcuro</code> 通过 gamma2/3/4 约束轴上 q、电流梯度和总电流。</td></tr>
<tr><td><code>iread_p=1</code></td><td><code>profile_p(psi_N,p)</code>，并数值求 p'。</td><td>替换前面建立的完整压力剖面；随后仍受 p 缩放、edge 与延伸处理。</td></tr>
<tr><td><code>iread_f=1</code></td><td><code>profile_f(psi_N,F)</code>，并数值求 FF'。</td><td>替换 F，同时按文件外点重设 <code>bzero</code>；随后仍受磁场缩放。</td></tr>
<tr><td><code>igs_pp_ffp_rescale=1</code></td><td>让文件 p'、FF' 的积分与 p、F 端点差匹配。</td><td>只在 gfile <code>create_profile</code> 路径执行，不修复普通 <code>profile_p/f</code>。</td></tr>
<tr><td><code>pedge/tedge/tiedge</code></td><td>平移剖面末端值；<code>tiedge</code> 会重算并覆盖 <code>pedge</code>。</td><td>在常数或径向缩放之后执行。<code>tedge</code> 的一条压力修正路径使用样条点数而非边缘密度，因此不建议采用该参数组合。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>源项的空间范围：</strong>GS 矩阵在整个 mesh 上组装，plasma、vacuum 与 conductor 都参与同一个椭圆磁场解；但 \(p'\) 与 \(FF'\) 源只在 <code>ZONE_PLASMA</code> 且被磁区判定为 <code>REGION_PLASMA</code> 的位置非零。LCFS 外或非 plasma zone 不能仅靠给定剖面产生等离子体电流源。</div>

<h4>第四步：Picard 迭代、约束与收敛</h4>
<ol class="case-steps">
<li><strong>固定矩阵。</strong>程序先在全部单元组装 GS 椭圆算子，并在计算域外边界施加 Dirichlet 条件；USE3D 编译可用 <code>eta_gs</code> 抑制 psi 的非轴对称变化。</li>
<li><strong>解线性化磁通。</strong>当前 p' 与 FF' 形成右端项，求得新的 psi。只有 <code>iread_eqdsk=1</code> 的第一轮跳过这次线性求解，以保留 gfile 初值。</li>
<li><strong>松弛更新。</strong>从第二个已求解轮次起按 \(\psi\leftarrow\mathtt{th\_gs}\,\psi_{solve}+(1-\mathtt{th\_gs})\,\psi_{old}\) 混合。</li>
<li><strong>重找磁轴和 LCFS。</strong>新的轴与边界磁通改变 \(s_\psi\)，程序据此重新评价 p'、FF' 与磁区。</li>
<li><strong>施加解析约束。</strong>非完整剖面约束时，<code>q0</code>、<code>djdpsi</code>、<code>tcuro</code> 分别通过 gamma2、gamma3、gamma4 调整 FF' 基函数；<code>nv1equ=1</code> 会把这三个 gamma 全部关掉。</li>
<li><strong>检查收敛。</strong>第二轮后若解变化误差小于 <code>tol_gs</code> 就提前退出，否则最多执行 <code>igs</code> 轮。</li>
</ol>

<h4>第五步：LCFS 不是从一个文件轮廓直接复制</h4>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>候选边界</th><th>启用条件</th><th>程序如何使用</th></tr></thead>
<tbody>
<tr><td>第一壁</td><td><code>iwall_is_limiter=1</code> 且 mesh/model 中存在 first-wall boundary</td><td>沿第一壁寻找不进入私有磁通区的最内层磁通候选。</td></tr>
<tr><td>X 点 #1/#2</td><td><code>xnull&gt;0</code> 或 <code>xnull2&gt;0</code></td><td>在搜索启动前只评价输入位置，之后在附近寻找鞍点；两个 X 点地位相同，谁的磁通面更靠近磁轴谁可成为 LCFS。</td></tr>
<tr><td>内部 limiter #1/#2</td><td><code>xlim!=0</code>，第二点还要求 <code>xlim2&gt;0</code></td><td>评价给定 R-Z 点的 psi，作为 LCFS 候选；若比壁/X 点磁通面更靠近磁轴，则等离子体成为 limiter-limited。</td></tr>
<tr><td>无内部 limiter</td><td><code>xlim=0</code></td><td>直接采用当前壁/X 点候选，不把 0 当作 R=0 的 limiter。</td></tr>
</tbody>
</table>
</div>
<p>最终边界取上述有效候选中与磁轴磁通差绝对值最小者。`xnull/znull`、limiter 和第一壁必须都位于 mesh 所覆盖的物理 R-Z 域并与 zone 几何相容；程序不会替用户验证这些物理关系。</p>

<h4>第六步：可选 PF 线圈位置反馈</h4>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>控制对象</th><th>目标</th><th>反馈参数</th><th>限制</th></tr></thead>
<tbody>
<tr><td>磁轴位置</td><td><code>xmag0,zmag0</code></td><td><code>gs_radial/vertical_feedback</code> 及对应 <code>_i</code></td><td>仅 <code>idevice=-1</code>；数组索引对应线圈组，P/I 误差按 GS 轮次更新。</td></tr>
<tr><td>X 点位置</td><td><code>xnull0,znull0</code></td><td>带 <code>_x</code> 的四组反馈数组</td><td>仅 <code>idevice=-1</code> 且从第 11 轮起；因此 <code>igs</code> 太小时不会动作。</td></tr>
<tr><td>generic 双 limiter 磁通差</td><td>令两个 limiter 的磁通更接近</td><td><code>igs_feedfac=1</code></td><td>只对 <code>idevice=0</code> 的固定公式生效；不是用户可调连续增益。</td></tr>
</tbody>
</table>
</div>
<p>反馈每轮重新计算 PF 线圈 psi；磁轴反馈结束后写出 <code>current.dat.out</code>。这些反馈是在 GS 初始化迭代中调线圈电流，不是 MHD 时间演化中的主动控制器。</p>

<h4>第七步：求解后才构造密度、温度与转动</h4>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>场</th><th>构造方式</th><th>是否直接改变 GS</th></tr></thead>
<tbody>
<tr><td>压力 p</td><td>按最终 psi 查询 p 样条；<code>irot=1</code> 时带 R 依赖指数因子。</td><td>是，p' 是 GS 源；旋转压力只有 <code>irot=1</code> 进入源。</td></tr>
<tr><td>环向场 F</td><td>由完整 g/F 剖面，或解析基函数与 gamma2/3/4 合成。</td><td>是，FF' 是 GS 源。</td></tr>
<tr><td>密度 n</td><td>读 <code>iread_ne</code> 文件，或由 <code>den0,den_edge,expn</code> 构造；<code>idenfunc</code> 可在平衡后再次重写。</td><td>静态无旋转时不直接进入 GS；旋转 alpha 和温度分解会用到。</td></tr>
<tr><td>转动 omega</td><td><code>irot!=0</code> 时读 Input 的 omega 文件或用 <code>alpha0...3</code> 构造，再乘 <code>vscale</code> 并可加抗磁换算。</td><td>只有 <code>irot=1</code> 通过 R 依赖压力进入 GS。</td></tr>
<tr><td>Te/Ti</td><td>由 Te 文件与 n，或按 <code>pefac=(p0-pi0)/p0</code> 分解总压力。</td><td>主要是最终热力学场；<code>igs_extend_p</code> 与旋转换算时可间接影响剖面。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4>plasma zone 外的最终场</h4>
<p>非 plasma zone 的 F 取 <code>bzero*rzero</code>，压力、密度和转动取各样条最外值。vacuum 与 conductor 的材料差异不由 GS 决定，而由后续 Resistive Wall、Transport 和模型方程处理。</p>
</div>
<div class="guide-block">
<h4>私有磁通区</h4>
<p>程序把 private-flux 区域的剖面坐标镜像到 LCFS 外；<code>gs_pf_psi_width</code> 控制镜像转接的平滑宽度。<code>igs_forcefree_lcfs</code> 可进一步把 LCFS 外的 p'、FF' 和转动约束为无源/常值。</p>
</div>
</div>

<h4>设置 case 时的最小检查顺序</h4>
<ol class="case-steps">
<li>确认三个平衡读取入口只有一个非零，并确认是否真的需要 <code>igs&gt;0</code>。</li>
<li>确认物理 R-Z mesh 覆盖磁轴、LCFS、所有 limiter/X 点、第一壁和线圈场所需区域。</li>
<li>确认 <code>imulti_region/zone_type</code> 中只有预期等离子体区域承载 GS 源。</li>
<li>确认 <code>ifixedb</code>、PF 线圈文件与 <code>icsubtract</code> 表达的是同一种固定/自由边界方案。</li>
<li>按覆盖顺序核对 p/F 文件、缩放、edge 设置，避免参数合法但前面已被后续剖面覆盖。</li>
<li>给足 <code>igs</code>，并检查收敛误差、磁轴、LCFS 限制类型及最终 <code>current.dat.out</code>，再进入 MHD 演化。</li>
</ol>

<div class="callout"><strong>使用注意：</strong><code>psiscale</code> 不执行剖面缩放；<code>igs_feedfac</code> 是开关而非连续系数；<code>xnull2</code> 可成为活动 LCFS X 点；<code>tedge</code> 的压力修正路径使用样条点数而非边缘密度；<code>adapt_qs/adapt_zlow/adapt_zup</code> 属于网格自适应参数。</div>
</section>
</div>
"""
    if group == "__legacy_mesh":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>网格如何进入计算</h3>
<p>Mesh 是计算域的几何与拓扑基础。程序先读取节点、三角形、边界环和区域分类，再建立物理几何，最后把平衡和初始场投影到有限元空间。</p>
</div>
<span class="guide-kicker">使用补充</span>
</div>
<div class="flow" aria-label="网格初始化流程">
<span>读取 mesh/model</span><b>→</b><span>识别边界与 zone</span><b>→</b><span>建立物理几何</span><b>→</b><span>投影平衡场</span><b>→</b><span>生成三维有限元域</span>
</div>
<div class="guide-grid">
<div class="guide-block">
<h4>托卡马克：网格坐标就是物理坐标</h4>
<p>标准 <code>igeometry=0</code> 路径中，二维 mesh 的坐标是柱坐标截面的 <code>(R,Z)</code>。读取 g-file 不会再次改变网格几何，而是把磁通、压力和磁场等平衡数据插值/投影到已有网格上。</p>
<p>g-file 的 LCFS、mesh 外边界、第一壁和各 zone 必须由用户保证几何与物理上相容；程序不会替用户完成这一一致性判断。g-file 数据也不是只投影到 <code>plasma zone</code>。</p>
</div>
<div class="guide-block">
<h4>仿星器：先有逻辑网格，再映射到物理空间</h4>
<p><code>igeometry=1</code> 且 <code>iread_vmec=1</code> 时，二维圆盘 mesh 主要承担逻辑坐标 <code>(rho,theta)</code> 的拓扑作用。VMEC 傅里叶几何把 <code>(rho,theta,phi)</code> 映射为物理柱坐标 <code>(R,Z,phi)</code>。</p>
<p>逻辑最外边界通常对应 <code>rho=1</code>；其物理位置由 VMEC 几何及 <code>bloat_factor</code>/<code>bloat_distance</code> 决定。逻辑圆形边界映射后通常不是物理空间中的圆。</p>
</div>
</div>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>网格信息</th><th>程序赋予的含义</th><th>用户必须保证</th></tr></thead>
<tbody>
<tr><td>节点与三角形</td><td>二维有限元拓扑和局部空间分辨率</td><td>单元质量、边界覆盖和目标区域分辨率合理</td></tr>
<tr><td><code>boundary_type(i)</code></td><td><code>1</code> 第一壁，<code>2</code> 计算域外边界</td><td>mesh loop 编号与输入数组下标对应</td></tr>
<tr><td><code>zone_type(i)</code></td><td><code>1</code> plasma，<code>2</code> conductor，<code>3</code> vacuum</td><td>区域标签与 g-file/VMEC 所代表的实际物理区域相容</td></tr>
<tr><td><code>imulti_region=1</code></td><td>启用多物理区域解释</td><td>不同 zone 的交界面已在原始 mesh/model 中建立</td></tr>
</tbody>
</table>
</div>
<div class="guide-grid compact">
<div class="guide-block">
<h4>区域标签不会改变坐标映射</h4>
<p>zone 是对既有单元的物理分类，不会将逻辑网格自动移动到等离子体、真空或导体壁位置。即使输入满足语法要求，不一致的 zone 与平衡对应关系仍会产生不符合预定物理模型的算例。</p>
</div>
<div class="guide-block">
<h4>环向三维结构</h4>
<p>二维三角网格按 <code>nplanes</code> 在环向复制并连接为六节点棱柱拓扑。极向采用 C1 高阶表示，环向采用三次 Hermite 表示，因此物理场和几何在环向是平滑插值，而不是逐平面的阶梯结构。</p>
</div>
</div>
<div class="callout"><strong>固定/自由边界提示：</strong>mesh 覆盖多大区域、是否包含真空和导体区，与平衡是固定边界还是包含外部场演化不是同一个概念。扩大 mesh 的 plasma zone 不能自动把固定边界平衡变成自由边界计算。</div>
</div>
"""
    if group == "__legacy_input":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Input 模块如何读取和覆盖初始数据</h3>
<p>本组 15 个参数均为整数、默认值均为 <code>0</code>。它们分别选择平衡文件、径向剖面、数值源项和 NEO 速度输入；同一个非零值在托卡马克、固定边界 VMEC 和自由边界仿星器路径中不一定具有相同含义。</p>
</div>
<span class="guide-kicker">使用补充</span>
</div>
<div class="flow" aria-label="Input 数据调用顺序">
<span>预读 NEO 文件</span><b>→</b><span>选择唯一平衡入口</span><b>→</b><span>GS/VMEC 读取剖面</span><b>→</b><span>应用 NEO 速度</span><b>→</b><span>密度后处理</span><b>→</b><span>演化中叠加源项</span>
</div>
<div class="callout"><strong>平衡入口优先级：</strong><code>iread_eqdsk</code> → <code>iread_dskbal</code> → <code>iread_jsolver</code> → <code>itaylor</code>。程序按此顺序选择首个非零入口，后续入口不再执行。因此这些参数不能彼此组合，也不能与 <code>itaylor=40/41</code> 的仿星器初始化混用。</div>

<div class="guide-grid">
<div class="guide-block">
<h4>托卡马克</h4>
<p><code>geqdsk</code>、<code>dskbal</code> 和 Jsolver <code>fixed</code> 都是轴对称平衡入口。平衡数据按现有物理 <code>(R,Z)</code> 网格插值或用于重新求解 GS，不会改变 mesh 几何。</p>
<p>普通 <code>iread_p/f/ne/te/omega</code> 剖面仅在 GS 路径调用 <code>define_profiles</code> 时读取。直接导入 <code>iread_eqdsk=1/2, igs=0</code> 或 <code>iread_jsolver&gt;0, igs=0</code> 时，这些标准剖面文件不会覆盖已投影的平衡。</p>
</div>
<div class="guide-block">
<h4>仿星器</h4>
<p>固定边界 VMEC 由 <code>itaylor=40, igeometry=1, iread_vmec=1, bloat_factor=0</code> 选择。Input 组只用 21 模式补充压力、密度和温度，不能替换 wout 的几何或磁场。</p>
<p>自由边界仿星器 <code>itaylor=41</code> 主要读取外部三维磁场；本组中可直接参与该路径的主要是密度 22/23 模式以及粒子源、热源。普通 GS 剖面和 VMEC 21 模式不生效。</p>
</div>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>平衡参数</th><th>文件</th><th>实际读取和使用</th><th>后续覆盖</th></tr></thead>
<tbody>
<tr><td><code>iread_eqdsk=1</code></td><td><code>geqdsk</code></td><td>把 <code>psirz</code>、压力和 F 投影到全部网格单元；读取磁轴、边界磁通、总电流和 q。GS 第一轮保留读入的 psi，更多轮次可以继续更新。</td><td>GS 中的 <code>profile_p/profile_f</code> 可替换压力和 F；缩放量及边缘条件继续修改剖面。</td></tr>
<tr><td><code>iread_eqdsk=2</code></td><td><code>geqdsk</code></td><td>仍读入并投影 gfile；仅在启用 GS 时改用默认解析压力/F，并从第一轮开始重新求解 psi。</td><td><code>iread_p=1</code>、<code>iread_f=1</code> 又可替换默认剖面。</td></tr>
<tr><td><code>iread_eqdsk=3</code></td><td><code>geqdsk</code></td><td>不使用 <code>psirz</code>；取磁轴、电流、压力/F/q 等信息，建立初始电流丝并重新求解 GS。该模式需要有效的 GS 迭代设置。</td><td>外部剖面和 GS 缩放设置具有更高优先级。</td></tr>
<tr><td><code>iread_dskbal=1/2</code></td><td><code>dskbal</code></td><td>1 使用文件中的 psi、F、FF′ 和 ne，并由 <code>ne(Te+Ti)</code> 计算压力；2 保留轴点、psi 和 ne，但压力/F 改为默认剖面。两者均强制固定边界并调用 GS。</td><td>GS 外部 p/F 可覆盖文件或默认剖面；GS 后又用 dskbal 的 ne 重写密度。</td></tr>
<tr><td><code>iread_jsolver=1/2</code></td><td><code>fixed</code></td><td>把 Jsolver 的 psi、p、F 按磁面位置映射到网格。<code>igs&gt;0</code> 时 1 使用文件 p/F，2 改用默认 p/F；<code>igs=0</code> 时二者相同。</td><td>仅在 GS 被调用时，外部 p/F 剖面可继续替换。</td></tr>
</tbody>
</table>
</div>

<div class="guide-grid compact">
<div class="guide-block">
<h4><code>geqdsk</code> 读取并使用的字段</h4>
<p>使用 R-Z 数据框和分辨率、<code>rmaxis/zmaxis</code>、<code>simag/sibry</code>、<code>current</code>、<code>fpol</code>、<code>press</code>、<code>ffprim</code>、<code>pprime</code>、<code>psirz</code> 和 <code>qpsi</code>。<code>bzero</code> 由最外点 <code>fpol/rmaxis</code> 设置，不采用文件中的 <code>bcentr</code>。</p>
</div>
<div class="guide-block">
<h4>gfile 边界不是 mesh 边界</h4>
<p>当前读取器没有读取 gfile 末尾的显式 LCFS 点 <code>rbbbs/zbbbs</code> 和 limiter 点 <code>rlim/zlim</code>。程序只通过 <code>sibry</code> 识别边界磁通，并在所有网格单元上插值；用户必须保证 mesh 位于 gfile R-Z 数据范围内，并自行保证第一壁、zone 与平衡相容。</p>
</div>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>参数</th><th>托卡马克 GS</th><th>固定边界 VMEC</th><th>自由边界/通用仿星器</th><th>覆盖关系</th></tr></thead>
<tbody>
<tr><td><code>iread_p</code></td><td>1：<code>profile_p(psi_N,p[J/m³])</code></td><td>21：<code>p_profile(s,p[J/m³])</code></td><td>不使用</td><td>GS 中替换平衡压力；VMEC 中替换 <code>presf</code> 压力场，但不改变 wout 几何和 B。</td></tr>
<tr><td><code>iread_f</code></td><td>1：<code>profile_f(psi_N,RBphi[T·m])</code></td><td>不使用</td><td>不使用</td><td>替换 F 并按文件最外点重设 <code>bzero</code>，之后仍受 <code>bscale/bpscale</code> 等修改。</td></tr>
<tr><td><code>iread_ne</code></td><td>1 <code>profile_ne</code>；2 <code>dne.xy</code>；4 rho；10 Corsica；20 iterdb</td><td>21：<code>n_profile(s,ne[m⁻³])</code></td><td>22：<code>n_profile(s)</code>；23：<code>n_profile_vs_p</code></td><td>21 在 VMEC 投影中写入；22/23 在平衡和 NEO 之后重新写入 <code>den_field(0)</code>。</td></tr>
<tr><td><code>iread_te</code></td><td>1 keV；2 eV；4 rho；10 Corsica；20 iterdb</td><td>21：<code>te_profile(s,Te[keV])</code></td><td>不使用</td><td>GS 中用于电子压力；特定单压力模型会用 p 和 Te 反算密度并销毁独立 Te spline。</td></tr>
<tr><td><code>iread_omega</code></td><td>1/2/3/4/5/20，且要求 <code>irot!=0</code></td><td>不使用</td><td>不使用</td><td>读入后乘 <code>vscale</code>；NEO 环向速度稍后继续叠加。</td></tr>
<tr><td><code>iread_omega_e</code><br><code>iread_omega_ExB</code></td><td>文件模式同 <code>iread_omega</code>，再分别扣除完整抗磁项或离子抗磁项</td><td>不使用</td><td>不使用</td><td>三种旋转入口严格互斥；<code>db=0</code> 时不进行抗磁换算。</td></tr>
<tr><td><code>iread_j=1</code></td><td colspan="3">仅特殊圆柱路径 <code>itor=0,itaylor=33</code> 使用 <code>profile_j(r,Jphi[A/m²])</code>；普通托卡马克 GS 和 VMEC 均忽略。</td><td>作为求解 psi 的电流源，不覆盖外部平衡文件。</td></tr>
</tbody>
</table>
</div>

<div class="flow" aria-label="GS 剖面覆盖顺序">
<span>平衡文件或默认剖面</span><b>→</b><span><code>profile_p/profile_f</code> 替换</span><b>→</b><span><code>pscale/bscale</code></span><b>→</b><span>径向 scale 文件</span><b>→</b><span><code>bpscale</code></span><b>→</b><span>边缘值修正</span>
</div>

<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>运行时输入</th><th>托卡马克坐标</th><th>仿星器坐标</th><th>写入方式与生效条件</th></tr></thead>
<tbody>
<tr><td><code>iread_particlesource=1</code><br><code>profile_particlesource</code></td><td>归一化 psi</td><td>逻辑 <code>s=xl²+zl²</code></td><td>第二列乘 C1input 的 <code>pellet_rate</code>，与 pellet、束源、电离和汇项相加；要求 <code>idens=1, linear=0</code>。</td></tr>
<tr><td><code>iread_heatsource=1</code><br><code>profile_heatsource</code></td><td>归一化 psi</td><td>逻辑 <code>s=xl²+zl²</code></td><td>第二列乘 <code>ghs_rate</code>，与束流、高斯热源和热沉相加；要求非线性且存在压力/温度方程。</td></tr>
<tr><td><code>iread_neo=1</code></td><td colspan="2"><code>out.neo.grid</code>、<code>out.neo.expnorm</code>、<code>out.neo.vel_fourier</code> 和 GYRO <code>input.profiles</code></td><td>只使用第一个物种；环向速度加到已有 <code>vz</code>，极向速度重写 <code>u/chi</code>，非 plasma 磁区置零。该坐标处理面向托卡马克。</td></tr>
<tr><td><code>ineo_subtract_diamag=1</code></td><td colspan="2">使用 NEO 应用时刻已有的 p、pe、ne 和 psi</td><td>仅在 <code>iread_neo=1</code> 且 <code>db!=0</code> 时扣除离子抗磁速度；后续 22/23 密度模式不会重新计算该修正。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>不建议的参数组合：</strong><code>den_edge&gt;0</code> 不应与非零 <code>iread_ne</code> 同时设置，<code>tedge&gt;0</code> 不应与非零 <code>iread_te</code> 同时设置。VMEC 或圆柱路径仅给定 Te 而未直接给定 ne 时，程序按 <code>n=Te/p</code> 计算密度；固定边界 VMEC 不应同时设置 <code>iread_ne=21</code> 和 <code>iread_te=21</code>。托卡马克源项中的 private-flux 修正值会被后续赋值覆盖，取样仍采用原始归一化 psi。</div>
</div>
"""
    if group == "Mesh Adaptation":
        return """
<div class="guide" data-guide>
<div class="guide-title">
<div>
<h3>Mesh Adaptation 在计算中的作用</h3>
<p>网格自适应根据预设磁通结构或当前离散误差重新分配局部空间分辨率。它会细化/粗化网格、转移已有场、重建有限元矩阵并重新进行并行划分，但不会重新判定 LCFS、第一壁或 zone 类型。</p>
</div>
<span class="guide-kicker">使用补充</span>
</div>
<div class="flow" aria-label="网格自适应流程">
<span>构造目标尺寸场</span><b>→</b><span>SCOREC/PUMI 细化与粗化</span><b>→</b><span>高阶场转移</span><b>→</b><span>重建网格和矩阵</span><b>→</b><span>继续时间推进</span>
</div>
<div class="guide-grid">
<div class="guide-block">
<h4>SCOREC 与 SPR</h4>
<p><strong>SCOREC</strong> 是 RPI 的 Scientific Computation Research Center；在程序中也指该中心开发的 PUMI/APF、MeshAdapt 和并行负载均衡软件栈，负责修改网格。</p>
<p><strong>SPR</strong> 是 Superconvergent Patch Recovery（超收敛斑片恢复）误差恢复算法，用于从解场恢复梯度并提出目标网格尺寸。</p>
</div>
<div class="guide-block">
<h4>边界与区域保持不变</h4>
<p>适配沿用原 mesh/model 的几何分类和 zone 标签。<code>iadapt_snap=1</code> 时，新边界节点会尽量贴回已有模型边界；它不会生成新的第一壁、真空区或导体壁，也不会把 LCFS 自动变成网格分区面。</p>
</div>
</div>
<div class="guide-table-wrap">
<table class="guide-table">
<thead><tr><th>适配路径</th><th>尺寸依据</th><th>主要用途</th><th>性质</th></tr></thead>
<tbody>
<tr><td><code>adapt_by_psi</code></td><td>平衡磁通 <code>psi</code>、q 面、线圈和 pellet 路径</td><td>计算开始前预布置 LCFS/SOL 等区域的网格</td><td>磁通面法向/切向可采用不同尺寸，属于各向异性适配</td></tr>
<tr><td><code>adapt_by_error</code></td><td>速度势 <code>U</code> 与磁通 <code>psi</code> 的边跳跃和方程残差</td><td>在时间推进中根据离散误差动态调整</td><td>合成节点误差后生成各向同性尺寸场</td></tr>
<tr><td><code>adapt_by_spr</code></td><td>当前 <code>psi</code> 场的 SPR 恢复梯度</td><td>多步演化中跟踪解的局部细尺度</td><td>由 <code>isprntime</code> 控制调用周期</td></tr>
</tbody>
</table>
</div>
<div class="guide-grid compact">
<div class="guide-block">
<h4><code>iadapt</code> 的模式选择</h4>
<dl class="mode-list">
<div><dt><code>0</code></dt><dd>关闭适配</dd></div>
<div><dt><code>1</code></dt><dd>初始化时按磁通适配</dd></div>
<div><dt><code>2</code></dt><dd>推进中按误差适配</dd></div>
<div><dt><code>3</code></dt><dd>初始化按磁通，推进中按误差</dd></div>
<div><dt><code>4</code></dt><dd>初始化及推进中均可按误差适配</dd></div>
</dl>
</div>
<div class="guide-block">
<h4>动态触发条件</h4>
<p><code>iadapt_ntime&gt;0</code> 时每隔指定步数检查；非线性计算且该值为零时每步检查；线性计算还可由 <code>adapt_ke</code> 的动能阈值触发。检查后只有估计误差超过 <code>adapt_target_error</code> 才实际换网格。</p>
<p><code>ispradapt=1</code> 时使用独立 SPR 路径，并抑制推进中的普通 error-estimator 路径。</p>
</div>
</div>
<div class="guide-grid compact">
<div class="guide-block">
<h4>三维 SPR 的处理</h4>
<p>多环向平面情况下，程序分别计算各平面的尺寸要求，对对应节点取最小值，再适配二维母网格并恢复全部环向平面。因此它改变极向网格拓扑，但不改变 <code>nplanes</code> 或环向平面间距。</p>
</div>
<div class="guide-block">
<h4>适配后的场</h4>
<p>SCOREC/PUMI 使用 M3D-C1 的高阶场转移把需要保留的解投影到新网格，随后更新节点所有权、单元几何和求解矩阵。初始磁通适配的非重启算例还会重新调用初始条件，把平衡再次投影到新网格。</p>
</div>
</div>
<div class="callout"><strong>使用限制：</strong>按磁通适配还需要工作目录中的 <code>sizefieldParam</code>（13 或 14 个数），并依赖 <code>USESCOREC</code> 编译选项。<code>adapt_factor</code> 和 <code>adapt_smooth</code> 虽可读入，但不参与活动计算。普通 error-estimator 尚未提供完整的多平面尺寸场处理；多平面计算应使用 SPR 路径。</div>
</div>
"""
    return ""


def write_simplified_html(params: list[Param], path: Path) -> None:
    by_group: dict[str, list[Param]] = {}
    for p in params:
        by_group.setdefault(p.group, []).append(p)
    group_order = [g for g in LOGICAL_GROUP_ORDER if g in by_group]
    group_order.extend(g for g in by_group if g not in group_order)

    css = """
:root { --bg:#f7f7f4; --panel:#fff; --ink:#202629; --muted:#627073; --line:#d9ddd8; --accent:#1f6f8b; }
* { box-sizing: border-box; }
body { margin:0; overflow-x:hidden; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC","Microsoft YaHei",Arial,sans-serif; line-height:1.55; }
code { background:#f0f2f1; border-radius:4px; padding:0.08rem 0.28rem; overflow-wrap:anywhere; word-break:break-word; }
.layout { display:grid; grid-template-columns:280px minmax(0,1fr); min-height:100vh; width:100%; max-width:100%; }
.sidebar { position:sticky; top:0; height:100vh; overflow:auto; padding:20px 16px; background:#fbfbf8; border-right:1px solid var(--line); }
.sidebar h1 { font-size:1.08rem; margin:0 0 12px; }
.small { color:var(--muted); font-size:0.88rem; margin:8px 0 14px; }
.search { width:100%; border:1px solid var(--line); border-radius:6px; padding:9px 10px; background:#fff; font-size:0.95rem; }
.nav { display:grid; gap:5px; margin-top:14px; }
.nav a { display:flex; justify-content:space-between; gap:8px; padding:7px 8px; border-radius:6px; color:var(--ink); text-decoration:none; }
.nav a:hover { background:#eef5f7; }
.content,.section,.guide { min-width:0; }
.content { padding:28px min(5vw,58px) 60px; }
.hero { border-bottom:1px solid var(--line); margin-bottom:24px; padding-bottom:18px; }
.hero h2 { margin:0 0 8px; font-size:clamp(1.5rem,2.4vw,2.25rem); }
.hero p { color:var(--muted); max-width:980px; margin:7px 0; }
.section { margin:32px 0 42px; }
.section h2 { border-bottom:1px solid var(--line); padding-bottom:8px; margin-bottom:10px; font-size:1.28rem; }
.note { color:var(--muted); max-width:960px; }
.guide { margin:18px 0 24px; padding:18px 0 20px; border-top:2px solid var(--accent); border-bottom:1px solid var(--line); }
.guide-title { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; }
.guide h3 { margin:0 0 5px; font-size:1.13rem; }
.guide h4 { margin:0 0 6px; font-size:0.98rem; }
.guide p { margin:6px 0; color:#344044; }
.guide-kicker { flex:0 0 auto; color:var(--accent); font-size:0.78rem; font-weight:700; padding-top:3px; }
.flow { display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin:15px 0 18px; padding:11px 0; color:#314247; font-size:0.9rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.flow span { font-weight:600; }
.flow b { color:var(--accent); font-weight:700; }
.sequence-pair { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin:16px 0 22px; padding:12px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.sequence-pair div { display:grid; gap:4px; min-width:0; }
.sequence-pair strong { color:var(--accent); font-size:0.84rem; }
.sequence-pair span { color:#344044; line-height:1.55; }
.device-band { margin:24px 0 30px; padding:18px 0 4px; border-top:1px solid var(--line); }
.device-heading { display:flex; align-items:baseline; gap:11px; margin-bottom:10px; }
.device-heading span { flex:0 0 auto; padding:3px 7px; border:1px solid currentColor; border-radius:4px; color:#176f79; font-size:0.78rem; font-weight:800; }
.device-heading h4 { margin:0; font-size:1.05rem; }
.stellarator-band .device-heading span { color:#855d1d; }
.case-steps { margin:10px 0 18px; padding-left:26px; }
.case-steps li { padding:4px 0 7px 5px; color:#344044; line-height:1.58; }
.case-steps li::marker { color:var(--accent); font-weight:800; }
.guide-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; margin:16px 0; }
.guide-grid.compact { margin-top:18px; }
.guide-block { min-width:0; border-left:3px solid #9dbdc6; padding-left:12px; }
.guide-table-wrap { overflow-x:auto; width:100%; max-width:100%; margin:16px 0; }
.guide-table { width:100%; border-collapse:collapse; min-width:700px; background:#fff; font-size:0.9rem; }
.guide-table th,.guide-table td { padding:9px 10px; border:1px solid var(--line); text-align:left; vertical-align:top; }
.guide-table th { background:#edf3f3; color:#304246; }
.mode-list { margin:7px 0 0; }
.mode-list div { display:grid; grid-template-columns:38px 1fr; gap:8px; padding:3px 0; }
.mode-list dt,.mode-list dd { margin:0; }
.callout { margin-top:18px; padding:11px 13px; border-left:4px solid #b8842f; background:#f7f2e7; color:#453c2d; }
.param { background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; padding:13px 14px; margin:10px 0; }
.head { display:flex; flex-wrap:wrap; gap:8px; align-items:baseline; justify-content:space-between; }
.name { font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; font-weight:700; overflow-wrap:anywhere; }
.meta { color:var(--muted); font-size:0.9rem; }
.meaning { margin-top:7px; }
.meaning-summary { margin:0; color:#344044; }
.meaning-parts { display:grid; margin-top:2px; }
.meaning-part { display:grid; grid-template-columns:112px minmax(0,1fr); gap:12px; padding:7px 0; border-top:1px solid #e7eae7; }
.meaning-part:first-child { border-top:0; }
.meaning-label { color:var(--muted); font-size:0.78rem; font-weight:750; line-height:1.55; }
.meaning-text { min-width:0; color:#344044; overflow-wrap:anywhere; }
.meaning-text code { overflow-wrap:anywhere; white-space:normal; }
.meaning-tokamak .meaning-label { color:#176f79; }
.meaning-stellarator .meaning-label { color:#855d1d; }
.meaning-common .meaning-label,.meaning-condition .meaning-label { color:#6f5b35; }
mjx-container { max-width:100%; overflow-x:auto; overflow-y:hidden; }
mjx-container[jax="CHTML"][display="false"] { display:inline-block; margin:0 0.08em; overflow:visible; vertical-align:-0.08em; }
.hidden { display:none !important; }
.empty { padding:18px; color:var(--muted); border:1px dashed var(--line); border-radius:8px; background:#fff; }
@media (max-width:900px) { .layout { grid-template-columns:minmax(0,1fr); } .sidebar { position:static; height:auto; min-width:0; border-right:0; border-bottom:1px solid var(--line); } .content { padding:22px 16px 42px; } .guide-grid,.sequence-pair { grid-template-columns:minmax(0,1fr); gap:14px; } .guide-title { gap:10px; } .device-heading { align-items:flex-start; } .meaning-part { grid-template-columns:1fr; gap:2px; } }
"""

    lines = [
        "<!doctype html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>M3D-C1 C1input 参数使用手册</title>",
        f"<style>{css}</style>",
        "<script>",
        "window.MathJax = {",
        "  tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] },",
        "  chtml: { displayAlign: 'left', displayIndent: '0' }",
        "};",
        "</script>",
        '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@4/tex-chtml.js"></script>',
        "</head>",
        "<body>",
        '<div class="layout">',
        '<aside class="sidebar">',
        "<h1>M3D-C1 C1input 参数使用手册</h1>",
        '<div class="small">参数名、数据类型、默认值与使用含义。</div>',
        '<input id="search" class="search" type="search" placeholder="搜索参数名、默认值或含义...">',
        '<div class="small" id="result-count"></div>',
        '<nav class="nav">',
    ]
    for group in group_order:
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        lines.append(f'<a href="#{h(anchor)}"><span>{h(GROUP_TRANSLATIONS.get(group, group))}</span><span>{len(by_group[group])}</span></a>')
    lines.extend([
        "</nav>",
        "</aside>",
        '<main class="content">',
        '<section class="hero">',
        "<h2>M3D-C1 主程序输入参数使用手册</h2>",
        f"<p>本文是独立发布的 M3D-C1 <code>C1input</code> 参数使用手册，共包含 {len(params)} 个参数。所有条目属于 <code>&amp;inputnl</code>；逻辑分组按照算例配置流程组织。参数未显式给定时采用表中默认值。</p>",
        "<p>各模块说明给出参数之间的生效条件、覆盖顺序、装置差异及相关模型方程。</p>",
        "</section>",
    ])

    for group in group_order:
        anchor = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        lines.append(f'<section class="section" id="{h(anchor)}" data-section>')
        lines.append(f"<h2>【{h(GROUP_TRANSLATIONS.get(group, group))}】 / {h(group)}</h2>")
        if group in GROUP_NOTES:
            lines.append(f'<p class="note">{paragraph(strip_audit_language(GROUP_NOTES[group]))}</p>')
        supplement = simplified_html_supplement(group)
        if supplement:
            lines.append(supplement)
        for p in sorted(by_group[group], key=lambda p: p.order):
            meaning = simplified_meaning(p)
            search_blob = " ".join([p.name, p.dtype, p.default, meaning, group, GROUP_TRANSLATIONS.get(group, group)]).lower()
            lines.append(f'<article class="param" data-param data-search="{h(search_blob)}">')
            lines.append('<div class="head">')
            lines.append(f'<div class="name">{h(p.name)}</div>')
            lines.append(f'<div class="meta">{h(p.dtype)} · 默认值 <code>{h(p.default)}</code></div>')
            lines.append("</div>")
            lines.append(f'<div class="meaning">{render_simplified_meaning(p)}</div>')
            lines.append("</article>")
        lines.append("</section>")

    lines.extend([
        '<div id="empty" class="empty hidden">没有匹配的参数。</div>',
        "</main>",
        "</div>",
        """
<script>
const search = document.getElementById('search');
const cards = Array.from(document.querySelectorAll('[data-param]'));
const guides = Array.from(document.querySelectorAll('[data-guide]'));
const sections = Array.from(document.querySelectorAll('[data-section]'));
const count = document.getElementById('result-count');
const empty = document.getElementById('empty');
function update() {
  const q = search.value.trim().toLowerCase();
  let visible = 0;
  let visibleGuides = 0;
  for (const card of cards) {
    const ok = !q || card.dataset.search.includes(q);
    card.classList.toggle('hidden', !ok);
    if (ok) visible++;
  }
  for (const guide of guides) {
    const ok = !q || guide.textContent.toLowerCase().includes(q);
    guide.classList.toggle('hidden', !ok);
    if (ok) visibleGuides++;
  }
  for (const section of sections) {
    const anyCard = Array.from(section.querySelectorAll('[data-param]')).some(card => !card.classList.contains('hidden'));
    const anyGuide = Array.from(section.querySelectorAll('[data-guide]')).some(guide => !guide.classList.contains('hidden'));
    const any = anyCard || anyGuide;
    section.classList.toggle('hidden', !any);
  }
  count.textContent = q
    ? `匹配 ${visible} / ${cards.length} 个参数${visibleGuides ? `，${visibleGuides} 个补充说明` : ''}`
    : `共 ${cards.length} 个参数`;
  empty.classList.toggle('hidden', visible !== 0 || visibleGuides !== 0);
}
search.addEventListener('input', update);
update();
</script>
""",
        "</body></html>",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def md_table(rows: list[list[str]]) -> str:
    out = []
    out.append("| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |")
    out.append("|---|---|---|---|---|---|---|---:|")
    for r in rows:
        out.append("| " + " | ".join(cell.replace("\n", "<br>").replace("|", "\\|") for cell in r) + " |")
    return "\n".join(out)


def write_markdown(params: list[Param], path: Path) -> None:
    by_group: dict[str, list[Param]] = {}
    for p in params:
        by_group.setdefault(p.group, []).append(p)

    doc_names = parse_doc_option_names(DOC_INPUTS.read_text(encoding="utf-8", errors="replace"))
    param_names = {p.name for p in params}
    doc_only = sorted(
        n for n in doc_names
        if n not in param_names
        and n not in DOC_ALIASES
        and len(n) > 1
        and "\\" not in n
    )

    lines: list[str] = []
    lines.append("# M3D-C1 `C1input` 参数整理（基于当前 master 源码）")
    lines.append("")
    lines.append("整理日期：2026-07-11。主要依据：`unstructured/input.f90` 的 `set_defaults` 和 `unstructured/read_namelist.cpp` 的解析规则；官方 `doc/` 仅作说明参考，默认值和可读参数一律以源码为准。")
    lines.append("")
    lines.append("## 读入格式与 namelist 说明")
    lines.append("")
    lines.append("- 主程序输入文件名固定为 `C1input`。惯例写成 `&inputnl ... /`，但源码解析器实际上逐行寻找 `name = value`，并不检查 namelist 名称。")
    lines.append("- 因此本文把所有主程序参数归为 namelist `&inputnl`；源码中的 “Model Options / Equilibrium / ...” 是帮助打印用的逻辑 group，不是多个 Fortran `NAMELIST` 块。")
    lines.append("- 注释以 `!` 开头；若 `!` 出现在 `=` 前，该行会被忽略。数组用一基索引：`param(1)=...`。")
    lines.append("- 开关类参数大多是 `integer`，通常 0=关闭、1=打开；源码没有把它们声明成 logical。")
    lines.append("- 默认值以源码 `add_var_*` 为准。若官方文档与源码不一致，表中采用源码值；不一致处单独列在审计文件中。")
    lines.append("- 条件编译参数：`condition` 列非空时，只有在相应编译宏启用时才会注册。Markdown 主表把这些参数保留并在说明中标注。")
    lines.append("- `内部变量` 是源码中实际被赋值/引用的 Fortran 变量名；少数输入名与内部变量名不同，例如 `pellet_r -> pellet_r_scl`。")
    lines.append("- `源码使用摘要` 来自程序源码自动索引；逐行引用见 `M3DC1_parameter_source_usage.md` / `m3dc1_parameter_source_usage.csv`，便于继续人工核查。")
    lines.append("")
    lines.append("最小格式示例：")
    lines.append("")
    lines.append("```fortran")
    lines.append("&inputnl")
    lines.append("  linear = 1")
    lines.append("  nplanes = 1")
    lines.append("  ntor = 1")
    lines.append("  dt = 0.1")
    lines.append("  ntimemax = 20")
    lines.append("/")
    lines.append("```")
    lines.append("")
    lines.append("## 参数总览")
    lines.append("")
    lines.append(f"- 共提取 `C1input` 参数：{len(params)} 个。")
    lines.append(f"- 官方 `doc/inputs.tex` 提到但当前 `set_defaults` 未注册的名称：{', '.join(doc_only[:60]) if doc_only else '无'}。")
    lines.append("- 官方文档中还存在若干旧名/错拼名，当前源码对应关系为：" + "；".join(f"`{k}` -> `{v}`" for k, v in DOC_ALIASES.items()) + "。")
    lines.append("- 官方文档与源码不一致清单见：[M3DC1_official_doc_vs_source_audit.md](M3DC1_official_doc_vs_source_audit.md)。")
    lines.append("- 面向阅读的可检索版本见：[M3DC1_C1input_reader_guide.html](M3DC1_C1input_reader_guide.html)。")
    lines.append("")

    group_order = [g for g in LOGICAL_GROUP_ORDER if g in by_group]
    group_order.extend(g for g in by_group if g not in group_order)
    for group in group_order:
        plist = sorted(by_group[group], key=lambda p: p.order)
        title = f"{GROUP_TRANSLATIONS.get(group, group)} / {group}"
        lines.append(f"## {title}")
        lines.append("")
        note = GROUP_NOTES.get(group)
        if note:
            lines.append(note)
            lines.append("")
        rows = []
        for p in plist:
            desc = p.description or "源码未给出说明；参考变量名、所在逻辑组和官方文档使用。"
            usage_parts = []
            if p.usage:
                usage_parts.append(p.usage)
            if p.condition:
                usage_parts.append(f"条件编译：`{p.condition}`。")
            if p.size != "1":
                usage_parts.append(f"数组长度/上限：`{p.size}`。")
            rows.append([
                f"`{p.name}`",
                f"`{p.internal_var}`",
                p.dtype,
                f"`{p.default}`",
                desc,
                " ".join(usage_parts) or "按需在 `C1input` 中写 `name = value`；未设置则使用默认值。",
                p.source_usage_summary,
                str(p.line),
            ])
        lines.append(md_table(rows))
        lines.append("")

    lines.append("## 附录 A：主程序相关的辅助输入文件")
    lines.append("")
    lines.append("| 文件/前缀 | 触发参数 | 用途 |")
    lines.append("|---|---|---|")
    aux = [
        ("`geqdsk`", "`iread_eqdsk`", "EFIT g-file；读入磁通/边界/剖面，具体选项见 `iread_eqdsk`。"),
        ("`dskbal`", "`iread_dskbal`", "读入 BAL 平衡。"),
        ("`fixed`", "`iread_jsolver`", "读入 Jsolver 平衡。"),
        ("`profile_ne`", "`iread_ne`", "电子密度剖面。"),
        ("`profile_te`", "`iread_te`", "电子温度剖面。"),
        ("`profile_p`", "`iread_p`", "压力剖面。"),
        ("`profile_f`", "`iread_f`", "GS 求解用 F=R*B_phi vs Psi_N。"),
        ("`profile_j`", "`iread_j`", "basicj 平衡用环向电流密度。"),
        ("`profile_bscale`", "`iread_bscale`", "F 或 toroidal field 缩放剖面。"),
        ("`profile_pscale`", "`iread_pscale`", "压力及 p' 缩放剖面。"),
        ("`profile_kappa`", "`ikappafunc=10/11`", "热扩散/热导剖面，10 为 m^2/s，11 为归一化。"),
        ("`profile_denm`", "`idenmfunc=10/11`", "粒子扩散剖面，10 为 m^2/s，11 为归一化。"),
        ("`profile_nz`", "`iread_prad`", "PRAD impurity density，单位 10^20/m^3。"),
        ("`rmp_coil.dat`, `rmp_current.dat`", "`irmp=1`", "RMP window-pane coil 位置、电流和相位。"),
        ("`pellet.dat`", "`iread_pellet=1`", "多 pellet 表格输入。"),
        ("`cloud.txt`", "`iread_lp_source>0`", "Lagrangian particle code source，开发中。"),
        ("`FIELDLINES`/`MGRID`/`fieldlines*`/`mgrid*`", "`type_ext_field=1/2`", "stellarator total/external field。"),
        ("`geometry.nc` 或 `vmec_filename`", "`iread_vmec=1`", "VMEC 几何。"),
        ("`plane_positions`", "`iread_planes=1`", "自定义环向平面位置。"),
        ("`C1.h5`, `time_nnn.h5`", "`irestart=1`, `irestart_slice`", "HDF5 restart 文件。"),
    ]
    for row in aux:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## 附录 B：mesh 生成器与转换工具输入")
    lines.append("")
    lines.append("这些不是主程序 `C1input` 的 `&inputnl` 参数，而是 `doc/mesh-gen.tex` 中描述的 mesh 工具输入文件。常见键包括：")
    lines.append("")
    lines.append("| 工具 | 输入格式/参数 | 说明 |")
    lines.append("|---|---|---|")
    mesh_rows = [
        ("`m3dc1_mfmgen` / `create_mesh.sh input`", "`inType`, `outFile`, `meshSize`, `modelFile`, `meshFile`, `bdryFile`, `faceBdry` 等", "ASCII key-value 输入；生成 `.dmg/.smb/.vtk` 等模型/网格文件。具体示例见各 `unstructured/templates/*/*_mesh/input`。"),
        ("`polar_meshgen`", "`inFile`, `meshSize` 等", "`POLAR`/jsolver 相关几何转 mesh；`meshSize` 缺省约 0.05。"),
        ("`simToM3dc1`", "SimModeler model/mesh 与 inner/outer model face 等", "把 SimModeler 数据转换为 M3D-C1 所需 mesh/model。"),
    ]
    for row in mesh_rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## 附录 C：官方 `doc/` 覆盖范围")
    lines.append("")
    lines.append("本整理扫描了当前 master 的 `doc/` 目录。与 `C1input` 参数直接相关的主要文件是 `inputs.tex`、`running_jobs.tex`、`units.tex`、`mesh-gen.tex`、`petsc_option.tex`、`physics-model.tex`、`output.tex`；其它文档主要提供安装、构建、后处理、版本协作和教程背景。")
    lines.append("")
    lines.append("| 文件 | 与本参数整理的关系 |")
    lines.append("|---|---|")
    doc_notes = {
        "inputs.tex": "官方参数表，提供大多数参数的使用说明；存在少量旧名/错拼名，本文已按源码校正。",
        "running_jobs.tex": "2D/3D、linear/nonlinear、bootstrap、restart、output 周期等运行方式说明。",
        "units.tex": "归一化单位说明，对 `b0_norm/n0_norm/l0_norm/ion_mass` 的解释有用。",
        "mesh-gen.tex": "mesh 生成器输入、`C1input` 中 mesh/model 文件名、`nplanes`、SimModeler/VMEC 相关背景。",
        "petsc_option.tex": "PETSc options 与 `nplanes`/bjacobi block 的配套关系。",
        "physics-model.tex": "MHD/two-fluid/temperature/impurity/radiation 物理模型背景。",
        "output.tex": "HDF5、time slice、`ntimepr`、后处理输出背景。",
        "mesh-adapt.tex": "网格自适应背景。",
        "tutorials.tex": "教程索引，提供典型算例入口。",
        "installation.tex": "安装/编译背景。",
        "building.tex": "构建系统背景。",
        "idl-postproc.tex": "IDL 后处理背景。",
        "app-paraview.tex": "ParaView 后处理背景。",
        "github.tex": "GitHub 工作流背景。",
        "doc.tex": "合并生成后的文档文本，内容与各章节有重复。",
        "M3DC1.tex": "LaTeX 主文件。",
        "M3DC1_License.tex": "许可证。",
        "color.tex": "LaTeX 样式/颜色定义。",
        "numerical_methods.tex": "数值方法背景，补充 `jadv` 等参数解释。",
    }
    for f in sorted((ROOT / "doc").glob("*.tex")):
        lines.append(f"| `{f.name}` | {doc_notes.get(f.name, '背景文档；未发现新的 `C1input` 注册参数。')} |")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_doc_audit(params: list[Param], md_path: Path) -> None:
    input_doc_text = DOC_INPUTS.read_text(encoding="utf-8", errors="replace")
    all_doc_text = all_official_doc_text()
    doc_names = parse_doc_option_names(input_doc_text)
    by_name = {p.name: p for p in params}

    unregistered = sorted(
        n for n in doc_names
        if n not in by_name
        and n not in DOC_ALIASES
        and len(n) > 1
        and "\\" not in n
    )
    undocumented = [
        p for p in sorted_params(params)
        if not mentioned_in_official_docs(p.name, all_doc_text)
        and not any(real == p.name and mentioned_in_official_docs(alias, all_doc_text)
                    for alias, real in DOC_ALIASES.items())
    ]

    lines: list[str] = []
    lines.append("# M3D-C1 官方文档与源码差异清单")
    lines.append("")
    lines.append("本清单只比较官方 `doc/` 与当前源码。用户提供的参考稿不参与差异统计。结论以 `unstructured/input.f90` 的 `add_var_*` 注册项和 `read_namelist.cpp` 的读入规则为准。")
    lines.append("")
    lines.append("## 1. 官方文档提到但源码未注册")
    lines.append("")
    lines.append("| 文档名称 | 说明 |")
    lines.append("|---|---|")
    if unregistered:
        for name in unregistered:
            lines.append(f"| `{name}` | `C1input` 使用该名称不会被当前源码识别。 |")
    else:
        lines.append("| 无 | - |")
    lines.append("")

    lines.append("## 2. 官方文档旧名/错拼名")
    lines.append("")
    lines.append("| 文档名称 | 源码实际名称 | 源码默认值 |")
    lines.append("|---|---|---:|")
    for alias, real in DOC_ALIASES.items():
        default = by_name[real].default if real in by_name else ""
        lines.append(f"| `{alias}` | `{real}` | `{default}` |")
    lines.append("")

    lines.append("## 3. 默认值不一致")
    lines.append("")
    lines.append("| 参数 | 源码默认值 | 官方文档默认值 | 说明 |")
    lines.append("|---|---:|---:|---|")
    for name, (doc_default, note) in DOC_DEFAULT_MISMATCHES.items():
        lines.append(f"| `{name}` | `{by_name[name].default}` | `{doc_default}` | {note} |")
    lines.append("")

    lines.append("## 4. 语义/取值范围与源码不一致或不完整")
    lines.append("")
    lines.append("| 参数 | 源码默认值 | 说明 |")
    lines.append("|---|---:|---|")
    for name, note in DOC_USAGE_MISMATCHES.items():
        if name in by_name:
            lines.append(f"| `{name}` | `{by_name[name].default}` | {note} |")
    lines.append("")

    lines.append("## 5. 运行时默认值/校验阶段会改写")
    lines.append("")
    lines.append("这些参数的注册默认值仍以源码表为准，但 `validate_input` 会在读入后根据其它开关改写，用户手册中应同时说明有效行为。")
    lines.append("")
    lines.append("| 参数 | 注册默认值 | 运行时行为 |")
    lines.append("|---|---:|---|")
    for name, note in RUNTIME_DEFAULT_NOTES.items():
        if name in by_name:
            lines.append(f"| `{name}` | `{by_name[name].default}` | {note} |")
    lines.append("")

    lines.append("## 6. 源码注册但官方文档未直接提到")
    lines.append("")
    lines.append(f"共 {len(undocumented)} 个，完整列于下表。")
    lines.append("")
    lines.append("| 参数 | 逻辑组 | 源码默认值 |")
    lines.append("|---|---|---:|")
    for p in undocumented:
        lines.append(f"| `{p.name}` | {p.group} | `{p.default}` |")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_template(params: list[Param], path: Path) -> None:
    lines = []
    lines.append("&inputnl")
    current = None
    for p in sorted_params(params):
        if p.group != current:
            current = p.group
            lines.append("")
            lines.append(f"  ! {GROUP_TRANSLATIONS.get(current, current)} / {current}")
        if p.condition:
            lines.append(f"  ! [conditional: {p.condition}]")
        value = p.default
        if p.dtype.startswith("character"):
            value = "''" if value == '""' else f"'{value}'"
        if "array" in p.dtype:
            lines.append(f"  ! {p.name}(1) = {value}   ! {p.dtype}, default all elements={p.default}")
        else:
            lines.append(f"  ! {p.name} = {value}   ! {p.dtype}")
    lines.append("/")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "m3dc1_official_doc_vs_source_audit.csv").unlink(missing_ok=True)
    params = parse_params()
    enrich_params(params)
    scan_source_usage(params)
    params_json = OUTDIR / "m3dc1_c1input_parameters.json"
    params_json.write_text(json.dumps([asdict(p) for p in sorted_params(params)], ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(params, OUTDIR / "m3dc1_c1input_parameters.csv")
    write_usage_files(params, USAGE_MD, USAGE_CSV)
    write_doc_audit(params, DOC_AUDIT_MD)
    write_simplified_markdown(params, SIMPLIFIED_MD)
    write_simplified_csv(params, SIMPLIFIED_CSV)
    write_simplified_html(params, SIMPLIFIED_HTML)
    shutil.copyfile(SIMPLIFIED_MD, OUTDIR / "M3DC1_C1input_parameters.md")
    shutil.copyfile(SIMPLIFIED_HTML, HTML_GUIDE)
    shutil.copyfile(SIMPLIFIED_HTML, PUBLISHED_HTML)
    write_template(params, OUTDIR / "C1input_all_parameters_template")
    print(f"params={len(params)}")
    print(f"groups={len(set(p.group for p in params))}")
    print(f"outputs={OUTDIR}")


if __name__ == "__main__":
    main()
