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
