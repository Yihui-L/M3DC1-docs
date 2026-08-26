# M3D-C1 `C1input` 参数简表

本简表面向写算例输入文件的用户，只保留用户需要提供/理解的四项：参数名、数据类型、默认值和含义。所有条目均为主程序 `C1input` 可读参数，属于 `&inputnl`；分组仅用于阅读。

参数总数：611。默认值以当前程序注册值为准。

## 归一化 / Normalizations

这些量定义 M3D-C1 默认归一化：B0_norm=10^4 G、n0_norm=10^14 cm^-3、L0_norm=100 cm；多数物理输入/输出使用归一化单位

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `b0_norm` | real | `1.e4` | Normalization magnetic field (in G) |
| `n0_norm` | real | `1.e14` | Normalization density (in e-/cm3) |
| `l0_norm` | real | `100.` | Normalization length (in cm) |

## 网格 / Mesh

主程序读取已有 mesh/model 文件；mesh 生成工具的 input 文件格式另见附录

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `nplanes` | integer | `1` | Number of toroidal planes；托卡马克：2D/complex 线性取 1，真实三维非线性取大于 1 的环向平面数。仿星器：表示所选环向计算域内的平面数，通常必须大于 1；需足以解析 VMEC/外场的最高环向模。3D+PETSc 当前要求 MPI 进程数等于 `nplanes` |
| `nperiods` | integer | `1` | Number of field periods；托卡马克：通常取 1。仿星器：表示整环面被划分的周期数；当 `ifull_torus=0` 时实际只计算 `1/nperiods` 环面，且 VMEC 的 `nfp` 必须能被它整除 |
| `ifull_torus` | integer | `1` | 0 = one field period; 1 = full torus；托卡马克：通常取 1；取 0 只有在明确采用周期扇区时才有意义。仿星器：0 计算一个由 `nperiods` 定义的周期扇区，1 计算完整环面；它控制环向域长度，不改变 VMEC 几何本身 |
| `iread_vmec` | integer | `0` | 1 = read geometry from VMEC file；托卡马克：保持 0，gfile 不通过该参数读取。仿星器：1 时从 `vmec_filename` 读取 VMEC 几何，并在固定边界初始化中同时提供平衡磁场和压力；通常与 `igeometry=1` 配合 |
| `vmec_filename` | character(len=256) | `geometry.nc` | name of vmec data file；托卡马克：不使用。仿星器：`iread_vmec=1` 时的 VMEC NetCDF 文件名；几何映射读取 R/Z 傅里叶系数、场周期和磁场系数，固定边界还使用其中的压力和磁场 |
| `igeometry` | integer | `0` | 0: default, identity；托卡马克：标准物理 R-Z 网格取 0，网格坐标不再映射。仿星器：取 1，先把二维 mesh 坐标解释为逻辑圆盘，再由 VMEC/边界傅里叶数据映射为物理 R-Z；取 2 是求解 Laplace 几何的内部路径，不是常规 VMEC 设置 |
| `xcenter` | real | `0.` | center of logical mesh (x)；托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 x 坐标，逻辑 rho 由 `sqrt((x-xcenter)^2+(z-zcenter)^2)` 计算；必须与生成逻辑 mesh 时采用的圆心一致 |
| `zcenter` | real | `0.` | center of logical mesh (z)；托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 z 坐标，与 `xcenter` 共同定义 rho 和 theta；必须与逻辑 mesh 圆心一致 |
| `bloat_factor` | real | `0.` | factor to expand VMEC domain；托卡马克：不使用。仿星器：把 VMEC 几何径向外推到放大的计算边界；0 不按比例扩展。固定边界 `itaylor=40` 的检查要求它为 0；自由边界/外场域可非零。若同时给 `bloat_distance`，后者优先并把本参数置 0 |
| `bloat_distance` | real | `0.` | factor to expand VMEC domain；托卡马克：不使用。仿星器：沿 VMEC 磁面外法向按距离扩展计算边界，并覆盖 `bloat_factor` 的作用。固定边界 case 建议保持 0；外扩域不会自动生成真空、壁或 LCFS 的 zone 标签 |
| `nzer_factor` | integer | `-1` | scale factor for order of VMEC interpolation；托卡马克：不使用。仿星器：控制 VMEC R/Z 几何转为 Zernike 径向表示的阶数；非负时取 `n_zer=mpol*nzer_factor`，但仅在 `nzer_manual<0` 时使用。-1 采用程序默认 |
| `nzer_manual` | integer | `-1` | order of VMEC interpolation；托卡马克：不使用。仿星器：手动指定 VMEC 几何的 Zernike 径向阶数；只有不低于程序默认阶数时才覆盖默认值，且优先于 `nzer_factor`。主要用于分辨率测试 |
| `iread_planes` | integer | `0` | Read positions of toroidal planes from plane_positions；托卡马克：3D 时 1 从 `plane_positions` 读取每个环向平面角度；否则均匀或按 toroidal packing 生成。仿星器：用法相同，但每个角度必须位于当前完整环面或周期扇区的范围内，文件行数必须等于 `nplanes` |
| `xzero` | real | `0.` | 托卡马克：某些解析初值、诊断和参考轴使用的 R 参考位置；不会移动 `mesh_filename` 中的节点，也不能用来使 mesh 对齐 gfile。仿星器：逻辑映射中心应使用 `xcenter`，本参数通常保持默认，仅少数测试/诊断使用 |
| `zzero` | real | `0.` | 托卡马克：某些解析初值、诊断和参考轴使用的 Z 参考位置；不会平移已读入 mesh。仿星器：逻辑映射中心应使用 `zcenter`，本参数通常保持默认 |
| `tiltangled` | real | `0.` | 托卡马克：给矩形测试网格的边界法向加入旋转角，不会旋转任意外部 mesh 的节点。仿星器：VMEC 曲边界使用映射几何法向，通常保持 0 |
| `mesh_filename` | character(len=256) | `struct-dmg.sms` | 托卡马克：二维物理 R-Z 有限元 mesh 文件；几何范围应覆盖目标等离子体、真空和壁区域并落在所需平衡数据范围内。仿星器：二维逻辑圆盘 mesh 文件，通常外边界 rho=1，随后映射为三维物理几何 |
| `mesh_model` | character(len=256) | `struct.dmg` | 托卡马克：与 `mesh_filename` 配套的几何模型，保存边界实体和 zone 拓扑。仿星器：与逻辑 mesh 配套的模型；模型标签定义逻辑分区，不会根据 VMEC 自动改成物理 plasma/vacuum/conductor 分区 |
| `model_info` | character(len=256) | `dummyInfo` | 托卡马克：仅 `USECADMODEL` 编译路径加载的额外 CAD model-info 文件，普通 `.dmg/.txt` 工作流不设置。仿星器：条件和用途相同，不参与 VMEC 几何映射 |
| `ipartitioned` | integer | `0` | 1 = the input mesh is partitioned；托卡马克：当前主程序只注册和保存该值，活动的 SCOREC `load_mesh` 没有按它分支。仿星器：行为相同，也不能用它切换逻辑 mesh 的装载方式；两者都应直接提供与运行方式匹配的 mesh 文件 |
| `imatassemble` | integer | `0` | 0: use scorec matrix parallel assembly; 1 use petsc；托卡马克：0 使用 SCOREC、1 使用 PETSc 进行并行矩阵装配，不改变物理 R-Z mesh。仿星器：后端选择相同，不改变逻辑到物理的几何映射、区域或平衡场 |
| `is1_agg_blks` | integer | `1` | number of blocks to divide each node of dofs into for matrix s1；托卡马克：仅 `REORDERED` 编译时注册，设置 S1 矩阵每节点自由度聚合块数。仿星器：用法相同；只影响求解性能，不改变物理网格或 VMEC 映射；仅在满足条件编译 `ifdef REORDERED` 时可用 |
| `is1_agg_scp` | integer | `0` | 0: per-rank aggregation, 1: per-plane aggregation, 2: global aggregation；托卡马克：仅 `REORDERED` 编译时注册；0 每 MPI rank、1 每环向平面、2 全局聚合。仿星器：取值相同，按所选周期域的平面组织聚合；不改变几何；仅在满足条件编译 `ifdef REORDERED` 时可用 |
| `imulti_region` | integer | `0` | 1 = Mesh has multiple physical regions；托卡马克：0 时全部单元自动视为 plasma；1 时必须用 `boundary_type/zone_type` 明确等离子体、真空和导体区，适合第一壁/电阻壁计算。仿星器：语法相同，但标签只分类逻辑 mesh 的既有单元，程序不会根据 VMEC LCFS 或外场自动判定区域；必须先保证映射后的物理位置合理 |
| `toroidal_pack_factor` | real | `1.` | ratio of longest to shortest toroidal element；托卡马克：3D 且 `iread_planes=0` 时，>1 在 `toroidal_pack_angle` 附近加密环向平面；1 均匀。仿星器：作用相同，但需在所选周期域内兼顾 VMEC/外场模数解析；不改变二维截面网格 |
| `toroidal_pack_angle` | real | `0.` | toroidal angle of maximum mesh packing；托卡马克：`toroidal_pack_factor>1` 且未读 `plane_positions` 时的最大环向加密角，必须位于托卡马克计算域内。仿星器：定义相同，但角度必须位于当前完整环面或场周期扇区内 |
| `boundary_type` | integer array | `0` | Type of each mesh boundary.；托卡马克：`imulti_region=1` 时按几何边编号标记 1=第一壁、2=计算域外边界；它决定边界条件作用位置。仿星器：取值相同，但标记的是逻辑模型边，映射后才成为物理边界；不会自动等于 VMEC LCFS；数组长度/上限：1000 |
| `zone_type` | integer array | `0` | Type of each mesh boundary.；托卡马克：`imulti_region=1` 时按 zone 编号标记 1=plasma、2=conductor、3=vacuum。仿星器：取值相同，但必须由用户确认逻辑 zone 经 VMEC/bloat 映射后确实落在相应物理区域；程序只检查标签是否存在，不检查与平衡的一致性；数组长度/上限：100 |

## 输入文件/剖面读入 / Input

控制是否从 geqdsk/dskbal/jsolver 及 profile_* 文件读入平衡、剖面、源项等。实际文件名多为固定约定，例如 geqdsk、profile_ne、profile_te、profile_p、profile_f、profile_j

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `iread_eqdsk` | integer | `0` | 托卡马克：轴对称 g-file 平衡入口。1 直接投影 `geqdsk`；2 读入 gfile 后在 GS 中改用默认压力/F；3 不使用 `psirz`，只取磁轴、电流和剖面重新求解 GS。仿星器：必须为 0，否则会在 `itaylor=40/41` 之前抢占初始化入口 |
| `iread_dskbal` | integer | `0` | 托卡马克：旧 BAL 平衡入口。1 使用文件 psi、F、FF′、ne 并由 ne(Te+Ti) 计算压力；2 压力/F 改用默认剖面；两者都调用 GS。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化 |
| `iread_jsolver` | integer | `0` | 托卡马克：旧 Jsolver 平衡入口，读取 `fixed`；`igs>0` 时 1 使用文件 p/F、2 改用默认 p/F，`igs=0` 时直接投影。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化 |
| `iread_omega` | integer | `0` | 托卡马克：仅 GS 且 `irot!=0` 时读取，模式 1/2/3/4/5/20 分别对应 `profile_omega`、`dtrot.xy`、`profile_vphi`、rho 文件、带表头文件和 `iterdb`，之后乘 `vscale`。仿星器：VMEC 与 `itaylor=41` 路径均不读取；`iread_omega_e` 与 `iread_omega_ExB` 会在校验阶段映射到同一个内部选择量；`irot=0` 时不会读取文件；`iread_omega_e` 或 `iread_omega_ExB` 非零时会写入同一个内部 `iread_omega`，且与已有 `iread_omega` 互斥 |
| `iread_omega_e` | integer | `0` | Read electron rotation (same options as iread_omega)；托卡马克：文件模式同 `iread_omega`，随后扣除完整抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_ExB` 严格互斥 |
| `iread_omega_ExB` | integer | `0` | Read ExB rotation (same options as iread_omega)；托卡马克：文件模式同 `iread_omega`，随后扣除离子抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_e` 严格互斥 |
| `iread_ne` | integer | `0` | 托卡马克：GS 使用 1/2/4/10/20 读取 psi、rho、Corsica 或 iterdb 密度。仿星器：固定边界 VMEC 用 21 读取 `n_profile(s)`；21 不用于 `itaylor=41`，该路径可用 22 的 `n_profile(s)` 或 23 的 `n_profile_vs_p` 在平衡后重写密度。两种装置中 `den_edge>0` 均与非零值冲突；GS 路径的 1/2/4/10/20 建立磁通函数；VMEC/ST 的 21/22/23 分别在 VMEC 投影中或后续 `den_eq` 中写入密度 |
| `iread_te` | integer | `0` | 托卡马克：GS 使用 1/2/4/10/20 读取不同坐标和单位的 Te。仿星器：仅固定边界 VMEC 的 21 读取 `te_profile(s)`；自由边界路径不读取。两种装置中 `tedge>0` 均与非零值冲突；GS 路径的 1/2/4/10/20 分别采用 psi、rho、Corsica 或 iterdb 坐标；VMEC 的 21 采用逻辑 `s=rho^2` |
| `iread_p` | integer | `0` | 托卡马克：GS 中 1 读取 `profile_p(psi_N,p)`，替换 gfile/旧平衡或默认压力剖面。仿星器：固定边界 VMEC 中 21 读取 `p_profile(s,p)` 并替换 wout 的 `presf` 压力场，但不改变几何和磁场；自由边界路径不读取；GS 外部压力剖面会替换 gfile/dskbal/jsolver 或默认剖面；VMEC 外部压力只替换压力场，不改变 wout 的几何和磁场 |
| `iread_f` | integer | `0` | Read profile_f file containing F=R*B_phi vs Psi_N for GS solve；托卡马克：GS 中 1 读取 `profile_f(psi_N,F)`，其中 F 满足 \(F=R B_\phi\)；该文件替换 F，并按最外点重设 `bzero`。仿星器：不读取，VMEC 磁场仍来自 wout，`itaylor=41` 磁场来自外场文件 |
| `iread_j` | integer | `0` | Read profile_j file containing toroidal J_phi(r) (basicj equilibrium only)；托卡马克：常规轴对称 GS 不使用；仅非托卡马克圆柱测试路径 `itor=0,itaylor=33` 读取 `profile_j(r,J_phi)`。仿星器：不使用 |
| `iread_heatsource` | integer | `0` | 托卡马克：1 读取 `profile_heatsource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘 `ghs_rate` 并与其他热源相加，且只在非线性压力/温度方程中生效 |
| `iread_particlesource` | integer | `0` | 托卡马克：1 读取 `profile_particlesource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘输入参数 `pellet_rate` 并与其他密度源相加，且要求 `idens=1,linear=0` |
| `iread_neo` | integer | `0` | Read velocity data from NEO output；托卡马克：1 读取三类 NEO 输出和 GYRO `input.profiles`；环向速度叠加到已有 `vz`，极向速度重写 `u/chi`，非 plasma 磁区置零。仿星器：没有与 VMEC 逻辑坐标配套的专用实现，建议保持 0 |
| `ineo_subtract_diamag` | integer | `0` | Subtract diamag. term from input vel. when reading NEO vel.；托卡马克：仅 `iread_neo=1,db!=0` 时从 NEO 环向速度扣除离子抗磁贡献。仿星器：随 `iread_neo` 保持 0 |

## 平衡与初始条件 / Equilibrium

选择/缩放初始平衡、外场、RMP、stellarator 场、basicj 模型以及初始扰动

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `itaylor` | integer | `0` | 选择预置初始条件/平衡：toroidal 几何中 1 常用于 GS，40/41 为 stellarator；slab/cylindrical 下有 Taylor、GEM、wave、RWM、basicJ 等测试平衡；主初始化分发开关；不同几何下选择 tilting cylinder、GS、VMEC/stellarator、fixed-q、basicJ、RWM、wave/diffusion tests 等分支 |
| `iupstream` | integer | `0` | 平衡与初始条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `magus` | real | `5.e-2` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iflip` | integer | `0` | 平衡与初始条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iflip_b` | integer | `0` | Reverse equilibrium toroidal field |
| `iflip_j` | integer | `0` | Reverse equilibrium toroidal current |
| `iflip_v` | integer | `0` | Reverse equilibrium toroidal velocity |
| `iflip_z` | integer | `0` | 平衡与初始条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `icsym` | integer | `0` | 平衡与初始条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `bzero` | real | `1.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `bx0` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `vzero` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `phizero` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `verzero` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `v0_cyl` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `v1_cyl` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `idevice` | integer | `0` | -1 读 coil.dat/current.dat；0 generic；1 CDX-U；2 NSTX；3 ITER；4 DIII-D（按文档） |
| `iwave` | integer | `0` | 平衡与初始条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `eps` | real | `0.01` | Magnitude of initial perturbations* |
| `maxn` | integer | `200` | 平衡与初始条件相关上限参数，用于限制迭代、场量、系数或网格/时间步控制范围 |
| `irmp` | integer | `0` | 1: Apply nonaxisym. fields throughout plasma； 2: Apply mpol/ntor vacuum fields (itor=0 only)；1 在等离子体内应用非轴对称 RMP/error field；2 仅边界应用真空 mpol/ntor 场。常配合 `type_ext_field`、RMP 文件和 `ntor` |
| `rmp_atten` | real | `0.` | Additional exponential decay of RMP field from r=1 for irmp=2 |
| `tf_tilt` | real | `0.` | Angle of TF from vertical (in degrees) |
| `tf_tilt_angle` | real | `0.` | Axis of rotation for TF tilt (in degrees) |
| `tf_shift` | real | `0.` | Horizontal shift of TF coil |
| `tf_shift_angle` | real | `0.` | Direction of TF shift (in degrees) |
| `pf_tilt` | real array | `0.` | Angle of PF from vertical (in degrees)；数组长度/上限：2000 |
| `pf_tilt_angle` | real array | `0.` | Axis of rotation for PF tilt (in degrees)；数组长度/上限：2000 |
| `pf_shift` | real array | `0.` | Horizontal shift of PF coil；数组长度/上限：2000 |
| `pf_shift_angle` | real array | `0.` | Direction of PF shift (in degrees)；数组长度/上限：2000 |
| `iread_ext_field` | integer | `0` | 1: Read external field |
| `isample_ext_field` | integer | `1` | Factor to down-sample external field data toroidally |
| `isample_ext_field_pol` | integer | `1` | Factor to down-sample external field data poloidally |
| `scale_ext_field` | real | `1.` | Factor to scale external field |
| `shift_ext_field` | real array | `0.` | Toroidal shift (in deg) of external fields；数组长度/上限：8 |
| `type_ext_field` | integer | `-1` | type of external field file；-1 默认；0 tokamak RMP/error field；1 free-boundary stellarator FIELDLINES/MGRID total field；2 stellarator total+external subtraction；`<=0` 用 tokamak RMP/error-field 分支，`=1/2` 用 stellarator/free-boundary 场文件，`=3` 从电流计算外场 |
| `file_ext_field` | character(len=256) | `error_field` | name of external field file；stellarator/free-boundary 场文件名，默认 `error_field`；支持 fieldlines/mgrid 前缀 |
| `file_total_field` | character(len=256) | `total_field` | name of total field file for ST；stellarator total field 文件名，默认 `total_field`；支持 fieldlines/mgrid 前缀 |
| `beta` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ln` | real | `0.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `elongation` | real | `1.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `basicj_nu` | real | `1.` | Exponent in basicj equilibrium |
| `basicj_j0` | real | `1.` | On-axis current density in basicj equilibrium |
| `basicj_q0` | real | `0.` | On-axis safety factor in basicj equilibrium (supersedes basicj_j0) |
| `basicj_qa` | real | `0.` | Edge safety factor in basicj equilibrium (supersedes basicj_nu) |
| `basicj_voff` | real | `1.` | Radial extent of flat toroidal rotation in basicj equilibrium |
| `basicj_vdelt` | real | `1.` | Width of velocity drop-off, as fraction of ln, in basicj equilibrium |
| `basicj_dexp` | real | `1.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `basicj_dvac` | real | `1.` | 平衡与初始条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ibasicj_solvep` | integer | `0` | 0: Uniform pressure, solve for F. 1: Uniform F, solve for pressure |

## Grad-Shafranov 求解器 / Grad-Shafranov Solver

控制 GS 迭代、轴/限制器/X 点、压力/电流/旋转/密度剖面及反馈参数

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `inumgs` | integer | `0` | Grad-Shafranov 求解器相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `igs` | integer | `80` | Grad-Shafranov 求解器相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `igs_pp_ffp_rescale` | integer | `0` | Rescale p' and FF' to match p and F |
| `igs_extend_p` | integer | `0` | Extend p past Psi=1 using ne and Te profiles |
| `igs_extend_diamag` | integer | `1` | Extend diamagnetic rotation Psi=1 |
| `igs_start_xpoint_search` | integer | `0` | Number of GS its. before searching for xpoint |
| `igs_forcefree_lcfs` | integer | `-1` | Ensure that GS solution is force-free at LCFS |
| `nv1equ` | integer | `0` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `igs_feedfac` | integer | `1` | Grad-Shafranov 求解器相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `eta_gs` | real | `1e3` | Factor for smoothing nonaxisymmetries in psi in GS solve |
| `tcuro` | real | `1.` | Total current in initial current filament |
| `xmag` | real | `1.` | R-coordinate of initial current filament |
| `zmag` | real | `0.` | Z-coordinate of initial current filament |
| `xmag0` | real | `0.` | Target R-coordinate of magnetic axis for feedback |
| `zmag0` | real | `0.` | Target Z-coordinate of magnetic axis for feedback |
| `xlim` | real | `0.` | R-coordinate of limiter #1 |
| `zlim` | real | `0.` | Z-coordinate of limiter #1 |
| `xlim2` | real | `0.` | R-coordinate of limiter #2 |
| `zlim2` | real | `0.` | Z-coordinate of limiter #2 |
| `rzero` | real | `-1.` | -1 表示校验后自动设置：toroidal 几何取 `xzero`，否则取 1；`rzero=-1` 时，toroidal 几何取 `xzero`，其它几何取 1；若最终 `rzero<=0` 只给 warning |
| `psifrac` | real | `1.` | Fraction of poloidal flux from psimin to psibound used for the mesh |
| `libetap` | real | `1.2` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `p0` | real | `0.01` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `pi0` | real | `0.005` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `p1` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `p2` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `pedge` | real | `0.` | Pressure outside separatrix (ignore if <= 0) |
| `tedge` | real | `0.` | Electron temperature outside separatrix (ignore if <= 0) |
| `tiedge` | real | `0.` | Outermost ion temperature (ignore if <= 0) |
| `expn` | real | `0.` | Density profile = p^expn |
| `q0` | real | `1.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `sigma0` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `djdpsi` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `th_gs` | real | `0.8` | Implicitness of GS Picard iterations |
| `tol_gs` | real | `1.e-8` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `psiscale` | real | `1.` | Grad-Shafranov 求解器相关乘性系数，用于缩放对应物理量、剖面、源项或数值模型强度 |
| `pscale` | real | `1.` | Factor multiplying pressure profile |
| `bscale` | real | `1.` | Factor multiplying toroidal field profile |
| `batemanscale` | real | `1.` | Bateman scaling factor for TF (keeping current density fixed) |
| `bpscale` | real | `1.` | Factor multiplying F' (keeping F0 constant) |
| `iread_bscale` | integer | `0` | 1: read profile_bscale for factor to scale F |
| `iread_pscale` | integer | `0` | 1: read profile_pscale for factor to scale p and p' |
| `vscale` | real | `1.` | Factor multiplying toroidal rotation profile |
| `gs_vertical_feedback` | real array | `0.` | Proportional feedback of each coil to vertical displacements；数组长度/上限：2000 |
| `gs_radial_feedback` | real array | `0.` | Proportional feedback of each coil to radial displacements；数组长度/上限：2000 |
| `gs_vertical_feedback_i` | real array | `0.` | Integral feedback of each coil to vertical displacements；数组长度/上限：2000 |
| `gs_radial_feedback_i` | real array | `0.` | Integral feedback of each coil to radial displacements；数组长度/上限：2000 |
| `gs_vertical_feedback_x` | real array | `0.` | Proportional feedback of each coil to vertical displacements；数组长度/上限：2000 |
| `gs_radial_feedback_x` | real array | `0.` | Proportional feedback of each coil to radial displacements；数组长度/上限：2000 |
| `gs_vertical_feedback_x_i` | real array | `0.` | Integral feedback of each coil to vertical displacements；数组长度/上限：2000 |
| `gs_radial_feedback_x_i` | real array | `0.` | Integral feedback of each coil to radial displacements；数组长度/上限：2000 |
| `irot` | integer | `0` | Include toroidal rotation |
| `iscale_rot_by_p` | integer | `1` | 0: omega^2 = 2.*p0*(alphai * Psi^i)/n0； 1: omega^2 = 2.*(alphai * Psi^i)/n0, 2: omega^2 = 2.*(alphai * Psi^i), alphai = a0 + a1*exp(-((psii-a2)/a3)**2) |
| `alpha0` | real | `0.` | Constant term in analytic rotation profile |
| `alpha1` | real | `0.` | Linear term in analytic rotation profile |
| `alpha2` | real | `0.` | Quadratic term in analytic rotation profile |
| `alpha3` | real | `0.` | Cubic term in analytic rotation profile |
| `idenfunc` | integer | `0` | Grad-Shafranov 求解器相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `den_edge` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `den0` | real | `1.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `dendelt` | real | `0.1` | Grad-Shafranov 求解器相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `denoff` | real | `1.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `divertors` | integer | `0` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `xdiv` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `zdiv` | real | `0.` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `divcur` | real | `0.1` | Grad-Shafranov 求解器相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `xnull` | real | `0.` | Guess for R-coordinate of active x-point |
| `znull` | real | `0.` | Guess for Z-coordinate of axtive x-point |
| `mod_null_rs` | integer | `0` | if 1, you can modify xnull,znull at restart |
| `xnull2` | real | `0.` | Guess for R-coordinate of inactive x-point |
| `znull2` | real | `0.` | Guess for Z-coordinate of inaxtive x-point |
| `mod_null_rs2` | integer | `0` | if 1, you can modify xnull2,znul2l at restart |
| `gs_pf_psi_width` | real | `0.` | Width of psi smoothing into private flux region |
| `xnull0` | real | `0.` | Target R-coordinate of x-point for feedback |
| `znull0` | real | `0.` | Target Z-coordinate of x-point for feedback |
| `adapt_qs` | real array | `0.` | Safety factor values to pack around；数组长度/上限：32 |
| `adapt_zlow` | real | `0.` | Z-coordinate below which SOL adaptation is coarse |
| `adapt_zup` | real | `0.` | Z-coordinate above which SOL adaptation is coarse |

## 模型选项 / Model Options

控制求解的 MHD 方程组、线性/非线性、two-fluid、bootstrap、runaway、温度/压力模型等

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `numvar` | integer | `3` | 1: 2-Field; 2: 4-Field; 3: 6-Field；1: 2-field；2: 4-field/reduced MHD；3: 6-field/compressible MHD |
| `linear` | integer | `0` | 1: Use linearized equations；0 非线性；1 线性化方程。2D 非线性通常需 RL=1；线性/complex 需 COM=1 且 `nplanes=1` |
| `eqsubtract` | integer | `0` | 1: Subtract equilibrium fields；线性模拟会在校验阶段强制置 1；非线性时设 1 表示从方程中扣除平衡场 |
| `extsubtract` | integer | `0` | 1: Subtract fields from non-axisymmetric coils |
| `icsubtract` | integer | `0` | 1: Subtract fields from poloidal field coils |
| `idens` | integer | `0` | 1: Include density equation |
| `ipres` | integer | `0` | 1: Include total pressure equation |
| `ipressplit` | integer | `0` | 1: Separate pressure solves from field solves；仅 `isplitstep=1` 且 `numvar=3` 时允许；把压力/温度求解从场求解分离 |
| `itemp` | integer | `0` | 1: Advance Temperatures rather than Pressures；1 时推进温度而不是压力；要求 `ipressplit=1`，且 `z_ion` 必须为 1 |
| `iadiabat` | integer | `1` | 1: Correct itemp=1 for time-varying density |
| `gyro` | integer | `0` | 1: Include Braginskii gyroviscosity |
| `igauge` | integer | `0` | 模型选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inertia` | integer | `1` | 1: Include V.Grad(V) terms |
| `itwofluid` | integer | `1` | 1: -electron 2F, 2: ion 2F |
| `ibootstrap` | integer | `0` | 模型选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `irunaway` | integer | `0` | 模型选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `cre` | integer | `0` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ra_cyc` | integer | `1` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `radiff` | real | `0.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `rjra` | real | `1.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ra_characteristics` | integer | `0` | 1: Use the method of characteristics to advance the RE advection equation |
| `bzsign` | real | `0.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `imp_bf` | integer | `0` | 1: Include implicit equation for f |
| `imp_temp` | integer | `0` | 1: Include implicit equation for temperature |
| `nosig` | integer | `0` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `itor` | integer | `0` | 1: Use toroidal geometry |
| `iohmic_heating` | integer | `1` | 1: Include Ohmic heating |
| `irad_heating` | integer | `1` | 1: Include radiation heat source |
| `gravr` | real | `0.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `gravz` | real | `0.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `istatic` | integer | `0` | 1: Do not advance velocity fields |
| `iestatic` | integer | `0` | 1: Do not advance magnetic fields |
| `chiiner` | real | `1.` | 模型选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ieq_bdotgradt` | integer | `1` | 模型选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iwall_is_limiter` | integer | `1` | 1 = Wall acts as limiter |
| `no_vdg_T` | integer | `0` | 1: do not include V dot grad T in Temp equation (debug) |
| `ibootstrap_model` | integer | `0` | 1: J_BS = alpha F <p,psi> B；选择 bootstrap closure：1/3 为 Sauter & Angioni，2/4 为 Redl，5 为 constant-Lambda 分支 |
| `bootstrap_alpha` | real | `0.` | alpha parameter in bootstrap current model |
| `ibootstrap_regular` | real | `1e-8` | Regularization parameter Default=1e-8 |
| `kinetic` | integer | `0` | 1: Use kinetic PIC; 2: CGL incompressible; 3: CGL；1: kinetic PIC hot ion pressure；2: incompressible CGL；3: full CGL。2/3 要求 linear=1,isplitstep=0,ipres=1,itemp=0,ipressplit=0 |

## 输运系数 / Transport Coefficients

粘性、电阻率、热导、粒子扩散等输运模型参数；若使用函数型模型，开关参数决定下面系数的解释

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `ivisfunc` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `amuoff` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amudelt` | real | `0.` | 输运系数相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `amuoff2` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amudelt2` | real | `0.` | 输运系数相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `amu` | real | `0.` | Isotropic viscosity |
| `amuc` | real | `0.` | Compressional viscosity |
| `amue` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amupar` | real | `0.` | Parallel viscosity |
| `amu_edge` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amu_wall` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amu_wall_off` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `amu_wall_delt` | real | `0.1` | 输运系数相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `iresfunc` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `etaoff` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `etadelt` | real | `0.` | 输运系数相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `etar` | real | `0.` | Isotropic resistivity |
| `eta0` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `eta_fac` | real | `1.` | Uniform resistivity multiplier |
| `eta_mod` | integer | `0` | 1 = remove d/dphi terms in resistivity |
| `eta_te_offset` | real | `0.` | Offset in Te when calculating eta |
| `ikprad_te_offset` | integer | `0` | If 1, eta_te_offset also applied to kprad |
| `eta_max` | real | `0.` | Maximum value of resistivity in the plasma region；若 <=0，校验阶段置为 `eta_vac`；`eta_max<=0` 时改为 `eta_vac` |
| `eta_min` | real | `0.` | Minimum value of resistivity in the plasma region；若 <=0，校验阶段置为 0；`eta_min<=0` 时改为 0 |
| `ikappafunc` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ikapparfunc` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ikapscale` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ikappar_ni` | integer | `1` | Include 1/n terms in parallel heat flux |
| `kappaoff` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `kappadelt` | real | `0.` | 输运系数相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `kappat` | real | `0.` | Isotropic thermal conductivity |
| `kappa0` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `kappar` | real | `0.` | Parallel thermal conductivity |
| `kappari_fac` | real | `1.` | Ion parallel thermal conductivity factor |
| `tcrit` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `k_fac` | real | `1.` | multiplies toroidal field in denominator of PTC |
| `kappax` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `kappah` | real | `0.` | 输运系数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `kappag` | real | `0.` | Thermal diffusion proportional to pressure gradient |
| `kappaf` | real | `1.` | Factor to multiply kappa when grad(p) < gradp_crit |
| `gradp_crit` | real | `0.` | Critical pressure gradient in kappag/kappaf models |
| `kappa_max` | real | `0.` | Maximum value of kappa in the plasma region；若 <=0，校验阶段置为 `kappar`；`kappa_max<=0` 时改为 `kappar` |
| `kappar_max` | real | `0.` | Maximum value of kappa in the plasma region；若 <=0，校验阶段置为 `kappar`；`kappar_max<=0` 时改为 `kappar` |
| `kappar_min` | real | `0.` | Maximum value of kappa in the plasma region；若 <=0，校验阶段置为 `kappar`；`kappar_min<=0` 时改为 `kappar` |
| `temin_qd` | real | `0.` | Min. Temp. used in Equipartition term for ipres=1 |
| `kappai_fac` | real | `1.` | Factor to multiply kappa when evaluating ion perp. thermal diffusivity |
| `idenmfunc` | integer | `0` | 输运系数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `denm` | real | `0.` | Density diffusion coefficient |
| `denmt` | real | `0.` | Temperature dependent density diffusion coefficient |
| `denmmin` | real | `0.` | Minimum density diffusion coefficient |
| `denmmax` | real | `1.e6` | Maximum density diffusion coefficient |

## 超扩散 / Hyper Diffusivity

磁场、压力和速度方程中的超扩散/平滑系数及其缩放方式

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `deex` | real | `1.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `hyper` | real | `0.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `hyperc` | real | `0.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `hyperi` | real | `0.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `hyperp` | real | `0.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `hyperv` | real | `0.` | 超扩散相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ihypdx` | integer | `0` | 超扩散相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ihypeta` | integer | `1` | 超扩散相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ihypkappa` | integer | `1` | 超扩散相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `imp_hyper` | integer | `0` | 1: implicit hyper-resistivity in psi equation |

## 边界条件 / Boundary Conditions

场、压力/温度/密度、速度和电流在计算边界上的约束

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `isurface` | integer | `1` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `icurv` | integer | `2` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `nonrect` | integer | `1` | 边界条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ifixedb` | integer | `0` | 1: Force psi=0 on boundary |
| `com_bc` | integer | `0` | 边界条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `vor_bc` | integer | `0` | 边界条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iconst_p` | integer | `1` | 1: Hold pressure constant on boundary |
| `iconst_n` | integer | `1` | 1: Hold density constant on boundary |
| `iconst_t` | integer | `1` | 1: Hold temperature constant on boundary |
| `iconst_bn` | integer | `1` | 1: Hold normal field constant on boundary |
| `iconst_bz` | integer | `0` | 1: Hold toroidal field constant on boundary |
| `inograd_p` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inograd_t` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inograd_n` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inonormalflow` | integer | `1` | 1: No-normal-flow boundary condition |
| `inoslip_pol` | integer | `1` | 1: No-slip boundary condition on pol. velocity |
| `inoslip_tor` | integer | `1` | 1: No-slip boundary condition on tor. velocity |
| `inostress_tor` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inocurrent_pol` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inocurrent_tor` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `inocurrent_norm` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ifbound` | integer | `-1` | Boundary condition on 'f' field. 1 = Dirichlet, 2 = Neumann；-1 表示校验后按编译版本设置：complex 为 2，real 为 1；`ifbound=-1` 时，complex 版本默认 2，real 版本默认 1 |
| `iconstflux` | integer | `0` | 边界条件相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iper` | integer | `0` | 1: Periodic boundary condition in R direction |
| `jper` | integer | `0` | 1: Preiodic boundary condition in Z direction |
| `tebound` | real | `-1.` | 边界条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `tibound` | real | `-1.` | 边界条件相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |

## 电阻壁/真空/导体区 / Resistive Wall

真空、导体壁、多区域、wall break、RE killer coil 等电阻参数

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `eta_wall` | real | `1e-3` | Resistivity of conducting wall region |
| `eta_wallRZ` | real | `-1.` | Resistivity of conducting wall region；-1 表示校验后取 `eta_wall`；`eta_wallRZ<0` 时改为 `eta_wall` |
| `eta_vac` | real | `1.` | Resistivity of vacuum region |
| `iwall_breaks` | integer | `0` | Number of wall break regions |
| `eta_break` | real array | `1.` | Resistivity of wall break；数组长度/上限：20 |
| `wall_break_xmin` | real array | `0.` | Minimum x coordinate for wall break；数组长度/上限：20 |
| `wall_break_xmax` | real array | `0.` | Maximum x coordinate for wall break；数组长度/上限：20 |
| `wall_break_zmin` | real array | `0.` | Minimum z coordinate for wall break；数组长度/上限：20 |
| `wall_break_zmax` | real array | `0.` | Maximum z coordinate for wall break；数组长度/上限：20 |
| `wall_break_phimin` | real array | `0.` | Minimum phi coordinate for wall break；数组长度/上限：20 |
| `wall_break_phimax` | real array | `0.` | Maximum phi coordinate for wall break；数组长度/上限：20 |
| `iwall_regions` | integer | `0` | Number of resistive wall regions |
| `wall_region_eta` | real array | `1e-3` | Resistivity of each wall region；数组长度/上限：20 |
| `wall_region_etaRZ` | real array | `-1.` | Poloidal Resistivity of each wall region；-1 表示校验后逐区域取对应 `wall_region_eta(i)`；每个 `wall_region_etaRZ(i)<0` 时改为对应 `wall_region_eta(i)`；数组长度/上限：20 |
| `eta_zone` | real array | `0.` | Resistivity of mesh zone；托卡马克：为 `zone_type(i)=2` 的导体 zone 指定标量电阻率，正值优先于全局 `eta_wall`；适合显式第一壁/导体区域。仿星器：数值优先级相同，但只有用户事先设计了与 VMEC/bloat 映射后物理位置一致的导体 zone 才有物理意义；数组长度/上限：100 |
| `etaRZ_zone` | real array | `0.` | Poloidal resistivity of mesh zone；托卡马克：为导体 zone 指定极向电阻率，正值优先于 `eta_zone`，否则回退到全局 `eta_wallRZ`。仿星器：用法相同，但程序不会检查该 zone 是否真的对应物理导体壁；数组长度/上限：100 |
| `wall_region_filename` | character(len=256) array | `""` | Resistivity of each wall region；字符数组；每个 wall region 轮廓点文件名；数组长度/上限：20 |
| `eta_rekc` | real | `0.` | Resistivity of runaway-electron killer coil (REKC) |
| `ntor_rekc` | integer | `0` | Toroidal mode number of REKC |
| `mpol_rekc` | integer | `0` | Poloidal mode number of REKC |
| `isym_rekc` | integer | `0` | if nonzero, a double helix |
| `phi_rekc` | real | `0.` | Toroidal angle of fixed point of REKC |
| `theta_rekc` | real | `0.` | Poloidal angle of fixed point of REKC |
| `sigma_rekc` | real | `0.` | Angular half-width of REKC |
| `rzero_rekc` | real | `0.` | R0 for computing theta of REKC |
| `zzero_rekc` | real | `0.` | Z0 for computing theta of REKC |

## 时间推进 / Time Step

时间积分、分裂/非分裂推进、可变时间步、矩阵/预条件器重算及线性增长率停止条件

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `ntimemax` | integer | `20` | Total number of timesteps |
| `integrator` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `isplitstep` | integer | `1` | 0: Unsplit time step; 1: Split time step |
| `iteratephi` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `imp_mod` | integer | `1` | Type of split step. 0: Standard; 1: Caramana；当前默认 1。0: standard/theta implicit；1: Caramana split-step 形式；`isplitstep=0` 时校验阶段强制 `imp_mod=0` |
| `caramana_fac` | real | `1.` | Coefficient for the explicit term in Caramana method. 1: Caramana; 0: implicit |
| `idiff` | integer | `0` | only solve for difference in B,p |
| `idifv` | integer | `0` | only solve for difference in v |
| `irecalc_eta` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iconst_eta` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `itime_independent` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `thimp` | real | `0.5` | Implicitness of timestep (.5<thimp<1) |
| `thimpsm` | real | `1.` | 时间推进相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `harned_mikic` | real | `0.` | 时间推进相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `isources` | integer | `0` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `nskip` | integer | `1` | 时间推进相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `pskip` | integer | `0` | 当前默认 0；控制预条件器重算/复用相关周期 |
| `iskippc` | integer | `1` | 时间推进相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `dt` | real | `0.1` | Size of time step |
| `ddt` | real | `0.` | 时间推进参数，用于设置时间步长及其允许变化范围 |
| `frequency` | real | `0.` | Frequency in time-independent calculations |
| `gamma_gr_stop` | integer | `0` | Stop linear simulation when growth rate gamma is converged |
| `nt_gamma_gr` | integer | `10` | Number of time steps considered for gamma convergence check |
| `gamma_gr_stop_std` | real | `0.01` | Standard deviation under which gamma is considered converged |
| `dtmin` | real | `4.0` | minimum time step |
| `dtmax` | real | `40.` | maximum time step |
| `dtkecrit` | real | `0.0` | ekin limit on timestep |
| `dtfrac` | real | `0.1` | fractional change of time step |
| `max_repeat` | integer | `1` | maximum number of times a time step can be attempted |
| `ksp_max` | integer | `10000` | maximum number of ksp iterations without repeating time step |
| `ksp_min` | integer | `500` | time step is increased if max ksp iterations is less than this |
| `ksp_warn` | integer | `1000` | time step is reduced if max ksp iterations exceeds this |

## 数值选项 / Numerical Options

积分点数、守恒/规整化、物理量 floor、线性模拟重标定等数值控制

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `jadv` | integer | `1` | Use Del*(psi) eqn. instead of psi eqn.；1 使用环向电流密度方程代替极向磁通方程 |
| `int_pts_main` | integer | `25` | 数值选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `int_pts_aux` | integer | `25` | 数值选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `int_pts_diag` | integer | `25` | 数值选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `int_pts_tor` | integer | `5` | 数值选项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `max_ke` | real | `1.` | Value of ke at which linear sims are rescaled；(ignore if 0) |
| `equilibrate` | integer | `0` | 数值选项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `regular` | real | `0.` | 数值选项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iset_pe_floor` | integer | `0` | 1: Do not let pe drop below pe_floor |
| `pe_floor` | real | `0.` | Minimum allowed value for pe when iset_pe_floor=1 |
| `iset_pi_floor` | integer | `0` | 1: Do not let pi drop below pi_floor |
| `pi_floor` | real | `0.` | Minimum allowed value for pi when iset_pi_floor=1 |
| `iset_ne_floor` | integer | `0` | 1: Do not let ne drop below ne_floor |
| `ne_floor` | real | `0.` | Minimum allowed value for ne when iset_ne_floor=1 |
| `iset_ni_floor` | integer | `0` | 1: Do not let ni drop below ni_floor |
| `ni_floor` | real | `0.` | Minimum allowed value for ni when iset_ni_floor=1 |
| `iset_te_floor` | integer | `0` | 1: Do not let Te drop below te_floor |
| `te_floor` | real | `0.` | Minimum allowed value for Te when iset_te_floor=1 |
| `iset_ti_floor` | integer | `0` | 1: Do not let Ti drop below ti_floor |
| `ti_floor` | real | `0.` | Minimum allowed value for Ti when iset_ti_floor=1 |
| `iprecompute_metric` | integer | `0` | 1: precompute full metric tensor |

## 线性求解器 / Solver

M3D-C1 内部线性求解器通用控制

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `solver_tol` | real | `1e-9` | solver tolerance |
| `solver_type` | integer | `0` | Solver type |
| `num_iter` | integer | `100` | Maximum number of iterations |
| `isolve_with_guess` | integer | `0` | newsolve with nonzero initial guess |

## Trilinos 选项 / Trilinos Options

Trilinos 编译/运行路径下的 Krylov 与预条件器选项

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `krylov_solver` | character(len=50) | `gmres` | Krylov solver |
| `preconditioner` | character(len=50) | `dom_decomp` | Preconditioner |
| `sub_dom_solver` | character(len=50) | `ilu` | Subdomain solver in preconditioner |
| `subdomain_overlap` | integer | `1` | subdomain overlap |
| `graph_fill` | integer | `0` | graph fill level |
| `drop_tolerance` | real | `0.0` | ILU drop tolerance |
| `ilu_fill_level` | real | `1.0` | ILU fill level |
| `ilu_omega` | real | `1.0` | Relaxation parameter for rILU |
| `poly_ord` | integer | `1` | Polynomial order for certain preconditioners |

## 网格自适应 / Mesh Adaptation

SCOREC/SPR 网格自适应控制；部分参数仅在启用对应库/流程时有效

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `iadapt` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ispradapt` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `isprntime` | integer | `10` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `isprweight` | real | `0.1` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `isprmaxsize` | real | `0.05` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `isprrefinelevel` | integer | `1` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `isprcoarsenlevel` | integer | `-1` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_writevtk` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_writesmb` | integer | `1` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_useH1` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_removeEquiv` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `adapt_target_error` | real | `0.0001` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_ke` | real | `0.0` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iadapt_ntime` | integer | `0` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_max_node` | integer | `10000` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `adapt_control` | integer | `1` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iadapt_order_p` | real | `3.0` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iadaptFaceNumber` | integer | `-1` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iadapt_snap` | integer | `1` | 网格自适应相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `adapt_factor` | real | `1.` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_hmin` | real | `0.001` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_hmax` | real | `0.1` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_hmin_rel` | real | `0.5` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_hmax_rel` | real | `2.0` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_smooth` | real | `2./3. (约 0.6667)` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_psin_vacuum` | real | `-1.` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `adapt_psin_wall` | real | `-1.` | 网格自适应相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `iadapt_pack_rationals` | integer | `0` | Number of mode-rational surfaces to pack mesh around |
| `adapt_pack_factor` | real | `0.02` | Width of Lorentzian (in psi_N) for rational mesh packing |
| `adapt_coil_delta` | real | `0.` | Parameter for packing mesh around coil locations |
| `adapt_pellet_length` | real | `0.` | Length of pellet path to pack mesh along |
| `adapt_pellet_delta` | real | `0.` | Parameter for packing mesh along pellet path |

## 源项/汇项 / Sources/Sinks

回路电压/电流控制、pellet、束源、电流驱动、高斯热源、粒子源/汇、ionization 等

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `iheat_sink` | integer | `0` | 源项/汇项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `vloop` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `vloopRZ` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `tcur` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `vloop_freq` | real | `0.` | Loop voltage frequency |
| `tcuri` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `tcurf` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `tcur_t0` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `tcur_tw` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `control_p` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `control_i` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `control_d` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `control_type` | integer | `-1` | -1 不启用电流控制；0 旧算法；1 标准 PID，配合 `control_p/i/d` |
| `ipellet` | integer | `0` | 1 = include a gaussian pellet source；选择密度源分布；正值为持续源，负值用于初始扰动；双位数分布按 `Lor_vol` 数值归一化 |
| `irestart_pellet` | integer | `0` | 1 = read some pellet restart parameters from C1input；restart 时仍从 C1input 覆盖部分 pellet 参数，如 pellet_rate、pellet_var_tor、pellet_var、cloud_pel、pellet_mix、cauchy_fraction |
| `ipellet_z` | integer | `0` | Atomic number of pellet (0 = main ion species) |
| `iread_pellet` | integer | `0` | 1: read pellet info from pellet.dat；0 用标量 pellet_* 定义单 pellet；1 读 `pellet.dat`，每行一个 pellet，列为 r,phi,z,rate,var,var_tor,velr,velphi,velz,r_p,cloud_pel,pellet_mix,cauchy_fraction |
| `pellet_r` | real | `0.` | Initial radial position of the pellet |
| `pellet_phi` | real | `0.` | Initial toroidal position of the pellet |
| `pellet_z` | real | `0.` | Initial vertical position of the pellet |
| `pellet_rate` | real | `0.` | 源项/汇项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `pellet_var` | real | `1.` | 源项/汇项相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `pellet_var_tor` | real | `0.` | 读入后若 <=0 会自动补值：`ipellet=15` 用 `pellet_var/pellet_r`，其它分支用 `pellet_var` |
| `pellet_velr` | real | `0.` | Initial radial velocity of the pellet |
| `pellet_velphi` | real | `0.` | Initial toroidal velocity of the pellet |
| `pellet_velz` | real | `0.` | Initial vertical velocity of the pellet |
| `ipellet_abl` | integer | `0` | 1 = include an ablation model；选择 pellet ablation 模型；1/2 lithium，3 neon，43 carbon/Sergeev06。`ipellet_z=0` 时会由模型推断默认 Z |
| `ipellet_fixed_dep` | integer | `0` | 1 = use fixed input pellet_var when ipellet_abl=1 |
| `r_p` | real | `1.e-3` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `cloud_pel` | real | `1.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `pellet_mix` | real | `0.` | Molar fraction of deuterium in pellet |
| `temin_abl` | real | `0.` | Min. Temp. at which ablation turns on |
| `cauchy_fraction` | real | `0.` | For ipellet=14, fraction of distribution that is Cauchy, vs von Mises |
| `abl_fac` | real | `1.` | Factor multiplying calculated ablation rate |
| `ibeam` | integer | `0` | GE 1: Include neutral beam source |
| `beam_x` | real | `0.` | R-coordinate of beam center |
| `beam_z` | real | `0.` | Z-coordinate of beam center |
| `beam_v` | real | `1.e4` | Beam voltage (in volts) |
| `beam_rate` | real | `0.` | Ions/second deposited by beam |
| `beam_dr` | real | `0.1` | Dispersion of beam deposition |
| `beam_dv` | real | `100.` | Dispersion of beam voltage (in volts) |
| `beam_fracpar` | real | `1.0` | Cosine of beam angle relative to parallel |
| `icd_source` | integer | `0` | 1: Include current drive source |
| `J_0cd` | real | `0.` | amplitude of current drive |
| `R_0cd` | real | `0.` | R-coordinate of cd maximum |
| `Z_0cd` | real | `0.` | Z-coordinate of cd maximum |
| `W_cd` | real | `0.` | width of cd gaussian |
| `delta_cd` | real | `0.` | shift of cd gaussian |
| `ipforce` | integer | `0` | 1: Include Poloidal momentum source |
| `dforce` | real | `0.` | half-width of poloidal momentum source |
| `xforce` | real | `0.` | location [0,1] of poloidal momentum source |
| `nforce` | integer | `0` | exponent of (1-x) multiplying poloidal mom. source |
| `aforce` | real | `0.` | magnitude of poloidal momentum source |
| `igaussian_heat_source` | integer | `0` | Include gaussian heat source |
| `ghs_x` | real | `0.` | R coordinate of gaussian heat source |
| `ghs_z` | real | `0.` | Z coordinate of gaussian heat source |
| `ghs_phi` | real | `0.` | Phi coordinate of gaussian heat source |
| `ghs_rate` | real | `0.` | Amplitude of gaussian heat source |
| `ghs_var` | real | `1.` | Variance of gaussian heat source |
| `ghs_var_tor` | real | `0.` | Toroidal variance of gaussian heat source |
| `ionization` | integer | `0` | 源项/汇项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ionization_rate` | real | `0.` | 源项/汇项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `coolrate` | real | `0.` | 源项/汇项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `ionization_temp` | real | `0.01` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `ionization_depth` | real | `0.01` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `isink` | integer | `0` | 源项/汇项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `sink1_x` | real | `0.` | 源项/汇项相关几何位置参数，用于给定 R/Z/phi 等空间坐标 |
| `sink1_z` | real | `0.` | 源项/汇项相关几何位置参数，用于给定 R/Z/phi 等空间坐标 |
| `sink1_rate` | real | `0.` | 源项/汇项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `sink1_var` | real | `1.` | 源项/汇项相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `sink2_x` | real | `0.` | 源项/汇项相关几何位置参数，用于给定 R/Z/phi 等空间坐标 |
| `sink2_z` | real | `0.` | 源项/汇项相关几何位置参数，用于给定 R/Z/phi 等空间坐标 |
| `sink2_rate` | real | `0.` | 源项/汇项相关速率/源强参数，表示注入、损失、冷却、控制或演化的强度 |
| `sink2_var` | real | `1.` | 源项/汇项相关宽度/方差参数，用于定义剖面过渡层、Gaussian 分布或数值平滑尺度 |
| `iarc_source` | integer | `0` | 源项/汇项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `arc_source_alpha` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `arc_source_eta` | real | `0.01` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `idenfloor` | integer | `0` | 源项/汇项相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `alphadenfloor` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `n_target` | real | `1.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `n_control_p` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `n_control_i` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `n_control_d` | real | `0.` | 源项/汇项相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `n_control_type` | integer | `-1` | -1 不启用密度控制；0 旧算法；1 标准 PID，配合 `n_control_p/i/d` |

## PRAD 简单辐射模型 / PRAD Options

简单单杂质辐射模型

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `iprad` | integer | `0` | 1: Teng's PRad module with one impurity species；1 启用 Teng PRAD 单杂质辐射模型；当前 PRAD 表中 C/Ar/Fe 常用 |
| `prad_z` | integer | `1` | Z of impurity species in PRad module；PRAD 杂质电荷数；程序警告只实现 6、18、26 |
| `prad_fz` | real | `1.` | Density of impurity species in PRad module, as fraction of ne |
| `iread_prad` | integer | `0` | 1: Read impurity density from profile_nz in units of 10^20 / m^3 |

## KPRAD 辐射/杂质模型 / KPRAD Options

KPRAD 杂质电离/复合/辐射与中性粒子演化控制

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `ikprad` | integer | `0` | 1: KPRad module with one impurity species；0 关闭；1 使用 KPRAD；-1 需 USEADAS 编译，使用 ADAS 数据；0 关闭；1 使用内置 KPRAD polynomial fit；-1 在 `USEADAS` 编译时读 ADAS ADF11，否则报错 |
| `kprad_z` | integer | `1` | Z of impurity species in KPRad module |
| `ikprad_evolve_neutrals` | integer | `0` | Model for advection/diffusion of neutrals；0 中性粒子不对流不扩散；1 推荐：同其它电荷态对流扩散；2 只扩散不对流 |
| `kprad_fz` | real | `0.` | Density of neutral impurity species in KPRad module, as fraction of ne |
| `kprad_nz` | real | `0.` | Density of neutral impurity species in KPRAD module |
| `iread_lp_source` | integer | `0` | Read source from Lagrangian Particle code |
| `ikprad_min_option` | integer | `1` | Control behavior for KPRAD minimum density & temperature；1 低 ne/Te 时无辐射/电离/复合；2 推荐：允许复合但无辐射/电离；3 按 subcycling 中 ne/Te 判断无辐射/电离/复合 |
| `kprad_nemin` | real | `1e-12` | Minimum elec. density for KPRAD evolution |
| `kprad_temin` | real | `2e-7` | Minimum elec. temperature for KPRAD evolution |
| `ikprad_max_dt` | integer | `0` | Use maximum value of dt for KPRAD ionization；0 用 MHD dt；1 推荐用 dt/(kprad_z+1)；也可配合 `kprad_max_dt` 显式限制 |
| `kprad_max_dt` | real | `-1.` | Specify maximum value of dt for KPRAD ionization |
| `ikprad_evolve_internal` | integer | `0` | Internally evolve ne and Te within KPRAD ionization |
| `kprad_n0_denm_fac` | real | `1.` | Scaling factor for neutral impurity diffusion |
| `adas_adf11` | character(len=256) | `""` | Path to ADAS folder with ADF11 data；仅在满足条件编译 `ifdef USEADAS` 时可用 |

## 粒子模拟选项 / Particle Simulation Options

仅在 USEPARTICLES 编译时注册

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `kinetic_fast_ion` | integer | `1` | 1: Enable fast ion PIC；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `kinetic_thermal_ion` | integer | `0` | 1: Enable thermal ion PIC and density coupling between MHD and PIC；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `igyroaverage` | integer | `0` | 1: Enable gyro-averaging for PIC simulation；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `particle_linear` | integer | `-1` | 1: Solve linear delta-f equation. 0: Include nonlinear terms in delta-f；`particle_linear=-1` 时改为当前 `linear`；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `particle_substeps` | integer | `40` | Number of substeps for particle pushing in one subcycle；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `particle_subcycles` | integer | `1` | Number of subcycles for particle pushing in one MHD timestep；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `particle_couple` | integer | `0` | -1: No coupling (test particle). 0: Pressure coupling. 1: Current coupling；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `particle_nodelete` | integer | `0` | Do not call delete_particle, keep particles' order；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `iconst_f0` | integer | `0` | Use a constant f0 for delta-f equation；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `ifullf` | integer | `0` | Do full-f simulation；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `fast_ion_mass` | real | `0.` | Fast ion mass (in units of m_p)；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `fast_ion_z` | real | `0.` | Zeff of fast ion；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `fast_ion_dist` | integer | `1` | Type of fast ion distribution function. 0: Read 3D distribution from file. 1: Maxwellian. 2. slowing-down.；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `fast_ion_max_energy` | real | `1000.` | Maximum energy of fast ion for slowing-down distribution；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `num_par_max` | integer | `4000000` | Maximum number of particles；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `num_par_scale` | real array | `1.` | Scaling factor for particle number initialization；仅在满足条件编译 `ifdef USEPARTICLES` 时可用；数组长度/上限：2 |
| `kinetic_nrmfac_scale` | real array | `1.` | Scaling factor of the normalization term in particle phase space integration；仅在满足条件编译 `ifdef USEPARTICLES` 时可用；数组长度/上限：2 |
| `ikinetic_vpar` | integer | `0` | 1: Synchronize particle parallel flow to MHD；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `kinetic_rhomax` | real | `1.` | Maximum rho for kinetic particle；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `vpar_reduce` | real | `0.` | Factor of parallel flow reduction for every timestep；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `idiamagnetic_advection` | integer | `0` | 1: Enable diamagnetic velocity advection term in momentum equation；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `imode_filter` | integer | `0` | Number of toroidal mode to be filtered；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `mode_filter_ntor` | integer array | `0` | Toroidal mode number to be filtered；仅在满足条件编译 `ifdef USEPARTICLES` 时可用；数组长度/上限：100 |
| `smooth_par` | real | `1.e-8` | Smoothing factor for particle pressure；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |
| `smooth_dens_parallel` | real | `0.` | Smoothing factor for electron density in parallel direction, used for calculating parallel electric field；仅在满足条件编译 `ifdef USEPARTICLES` 时可用 |

## 诊断 / Diagnostics

X-ray、磁探针、磁通环等诊断的几何参数

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `xray_detector_enabled` | integer | `0` | 1: enable xray detector |
| `xray_r0` | real | `0.` | R coordinate of xray detector |
| `xray_phi0` | real | `0.` | Phi coordinate of xray detector |
| `xray_z0` | real | `0.` | Z coordinate of xray detector |
| `xray_theta` | real | `0.` | Angle of xray detector chord (degrees) |
| `xray_sigma` | real | `1.` | Spread of xray detector chord (degrees) |
| `imag_probes` | integer | `0` | Number of magnetic probes；磁探针数量；对应数组用 `mag_probe_x(i)` 等一基索引给出 |
| `mag_probe_x` | real array | `0.` | X-coordinate of magnetic probes；数组长度/上限：100 |
| `mag_probe_phi` | real array | `0.` | Phi-coordinate of magnetic probes；数组长度/上限：100 |
| `mag_probe_z` | real array | `0.` | Z-coordinate of magnetic probes；数组长度/上限：100 |
| `mag_probe_nx` | real array | `0.` | X-component of magnetic probe normal；数组长度/上限：100 |
| `mag_probe_nphi` | real array | `0.` | Phi-component of magnetic probe normal；数组长度/上限：100 |
| `mag_probe_nz` | real array | `0.` | Z-component of magnetic probe normal；数组长度/上限：100 |
| `iflux_loops` | integer | `0` | Number of flux loops；磁通环数量；对应数组用 `flux_loop_x(i)`、`flux_loop_z(i)` 一基索引给出 |
| `flux_loop_x` | real array | `0.` | X-coordinate of flux loop；数组长度/上限：100 |
| `flux_loop_z` | real array | `0.` | Z-coordinate of flux loop；数组长度/上限：100 |
| `ifixed_temax` | integer | `0` | if nonzero, evaluate temax at xmag0,zmag0 |

## 输出与重启 / Output

HDF5/标量/辅助变量输出、重启读写、调试打印和 Slurm 超时写时间片

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `iprint` | integer | `0` | 输出与重启相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `ntimepr` | integer | `1` | Number of time steps per field output |
| `ntimers` | integer | `0` | Number of time steps per restart output；0 表示校验后取 `ntimepr`；否则为 restart 输出周期；`ntimers<=0` 时程序把它设为 `ntimepr` |
| `ifout` | integer | `-1` | -1 表示校验后按编译维度默认：3D 输出 f，2D 不输出；也可显式 0/1；`ifout=-1` 在 `validate_input` 中改为 `i3d`：3D 默认输出 f 场，2D 默认不输出 |
| `icalc_scalars` | integer | `1` | 1: Calculate scalar diagnostics |
| `ike_only` | integer | `0` | 1: Only calculate ke scalar diagnostic |
| `ike_harmonics` | integer | `0` | Number of Fourier harmonics of ke to be calculated and output |
| `ibh_harmonics` | integer | `0` | Number of Fourier harmonics of magnetic perturbation to be calculated and output |
| `irestart` | integer | `0` | 0 从头启动；1 从 HDF5 restart；2 用 restart 初始化 GS；3 用 2D real restart 初始化 2D complex |
| `itimer` | integer | `0` | 1: Output internal timer data |
| `iwrite_transport_coeffs` | integer | `1` | 1: Output transport coefficient fields |
| `iwrite_aux_vars` | integer | `1` | 1: Output auxiliary variable fields |
| `iwrite_adjacency` | integer | `1` | 1: Output mesh adjacency info |
| `iwrite_quad_points` | integer | `0` | 1: Output integration quadrature points |
| `itemp_plot` | integer | `0` | 1: Output additional temperature plots |
| `ibdgp` | integer | `0` | ne.0: bdgp plot contains only partial results |
| `idouble_out` | integer | `0` | 1: Use double-precision floating points in output |
| `irestart_slice` | integer | `-1` | Field output slice from which to restart；-1 使用最后一个 time slice；否则从指定 `time_nnn.h5` restart |
| `iveldif` | integer | `0` | ne.0: veldif plot contains only partial results |
| `write_ts_on_job_timeout` | integer | `0` | 1: Write time slice and stop code before job hits timeout or is preempted |

## 杂项物理参数 / Miscellaneous

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `gam` | real | `5./3. (约 1.6667)` | Ratio of specific heats |
| `db` | real | `-1.` | Collisionless ion skin depth (overrides db_fac)；默认 -1，表示按物理归一化自动计算 ion skin depth 并乘以 `db_fac`；若显式给非负值则覆盖；`db<0` 时程序按 `b0_norm/n0_norm/l0_norm/ion_mass` 计算物理 ion skin depth，再乘 `db_fac`；显式给非负 `db` 会覆盖该自动计算 |
| `db_fac` | real | `0.` | Factor multiplying physical value of ion skin depth；`db<0` 时乘在物理 ion skin depth 上；默认 0 等价于关闭 two-fluid skin-depth 贡献 |
| `mass_ratio` | real | `0.` | 杂项物理参数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `lambdae` | real | `0.` | 杂项物理参数相关参数，用于控制该组对应的物理模型、输入输出或数值算法；通常只在对应功能启用时显式设置 |
| `z_ion` | real | `1.` | Z effective |
| `ion_mass` | real | `1.` | Ion mass (in units of m_p) |
| `lambda_coulomb` | real | `17.` | Coulomb logarithm |
| `thermal_force_coeff` | real | `0.` | Coefficient of thermal force |
| `ntor` | integer | `0` | Toroidal mode number；2D/complex 线性模拟的环向模数；RMP 等也会使用 |
| `mpol` | integer | `0` | 若干测试/外场/REKC 设置中使用的极向模数 |

## 已废弃兼容参数 / Deprecated

仍可被解析以兼容旧输入，但新算例不建议使用

| 参数名 | 数据类型 | 默认值 | 含义 |
|---|---|---:|---|
| `ibform` | integer | `-1` | 已废弃兼容参数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `igs_method` | integer | `-1` | 已废弃兼容参数相关整数开关或模式选择参数；通常 0 表示关闭或默认路径，非零值选择相应物理模型、输入输出或数值算法 |
| `iwrite_restart` | integer | `0` | 1: Write restart files |
| `zeff` | real | `0.` | zeff is deprecated. Use z_ion instead. |
| `ivform` | integer | `1` | ivform is deprecated. Only ivform=1 is now implemented. |
| `iwrite_adios` | integer | `0` | iwrite_adios is deprecated. |
| `iglobalout` | integer | `0` | iglobalout is deprecated |
| `iglobalin` | integer | `0` | iglobalin is deprecated |
| `iread_adios` | integer | `0` | iread_adios is deprecated |
| `iread_hdf5` | integer | `1` | iread_hdf5 is deprecated |
