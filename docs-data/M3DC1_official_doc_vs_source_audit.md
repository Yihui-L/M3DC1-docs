# M3D-C1 官方文档与源码差异清单

本清单只比较官方 `doc/` 与当前源码。用户提供的参考稿不参与差异统计。结论以 `unstructured/input.f90` 的 `add_var_*` 注册项和 `read_namelist.cpp` 的读入规则为准。

## 1. 官方文档提到但源码未注册

| 文档名称 | 说明 |
|---|---|
| `delta_wall` | `C1input` 使用该名称不会被当前源码识别。 |
| `ihypamu` | `C1input` 使用该名称不会被当前源码识别。 |

## 2. 官方文档旧名/错拼名

| 文档名称 | 源码实际名称 | 源码默认值 |
|---|---|---:|
| `bound_type` | `boundary_type` | `0` |
| `ikprad_z` | `kprad_z` | `1` |
| `iread_partilesource` | `iread_particlesource` | `0` |
| `iwall_break` | `iwall_breaks` | `0` |
| `iwrite_transport_coefs` | `iwrite_transport_coeffs` | `1` |
| `pellet_R` | `pellet_r` | `0.` |
| `temin_q0` | `temin_qd` | `0.` |
| `igs_extend_diagmag` | `igs_extend_diamag` | `1` |

## 3. 默认值不一致

| 参数 | 源码默认值 | 官方文档默认值 | 说明 |
|---|---:|---:|---|
| `idens` | `0` | `1` | 源码默认 0；官方文档旧表写 1。 |
| `bootstrap_alpha` | `0.` | `1` | 源码默认 0；官方文档旧表写 1。 |
| `eta_fac` | `1.` | `0` | 源码默认 1；官方文档输运表写 0。 |
| `ikappar_ni` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `ihypdx` | `0` | `2` | 源码默认 0；官方文档表写 2。 |
| `nonrect` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `inoslip_pol` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `iconst_bz` | `0` | `1` | 源码默认 0；官方文档表写 1。 |
| `iconst_n` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `iconst_t` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `imp_mod` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `pskip` | `0` | `1` | 源码默认 0；官方文档表写 1。 |
| `max_repeat` | `1` | `3` | 源码默认 1；官方文档表写 3。 |
| `ksp_min` | `500` | `1200` | 源码默认 500；官方文档表写 1200。 |
| `ksp_warn` | `1000` | `1600` | 源码默认 1000；官方文档表写 1600。 |
| `jadv` | `1` | `0` | 源码默认 1；官方文档表写 0。 |
| `ntimepr` | `1` | `5` | 源码默认 1；官方文档表写 5。 |
| `ifull_torus` | `1` | `0` | 源码默认 1；官方文档 mesh/stellarator 小节写 0。 |
| `rzero` | `-1.` | `1` | 源码读入默认 -1，`validate_input` 中若为 -1 则 toroidal 几何取 `xzero`，否则取 1；官方文档直接写 1。 |
| `db` | `-1.` | `0` | 源码默认 -1，表示按物理归一化自动计算 ion skin depth 后乘 `db_fac`；官方文档写 0。 |
| `ghs_var` | `1.` | `0` | 源码默认 1；官方文档 Gaussian heat source 表写 0。 |
| `eta_wallRZ` | `-1.` | `.001` | 源码读入默认 -1，`validate_input` 中若 <0 则取 `eta_wall`；官方文档直接写 .001。 |
| `wall_region_etaRZ` | `-1.` | `1.e-3` | 源码读入默认 -1，`validate_input` 中若 <0 则逐区取 `wall_region_eta(i)`；官方文档直接写 1.e-3。 |

## 4. 语义/取值范围与源码不一致或不完整

| 参数 | 源码默认值 | 说明 |
|---|---:|---|
| `idevice` | `0` | 官方文档列出 1=CDX-U、2=NSTX、3=ITER、4=DIII-D；当前 `gradshafranov.f90` 的活动 `select case` 只实现 -1（读 `coil.dat/current.dat`）和 0（generic dipole），其它值进入无 PF 线圈的默认分支。 |
| `irmp` | `0` | 官方文档写 1 只在 plasma、2 只在 boundary 施加；当前 `rmp.f90` 对所有计算单元评价并投影该场，且 2 仅允许 `itor=0`，不是环形托卡马克的边界条件。 |
| `icsym` | `0` | 官方文档只列 0-2；当前源码还实现 3，使用确定性的 (1,1) 型初始扰动而不是随机噪声。 |
| `iflip_z` | `0` | 官方文档称其翻转整个平衡；当前活动使用点只在 gfile 初始化中反号 `zmaxis`，没有同时镜像 `psirz`、mesh 节点或其它平衡场。 |
| `iread_ext_field` | `0` | 官方文档只说明 1=读取外场；tokamak 源码把它作为数据组数量，1 读 `error_field`，大于 1 读 `error_fieldNN`。stellarator 读取器则只装载数组索引 `iread_ext_field`，常规可靠用法是 1。 |
| `ibasicj_solvep` | `0` | 官方文档把 0 概括为 uniform p；源码中 `itaylor=29` 的解析压力确为常数，但 `itaylor=31` 使用随半径衰减的解析压力，因此 0 的准确含义是使用所选 basicJ 解析压力并求 F。 |
| `ibootstrap_model` | `0` | 官方文档列出 1-4；源码 `bootstrap.f90` 还显式实现 `ibootstrap_model=5` 的 constant-Lambda 分支。源码 `input.f90` 内联说明仍是旧的一行模型说明，使用时以 `bootstrap.f90` 为准。 |
| `iread_te` | `0` | 官方文档主要写 `1: profile_te`；源码 GS 路径还支持 2(eV vs Psi)、4(keV vs rho)、10(Corsica)、20(iterdb)，VMEC 路径支持 21(`te_profile`)。 |
| `iread_ne` | `0` | 官方文档主要写 `1: profile_ne`；源码 GS 路径还支持 2、4、10、20，VMEC/ST 相关路径支持 21、22、23 等专用剖面读入方式。 |
| `iread_omega` | `0` | 官方文档主要写 `1: profile_omega`；源码还支持 2(`dtrot.xy`)、3(`profile_vphi`)、4(`profile_omega_rho_0`)、5(J. Menard profile_omega 格式)、20(iterdb)。 |
| `iread_p` | `0` | 官方文档写 `1: profile_p`；源码 VMEC 路径还测试 `iread_p=21` 并读 `p_profile`。 |
| `ikprad` | `0` | 官方文档只说明 `ikprad=1` 的 KPRAD 模型；源码还允许 `ikprad=-1`，在 `USEADAS` 编译时走 ADAS ADF11 数据路径，否则校验报错。 |
| `type_ext_field` | `-1` | 官方文档列出 tokamak/stellarator 主要取值；源码 `rmp.f90` 中 `type_ext_field<=0` 走 RMP/error-field 分支，`=1/2` 走 stellarator/free-boundary 分支，另有 `=3` 从电流计算外场的分支。 |
| `ipellet` | `0` | 官方文档列到 15；源码 `pellet.f90` 还支持 `abs(ipellet)=16`，即 toroidal von-Mises 分布并带 1/R 权重。双位数取值在归一化时还会除以 `Lor_vol`。 |
| `pellet_var_tor` | `0.` | 官方文档写 0 时取 `pellet_var`；源码中若 `ipellet=15` 且 `pellet_var_tor<=0`，实际设为 `pellet_var/pellet_r`，其它 pellet 分支才取 `pellet_var`。 |
| `ipellet_abl` | `0` | 官方文档列出 1、2、3；源码另有 `ipellet_abl=43` 的 Sergeev06 carbon ablation 分支，并且 `ipellet_z=0` 时会按 ablation 模型推断默认 Z。 |
| `itaylor` | `0` | 官方文档列出常用初始条件；源码 `init_conds.f90` 还包含 -1、24、25、26、28、30、31、32、33、34 等分支，实际可用性取决于编译宏和对应初始化例程。 |
| `inumgs` | `0` | 官方文档写读取 `profile-p` 与 `profile-g`；当前源码固定打开的文件名实际是复数 `profiles-p` 与 `profiles-g`，并按固定宽度格式读取 p/p' 和 g/FF'。 |
| `igs` | `80` | 官方文档只称其为最大 Picard 迭代次数；当前活动循环是 `do itnum=1,igs`。源码旁仍保留关于 `abs(igs)`/负值继续运行的旧注释，但负 `igs` 在当前实现中不会执行 GS 迭代。 |
| `igs_feedfac` | `1` | 官方文档称其为 external-field feedback 的 proportionality factor；当前源码只检查 `igs_feedfac.eq.1`，实际是 0/1 型开关，反馈幅值由固定公式计算。 |
| `igs_forcefree_lcfs` | `-1` | 官方文档主要说明取 1 时使 LCFS force-free；当前源码还区分 0、1、2，并把读入默认 -1 自动改为 0 或 2。1 令 LCFS 外转动为 0，2 则保持 LCFS 转动值。 |
| `psiscale` | `1.` | 源码声明注释称小于 1 可丢弃边缘剖面点，但当前活动代码只把大于 1 的值重置为 1，之后没有任何计算读取 `psiscale`；实际剖面磁通范围缩放使用的是 `psifrac`。 |
| `p1` | `0.` | 官方文档把它写成轴上 p'(Psi)；内置解析式使用归一化磁通，实际轴上导数系数为 `p0*p1`，不是参数值本身。 |
| `p2` | `0.` | 官方文档把它写成轴上 p''(Psi)；内置解析式的实际轴上二阶导数系数为 `2*p0*p2`，且自变量是归一化磁通。 |
| `xnull2` | `0.` | 官方文档称第二 X 点为 inactive；当前 `lcfs` 对两个 X 点使用同样的搜索和 LCFS 候选比较，第二点若更靠近磁轴磁通会成为活动 LCFS 限制点。 |
| `idenfunc` | `0` | 官方文档把 0-3 都列为平衡密度函数；当前初始化流程中 0/4 直接保留 GS/profile 密度，1/2 在 `den_eq` 中重写，3 主要在场评价算子中按磁通梯度重写，源码还实现文档未列出的 20 与专用 21。 |
| `tedge` | `0.` | 官方文档把它概括为真空区电子温度并给出边界关系；当前 GS 源码先平移 Te 样条，随后在 `pedge<=0` 时用 `n0_spline%n`（样条点数）而非边缘密度修正压力，行为与文档公式不一致，使用该组合前应验证或修正源码。 |
| `adapt_qs` | `0.` | 官方输入表把它放在 GS 小节，且源码也误用 `gs_grp` 注册；实际唯一活动使用位于 `adapt.f90`，用于按 q 面打包自适应网格，不参与 GS 求解。 |
| `adapt_zlow` | `0.` | 官方输入表和源码注册把它归入 GS；实际只在 `adapt.f90` 中控制 SOL 粗化区域，不参与 GS 方程。 |
| `adapt_zup` | `0.` | 官方输入表和源码注册把它归入 GS；实际只在 `adapt.f90` 中控制 SOL 粗化区域，不参与 GS 方程。 |
| `ivisfunc` | `0` | 官方文档只说明 0-3；当前源码还实现 4、10/11（读取 `profile_amu`）、12（basicJ 专用）以及 USEST 条件下的 21（逻辑 rho）。 |
| `iresfunc` | `0` | 官方文档把 2/3/4 分别描述为解析台阶/Spitzer 等模型；当前 `resistivity_func` 中 2、3、4 都直接使用预先构造的 `eta_field`。源码还实现 10/11 的 `profile_eta` 和 USEST 模式 21。 |
| `ikappafunc` | `0` | 官方文档列到 12；当前源码还在 USEST 条件下实现 21，按逻辑 rho 构造 tanh 热导。 |
| `ikapparfunc` | `0` | 官方文档只列 0/1；当前源码还实现 2，使用按 Te^(5/2) 构造并由 `kappar_min/max` 截断的场。 |
| `kappag` | `0.` | 官方文档称其按压力梯度阈值启用。CPU 弱式的热流项确含压力梯度平方范数，但当前 mask 实际比较 `p**2` 与 `gradp_crit**2`；GPU 对应实现被注释。 |
| `kappax` | `0.` | 官方文档把它列为 B×grad(T) 交叉热输运。当前普通 CPU、非 USEPARTICLES 路径有耦合项；GPU 版本的对应块被注释，USEPARTICLES 编译也排除该项。 |
| `ifixedb` | `0` | 官方边界表把它概括为运行时 `psi=0` 边界；当前活动用途集中在 gfile/GS 初始化和 LCFS 诊断。时间演化磁边界由 `iconst_bn`、`inocurrent_*`、`ifbound` 与多区域模型决定。 |
| `jper` | `0` | 官方文档表写 `2: Top/bottom boundaries periodic`；当前网格与边界源码实际测试 `jper.eq.1`。 |
| `imp_mod` | `1` | 官方文档称模式 1 为 implicit leapfrog；当前输入注册和活动分支将其称为 Caramana split-step，并由 `caramana_fac` 控制显式部分。 |
| `mass_ratio` | `0.` | 官方文档列出该输入但没有说明；当前源码除注册/存储外没有活动计算引用，电子质量仍使用内部常数。 |
| `lambdae` | `0.` | 官方文档只写 `lambdae`；当前源码除注册/存储外没有活动计算引用，非零值不会打开电子惯性。 |
| `imode_filter` | `0` | 输入注册说明称其为要过滤的环向模数量；当前实现中负值只保留所列模，而正值只从各场减去所列模重构幅值的 0.1，并非完全删除。 |

## 5. 运行时默认值/校验阶段会改写

这些参数的注册默认值仍以源码表为准，但 `validate_input` 会在读入后根据其它开关改写，用户手册中应同时说明有效行为。

| 参数 | 注册默认值 | 运行时行为 |
|---|---:|---|
| `ifout` | `-1` | `ifout=-1` 在 `validate_input` 中改为 `i3d`：3D 默认输出 f 场，2D 默认不输出。 |
| `ntimers` | `0` | `ntimers<=0` 时源码把它设为 `ntimepr`。 |
| `rzero` | `-1.` | `rzero=-1` 时，toroidal 几何取 `xzero`，其它几何取 1；若最终 `rzero<=0` 只给 warning。 |
| `ifbound` | `-1` | `ifbound=-1` 时，complex 版本默认 2，real 版本默认 1。 |
| `eta_wallRZ` | `-1.` | `eta_wallRZ<0` 时改为 `eta_wall`。 |
| `wall_region_etaRZ` | `-1.` | 每个 `wall_region_etaRZ(i)<0` 时改为对应 `wall_region_eta(i)`。 |
| `eta_max` | `0.` | `eta_max<=0` 时改为 `eta_vac`。 |
| `eta_min` | `0.` | `eta_min<=0` 时改为 0。 |
| `kappa_max` | `0.` | `kappa_max<=0` 时改为 `kappar`。 |
| `kappar_max` | `0.` | `kappar_max<=0` 时改为 `kappar`。 |
| `kappar_min` | `0.` | `kappar_min<=0` 时改为 `kappar`。 |
| `db` | `-1.` | `db<0` 时源码按 `b0_norm/n0_norm/l0_norm/ion_mass` 计算物理 ion skin depth，再乘 `db_fac`；显式给非负 `db` 会覆盖该自动计算。 |
| `particle_linear` | `-1` | `particle_linear=-1` 时改为当前 `linear`。 |
| `imp_mod` | `1` | `isplitstep=0` 时校验阶段强制 `imp_mod=0`。 |
| `iread_omega` | `0` | `iread_omega_e` 或 `iread_omega_ExB` 非零时会写入同一个内部 `iread_omega`，且与已有 `iread_omega` 互斥。 |

## 6. 源码注册但官方文档未直接提到

共 90 个。完整机器可筛选清单见 `m3dc1_official_doc_vs_source_audit.csv` 的 `source_registered_not_found_in_official_doc` 行。

| 参数 | 逻辑组 | 源码默认值 |
|---|---|---:|
| `model_info` | Mesh | `dummyInfo` |
| `is1_agg_blks` | Mesh | `1` |
| `is1_agg_scp` | Mesh | `0` |
| `psifrac` | Grad-Shafranov Solver | `1.` |
| `psiscale` | Grad-Shafranov Solver | `1.` |
| `ra_cyc` | Model Options | `1` |
| `radiff` | Model Options | `0.` |
| `rjra` | Model Options | `1.` |
| `ra_characteristics` | Model Options | `0` |
| `bzsign` | Model Options | `0.` |
| `amu_wall` | Transport Coefficients | `0.` |
| `amu_wall_off` | Transport Coefficients | `0.` |
| `amu_wall_delt` | Transport Coefficients | `0.1` |
| `kappar_max` | Transport Coefficients | `0.` |
| `kappar_min` | Transport Coefficients | `0.` |
| `sigma_rekc` | Resistive Wall | `0.` |
| `caramana_fac` | Time Step | `1.` |
| `isolve_with_guess` | Solver | `0` |
| `ispradapt` | Mesh Adaptation | `0` |
| `isprntime` | Mesh Adaptation | `10` |
| `isprweight` | Mesh Adaptation | `0.1` |
| `isprmaxsize` | Mesh Adaptation | `0.05` |
| `isprrefinelevel` | Mesh Adaptation | `1` |
| `isprcoarsenlevel` | Mesh Adaptation | `-1` |
| `iadapt_writevtk` | Mesh Adaptation | `0` |
| `iadapt_writesmb` | Mesh Adaptation | `1` |
| `iadapt_useH1` | Mesh Adaptation | `0` |
| `iadapt_removeEquiv` | Mesh Adaptation | `0` |
| `adapt_target_error` | Mesh Adaptation | `0.0001` |
| `adapt_ke` | Mesh Adaptation | `0.0` |
| `iadapt_ntime` | Mesh Adaptation | `0` |
| `iadapt_max_node` | Mesh Adaptation | `10000` |
| `adapt_control` | Mesh Adaptation | `1` |
| `iadapt_order_p` | Mesh Adaptation | `3.0` |
| `iadaptFaceNumber` | Mesh Adaptation | `-1` |
| `iadapt_snap` | Mesh Adaptation | `1` |
| `adapt_factor` | Mesh Adaptation | `1.` |
| `adapt_hmin` | Mesh Adaptation | `0.001` |
| `adapt_hmax` | Mesh Adaptation | `0.1` |
| `adapt_hmin_rel` | Mesh Adaptation | `0.5` |
| `adapt_hmax_rel` | Mesh Adaptation | `2.0` |
| `adapt_smooth` | Mesh Adaptation | `2./3. (约 0.6667)` |
| `adapt_psin_vacuum` | Mesh Adaptation | `-1.` |
| `adapt_psin_wall` | Mesh Adaptation | `-1.` |
| `iadapt_pack_rationals` | Mesh Adaptation | `0` |
| `adapt_pack_factor` | Mesh Adaptation | `0.02` |
| `adapt_coil_delta` | Mesh Adaptation | `0.` |
| `adapt_pellet_length` | Mesh Adaptation | `0.` |
| `adapt_pellet_delta` | Mesh Adaptation | `0.` |
| `vloopRZ` | Sources/Sinks | `0.` |
| `vloop_freq` | Sources/Sinks | `0.` |
| `ipellet_fixed_dep` | Sources/Sinks | `0` |
| `n_target` | Sources/Sinks | `1.` |
| `kprad_n0_denm_fac` | KPRAD Options | `1.` |
| `adas_adf11` | KPRAD Options | `""` |
| `kinetic_fast_ion` | Particle Simulation Options | `1` |
| `kinetic_thermal_ion` | Particle Simulation Options | `0` |
| `igyroaverage` | Particle Simulation Options | `0` |
| `particle_linear` | Particle Simulation Options | `-1` |
| `particle_substeps` | Particle Simulation Options | `40` |
| `particle_subcycles` | Particle Simulation Options | `1` |
| `particle_couple` | Particle Simulation Options | `0` |
| `particle_nodelete` | Particle Simulation Options | `0` |
| `iconst_f0` | Particle Simulation Options | `0` |
| `ifullf` | Particle Simulation Options | `0` |
| `fast_ion_mass` | Particle Simulation Options | `0.` |
| `fast_ion_z` | Particle Simulation Options | `0.` |
| `fast_ion_dist` | Particle Simulation Options | `1` |
| `fast_ion_max_energy` | Particle Simulation Options | `1000.` |
| `num_par_max` | Particle Simulation Options | `4000000` |
| `num_par_scale` | Particle Simulation Options | `1.` |
| `kinetic_nrmfac_scale` | Particle Simulation Options | `1.` |
| `ikinetic_vpar` | Particle Simulation Options | `0` |
| `kinetic_rhomax` | Particle Simulation Options | `1.` |
| `vpar_reduce` | Particle Simulation Options | `0.` |
| `idiamagnetic_advection` | Particle Simulation Options | `0` |
| `imode_filter` | Particle Simulation Options | `0` |
| `mode_filter_ntor` | Particle Simulation Options | `0` |
| `smooth_par` | Particle Simulation Options | `1.e-8` |
| `smooth_dens_parallel` | Particle Simulation Options | `0.` |
| ... | 另有 10 个，见 CSV | ... |
