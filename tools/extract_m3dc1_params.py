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


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT = REPO_ROOT / "M3DC1"
INPUT_F90 = ROOT / "unstructured/input.f90"
DOC_INPUTS = ROOT / "doc/inputs.tex"
OLD_DOC = REPO_ROOT / "tools/reference_old_doc.txt"
OUTDIR = REPO_ROOT / "docs-data"
DOC_AUDIT_MD = OUTDIR / "M3DC1_official_doc_vs_source_audit.md"
DOC_AUDIT_CSV = OUTDIR / "m3dc1_official_doc_vs_source_audit.csv"
USAGE_MD = OUTDIR / "M3DC1_parameter_source_usage.md"
USAGE_CSV = OUTDIR / "m3dc1_parameter_source_usage.csv"
HTML_GUIDE = OUTDIR / "M3DC1_C1input_reader_guide.html"
SIMPLIFIED_MD = OUTDIR / "M3DC1_C1input_parameters_simplified.md"
SIMPLIFIED_CSV = OUTDIR / "m3dc1_c1input_parameters_simplified.csv"
SIMPLIFIED_HTML = OUTDIR / "M3DC1_C1input_simplified_guide.html"
PUBLISHED_HTML = REPO_ROOT / "index.html"


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
    "iread_eqdsk": "托卡马克：轴对称 g-file 平衡入口。1 直接投影 `geqdsk`；2 读入 gfile 后在 GS 中改用默认压力/F；3 不使用 `psirz`，只取磁轴、电流和剖面重新求解 GS。仿星器：必须为 0，否则会在 `itaylor=40/41` 之前抢占初始化入口。",
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
    "jadv": "1 使用环向电流密度方程代替极向磁通方程；官方文档旧表写 0，但当前源码默认是 1。",
    "imp_mod": "源码当前默认 1。0: standard/theta implicit；1: Caramana split-step 形式。",
    "pskip": "源码当前默认 0；官方文档写 1。控制预条件器重算/复用相关周期。",
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
        w = csv.DictWriter(f, fieldnames=list(asdict(params[0]).keys()))
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
        w = csv.DictWriter(f, fieldnames=fields)
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
        w = csv.DictWriter(f, fieldnames=["参数名", "数据类型", "默认值", "含义"])
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
    lines.append("# M3D-C1 `C1input` 参数简表")
    lines.append("")
    lines.append("本简表面向写算例输入文件的用户，只保留用户需要提供/理解的四项：参数名、数据类型、默认值和含义。所有条目均为主程序 `C1input` 可读参数，属于 `&inputnl`；分组仅用于阅读。")
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


def simplified_html_supplement(group: str) -> str:
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
<tr><td>固定边界 VMEC</td><td><code>itaylor=40</code>, <code>igeometry=1</code>, <code>iread_vmec=1</code>, <code>bloat_factor=0</code>, <code>bloat_distance=0</code></td><td>逻辑外边界与 wout 最外磁面对应；通常使用单一 plasma zone。源码只显式检查 <code>bloat_factor=0</code>，但物理上的固定边界也应关闭距离外扩。</td></tr>
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

<div class="callout"><strong>唯一平衡入口：</strong>初始化分支的源码优先级为 <code>iread_eqdsk</code> → <code>iread_dskbal</code> → <code>iread_jsolver</code> → <code>itaylor</code>。前一个非零值会直接屏蔽后面的入口而不报冲突。因此一个 case 只能有一个平衡入口；仿星器使用 <code>itaylor=40/41</code> 时，三个托卡马克平衡读取参数必须全部为 0。</div>

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
<li><strong>先清空托卡马克平衡入口。</strong><code>iread_eqdsk=iread_dskbal=iread_jsolver=0</code>，否则源码会先进入轴对称分支，<code>itaylor=40/41</code> 不会执行。</li>
<li><strong>选择固定边界 VMEC 或外场/自由边界路径。</strong><code>itaylor=40</code> 直接读取 wout 的既有平衡结果，M3D-C1 不在此路径求解 VMEC 平衡；<code>itaylor=41</code> 使用外部/总磁场文件初始化三维场，相关文件与类型参数位于 Equilibrium 组。</li>
<li><strong>先完成逻辑 mesh 与物理几何映射。</strong>通常用 <code>igeometry=1, iread_vmec=1</code>。固定边界关闭 bloat；外场路径可按计算域需要外扩。Input 参数不负责识别 LCFS、壁或真空 zone。</li>
<li><strong>再选择该路径真正支持的剖面。</strong>固定 VMEC 使用 21 模式覆盖 p/ne/Te；外场路径不读取 21 模式，可用密度 22/23 在初始场完成后重写密度。旋转、F 和普通 GS 剖面均不进入这些仿星器分支。</li>
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
<tr><td><code>iread_eqdsk</code>, <code>iread_dskbal</code>, <code>iread_jsolver</code></td><td colspan="2">必须为 0。</td><td>任一非零都会抢占 <code>itaylor=40/41</code>。</td></tr>
<tr><td><code>iread_p</code></td><td><code>21</code> 读取 <code>p_profile(s,p)</code>，替换 wout <code>presf</code>。</td><td>不读取。</td><td>只改压力场，不重新计算 VMEC 几何或磁场。</td></tr>
<tr><td><code>iread_ne</code></td><td><code>21</code> 读取 <code>n_profile(s,ne)</code>。</td><td><code>22</code> 读 <code>n_profile(s)</code>；<code>23</code> 读 <code>n_profile_vs_p</code>。</td><td>22/23 在平衡与 NEO 应用之后重写密度；<code>den_edge&gt;0</code> 与非零模式冲突。</td></tr>
<tr><td><code>iread_te</code></td><td><code>21</code> 读取 <code>te_profile(s,Te)</code>。</td><td>不读取。</td><td><code>tedge&gt;0</code> 与非零模式冲突。</td></tr>
<tr><td><code>iread_f</code>, <code>iread_j</code></td><td colspan="2">不读取。</td><td>磁场分别来自 wout 或外场数据；<code>iread_j</code> 只属于特殊圆柱测试。</td></tr>
<tr><td><code>iread_omega</code>, <code>iread_omega_e</code>, <code>iread_omega_ExB</code></td><td colspan="2">不读取。</td><td>这些实现位于托卡马克 GS 剖面路径。</td></tr>
<tr><td><code>iread_neo</code>, <code>ineo_subtract_diamag</code></td><td colspan="2">没有与 VMEC 逻辑坐标配套的专用实现，建议均为 0。</td><td>当前坐标和磁区处理面向托卡马克。</td></tr>
<tr><td><code>iread_particlesource</code></td><td colspan="2"><code>1</code> 读 <code>profile_particlesource(s)</code>，其中 \\(s=x_l^2+z_l^2\\)。</td><td>乘 <code>pellet_rate</code>，要求 <code>idens=1, linear=0</code>。</td></tr>
<tr><td><code>iread_heatsource</code></td><td colspan="2"><code>1</code> 读 <code>profile_heatsource(s)</code>，其中 \\(s=x_l^2+z_l^2\\)。</td><td>乘 <code>ghs_rate</code>，要求非线性压力/温度方程。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>源码行为提示：</strong>仿星器/圆柱的 Te-only 单压力分支当前实际按 \\(n=T_e/p\\) 计算密度；固定 VMEC 同时设置 <code>iread_ne=21</code> 与 <code>iread_te=21</code> 时，温度输出变量存在未赋值路径。这两种组合应避免，除非先核对并修正所用源码版本。</div>
</section>

<div class="callout"><strong>共同的文件覆盖原则：</strong>平衡入口决定初始几何和主场；剖面读取只在所属初始化分支中生效；NEO 与 22/23 密度属于平衡后的重写；热源和粒子源属于时间推进中的附加项。参数非零并不保证文件一定会被读到，必须同时满足装置路径和方程开关。</div>
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
<p>zone 是对既有单元的物理分类，不会把某块逻辑网格自动移动到等离子体、真空或导体壁的位置。即使输入在语法上合法，错误的 zone 与平衡对应关系仍会产生物理上不合理的算例。</p>
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
<div class="callout"><strong>平衡入口优先级：</strong><code>iread_eqdsk</code> → <code>iread_dskbal</code> → <code>iread_jsolver</code> → <code>itaylor</code>。程序使用 <code>if / else if</code> 选择，前一个非零参数会静默屏蔽后面的入口。因此这些参数不能彼此组合，也不能与 <code>itaylor=40/41</code> 的仿星器初始化混用。</div>

<div class="guide-grid">
<div class="guide-block">
<h4>托卡马克</h4>
<p><code>geqdsk</code>、<code>dskbal</code> 和 Jsolver <code>fixed</code> 都是轴对称平衡入口。平衡数据按现有物理 <code>(R,Z)</code> 网格插值或用于重新求解 GS，不会改变 mesh 几何。</p>
<p>普通 <code>iread_p/f/ne/te/omega</code> 剖面只有在 GS 路径真正调用 <code>define_profiles</code> 时才读取。直接导入 <code>iread_eqdsk=1/2, igs=0</code> 或 <code>iread_jsolver&gt;0, igs=0</code> 时，这些标准剖面文件不会覆盖已投影的平衡。</p>
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
<h4><code>geqdsk</code> 真正使用的字段</h4>
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
<tr><td><code>ineo_subtract_diamag=1</code></td><td colspan="2">使用 NEO 应用时刻已有的 p、pe、ne 和 psi</td><td>仅在 <code>iread_neo=1</code> 且 <code>db!=0</code> 时扣除离子抗磁速度；之后的 22/23 密度模式不会回头重算该修正。</td></tr>
</tbody>
</table>
</div>

<div class="callout"><strong>程序可接受但不建议的组合：</strong><code>den_edge&gt;0</code> 与非零 <code>iread_ne</code> 冲突，<code>tedge&gt;0</code> 与非零 <code>iread_te</code> 冲突。VMEC 或圆柱路径只给 Te、不直接给 ne 时，当前程序实际按 <code>n=Te/p</code> 计算；VMEC 同时设置 <code>iread_ne=21</code> 和 <code>iread_te=21</code> 时温度输出未被赋值。托卡马克源项中的 private-flux 修正值也会被下一行覆盖，实际仍按原始归一化 psi 取样。</div>
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
<h4><code>iadapt</code> 的源码分派</h4>
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
<div class="callout"><strong>使用限制：</strong>按磁通适配还需要工作目录中的 <code>sizefieldParam</code>（13或14个数）。当前实现依赖 <code>USESCOREC</code>；<code>adapt_factor</code> 和 <code>adapt_smooth</code> 虽可读入但没有活动使用点。普通 error-estimator 的多平面尺寸场分支在当前源码中看起来尚未完成，真正具有明确多平面处理流程的是 SPR 路径。</div>
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
code { background:#f0f2f1; border-radius:4px; padding:0.08rem 0.28rem; }
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
        "<title>M3D-C1 C1input 参数简表</title>",
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
        "<h1>M3D-C1 C1input 参数简表</h1>",
        '<div class="small">只显示参数名、类型、默认值和含义。</div>',
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
        "<h2>M3D-C1 主程序输入参数简表</h2>",
        f"<p>共 {len(params)} 个 `C1input` 参数。所有条目属于 `<code>&amp;inputnl</code>`；逻辑分组仅用于阅读。默认值以当前程序注册值为准。</p>",
        "<p>本版刻意去掉开发者核查信息，只保留用户写输入文件时最需要看的四项。</p>",
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


def write_doc_audit(params: list[Param], md_path: Path, csv_path: Path) -> None:
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

    rows: list[dict[str, str]] = []
    for name in unregistered:
        rows.append({
            "category": "doc_name_not_registered",
            "doc_name": name,
            "source_name": "",
            "source_default": "",
            "doc_default": "",
            "note": "官方 doc/inputs.tex 提到，但源码 set_defaults 未注册；C1input 中使用会触发未识别变量警告。",
        })
    for alias, real in DOC_ALIASES.items():
        rows.append({
            "category": "doc_old_or_misspelled_name",
            "doc_name": alias,
            "source_name": real,
            "source_default": by_name[real].default if real in by_name else "",
            "doc_default": "",
            "note": "官方文档中的旧名/错拼名；实际 C1input 应使用 source_name。",
        })
    for name, (doc_default, note) in DOC_DEFAULT_MISMATCHES.items():
        p = by_name[name]
        rows.append({
            "category": "default_mismatch",
            "doc_name": name,
            "source_name": name,
            "source_default": p.default,
            "doc_default": doc_default,
            "note": note,
        })
    for name, note in DOC_USAGE_MISMATCHES.items():
        if name not in by_name:
            continue
        rows.append({
            "category": "usage_or_value_range_mismatch",
            "doc_name": name,
            "source_name": name,
            "source_default": by_name[name].default,
            "doc_default": "",
            "note": note,
        })
    for name, note in RUNTIME_DEFAULT_NOTES.items():
        if name not in by_name:
            continue
        rows.append({
            "category": "runtime_default_or_validation_behavior",
            "doc_name": name,
            "source_name": name,
            "source_default": by_name[name].default,
            "doc_default": "",
            "note": note,
        })
    for p in undocumented:
        rows.append({
            "category": "source_registered_not_found_in_official_doc",
            "doc_name": "",
            "source_name": p.name,
            "source_default": p.default,
            "doc_default": "",
            "note": f"源码注册在 {p.group}；未在 doc/*.tex 中直接提到。",
        })

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "category",
                "doc_name",
                "source_name",
                "source_default",
                "doc_default",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(rows)

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
    lines.append(f"共 {len(undocumented)} 个。完整机器可筛选清单见 `m3dc1_official_doc_vs_source_audit.csv` 的 `source_registered_not_found_in_official_doc` 行。")
    lines.append("")
    lines.append("| 参数 | 逻辑组 | 源码默认值 |")
    lines.append("|---|---|---:|")
    preview = undocumented[:80]
    for p in preview:
        lines.append(f"| `{p.name}` | {p.group} | `{p.default}` |")
    if len(undocumented) > len(preview):
        lines.append(f"| ... | 另有 {len(undocumented) - len(preview)} 个，见 CSV | ... |")
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
    params = parse_params()
    enrich_params(params)
    scan_source_usage(params)
    params_json = OUTDIR / "m3dc1_c1input_parameters.json"
    params_json.write_text(json.dumps([asdict(p) for p in sorted_params(params)], ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(params, OUTDIR / "m3dc1_c1input_parameters.csv")
    write_usage_files(params, USAGE_MD, USAGE_CSV)
    write_markdown(params, OUTDIR / "M3DC1_C1input_parameters.md")
    write_doc_audit(params, DOC_AUDIT_MD, DOC_AUDIT_CSV)
    write_html_guide(params, HTML_GUIDE)
    write_simplified_markdown(params, SIMPLIFIED_MD)
    write_simplified_csv(params, SIMPLIFIED_CSV)
    write_simplified_html(params, SIMPLIFIED_HTML)
    shutil.copyfile(SIMPLIFIED_HTML, PUBLISHED_HTML)
    write_template(params, OUTDIR / "C1input_all_parameters_template")
    print(f"params={len(params)}")
    print(f"groups={len(set(p.group for p in params))}")
    print(f"outputs={OUTDIR}")


if __name__ == "__main__":
    main()
