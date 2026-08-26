# M3D-C1 `C1input` 参数整理（基于当前 master 源码）

整理日期：2026-07-11。主要依据：`unstructured/input.f90` 的 `set_defaults` 和 `unstructured/read_namelist.cpp` 的解析规则；官方 `doc/` 仅作说明参考，默认值和可读参数一律以源码为准。

## 读入格式与 namelist 说明

- 主程序输入文件名固定为 `C1input`。惯例写成 `&inputnl ... /`，但源码解析器实际上逐行寻找 `name = value`，并不检查 namelist 名称。
- 因此本文把所有主程序参数归为 namelist `&inputnl`；源码中的 “Model Options / Equilibrium / ...” 是帮助打印用的逻辑 group，不是多个 Fortran `NAMELIST` 块。
- 注释以 `!` 开头；若 `!` 出现在 `=` 前，该行会被忽略。数组用一基索引：`param(1)=...`。
- 开关类参数大多是 `integer`，通常 0=关闭、1=打开；源码没有把它们声明成 logical。
- 默认值以源码 `add_var_*` 为准。若官方文档与源码不一致，表中采用源码值；不一致处单独列在审计文件中。
- 条件编译参数：`condition` 列非空时，只有在相应编译宏启用时才会注册。Markdown 主表把这些参数保留并在说明中标注。
- `内部变量` 是源码中实际被赋值/引用的 Fortran 变量名；少数输入名与内部变量名不同，例如 `pellet_r -> pellet_r_scl`。
- `源码使用摘要` 来自程序源码自动索引；逐行引用见 `M3DC1_parameter_source_usage.md` / `m3dc1_parameter_source_usage.csv`，便于继续人工核查。

最小格式示例：

```fortran
&inputnl
  linear = 1
  nplanes = 1
  ntor = 1
  dt = 0.1
  ntimemax = 20
/
```

## 参数总览

- 共提取 `C1input` 参数：611 个。
- 官方 `doc/inputs.tex` 提到但当前 `set_defaults` 未注册的名称：delta_wall, ihypamu。
- 官方文档中还存在若干旧名/错拼名，当前源码对应关系为：`bound_type` -> `boundary_type`；`ikprad_z` -> `kprad_z`；`iread_partilesource` -> `iread_particlesource`；`iwall_break` -> `iwall_breaks`；`iwrite_transport_coefs` -> `iwrite_transport_coeffs`；`pellet_R` -> `pellet_r`；`temin_q0` -> `temin_qd`；`igs_extend_diagmag` -> `igs_extend_diamag`。
- 官方文档与源码不一致清单见：[M3DC1_official_doc_vs_source_audit.md](M3DC1_official_doc_vs_source_audit.md)。
- 面向阅读的可检索版本见：[M3DC1_C1input_reader_guide.html](M3DC1_C1input_reader_guide.html)。

## 归一化 / Normalizations

这些量定义 M3D-C1 默认归一化：B0_norm=10^4 G、n0_norm=10^14 cm^-3、L0_norm=100 cm；多数物理输入/输出使用归一化单位。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `b0_norm` | `b0_norm` | real | `1.e4` | Normalization magnetic field (in G) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 73 处；主要在 `gradshafranov.f90` 16处, `particle.f90` 16处, `particle_com.f90` 12处, `input.f90` 7处。 | 217 |
| `n0_norm` | `n0_norm` | real | `1.e14` | Normalization density (in e-/cm3) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 109 处；主要在 `gradshafranov.f90` 21处, `particle.f90` 15处, `kprad_m3dc1.f90` 12处, `particle_com.f90` 11处。 | 219 |
| `l0_norm` | `l0_norm` | real | `100.` | Normalization length (in cm) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 53 处；主要在 `pellet.f90` 19处, `gradshafranov.f90` 7处, `input.f90` 6处, `diagnostics.f90` 5处。 | 221 |

## 网格 / Mesh

主程序读取已有 mesh/model 文件；mesh 生成工具的 input 文件格式另见附录。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `nplanes` | `nplanes` | integer | `1` | Number of toroidal planes | 托卡马克：2D/complex 线性取 1，真实三维非线性取大于 1 的环向平面数。仿星器：表示所选环向计算域内的平面数，通常必须大于 1；需足以解析 VMEC/外场的最高环向模。3D+PETSc 当前要求 MPI 进程数等于 `nplanes`。 | 源码引用 113 处；主要在 `basic_mesh.f90` 30处, `diagnostics.f90` 15处, `input.f90` 11处, `m3dc1_matrix.cc` 10处。 | 1186 |
| `nperiods` | `nperiods` | integer | `1` | Number of field periods | 托卡马克：通常取 1。仿星器：表示整环面被划分的周期数；当 `ifull_torus=0` 时实际只计算 `1/nperiods` 环面，且 VMEC 的 `nfp` 必须能被它整除。 | 源码引用 33 处；主要在 `physical_mesh.f90` 15处, `diagnostics.f90` 11处, `scorec_mesh.f90` 6处, `output.f90` 1处。 | 1188 |
| `ifull_torus` | `ifull_torus` | integer | `1` | 0 = one field period; 1 = full torus | 托卡马克：通常取 1；取 0 只有在明确采用周期扇区时才有意义。仿星器：0 计算一个由 `nperiods` 定义的周期扇区，1 计算完整环面；它控制环向域长度，不改变 VMEC 几何本身。 | 源码引用 7 处；主要在 `diagnostics.f90` 3处, `scorec_mesh.f90` 3处, `output.f90` 1处。 | 1190 |
| `iread_vmec` | `iread_vmec` | integer | `0` | 1 = read geometry from VMEC file | 托卡马克：保持 0，gfile 不通过该参数读取。仿星器：1 时从 `vmec_filename` 读取 VMEC 几何，并在固定边界初始化中同时提供平衡磁场和压力；通常与 `igeometry=1` 配合。 | 源码引用 6 处；主要在 `init_conds.f90` 3处, `physical_mesh.f90` 2处, `scorec_mesh.f90` 1处。 | 1192 |
| `vmec_filename` | `vmec_filename` | character(len=256) | `geometry.nc` | name of vmec data file | 托卡马克：不使用。仿星器：`iread_vmec=1` 时的 VMEC NetCDF 文件名；几何映射读取 R/Z 傅里叶系数、场周期和磁场系数，固定边界还使用其中的压力和磁场。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 4 处；主要在 `read_schaffer_field.f90` 2处, `read_vmec.f90` 1处, `rmp.f90` 1处。 | 1194 |
| `igeometry` | `igeometry` | integer | `0` | 0: default, identity | 托卡马克：标准物理 R-Z 网格取 0，网格坐标不再映射。仿星器：取 1，先把二维 mesh 坐标解释为逻辑圆盘，再由 VMEC/边界傅里叶数据映射为物理 R-Z；取 2 是求解 Laplace 几何的内部路径，不是常规 VMEC 设置。 | 源码引用 39 处；主要在 `newpar.f90` 6处, `scorec_mesh.f90` 6处, `transport.f90` 6处, `init_common.f90` 5处。 | 1196 |
| `xcenter` | `xcenter` | real | `0.` | center of logical mesh (x) | 托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 x 坐标，逻辑 rho 由 `sqrt((x-xcenter)^2+(z-zcenter)^2)` 计算；必须与生成逻辑 mesh 时采用的圆心一致。 | 源码引用 19 处；主要在 `init_common.f90` 9处, `transport.f90` 5处, `physical_mesh.f90` 3处, `init_vmec.f90` 2处。 | 1197 |
| `zcenter` | `zcenter` | real | `0.` | center of logical mesh (z) | 托卡马克：`igeometry=0` 时不用于平衡与 mesh 对齐。仿星器：逻辑圆盘中心的 z 坐标，与 `xcenter` 共同定义 rho 和 theta；必须与逻辑 mesh 圆心一致。 | 源码引用 19 处；主要在 `init_common.f90` 9处, `transport.f90` 5处, `physical_mesh.f90` 3处, `init_vmec.f90` 2处。 | 1198 |
| `bloat_factor` | `bloat_factor` | real | `0.` | factor to expand VMEC domain | 托卡马克：不使用。仿星器：把 VMEC 几何径向外推到放大的计算边界；0 不按比例扩展。固定边界 `itaylor=40` 的检查要求它为 0；自由边界/外场域可非零。若同时给 `bloat_distance`，后者优先并把本参数置 0。 | 源码引用 7 处；主要在 `read_vmec.f90` 5处, `init_conds.f90` 2处。 | 1199 |
| `bloat_distance` | `bloat_distance` | real | `0.` | factor to expand VMEC domain | 托卡马克：不使用。仿星器：沿 VMEC 磁面外法向按距离扩展计算边界，并覆盖 `bloat_factor` 的作用。固定边界 case 建议保持 0；外扩域不会自动生成真空、壁或 LCFS 的 zone 标签。 | 源码引用 6 处；主要在 `read_vmec.f90` 6处。 | 1200 |
| `nzer_factor` | `nzer_factor` | integer | `-1` | scale factor for order of VMEC interpolation | 托卡马克：不使用。仿星器：控制 VMEC R/Z 几何转为 Zernike 径向表示的阶数；非负时取 `n_zer=mpol*nzer_factor`，但仅在 `nzer_manual<0` 时使用。-1 采用程序默认。 | 源码引用 2 处；主要在 `read_vmec.f90` 2处。 | 1201 |
| `nzer_manual` | `nzer_manual` | integer | `-1` | order of VMEC interpolation | 托卡马克：不使用。仿星器：手动指定 VMEC 几何的 Zernike 径向阶数；只有不低于程序默认阶数时才覆盖默认值，且优先于 `nzer_factor`。主要用于分辨率测试。 | 源码引用 3 处；主要在 `read_vmec.f90` 3处。 | 1203 |
| `iread_planes` | `iread_planes` | integer | `0` | Read positions of toroidal planes from plane_positions | 托卡马克：3D 时 1 从 `plane_positions` 读取每个环向平面角度；否则均匀或按 toroidal packing 生成。仿星器：用法相同，但每个角度必须位于当前完整环面或周期扇区的范围内，文件行数必须等于 `nplanes`。 | 源码引用 1 处；主要在 `scorec_mesh.f90` 1处。 | 1205 |
| `xzero` | `xzero` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：某些解析初值、诊断和参考轴使用的 R 参考位置；不会移动 `mesh_filename` 中的节点，也不能用来使 mesh 对齐 gfile。仿星器：逻辑映射中心应使用 `xcenter`，本参数通常保持默认，仅少数测试/诊断使用。 | 源码引用 32 处；主要在 `init_gmode.f90` 6处, `init_mri.f90` 6处, `read_jsolver.f90` 3处, `scorec_mesh.f90` 3处。 | 1207 |
| `zzero` | `zzero` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：某些解析初值、诊断和参考轴使用的 Z 参考位置；不会平移已读入 mesh。仿星器：逻辑映射中心应使用 `zcenter`，本参数通常保持默认。 | 源码引用 28 处；主要在 `init_gmode.f90` 6处, `init_mri.f90` 6处, `scorec_mesh.f90` 3处, `diagnostics.f90` 2处。 | 1208 |
| `tiltangled` | `tiltangled` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：给矩形测试网格的边界法向加入旋转角，不会旋转任意外部 mesh 的节点。仿星器：VMEC 曲边界使用映射几何法向，通常保持 0。 | 源码引用 1 处；主要在 `scorec_mesh.f90` 1处。 | 1209 |
| `mesh_filename` | `mesh_filename` | character(len=256) | `struct-dmg.sms` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：二维物理 R-Z 有限元 mesh 文件；几何范围应覆盖目标等离子体、真空和壁区域并落在所需平衡数据范围内。仿星器：二维逻辑圆盘 mesh 文件，通常外边界 rho=1，随后映射为三维物理几何。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 3 处；主要在 `scorec_mesh.f90` 3处。 | 1210 |
| `mesh_model` | `mesh_model` | character(len=256) | `struct.dmg` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：与 `mesh_filename` 配套的几何模型，保存边界实体和 zone 拓扑。仿星器：与逻辑 mesh 配套的模型；模型标签定义逻辑分区，不会根据 VMEC 自动改成物理 plasma/vacuum/conductor 分区。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 3 处；主要在 `scorec_mesh.f90` 3处。 | 1212 |
| `model_info` | `model_info` | character(len=256) | `dummyInfo` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：仅 `USECADMODEL` 编译路径加载的额外 CAD model-info 文件，普通 `.dmg/.txt` 工作流不设置。仿星器：条件和用途相同，不参与 VMEC 几何映射。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 3 处；主要在 `scorec_mesh.f90` 2处, `m3dc1_scorec.cc` 1处。 | 1214 |
| `ipartitioned` | `ipartitioned` | integer | `0` | 1 = the input mesh is partitioned | 托卡马克：当前主源码只注册和保存该值，活动的 SCOREC `load_mesh` 没有按它分支。仿星器：行为相同，也不能用它切换逻辑 mesh 的装载方式；两者都应直接提供与运行方式匹配的 mesh 文件。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 1216 |
| `imatassemble` | `imatassemble` | integer | `0` | 0: use scorec matrix parallel assembly; 1 use petsc | 托卡马克：0 使用 SCOREC、1 使用 PETSc 进行并行矩阵装配，不改变物理 R-Z mesh。仿星器：后端选择相同，不改变逻辑到物理的几何映射、区域或平衡场。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1218 |
| `is1_agg_blks` | `is1_agg_blk_cnt` | integer | `1` | number of blocks to divide each node of dofs into for matrix s1 | 托卡马克：仅 `REORDERED` 编译时注册，设置 S1 矩阵每节点自由度聚合块数。仿星器：用法相同；只影响求解性能，不改变物理网格或 VMEC 映射。 条件编译：`ifdef REORDERED`。 | 源码引用 2 处；主要在 `time_step_split.f90` 1处, `time_step_unsplit.f90` 1处。 | 1221 |
| `is1_agg_scp` | `is1_agg_scp` | integer | `0` | 0: per-rank aggregation, 1: per-plane aggregation, 2: global aggregation | 托卡马克：仅 `REORDERED` 编译时注册；0 每 MPI rank、1 每环向平面、2 全局聚合。仿星器：取值相同，按所选周期域的平面组织聚合；不改变几何。 条件编译：`ifdef REORDERED`。 | 源码引用 2 处；主要在 `time_step_split.f90` 1处, `time_step_unsplit.f90` 1处。 | 1223 |
| `imulti_region` | `imulti_region` | integer | `0` | 1 = Mesh has multiple physical regions | 托卡马克：0 时全部单元自动视为 plasma；1 时必须用 `boundary_type/zone_type` 明确等离子体、真空和导体区，适合第一壁/电阻壁计算。仿星器：语法相同，但标签只分类逻辑 mesh 的既有单元，程序不会根据 VMEC LCFS 或外场自动判定区域；必须先保证映射后的物理位置合理。 | 源码引用 50 处；主要在 `metricterms_new_gpu.f90` 39处, `scorec_mesh.f90` 5处, `adapt.f90` 1处, `diagnostics.f90` 1处。 | 1226 |
| `toroidal_pack_factor` | `toroidal_pack_factor` | real | `1.` | ratio of longest to shortest toroidal element | 托卡马克：3D 且 `iread_planes=0` 时，>1 在 `toroidal_pack_angle` 附近加密环向平面；1 均匀。仿星器：作用相同，但需在所选周期域内兼顾 VMEC/外场模数解析；不改变二维截面网格。 | 源码引用 2 处；主要在 `scorec_mesh.f90` 2处。 | 1228 |
| `toroidal_pack_angle` | `toroidal_pack_angle` | real | `0.` | toroidal angle of maximum mesh packing | 托卡马克：`toroidal_pack_factor>1` 且未读 `plane_positions` 时的最大环向加密角，必须位于托卡马克计算域内。仿星器：定义相同，但角度必须位于当前完整环面或场周期扇区内。 | 源码引用 1 处；主要在 `scorec_mesh.f90` 1处。 | 1230 |
| `boundary_type` | `boundary_type` | integer array | `0` | Type of each mesh boundary. | 托卡马克：`imulti_region=1` 时按几何边编号标记 1=第一壁、2=计算域外边界；它决定边界条件作用位置。仿星器：取值相同，但标记的是逻辑模型边，映射后才成为物理边界；不会自动等于 VMEC LCFS。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`1000`。 | 源码引用 20 处；主要在 `scorec_mesh.f90` 17处, `output.f90` 3处。 | 1232 |
| `zone_type` | `zone_type` | integer array | `0` | Type of each mesh boundary. | 托卡马克：`imulti_region=1` 时按 zone 编号标记 1=plasma、2=conductor、3=vacuum。仿星器：取值相同，但必须由用户确认逻辑 zone 经 VMEC/bloat 映射后确实落在相应物理区域；程序只检查标签是否存在，不检查与平衡的一致性。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 15 处；主要在 `scorec_mesh.f90` 9处, `diagnostics.f90` 4处, `transport.f90` 2处。 | 1234 |

## 输入文件/剖面读入 / Input

控制是否从 geqdsk/dskbal/jsolver 及 profile_* 文件读入平衡、剖面、源项等。实际文件名多为固定约定，例如 geqdsk、profile_ne、profile_te、profile_p、profile_f、profile_j。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `iread_eqdsk` | `iread_eqdsk` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：轴对称 g-file 平衡入口。1 直接投影 `geqdsk`；2 读入 gfile 后在 GS 中改用默认压力/F；3 不使用 `psirz`，只取磁轴、电流和剖面重新求解 GS。仿星器：必须为 0，否则会在 `itaylor=40/41` 之前抢占初始化入口。 | 源码引用 10 处；主要在 `init_eqdsk.f90` 6处, `gradshafranov.f90` 2处, `init_conds.f90` 1处, `input.f90` 1处。 | 225 |
| `iread_dskbal` | `iread_dskbal` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：旧 BAL 平衡入口。1 使用文件 psi、F、FF′、ne 并由 ne(Te+Ti) 计算压力；2 压力/F 改用默认剖面；两者都调用 GS。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化。 | 源码引用 2 处；主要在 `init_conds.f90` 1处, `init_dskbal.f90` 1处。 | 226 |
| `iread_jsolver` | `iread_jsolver` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：旧 Jsolver 平衡入口，读取 `fixed`；`igs>0` 时 1 使用文件 p/F、2 改用默认 p/F，`igs=0` 时直接投影。仿星器：必须为 0，否则屏蔽 VMEC/外场初始化。 | 源码引用 2 处；主要在 `init_conds.f90` 1处, `init_jsolver.f90` 1处。 | 227 |
| `iread_omega` | `iread_omega` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：仅 GS 且 `irot!=0` 时读取，模式 1/2/3/4/5/20 分别对应 `profile_omega`、`dtrot.xy`、`profile_vphi`、rho 文件、带表头文件和 `iterdb`，之后乘 `vscale`。仿星器：VMEC 与 `itaylor=41` 路径均不读取。 源码用法：`iread_omega_e` 与 `iread_omega_ExB` 会在校验阶段映射到同一个内部选择量；`irot=0` 时不会读取文件。 运行时默认：`iread_omega_e` 或 `iread_omega_ExB` 非零时会写入同一个内部 `iread_omega`，且与已有 `iread_omega` 互斥。 | 源码引用 10 处；主要在 `input.f90` 6处, `gradshafranov.f90` 2处, `init_cyl.f90` 2处。 | 228 |
| `iread_omega_e` | `iread_omega_e` | integer | `0` | Read electron rotation (same options as iread_omega) | 托卡马克：文件模式同 `iread_omega`，随后扣除完整抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_ExB` 严格互斥。 | 源码引用 4 处；主要在 `gradshafranov.f90` 2处, `input.f90` 2处。 | 229 |
| `iread_omega_ExB` | `iread_omega_ExB` | integer | `0` | Read ExB rotation (same options as iread_omega) | 托卡马克：文件模式同 `iread_omega`，随后扣除离子抗磁项换算为离子角频率。仿星器：不读取。与 `iread_omega`、`iread_omega_e` 严格互斥。 | 源码引用 4 处；主要在 `gradshafranov.f90` 2处, `input.f90` 2处。 | 231 |
| `iread_ne` | `iread_ne` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：GS 使用 1/2/4/10/20 读取 psi、rho、Corsica 或 iterdb 密度。仿星器：固定边界 VMEC 用 21 读取 `n_profile(s)`；21 不用于 `itaylor=41`，该路径可用 22 的 `n_profile(s)` 或 23 的 `n_profile_vs_p` 在平衡后重写密度。两种装置中 `den_edge>0` 均与非零值冲突。 源码用法：GS 路径的 1/2/4/10/20 建立磁通函数；VMEC/ST 的 21/22/23 分别在 VMEC 投影中或后续 `den_eq` 中写入密度。 | 源码引用 18 处；主要在 `init_common.f90` 6处, `init_vmec.f90` 5处, `gradshafranov.f90` 3处, `init_cyl.f90` 2处。 | 233 |
| `iread_te` | `iread_te` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：GS 使用 1/2/4/10/20 读取不同坐标和单位的 Te。仿星器：仅固定边界 VMEC 的 21 读取 `te_profile(s)`；自由边界路径不读取。两种装置中 `tedge>0` 均与非零值冲突。 源码用法：GS 路径的 1/2/4/10/20 分别采用 psi、rho、Corsica 或 iterdb 坐标；VMEC 的 21 采用逻辑 `s=rho^2`。 | 源码引用 11 处；主要在 `init_vmec.f90` 5处, `gradshafranov.f90` 2处, `init_cyl.f90` 2处, `input.f90` 2处。 | 234 |
| `iread_p` | `iread_p` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：GS 中 1 读取 `profile_p(psi_N,p)`，替换 gfile/旧平衡或默认压力剖面。仿星器：固定边界 VMEC 中 21 读取 `p_profile(s,p)` 并替换 wout 的 `presf` 压力场，但不改变几何和磁场；自由边界路径不读取。 源码用法：GS 外部压力剖面会替换 gfile/dskbal/jsolver 或默认剖面；VMEC 外部压力只替换压力场，不改变 wout 的几何和磁场。 | 源码引用 11 处；主要在 `init_vmec.f90` 7处, `init_cyl.f90` 3处, `gradshafranov.f90` 1处。 | 235 |
| `iread_f` | `iread_f` | integer | `0` | Read profile_f file containing F=R*B_phi vs Psi_N for GS solve | 托卡马克：GS 中 1 读取 `profile_f(psi_N,F)`，其中 F 满足 \(F=R B_\phi\)；该文件替换 F，并按最外点重设 `bzero`。仿星器：不读取，VMEC 磁场仍来自 wout，`itaylor=41` 磁场来自外场文件。 | 源码引用 3 处；主要在 `init_cyl.f90` 2处, `gradshafranov.f90` 1处。 | 236 |
| `iread_j` | `iread_j` | integer | `0` | Read profile_j file containing toroidal J_phi(r) (basicj equilibrium only) | 托卡马克：常规轴对称 GS 不使用；仅非托卡马克圆柱测试路径 `itor=0,itaylor=33` 读取 `profile_j(r,J_phi)`。仿星器：不使用。 | 源码引用 2 处；主要在 `init_cyl.f90` 2处。 | 239 |
| `iread_heatsource` | `iread_heatsource` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：1 读取 `profile_heatsource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘 `ghs_rate` 并与其他热源相加，且只在非线性压力/温度方程中生效。 | 源码引用 2 处；主要在 `input.f90` 1处, `transport.f90` 1处。 | 242 |
| `iread_particlesource` | `iread_particlesource` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：1 读取 `profile_particlesource(psi_N)`。仿星器：1 读取同名文件，但横坐标解释为逻辑 `s=xl^2+zl^2`。两者均把第二列乘输入参数 `pellet_rate` 并与其他密度源相加，且要求 `idens=1,linear=0`。 | 源码引用 2 处；主要在 `input.f90` 1处, `transport.f90` 1处。 | 244 |
| `iread_neo` | `iread_neo` | integer | `0` | Read velocity data from NEO output | 托卡马克：1 读取三类 NEO 输出和 GYRO `input.profiles`；环向速度叠加到已有 `vz`，极向速度重写 `u/chi`，非 plasma 磁区置零。仿星器：没有与 VMEC 逻辑坐标配套的专用实现，建议保持 0。 | 源码引用 2 处；主要在 `init_conds.f90` 2处。 | 245 |
| `ineo_subtract_diamag` | `ineo_subtract_diamag` | integer | `0` | Subtract diamag. term from input vel. when reading NEO vel. | 托卡马克：仅 `iread_neo=1,db!=0` 时从 NEO 环向速度扣除离子抗磁贡献。仿星器：随 `iread_neo` 保持 0。 | 源码引用 7 处；主要在 `init_conds.f90` 7处。 | 247 |

## 平衡与初始条件 / Equilibrium

选择/缩放初始平衡、外场、RMP、stellarator 场、basicj 模型以及初始扰动。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `itaylor` | `itaylor` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：当三个外部平衡入口均为 0 时选择内置初始化；`itaylor=1` 进入 GS，19 为 Solovev，24 为 RWM，29/31 为 basicJ，-1 为常量场。仿星器：40 直接投影固定边界 VMEC 平衡；41 从三维 total/external field 初始化，程序不求解 VMEC 自由边界平衡。 源码用法：主初始化分发开关；不同几何下选择 tilting cylinder、GS、VMEC/stellarator、fixed-q、basicJ、RWM、wave/diffusion tests 等分支。 | 源码引用 20 处；主要在 `transport.f90` 4处, `init_basicj.f90` 3处, `init_basicq.f90` 3处, `init_conds.f90` 3处。 | 560 |
| `iupstream` | `iupstream` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器：环向数值上风/稳定化开关，不选择平衡。0 关闭；1 把 `magus` 给出的人工环向二阶项加到已有系数；2 用该人工项替代相应系数。它在时间演化算子中生效。 | 源码引用 25 处；主要在 `metricterms_new.f90` 12处, `metricterms_new_gpu.f90` 9处, `parallel_heat_flux.f90` 4处。 | 561 |
| `magus` | `magus` | real | `5.e-2` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器：`iupstream=1/2` 时人工环向二阶稳定项的无量纲强度；常与局部场或速度绝对值相乘。0 不一定关闭，关闭应设 `iupstream=0`。 | 源码引用 25 处；主要在 `metricterms_new.f90` 12处, `metricterms_new_gpu.f90` 9处, `parallel_heat_flux.f90` 4处。 | 562 |
| `iflip` | `iflip` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器：新启动时把坐标系手性翻转，统一反号 psi、环向场、速度势和环向速度，并反号 `vloop/tcur`；这是整体坐标约定变换，不等同于单独反转 B、J 或 V。restart 路径不再次调用该初始翻转。 | 源码引用 2 处；主要在 `input.f90` 1处, `newpar.f90` 1处。 | 563 |
| `iflip_b` | `iflip_b` | integer | `0` | Reverse equilibrium toroidal field | 托卡马克：平衡和已构造外场的环向磁场反号。仿星器：固定 VMEC 或外场初始化后同样反转环向场分量；必须确保输入场、诊断和模数符号约定一致。 | 源码引用 2 处；主要在 `init_conds.f90` 1处, `rmp.f90` 1处。 | 564 |
| `iflip_j` | `iflip_j` | integer | `0` | Reverse equilibrium toroidal current | 托卡马克：反转平衡极向磁通，从而反转环向电流；`icsubtract=1` 时线圈磁通也反号。gfile 负电流已自动处理，`iflip_j=1` 会中止并提示用 2 强制覆盖。仿星器：同样反转 psi 表示，通常不应把它当作重新求解电流剖面。 | 源码引用 6 处；主要在 `init_eqdsk.f90` 3处, `gradshafranov.f90` 1处, `init_conds.f90` 1处, `rmp.f90` 1处。 | 566 |
| `iflip_v` | `iflip_v` | integer | `0` | Reverse equilibrium toroidal velocity | 托卡马克与仿星器：1 反转平衡环向速度；-1 把平衡环向速度清零；0 保持初始化结果。它在平衡与 NEO 速度处理完成后执行。 | 源码引用 3 处；主要在 `init_conds.f90` 2处, `gradshafranov.f90` 1处。 | 568 |
| `iflip_z` | `iflip_z` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：当前源码只在 gfile 初始化中令 `zmaxis=-zmaxis`，并未同时镜像 `psirz`、mesh 或其它场，不能视为完整的上下翻转。仿星器：VMEC/外场路径没有活动使用。 | 源码引用 1 处；主要在 `init_eqdsk.f90` 1处。 | 570 |
| `icsym` | `icsym` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：控制 `eps` 初始扰动的上下对称性，0 无约束，1 仅给 U 加奇对称扰动，2 仅给 U 加偶对称扰动，3 使用确定性的 (1,1) 型扰动。仿星器：取值相同，但随机形状在逻辑网格坐标中构造后映射到物理空间。 | 源码引用 2 处；主要在 `init_common.f90` 1处, `init_conds.f90` 1处。 | 571 |
| `bzero` | `bzero` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：解析/GS 初始化的参考环向场，通常表示 `rzero` 处 Bphi；gfile 会以最外层 `fpol/rmaxis` 覆盖它，`profile_f` 与 GS 磁场缩放还可再次改写。仿星器：固定 VMEC 的 B 直接来自 wout，三维外场来自场文件，本参数不替代这些数据；TF 倾斜/平移解析误差场仍会用到它。 | 源码引用 99 处；主要在 `gradshafranov.f90` 23处, `init_3dwave.f90` 17处, `init_basicj.f90` 7处, `init_mri.f90` 4处。 | 572 |
| `bx0` | `bx0` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：仅 wave、3D diffusion 等内置测试平衡的初始 x 向磁场幅值，gfile/GS 生产路径不使用。仿星器：`itaylor=40/41` 不使用。 | 源码引用 27 处；主要在 `init_3dwave.f90` 16处, `init_3ddiffusion.f90` 6处, `init_wave.f90` 5处。 | 573 |
| `vzero` | `vzero` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：若干解析初始化的环向/轴向速度标度；basicJ 用作核心平坦转动值，`itaylor=-1` 直接作为均匀环向速度。gfile/GS 的文件旋转由 Input 组控制。仿星器：VMEC/外场路径不从本参数建立旋转。 | 源码引用 8 处；主要在 `init_rotating_cylinder.f90` 4处, `init_basicj.f90` 2处, `init_conds.f90` 1处, `init_cyl.f90` 1处。 | 574 |
| `phizero` | `phizero` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：FRS、FTZ、eigen 等测试初始化中速度流函数 U 的扰动幅值；常规 gfile/GS 不使用。仿星器：`itaylor=40/41` 不使用。 | 源码引用 3 处；主要在 `init_eigen.f90` 1处, `init_frs.f90` 1处, `init_ftz.f90` 1处。 | 575 |
| `verzero` | `verzero` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器：在 `init_perturbations` 中向 plasma zone 的扰动速度势加入 `R*verzero`，用于给定初始竖直速度；它是扰动层，不会改变读入平衡或 LCFS。 | 源码引用 1 处；主要在 `init_common.f90` 1处。 | 576 |
| `v0_cyl` | `v0_cyl` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：只在 fixed-q/cylindrical 测试剖面中作为中心轴向速度常数项；gfile/GS 不使用。仿星器：`itaylor=40/41` 不使用。 | 源码引用 1 处；主要在 `init_basicq.f90` 1处。 | 577 |
| `v1_cyl` | `v1_cyl` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：只在 fixed-q/cylindrical 测试剖面中作为随归一化磁通变化的速度幅值，形式为 `v0_cyl+v1_cyl*psi^beta`。仿星器：`itaylor=40/41` 不使用。 | 源码引用 1 处；主要在 `init_basicq.f90` 1处。 | 578 |
| `idevice` | `idevice` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：只服务 GS/PF 线圈场。当前源码实际实现 -1 读取 `coil.dat/current.dat`，0 使用 generic dipole；其它值进入无 PF 线圈的默认分支。仿星器：VMEC/三维场初始化不使用该设备选择。 | 源码引用 5 处；主要在 `gradshafranov.f90` 4处, `init_eqdsk.f90` 1处。 | 579 |
| `iwave` | `iwave` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器生产平衡均不使用；只为 wave 测试初始化选择波支，具体可用取值随二维/三维测试例程而异。 | 源码引用 16 处；主要在 `init_3dwave.f90` 13处, `init_wave.f90` 3处。 | 580 |
| `eps` | `eps` | real | `0.01` | Magnitude of initial perturbations* | 托卡马克：初始随机/确定性扰动幅度；`itor=0,irmp=2` 时还作为解析 m/n 真空场幅度。仿星器：固定 VMEC 和 total-field 路径也可用它给 plasma zone 添加初始流扰动，但不改变 wout/外场基态。 | 源码引用 84 处；主要在 `init_conds.f90` 36处, `init_3dwave.f90` 12处, `init_gem.f90` 6处, `init_gmode.f90` 6处。 | 581 |
| `maxn` | `maxn` | integer | `200` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克与仿星器：`icsym=0/1/2` 随机初始扰动的模循环上限，值越大包含的平面波越多、初始化代价越高；不控制 M3D-C1 实际环向网格分辨率。 | 源码引用 10 处；主要在 `init_common.f90` 6处, `init_conds.f90` 4处。 | 583 |
| `irmp` | `irmp` | integer | `0` | 1: Apply nonaxisym. fields throughout plasma； 2: Apply mpol/ntor vacuum fields (itor=0 only) | 托卡马克：1 读取/计算 RMP 与 error field 并投影到整个计算域；2 仅 `itor=0` 可用，在整个域评价解析 mpol/ntor 真空场。仿星器：`itaylor=41,type_ext_field=1,extsubtract=0` 已装入 total field 后会跳过第二次 RMP；固定 VMEC 或 subtraction 路径可另行调用外场处理。 | 源码引用 10 处；主要在 `rmp.f90` 4处, `input.f90` 2处, `init_basicj.f90` 1处, `init_conds.f90` 1处。 | 584 |
| `rmp_atten` | `rmp_atten` | real | `0.` | Additional exponential decay of RMP field from r=1 for irmp=2 | 托卡马克与仿星器环形生产路径不使用；只在 `itor=0,irmp=2` 中控制解析真空扰动从 r=1 起的指数因子。0 表示不加该衰减/增长因子。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 587 |
| `tf_tilt` | `tf_tilt` | real | `0.` | Angle of TF from vertical (in degrees) | 托卡马克：TF 线圈相对竖直方向的小倾斜角，单位度；源码据此构造非轴对称误差场并在基态后加入，不移动 mesh。仿星器：不是 VMEC 场线圈几何参数，通常保持 0。 | 源码引用 6 处；主要在 `rmp.f90` 3处, `init_conds.f90` 1处, `input.f90` 1处, `restart_hdf5.f90` 1处。 | 589 |
| `tf_tilt_angle` | `tf_tilt_angle` | real | `0.` | Axis of rotation for TF tilt (in degrees) | 托卡马克：`tf_tilt` 的旋转轴环向方位，单位度，只在 `tf_tilt!=0` 时生效。仿星器：通常不使用。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 591 |
| `tf_shift` | `tf_shift` | real | `0.` | Horizontal shift of TF coil | 托卡马克：TF 线圈水平平移幅度，用解析式生成误差场，不改变 mesh 或 GS 线圈坐标。仿星器：通常不使用。 | 源码引用 6 处；主要在 `rmp.f90` 3处, `init_conds.f90` 1处, `input.f90` 1处, `restart_hdf5.f90` 1处。 | 593 |
| `tf_shift_angle` | `tf_shift_angle` | real | `0.` | Direction of TF shift (in degrees) | 托卡马克：`tf_shift` 的平移方向方位角，单位度，只在 `tf_shift!=0` 时生效。仿星器：通常不使用。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 595 |
| `pf_tilt` | `pf_tilt` | real array | `0.` | Angle of PF from vertical (in degrees) | 托卡马克：PF 线圈逐线圈倾斜角数组，单位度；只有已经由 GS/`idevice=-1` 装载到 PF 线圈表的线圈才会产生误差场。仿星器：VMEC/外场路径没有 PF 线圈表，通常不使用。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 9 处；主要在 `rmp.f90` 6处, `init_conds.f90` 1处, `input.f90` 1处, `restart_hdf5.f90` 1处。 | 597 |
| `pf_tilt_angle` | `pf_tilt_angle` | real array | `0.` | Axis of rotation for PF tilt (in degrees) | 托卡马克：每个 `pf_tilt(i)` 的旋转轴方位角数组，单位度，索引对应线圈组标签。仿星器：通常不使用。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 4 处；主要在 `rmp.f90` 4处。 | 599 |
| `pf_shift` | `pf_shift` | real array | `0.` | Horizontal shift of PF coil | 托卡马克：PF 线圈逐线圈水平平移数组；基于已加载线圈场导数构造非轴对称误差场，不修改轴对称 GS 线圈位置。仿星器：通常不使用。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 9 处；主要在 `rmp.f90` 6处, `init_conds.f90` 1处, `input.f90` 1处, `restart_hdf5.f90` 1处。 | 601 |
| `pf_shift_angle` | `pf_shift_angle` | real array | `0.` | Direction of PF shift (in degrees) | 托卡马克：每个 `pf_shift(i)` 的平移方向方位角数组，单位度。仿星器：通常不使用。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 4 处；主要在 `rmp.f90` 4处。 | 603 |
| `iread_ext_field` | `iread_ext_field` | integer | `0` | 1: Read external field | 托卡马克：对 `type_ext_field<=0` 表示要读的 error-field 数据组数；1 读 `error_field`，大于 1 读 `error_field01...`。仿星器：`itaylor=41` 必须非零，当前读取器实际只装载索引 `iread_ext_field`，常规用法应取 1。 | 源码引用 20 处；主要在 `rmp.f90` 16处, `init_conds.f90` 2处, `input.f90` 1处, `restart_hdf5.f90` 1处。 | 606 |
| `isample_ext_field` | `isample_ext_field` | integer | `1` | Factor to down-sample external field data toroidally | 托卡马克：Schaffer error-field 数据的环向降采样因子。仿星器：仅场文件回退到 Schaffer 格式时使用；FIELDLINES/MGRID/HINT/MIPS 专用读取器不使用该因子。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 608 |
| `isample_ext_field_pol` | `isample_ext_field_pol` | integer | `1` | Factor to down-sample external field data poloidally | 托卡马克：Schaffer error-field 数据的极向降采样因子。仿星器：仅 Schaffer 回退格式使用，专用三维场读取器不使用。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 610 |
| `scale_ext_field` | `scale_ext_field` | real | `1.` | Factor to scale external field | 托卡马克与仿星器：投影已读场数据时统一乘的幅值因子；会作用于该读取器装入的 `file_total_field/file_ext_field/error_field`，但不缩放 gfile 或 `itaylor=40` 直接读取的 wout 基态，也不重新求解平衡。 | 源码引用 6 处；主要在 `rmp.f90` 6处。 | 612 |
| `shift_ext_field` | `shift_ext_field` | real array | `0.` | Toroidal shift (in deg) of external fields | 托卡马克与仿星器：各外场数据组的环向相位平移数组，单位度；3D 中通过改变取样角实现，complex 中转化为所选 `ntor` 的相位因子。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`8`。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 614 |
| `type_ext_field` | `type_ext_field` | integer | `-1` | type of external field file | 托卡马克：<=0 走 RMP/error-field；3 可从 `external_j` 电流数据求外场。仿星器：1 在 `itaylor=41` 中直接把 `file_total_field` 作为 total field；2 要求 `extsubtract=1`，先装 total field、再读 `file_ext_field` 并保存/扣除外场。 源码用法：`<=0` 用 tokamak RMP/error-field 分支，`=1/2` 用 stellarator/free-boundary 场文件，`=3` 从电流计算外场。 | 源码引用 11 处；主要在 `rmp.f90` 10处, `init_conds.f90` 1处。 | 616 |
| `file_ext_field` | `file_ext_field` | character(len=256) | `error_field` | name of external field file | 托卡马克：`type_ext_field<=0` 时此名称被忽略，文件名固定为 `error_field` 或 `error_fieldNN`。仿星器：`type_ext_field=2` 的真空/外部场文件；文件名前缀选择 FIELDLINES、MIPS、HINT、MGRID 读取器，其它名称按 Schaffer 格式。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 1 处；主要在 `rmp.f90` 1处。 | 618 |
| `file_total_field` | `file_total_field` | character(len=256) | `total_field` | name of total field file for ST | 托卡马克：常规 RMP/GS 不使用。仿星器：`itaylor=41,type_ext_field=1/2` 的总磁场文件；1 直接作为基态，2 与 `file_ext_field` 组成 total-minus-external 的演化场分解。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 2 处；主要在 `rmp.f90` 2处。 | 620 |
| `beta` | `beta` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：仅 tilting/fixed-q 等模型平衡或测试问题中的无量纲形状/速度幂参数，不是由 gfile 得到的等离子体 beta，也不会覆盖压力。仿星器：`itaylor=40/41` 不使用。 | 源码引用 58 处；主要在 `mackenbach_profiles.f90` 23处, `ReducedQuinticImplicit.cc` 10处, `metricterms_new.f90` 8处, `metricterms_new_gpu.f90` 8处。 | 622 |
| `ln` | `ln` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：多个解析/测试平衡的特征径向尺度；basicJ 中是电流剖面半径，Solovev 中控制横向尺寸。它不是自然对数。仿星器：VMEC/外场平衡不使用，但 `icsym=3` 扰动包络仍可能引用。 | 源码引用 64 处；主要在 `init_conds.f90` 17处, `init_solovev.f90` 12处, `init_basicj.f90` 10处, `init_3ddiffusion.f90` 7处。 | 623 |
| `elongation` | `elongation` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：仅 `itaylor=19` Solovev 解析平衡的伸长率。仿星器：VMEC 几何由傅里叶系数给出，本参数不使用。 | 源码引用 8 处；主要在 `init_solovev.f90` 8处。 | 624 |
| `basicj_nu` | `basicj_nu` | real | `1.` | Exponent in basicj equilibrium | 托卡马克：`itaylor=29/31` 电流剖面指数；若 `basicj_qa!=0` 会由 q0/qa 关系覆盖。仿星器：`itaylor=40/41` 不使用。 | 源码引用 6 处；主要在 `init_basicj.f90` 5处, `input.f90` 1处。 | 625 |
| `basicj_j0` | `basicj_j0` | real | `1.` | On-axis current density in basicj equilibrium | 托卡马克：basicJ 轴上电流密度幅值；若 `basicj_q0!=0`，源码用 `2*bzero/(rzero*q0)` 覆盖本值。仿星器：不使用。 | 源码引用 9 处；主要在 `init_basicj.f90` 8处, `input.f90` 1处。 | 627 |
| `basicj_q0` | `basicj_q0` | real | `0.` | On-axis safety factor in basicj equilibrium (supersedes basicj_j0) | 托卡马克：basicJ 轴上安全因子；非零时优先于 `basicj_j0` 并反算轴上电流。0 表示由 `basicj_j0` 反算 q0。仿星器：不使用。 | 源码引用 5 处；主要在 `init_basicj.f90` 5处。 | 629 |
| `basicj_qa` | `basicj_qa` | real | `0.` | Edge safety factor in basicj equilibrium (supersedes basicj_nu) | 托卡马克：basicJ 目标边缘安全因子；非零时覆盖 `basicj_nu`。`itaylor=31` 且显式给 `xlim!=0` 时源码会报错。仿星器：不使用。 | 源码引用 4 处；主要在 `init_basicj.f90` 4处。 | 631 |
| `basicj_voff` | `basicj_voff` | real | `1.` | Radial extent of flat toroidal rotation in basicj equilibrium | 托卡马克：basicJ 核心平坦环向速度区的径向范围；范围内速度基值为 `vzero`。仿星器：不使用。 | 源码引用 3 处；主要在 `init_basicj.f90` 3处。 | 633 |
| `basicj_vdelt` | `basicj_vdelt` | real | `1.` | Width of velocity drop-off, as fraction of ln, in basicj equilibrium | 托卡马克：basicJ 平坦转动区外速度衰减宽度相对 `ln` 的系数，进入高斯型衰减分母。仿星器：不使用。 | 源码引用 2 处；主要在 `init_basicj.f90` 2处。 | 635 |
| `basicj_dexp` | `basicj_dexp` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：basicJ 专用输运系数径向缩放函数的幂指数，配合 `basicj_dvac` 使黏性/热传导向外变化；不改变初始密度场本身。仿星器：不使用。 | 源码引用 1 处；主要在 `init_basicj.f90` 1处。 | 637 |
| `basicj_dvac` | `basicj_dvac` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：basicJ 专用输运系数缩放函数在 `r=ln` 处的目标倍率，影响相关黏性与热传导系数，不是外部真空区密度。仿星器：不使用。 | 源码引用 1 处；主要在 `init_basicj.f90` 1处。 | 638 |
| `ibasicj_solvep` | `ibasicj_solvep` | integer | `0` | 0: Uniform pressure, solve for F.  1: Uniform F, solve for pressure | 托卡马克：仅 `itaylor=29/31`。0 使用解析压力并由给定 J 求 F；1 令 F 均匀并由 J 求压力。`itaylor=29` 的解析压力为常数，`itaylor=31` 的解析压力随半径衰减。仿星器：不使用。 | 源码引用 10 处；主要在 `init_basicj.f90` 10处。 | 639 |

## Grad-Shafranov 求解器 / Grad-Shafranov Solver

控制 GS 迭代、轴/限制器/X 点、压力/电流/旋转/密度剖面及反馈参数。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `inumgs` | `inumgs` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 643 |
| `igs` | `igs` | integer | `80` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：大于 0 时给出 GS 最大迭代次数，收敛误差达到 `tol_gs` 可提前退出；0 不求解 GS。它与 Input 的平衡入口、Boundary 的 `ifixedb`、Mesh 的 zone 共同决定初始平衡。仿星器：`itaylor=40/41` 不调用 GS。 | 源码引用 9 处；主要在 `gradshafranov.f90` 4处, `init_conds.f90` 1处, `init_eqdsk.f90` 1处, `init_jsolver.f90` 1处。 | 644 |
| `igs_pp_ffp_rescale` | `igs_pp_ffp_rescale` | integer | `0` | Rescale p' and FF' to match p and F | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `gradshafranov.f90` 2处, `init_eqdsk.f90` 2处。 | 645 |
| `igs_extend_p` | `igs_extend_p` | integer | `0` | Extend p past Psi=1 using ne and Te profiles | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `gradshafranov.f90` 1处, `input.f90` 1处。 | 647 |
| `igs_extend_diamag` | `igs_extend_diamag` | integer | `1` | Extend diamagnetic rotation Psi=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 649 |
| `igs_start_xpoint_search` | `igs_start_xpoint_search` | integer | `0` | Number of GS its. before searching for xpoint | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 651 |
| `igs_forcefree_lcfs` | `igs_forcefree_lcfs` | integer | `-1` | Ensure that GS solution is force-free at LCFS | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `gradshafranov.f90` 5处, `input.f90` 3处。 | 653 |
| `nv1equ` | `nv1equ` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 655 |
| `igs_feedfac` | `igs_feedfac` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 656 |
| `eta_gs` | `eta_gs` | real | `1e3` | Factor for smoothing nonaxisymmetries in psi in GS solve | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 657 |
| `tcuro` | `tcuro` | real | `1.` | Total current in initial current filament | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 20 处；主要在 `gradshafranov.f90` 8处, `init_eqdsk.f90` 7处, `init_jsolver.f90` 4处, `init_dskbal.f90` 1处。 | 659 |
| `xmag` | `xmag` | real | `1.` | R-coordinate of initial current filament | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 100 处；主要在 `gradshafranov.f90` 15处, `diagnostics.f90` 11处, `init_eqdsk.f90` 7处, `init_jsolver.f90` 6处。 | 661 |
| `zmag` | `zmag` | real | `0.` | Z-coordinate of initial current filament | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 92 处；主要在 `diagnostics.f90` 12处, `gradshafranov.f90` 10处, `init_eqdsk.f90` 7处, `init_jsolver.f90` 6处。 | 663 |
| `xmag0` | `xmag0` | real | `0.` | Target R-coordinate of magnetic axis for feedback | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 11 处；主要在 `gradshafranov.f90` 6处, `newpar.f90` 3处, `init_eqdsk.f90` 2处。 | 665 |
| `zmag0` | `zmag0` | real | `0.` | Target Z-coordinate of magnetic axis for feedback | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `gradshafranov.f90` 4处, `newpar.f90` 3处, `init_eqdsk.f90` 1处。 | 667 |
| `xlim` | `xlim` | real | `0.` | R-coordinate of limiter #1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 21 处；主要在 `init_basicj.f90` 4处, `init_solovev.f90` 3处, `diagnostics.f90` 2处, `gradshafranov.f90` 2处。 | 669 |
| `zlim` | `zlim` | real | `0.` | Z-coordinate of limiter #1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 13 处；主要在 `init_solovev.f90` 2处, `output.f90` 2处, `diagnostics.f90` 1处, `gradshafranov.f90` 1处。 | 671 |
| `xlim2` | `xlim2` | real | `0.` | R-coordinate of limiter #2 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `diagnostics.f90` 2处, `gradshafranov.f90` 2处, `output.f90` 2处, `particle.f90` 1处。 | 673 |
| `zlim2` | `zlim2` | real | `0.` | Z-coordinate of limiter #2 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `output.f90` 2处, `diagnostics.f90` 1处, `gradshafranov.f90` 1处, `restart_hdf5.f90` 1处。 | 675 |
| `rzero` | `rzero` | real | `-1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | -1 表示校验后自动设置：toroidal 几何取 `xzero`，否则取 1。 运行时默认：`rzero=-1` 时，toroidal 几何取 `xzero`，其它几何取 1；若最终 `rzero<=0` 只给 warning。 | 源码引用 130 处；主要在 `gradshafranov.f90` 29处, `init_frs.f90` 19处, `init_solovev.f90` 15处, `init_ftz.f90` 10处。 | 677 |
| `psifrac` | `psifrac` | real | `1.` | Fraction of poloidal flux from psimin to psibound used for the mesh | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 12 处；主要在 `gradshafranov.f90` 12处。 | 678 |
| `libetap` | `libetap` | real | `1.2` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `gradshafranov.f90` 3处, `init_basicq.f90` 1处, `metricterms_new.f90` 1处, `metricterms_new_gpu.f90` 1处。 | 679 |
| `p0` | `p0` | real | `0.01` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 132 处；主要在 `init_3dwave.f90` 19处, `init_frs.f90` 14处, `gradshafranov.f90` 13处, `init_wave.f90` 9处。 | 680 |
| `pi0` | `pi0` | real | `0.005` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 18 处；主要在 `init_tilt.f90` 3处, `init_wave.f90` 3处, `init_mri.f90` 2处, `gradshafranov.f90` 1处。 | 681 |
| `p1` | `p1` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 68 处；主要在 `metricterms_new_gpu.f90` 31处, `gradshafranov.f90` 12处, `read_schaffer_field.f90` 10处, `read_vmec.f90` 7处。 | 682 |
| `p2` | `p2` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 32 处；主要在 `metricterms_new_gpu.f90` 14处, `gradshafranov.f90` 12处, `read_namelist.cpp` 3处, `init_basicq.f90` 1处。 | 683 |
| `pedge` | `pedge` | real | `0.` | Pressure outside separatrix (ignore if <= 0) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 39 处；主要在 `gradshafranov.f90` 7处, `input.f90` 7处, `init_rwm.f90` 3处, `init_solovev.f90` 3处。 | 684 |
| `tedge` | `tedge` | real | `0.` | Electron temperature outside separatrix (ignore if <= 0) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `input.f90` 6处, `gradshafranov.f90` 3处, `model.f90` 1处。 | 686 |
| `tiedge` | `tiedge` | real | `0.` | Outermost ion temperature (ignore if <= 0) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `gradshafranov.f90` 4处。 | 688 |
| `expn` | `expn` | real | `0.` | Density profile = p^expn | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 12 处；主要在 `gradshafranov.f90` 3处, `init_common.f90` 2处, `init_eqdsk.f90` 2处, `input.f90` 2处。 | 690 |
| `q0` | `q0` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 37 处；主要在 `init_frs.f90` 17处, `init_solovev.f90` 5处, `init_rwm.f90` 3处, `gradshafranov.f90` 2处。 | 692 |
| `sigma0` | `sigma0` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `gradshafranov.f90` 4处, `init_eqdsk.f90` 4处, `init_jsolver.f90` 2处。 | 693 |
| `djdpsi` | `djdpsi` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `gradshafranov.f90` 2处, `init_basicq.f90` 1处。 | 694 |
| `th_gs` | `th_gs` | real | `0.8` | Implicitness of GS Picard iterations | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `gradshafranov.f90` 2处, `init_basicq.f90` 1处。 | 695 |
| `tol_gs` | `tol_gs` | real | `1.e-8` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 697 |
| `psiscale` | `psiscale` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `input.f90` 3处。 | 698 |
| `pscale` | `pscale` | real | `1.` | Factor multiplying pressure profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 699 |
| `bscale` | `bscale` | real | `1.` | Factor multiplying toroidal field profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `gradshafranov.f90` 3处。 | 701 |
| `batemanscale` | `batemanscale` | real | `1.` | Bateman scaling factor for TF (keeping current density fixed) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `gradshafranov.f90` 2处, `init_eqdsk.f90` 2处。 | 703 |
| `bpscale` | `bpscale` | real | `1.` | Factor multiplying F' (keeping F0 constant) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `gradshafranov.f90` 8处。 | 705 |
| `iread_bscale` | `iread_bscale` | integer | `0` | 1: read profile_bscale for factor to scale F | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 707 |
| `iread_pscale` | `iread_pscale` | integer | `0` | 1: read profile_pscale for factor to scale p and p' | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 709 |
| `vscale` | `vscale` | real | `1.` | Factor multiplying toroidal rotation profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 711 |
| `gs_vertical_feedback` | `gs_vertical_feedback` | real array | `0.` | Proportional feedback of each coil to vertical displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 713 |
| `gs_radial_feedback` | `gs_radial_feedback` | real array | `0.` | Proportional feedback of each coil to radial displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 716 |
| `gs_vertical_feedback_i` | `gs_vertical_feedback_i` | real array | `0.` | Integral feedback of each coil to vertical displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 719 |
| `gs_radial_feedback_i` | `gs_radial_feedback_i` | real array | `0.` | Integral feedback of each coil to radial displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 722 |
| `gs_vertical_feedback_x` | `gs_vertical_feedback_x` | real array | `0.` | Proportional feedback of each coil to vertical displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 725 |
| `gs_radial_feedback_x` | `gs_radial_feedback_x` | real array | `0.` | Proportional feedback of each coil to radial displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 728 |
| `gs_vertical_feedback_x_i` | `gs_vertical_feedback_x_i` | real array | `0.` | Integral feedback of each coil to vertical displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 731 |
| `gs_radial_feedback_x_i` | `gs_radial_feedback_x_i` | real array | `0.` | Integral feedback of each coil to radial displacements | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`2000`。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 734 |
| `irot` | `irot` | integer | `0` | Include toroidal rotation | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 20 处；主要在 `gradshafranov.f90` 19处, `input.f90` 1处。 | 738 |
| `iscale_rot_by_p` | `iscale_rot_by_p` | integer | `1` | 0: omega^2 = 2.*p0*(alphai * Psi^i)/n0； 1: omega^2 = 2.*(alphai * Psi^i)/n0, 2: omega^2 = 2.*(alphai * Psi^i), alphai = a0 + a1*exp(-((psii-a2)/a3)**2) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `gradshafranov.f90` 3处。 | 740 |
| `alpha0` | `alpha0` | real | `0.` | Constant term in analytic rotation profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `gradshafranov.f90` 2处, `init_basicj.f90` 1处, `init_basicq.f90` 1处, `init_conds.f90` 1处。 | 744 |
| `alpha1` | `alpha1` | real | `0.` | Linear term in analytic rotation profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `gradshafranov.f90` 2处, `init_basicj.f90` 1处, `init_basicq.f90` 1处, `init_conds.f90` 1处。 | 746 |
| `alpha2` | `alpha2` | real | `0.` | Quadratic term in analytic rotation profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `gradshafranov.f90` 2处, `init_basicq.f90` 1处, `init_conds.f90` 1处, `init_kstar.f90` 1处。 | 748 |
| `alpha3` | `alpha3` | real | `0.` | Cubic term in analytic rotation profile | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `gradshafranov.f90` 2处, `init_basicq.f90` 1处, `init_conds.f90` 1处, `init_kstar.f90` 1处。 | 750 |
| `idenfunc` | `idenfunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `init_common.f90` 4处, `m3dc1_nint.f90` 3处, `gradshafranov.f90` 1处。 | 753 |
| `den_edge` | `den_edge` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 19 处；主要在 `input.f90` 7处, `init_common.f90` 5处, `gradshafranov.f90` 2处, `m3dc1_nint.f90` 2处。 | 754 |
| `den0` | `den0` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 25 处；主要在 `init_common.f90` 7处, `gradshafranov.f90` 3处, `init_basicq.f90` 2处, `init_circle.f90` 2处。 | 755 |
| `dendelt` | `dendelt` | real | `0.1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `init_common.f90` 3处。 | 756 |
| `denoff` | `denoff` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `init_common.f90` 3处, `m3dc1_nint.f90` 2处。 | 757 |
| `divertors` | `divertors` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `gradshafranov.f90` 4处。 | 759 |
| `xdiv` | `xdiv` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 760 |
| `zdiv` | `zdiv` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `gradshafranov.f90` 2处。 | 761 |
| `divcur` | `divcur` | real | `0.1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `gradshafranov.f90` 1处, `init_basicq.f90` 1处。 | 762 |
| `xnull` | `xnull` | real | `0.` | Guess for R-coordinate of active x-point | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 20 处；主要在 `diagnostics.f90` 11处, `gradshafranov.f90` 4处, `restart_hdf5.f90` 2处, `gread_restart_c11.fh` 1处。 | 764 |
| `znull` | `znull` | real | `0.` | Guess for Z-coordinate of axtive x-point | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 15 处；主要在 `diagnostics.f90` 6处, `gradshafranov.f90` 4处, `restart_hdf5.f90` 2处, `gread_restart_c11.fh` 1处。 | 766 |
| `mod_null_rs` | `mod_null_rs` | integer | `0` | if 1, you can modify xnull,znull at restart | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `restart_hdf5.f90` 1处。 | 768 |
| `xnull2` | `xnull2` | real | `0.` | Guess for R-coordinate of inactive x-point | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 15 处；主要在 `diagnostics.f90` 11处, `restart_hdf5.f90` 2处, `input.f90` 1处, `output.f90` 1处。 | 770 |
| `znull2` | `znull2` | real | `0.` | Guess for Z-coordinate of inaxtive x-point | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `diagnostics.f90` 6处, `restart_hdf5.f90` 2处, `output.f90` 1处。 | 772 |
| `mod_null_rs2` | `mod_null_rs2` | integer | `0` | if 1, you can modify xnull2,znul2l at restart | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `restart_hdf5.f90` 1处。 | 774 |
| `gs_pf_psi_width` | `gs_pf_psi_width` | real | `0.` | Width of psi smoothing into private flux region | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `gradshafranov.f90` 3处。 | 776 |
| `xnull0` | `xnull0` | real | `0.` | Target R-coordinate of x-point for feedback | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `gradshafranov.f90` 6处。 | 778 |
| `znull0` | `znull0` | real | `0.` | Target Z-coordinate of x-point for feedback | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `gradshafranov.f90` 4处。 | 780 |
| `adapt_qs` | `adapt_qs` | real array | `0.` | Safety factor values to pack around | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`32`。 | 源码引用 3 处；主要在 `adapt.f90` 3处。 | 1175 |
| `adapt_zlow` | `adapt_zlow` | real | `0.` | Z-coordinate below which SOL adaptation is coarse | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1178 |
| `adapt_zup` | `adapt_zup` | real | `0.` | Z-coordinate above which SOL adaptation is coarse | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1180 |

## 模型选项 / Model Options

控制求解的 MHD 方程组、线性/非线性、two-fluid、bootstrap、runaway、温度/压力模型等。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `numvar` | `numvar` | integer | `3` | 1: 2-Field;  2: 4-Field;  3: 6-Field | 1: 2-field；2: 4-field/reduced MHD；3: 6-field/compressible MHD。 | 源码引用 534 处；主要在 `ludef_t.f90` 184处, `ludef_t_gpu.f90` 115处, `time_step_split.f90` 43处, `time_step_unsplit.f90` 27处。 | 399 |
| `linear` | `linear` | integer | `0` | 1: Use linearized equations | 0 非线性；1 线性化方程。2D 非线性通常需 RL=1；线性/complex 需 COM=1 且 `nplanes=1`。 | 源码引用 221 处；主要在 `ludef_t.f90` 69处, `ludef_t_gpu.f90` 40处, `input.f90` 19处, `metricterms_new.f90` 12处。 | 401 |
| `eqsubtract` | `eqsubtract` | integer | `0` | 1: Subtract equilibrium fields | 托卡马克与仿星器：在时间演化方程中扣除已初始化的平衡场，使 0 层作为参考基态；线性模拟会在校验阶段强制为 1。它不改变平衡读取和投影结果。 | 源码引用 195 处；主要在 `ludef_t.f90` 68处, `ludef_t_gpu.f90` 35处, `output.f90` 14处, `diagnostics.f90` 13处。 | 403 |
| `extsubtract` | `extsubtract` | integer | `0` | 1: Subtract fields from non-axisymmetric coils | 托卡马克：1 把 RMP/error field 保存为独立外场，而不是直接写入扰动场。仿星器：`itaylor=41,type_ext_field=2` 必须为 1，程序先读 total field，再读 external field，并把 total-external 作为动态场。 | 源码引用 32 处；主要在 `rmp.f90` 14处, `output.f90` 11处, `newpar.f90` 3处, `input.f90` 2处。 | 405 |
| `icsubtract` | `icsubtract` | integer | `0` | 1: Subtract fields from poloidal field coils | 托卡马克：1 把 PF 线圈磁通与等离子体磁通分开保存；求总磁场/磁区时仍会重新相加。0 直接把线圈磁通加入 `psi_field(0)`。仿星器：没有对应的 VMEC 线圈分解路径，通常保持 0。 | 源码引用 82 处；主要在 `ludef_t.f90` 34处, `ludef_t_gpu.f90` 18处, `gradshafranov.f90` 13处, `output.f90` 7处。 | 407 |
| `idens` | `idens` | integer | `0` | 1: Include density equation | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 111 处；主要在 `ludef_t.f90` 31处, `time_step_split.f90` 18处, `ludef_t_gpu.f90` 15处, `metricterms_new_gpu.f90` 14处。 | 409 |
| `ipres` | `ipres` | integer | `0` | 1: Include total pressure equation | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 128 处；主要在 `time_step_split.f90` 45处, `ludef_t.f90` 21处, `ludef_t_gpu.f90` 20处, `time_step_unsplit.f90` 17处。 | 411 |
| `ipressplit` | `ipressplit` | integer | `0` | 1: Separate pressure solves from field solves | 仅 `isplitstep=1` 且 `numvar=3` 时允许；把压力/温度求解从场求解分离。 | 源码引用 69 处；主要在 `time_step_split.f90` 32处, `ludef_t_gpu.f90` 14处, `ludef_t.f90` 12处, `input.f90` 8处。 | 413 |
| `itemp` | `itemp` | integer | `0` | 1: Advance Temperatures rather than Pressures | 1 时推进温度而不是压力；要求 `ipressplit=1`，且 `z_ion` 必须为 1。 | 源码引用 50 处；主要在 `input.f90` 11处, `time_step_split.f90` 8处, `transport.f90` 7处, `ludef_t.f90` 6处。 | 415 |
| `iadiabat` | `iadiabat` | integer | `1` | 1: Correct itemp=1 for time-varying density | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `ludef_t.f90` 3处, `ludef_t_gpu.f90` 3处, `temperature_plots.f90` 1处。 | 417 |
| `gyro` | `gyro` | integer | `0` | 1: Include Braginskii gyroviscosity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 25 处；主要在 `ludef_t.f90` 8处, `diagnostics.f90` 3处, `read_gyro.f90` 3处, `ludef_t_gpu.f90` 2处。 | 419 |
| `igauge` | `igauge` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处, `model.f90` 1处。 | 421 |
| `inertia` | `inertia` | integer | `1` | 1: Include V.Grad(V) terms | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 72 处；主要在 `metricterms_new_gpu.f90` 51处, `metricterms_new.f90` 21处。 | 422 |
| `itwofluid` | `itwofluid` | integer | `1` | 1: -electron 2F,  2: ion 2F | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 89 处；主要在 `metricterms_new.f90` 33处, `metricterms_new_gpu.f90` 33处, `ludef_t.f90` 13处, `electrostatic_potential.f90` 6处。 | 424 |
| `ibootstrap` | `ibootstrap` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 托卡马克：0 关闭；1 按 psi 读取 bootstrap 系数，2 按 Te，3 按 `1-Te/Temax` 并使用扩展系数文件。它在平衡完成后的磁通/环向场演化方程中加入 bootstrap 项，不覆盖初始电流。仿星器：没有专用 VMEC/ST bootstrap 初始化，除非已验证模型与系数，否则保持 0。 | 源码引用 115 处；主要在 `newpar.f90` 25处, `adapt.f90` 20处, `bootstrap.f90` 19处, `transport.f90` 19处。 | 426 |
| `irunaway` | `irunaway` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 86 处；主要在 `time_step_split.f90` 19处, `time_step_unsplit.f90` 12处, `ludef_t.f90` 10处, `ludef_t_gpu.f90` 10处。 | 427 |
| `cre` | `cre` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `metricterms_new.f90` 2处, `metricterms_new_gpu.f90` 2处, `runaway.f90` 2处, `runaway_advection.f90` 2处。 | 428 |
| `ra_cyc` | `ra_cyc` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 15 处；主要在 `ludef_t.f90` 11处, `runaway_advection.f90` 2处, `ludef_t_gpu.f90` 1处, `time_step_split.f90` 1处。 | 429 |
| `radiff` | `radiff` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处。 | 430 |
| `rjra` | `rjra` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `init_common.f90` 1处。 | 431 |
| `ra_characteristics` | `ra_characteristics` | integer | `0` | 1: Use the method of characteristics to advance the RE advection equation | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `electric_field.f90` 3处, `ludef_t.f90` 1处, `newpar.f90` 1处, `time_step_split.f90` 1处。 | 432 |
| `bzsign` | `bzsign` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 13 处；主要在 `runaway_advection.f90` 4处, `particle.f90` 3处, `init_common.f90` 2处, `metricterms_new.f90` 2处。 | 434 |
| `imp_bf` | `imp_bf` | integer | `0` | 1: Include implicit equation for f | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 64 处；主要在 `ludef_t.f90` 21处, `ludef_t_gpu.f90` 21处, `time_step_split.f90` 8处, `time_step_unsplit.f90` 6处。 | 435 |
| `imp_temp` | `imp_temp` | integer | `0` | 1: Include implicit equation for temperature | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `input.f90` 3处, `newpar.f90` 1处。 | 437 |
| `nosig` | `nosig` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 15 处；主要在 `metricterms_new_gpu.f90` 10处, `metricterms_new.f90` 5处。 | 439 |
| `itor` | `itor` | integer | `0` | 1: Use toroidal geometry | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 457 处；主要在 `metricterms_new_gpu.f90` 192处, `metricterms_new.f90` 133处, `gyroviscosity.f90` 40处, `harned_mikic.f90` 14处。 | 440 |
| `iohmic_heating` | `iohmic_heating` | integer | `1` | 1: Include Ohmic heating | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `ludef_t.f90` 2处, `ludef_t_gpu.f90` 2处。 | 442 |
| `irad_heating` | `irad_heating` | integer | `1` | 1: Include radiation heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `ludef_t.f90` 4处, `ludef_t_gpu.f90` 4处。 | 444 |
| `gravr` | `gravr` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 42 处；主要在 `metricterms_new.f90` 19处, `metricterms_new_gpu.f90` 19处, `init_mri.f90` 2处, `output.f90` 1处。 | 447 |
| `gravz` | `gravz` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 47 处；主要在 `metricterms_new.f90` 22处, `metricterms_new_gpu.f90` 22处, `init_gmode.f90` 1处, `output.f90` 1处。 | 448 |
| `istatic` | `istatic` | integer | `0` | 1: Do not advance velocity fields | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `ludef_t.f90` 4处, `ludef_t_gpu.f90` 4处, `time_step.f90` 1处, `time_step_split.f90` 1处。 | 449 |
| `iestatic` | `iestatic` | integer | `0` | 1: Do not advance magnetic fields | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `ludef_t.f90` 3处, `ludef_t_gpu.f90` 3处, `time_step.f90` 1处, `time_step_split.f90` 1处。 | 451 |
| `chiiner` | `chiiner` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `ludef_t_gpu.f90` 5处, `ludef_t.f90` 3处。 | 453 |
| `ieq_bdotgradt` | `ieq_bdotgradt` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 24 处；主要在 `ludef_t.f90` 12处, `ludef_t_gpu.f90` 12处。 | 454 |
| `iwall_is_limiter` | `iwall_is_limiter` | integer | `1` | 1 = Wall acts as limiter | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `gradshafranov.f90` 3处, `diagnostics.f90` 2处, `particle.f90` 1处, `particle_com.f90` 1处。 | 455 |
| `no_vdg_T` | `no_vdg_T` | integer | `0` | 1: do not include V dot grad T in Temp equation (debug) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处。 | 457 |
| `ibootstrap_model` | `ibootstrap_model` | integer | `0` | 1: J_BS = alpha F <p,psi> B | 托卡马克：1/3 选 Sauter-Angioni，2/4 选 Redl，3/4 为简化方程实现，5 为 constant-Lambda；应与非零 `ibootstrap` 配套。`ibootstrap=3` 配模型 1/3 当前会停止。仿星器：没有专用三维 bootstrap 平衡闭合。 源码用法：在 `bootstrap.f90` 中选择 bootstrap closure：1/3 为 Sauter & Angioni，2/4 为 Redl，5 为 constant-Lambda 分支。 | 源码引用 29 处；主要在 `bootstrap.f90` 24处, `ludef_t.f90` 4处, `output.f90` 1处。 | 460 |
| `bootstrap_alpha` | `bootstrap_alpha` | real | `0.` | alpha parameter in bootstrap current model | 托卡马克：bootstrap 项的统一幅值乘子，默认 0；打开 `ibootstrap/model` 后仍需给非零值才有驱动。仿星器：仅在自行验证并启用同一演化闭合时有意义。 | 源码引用 13 处；主要在 `bootstrap.f90` 12处, `output.f90` 1处。 | 462 |
| `ibootstrap_regular` | `ibootstrap_regular` | real | `1e-8` | Regularization parameter Default=1e-8 | 托卡马克：bootstrap 计算中小 Bp、温度梯度和归一化温度的正则化尺度，默认 `1e-8`，不表示电流比例。仿星器：只有启用并验证 bootstrap 路径时使用。 | 源码引用 8 处；主要在 `bootstrap.f90` 8处。 | 464 |
| `kinetic` | `kinetic` | integer | `0` | 1: Use kinetic PIC; 2: CGL incompressible; 3: CGL | 1: kinetic PIC hot ion pressure；2: incompressible CGL；3: full CGL。2/3 要求 linear=1,isplitstep=0,ipres=1,itemp=0,ipressplit=0。 | 源码引用 60 处；主要在 `ludef_t.f90` 15处, `ludef_t_gpu.f90` 9处, `gradshafranov.f90` 6处, `init_common.f90` 5处。 | 466 |

## 输运系数 / Transport Coefficients

粘性、电阻率、热导、粒子扩散等输运模型参数；若使用函数型模型，开关参数决定下面系数的解释。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `ivisfunc` | `ivisfunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `transport.f90` 6处, `m3dc1_nint.f90` 4处。 | 299 |
| `amuoff` | `amuoff` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `transport.f90` 3处, `m3dc1_nint.f90` 2处。 | 300 |
| `amudelt` | `amudelt` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 3处。 | 301 |
| `amuoff2` | `amuoff2` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 302 |
| `amudelt2` | `amudelt2` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 303 |
| `amu` | `amu` | real | `0.` | Isotropic viscosity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 13 处；主要在 `input.f90` 3处, `transport.f90` 3处, `m3dc1_nint.f90` 2处, `read_namelist.cpp` 2处。 | 304 |
| `amuc` | `amuc` | real | `0.` | Compressional viscosity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `input.f90` 3处, `m3dc1_nint.f90` 2处, `output.f90` 1处, `transport.f90` 1处。 | 306 |
| `amue` | `amue` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 308 |
| `amupar` | `amupar` | real | `0.` | Parallel viscosity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 17 处；主要在 `ludef_t.f90` 7处, `diagnostics.f90` 2处, `metricterms_new.f90` 2处, `metricterms_new_gpu.f90` 2处。 | 309 |
| `amu_edge` | `amu_edge` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `transport.f90` 5处, `m3dc1_nint.f90` 4处。 | 311 |
| `amu_wall` | `amu_wall` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 312 |
| `amu_wall_off` | `amu_wall_off` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 313 |
| `amu_wall_delt` | `amu_wall_delt` | real | `0.1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 314 |
| `iresfunc` | `iresfunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 11 处；主要在 `m3dc1_nint.f90` 5处, `transport.f90` 5处, `input.f90` 1处。 | 316 |
| `etaoff` | `etaoff` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 3处, `transport.f90` 2处。 | 317 |
| `etadelt` | `etadelt` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `m3dc1_nint.f90` 2处, `transport.f90` 2处。 | 318 |
| `etar` | `etar` | real | `0.` | Isotropic resistivity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 16 处；主要在 `transport.f90` 10处, `m3dc1_nint.f90` 2处, `read_namelist.cpp` 2处, `error_estimate.f90` 1处。 | 319 |
| `eta0` | `eta0` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 17 处；主要在 `transport.f90` 8处, `mackenbach_profiles.f90` 4处, `input.f90` 2处, `m3dc1_nint.f90` 2处。 | 321 |
| `eta_fac` | `eta_fac` | real | `1.` | Uniform resistivity multiplier | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 21 处；主要在 `transport.f90` 14处, `mackenbach_profiles.f90` 4处, `m3dc1_nint.f90` 2处, `input.f90` 1处。 | 322 |
| `eta_mod` | `eta_mod` | integer | `0` | 1 = remove d/dphi terms in resistivity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `ludef_t.f90` 4处, `ludef_t_gpu.f90` 4处。 | 324 |
| `eta_te_offset` | `eta_te_offset` | real | `0.` | Offset in Te when calculating eta | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `m3dc1_nint.f90` 2处, `transport.f90` 2处, `diagnostics.f90` 1处, `input.f90` 1处。 | 326 |
| `ikprad_te_offset` | `ikprad_te_offset` | integer | `0` | If 1, eta_te_offset also applied to kprad | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `diagnostics.f90` 1处, `kprad_m3dc1.f90` 1处。 | 328 |
| `eta_max` | `eta_max` | real | `0.` | Maximum value of resistivity in the plasma region | 若 <=0，校验阶段置为 `eta_vac`。 运行时默认：`eta_max<=0` 时改为 `eta_vac`。 | 源码引用 8 处；主要在 `input.f90` 3处, `m3dc1_nint.f90` 3处, `transport.f90` 2处。 | 330 |
| `eta_min` | `eta_min` | real | `0.` | Minimum value of resistivity in the plasma region | 若 <=0，校验阶段置为 0。 运行时默认：`eta_min<=0` 时改为 0。 | 源码引用 7 处；主要在 `input.f90` 4处, `transport.f90` 2处, `m3dc1_nint.f90` 1处。 | 332 |
| `ikappafunc` | `ikappafunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `transport.f90` 8处, `m3dc1_nint.f90` 2处。 | 335 |
| `ikapparfunc` | `ikapparfunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 13 处；主要在 `m3dc1_nint.f90` 3处, `transport.f90` 3处, `input.f90` 2处, `ludef_t.f90` 2处。 | 336 |
| `ikapscale` | `ikapscale` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `m3dc1_nint.f90` 1处。 | 337 |
| `ikappar_ni` | `ikappar_ni` | integer | `1` | Include 1/n terms in parallel heat flux | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `ludef_t.f90` 1处, `parallel_heat_flux.f90` 1处。 | 338 |
| `kappaoff` | `kappaoff` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 3处。 | 340 |
| `kappadelt` | `kappadelt` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `transport.f90` 6处。 | 341 |
| `kappat` | `kappat` | real | `0.` | Isotropic thermal conductivity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `m3dc1_nint.f90` 3处, `transport.f90` 3处, `read_namelist.cpp` 2处, `mackenbach_profiles.f90` 1处。 | 342 |
| `kappa0` | `kappa0` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 22 处；主要在 `transport.f90` 11处, `mackenbach_profiles.f90` 5处, `m3dc1_nint.f90` 4处, `init_basicq.f90` 1处。 | 344 |
| `kappar` | `kappar` | real | `0.` | Parallel thermal conductivity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 23 处；主要在 `ludef_t.f90` 4处, `ludef_t_gpu.f90` 4处, `input.f90` 3处, `transport.f90` 3处。 | 345 |
| `kappari_fac` | `kappari_fac` | real | `1.` | Ion parallel thermal conductivity factor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处。 | 347 |
| `tcrit` | `tcrit` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 349 |
| `k_fac` | `k_fac` | real | `1.` | multiplies toroidal field in denominator of PTC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `m3dc1_nint.f90` 3处。 | 350 |
| `kappax` | `kappax` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `ludef_t.f90` 2处, `m3dc1_nint.f90` 1处。 | 352 |
| `kappah` | `kappah` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `m3dc1_nint.f90` 8处, `transport.f90` 2处。 | 353 |
| `kappag` | `kappag` | real | `0.` | Thermal diffusion proportional to pressure gradient | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `metricterms_new.f90` 2处, `metricterms_new_gpu.f90` 2处, `input.f90` 1处, `ludef_t.f90` 1处。 | 354 |
| `kappaf` | `kappaf` | real | `1.` | Factor to multiply kappa when grad(p) < gradp_crit | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 2处, `transport.f90` 2处, `input.f90` 1处。 | 356 |
| `gradp_crit` | `gradp_crit` | real | `0.` | Critical pressure gradient in kappag/kappaf models | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `m3dc1_nint.f90` 2处, `transport.f90` 2处, `input.f90` 1处, `ludef_t.f90` 1处。 | 358 |
| `kappa_max` | `kappa_max` | real | `0.` | Maximum value of kappa in the plasma region | 若 <=0，校验阶段置为 `kappar`。 运行时默认：`kappa_max<=0` 时改为 `kappar`。 | 源码引用 6 处；主要在 `m3dc1_nint.f90` 5处, `input.f90` 1处。 | 360 |
| `kappar_max` | `kappar_max` | real | `0.` | Maximum value of kappa in the plasma region | 若 <=0，校验阶段置为 `kappar`。 运行时默认：`kappar_max<=0` 时改为 `kappar`。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `input.f90` 1处。 | 362 |
| `kappar_min` | `kappar_min` | real | `0.` | Maximum value of kappa in the plasma region | 若 <=0，校验阶段置为 `kappar`。 运行时默认：`kappar_min<=0` 时改为 `kappar`。 | 源码引用 4 处；主要在 `m3dc1_nint.f90` 3处, `input.f90` 1处。 | 364 |
| `temin_qd` | `temin_qd` | real | `0.` | Min. Temp. used in Equipartition term for ipres=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 366 |
| `kappai_fac` | `kappai_fac` | real | `1.` | Factor to multiply kappa when evaluating ion perp. thermal diffusivity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `input.f90` 2处, `ludef_t.f90` 2处, `ludef_t_gpu.f90` 2处, `metricterms_new.f90` 1处。 | 368 |
| `idenmfunc` | `idenmfunc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `transport.f90` 4处, `m3dc1_nint.f90` 2处。 | 371 |
| `denm` | `denm` | real | `0.` | Density diffusion coefficient | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 11 处；主要在 `m3dc1_nint.f90` 5处, `output.f90` 2处, `transport.f90` 2处, `diagnostics.f90` 1处。 | 372 |
| `denmt` | `denmt` | real | `0.` | Temperature dependent density diffusion coefficient | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 5处。 | 374 |
| `denmmin` | `denmmin` | real | `0.` | Minimum density diffusion coefficient | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `transport.f90` 1处。 | 376 |
| `denmmax` | `denmmax` | real | `1.e6` | Maximum density diffusion coefficient | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `m3dc1_nint.f90` 5处, `transport.f90` 1处。 | 378 |

## 超扩散 / Hyper Diffusivity

磁场、压力和速度方程中的超扩散/平滑系数及其缩放方式。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `deex` | `deex` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `m3dc1_nint.f90` 1处。 | 785 |
| `hyper` | `hyper` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `input.f90` 3处, `diagnostics.f90` 1处, `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处。 | 786 |
| `hyperc` | `hyperc` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `hypervisc.f90` 1处, `input.f90` 1处, `m3dc1_nint.f90` 1处, `output.f90` 1处。 | 787 |
| `hyperi` | `hyperi` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `m3dc1_nint.f90` 1处, `output.f90` 1处。 | 788 |
| `hyperp` | `hyperp` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `m3dc1_nint.f90` 1处, `output.f90` 1处。 | 789 |
| `hyperv` | `hyperv` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `hypervisc.f90` 1处, `m3dc1_nint.f90` 1处, `output.f90` 1处。 | 790 |
| `ihypdx` | `ihypdx` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `m3dc1_nint.f90` 2处。 | 791 |
| `ihypeta` | `ihypeta` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 66 处；主要在 `metricterms_new_gpu.f90` 31处, `metricterms_new.f90` 28处, `input.f90` 4处, `electrostatic_potential.f90` 2处。 | 792 |
| `ihypkappa` | `ihypkappa` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `metricterms_new_gpu.f90` 5处, `metricterms_new.f90` 4处。 | 793 |
| `imp_hyper` | `imp_hyper` | integer | `0` | 1: implicit hyper-resistivity in psi equation | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 44 处；主要在 `ludef_t.f90` 10处, `metricterms_new_gpu.f90` 8处, `time_step_split.f90` 6处, `ludef_t_gpu.f90` 5处。 | 794 |

## 边界条件 / Boundary Conditions

场、压力/温度/密度、速度和电流在计算边界上的约束。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `isurface` | `isurface` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `biharmonic.f90` 1处。 | 799 |
| `icurv` | `icurv` | integer | `2` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `scorec_mesh.f90` 1处。 | 800 |
| `nonrect` | `nonrect` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `init_eigen.f90` 1处, `init_frs.f90` 1处, `init_ftz.f90` 1处, `input.f90` 1处。 | 801 |
| `ifixedb` | `ifixedb` | integer | `0` | 1: Force psi=0 on boundary | 托卡马克：GS 外边界开关；大于等于 1 时把计算域外边界磁通置 0，0 时使用已建立的 plasma/PF 线圈真空场边界值并允许 LCFS 在域内更新。仿星器：VMEC/外场初始化不通过它选择固定或自由边界。 | 源码引用 11 处；主要在 `gradshafranov.f90` 3处, `init_eqdsk.f90` 2处, `diagnostics.f90` 1处, `init_dskbal.f90` 1处。 | 802 |
| `com_bc` | `com_bc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 3处。 | 804 |
| `vor_bc` | `vor_bc` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 3处。 | 805 |
| `iconst_p` | `iconst_p` | integer | `1` | 1: Hold pressure constant on boundary | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 12 处；主要在 `model.f90` 8处, `metricterms_new_gpu.f90` 3处, `metricterms_new.f90` 1处。 | 806 |
| `iconst_n` | `iconst_n` | integer | `1` | 1: Hold density constant on boundary | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 2处, `kprad_m3dc1.f90` 1处。 | 808 |
| `iconst_t` | `iconst_t` | integer | `1` | 1: Hold temperature constant on boundary | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `model.f90` 4处。 | 810 |
| `iconst_bn` | `iconst_bn` | integer | `1` | 1: Hold normal field constant on boundary | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 2处, `ludef_t.f90` 1处。 | 812 |
| `iconst_bz` | `iconst_bz` | integer | `0` | 1: Hold toroidal field constant on boundary | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `model.f90` 2处。 | 814 |
| `inograd_p` | `inograd_p` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 3处。 | 816 |
| `inograd_t` | `inograd_t` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `model.f90` 3处。 | 817 |
| `inograd_n` | `inograd_n` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `metricterms_new_gpu.f90` 3处, `model.f90` 2处, `kprad_m3dc1.f90` 1处。 | 818 |
| `inonormalflow` | `inonormalflow` | integer | `1` | 1: No-normal-flow boundary condition | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 34 处；主要在 `metricterms_new_gpu.f90` 22处, `model.f90` 7处, `ludef_t.f90` 3处, `ludef_t_gpu.f90` 2处。 | 819 |
| `inoslip_pol` | `inoslip_pol` | integer | `1` | 1: No-slip boundary condition on pol. velocity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 36 处；主要在 `metricterms_new_gpu.f90` 23处, `model.f90` 7处, `ludef_t.f90` 3处, `ludef_t_gpu.f90` 2处。 | 821 |
| `inoslip_tor` | `inoslip_tor` | integer | `1` | 1: No-slip boundary condition on tor. velocity | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 14 处；主要在 `metricterms_new_gpu.f90` 12处, `model.f90` 2处。 | 823 |
| `inostress_tor` | `inostress_tor` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `model.f90` 2处。 | 825 |
| `inocurrent_pol` | `inocurrent_pol` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 19 处；主要在 `metricterms_new_gpu.f90` 17处, `model.f90` 2处。 | 826 |
| `inocurrent_tor` | `inocurrent_tor` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 11 处；主要在 `metricterms_new_gpu.f90` 7处, `model.f90` 2处, `newpar.f90` 1处, `newvar.f90` 1处。 | 827 |
| `inocurrent_norm` | `inocurrent_norm` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 17 处；主要在 `metricterms_new_gpu.f90` 15处, `model.f90` 2处。 | 828 |
| `ifbound` | `ifbound` | integer | `-1` | Boundary condition on 'f' field. 1 = Dirichlet, 2 = Neumann | -1 表示校验后按编译版本设置：complex 为 2，real 为 1。 运行时默认：`ifbound=-1` 时，complex 版本默认 2，real 版本默认 1。 | 源码引用 12 处；主要在 `model.f90` 4处, `input.f90` 3处, `newvar.f90` 3处, `ludef_t.f90` 1处。 | 829 |
| `iconstflux` | `iconstflux` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `newpar.f90` 1处, `time_step.f90` 1处。 | 831 |
| `iper` | `iper` | integer | `0` | 1: Periodic boundary condition in R direction | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 24 处；主要在 `model.f90` 9处, `boundary.f90` 4处, `rmp.f90` 3处, `biharmonic.f90` 1处。 | 832 |
| `jper` | `jper` | integer | `0` | 1: Preiodic boundary condition in Z direction | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 24 处；主要在 `model.f90` 9处, `boundary.f90` 4处, `rmp.f90` 3处, `biharmonic.f90` 1处。 | 834 |
| `tebound` | `tebound` | real | `-1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `model.f90` 2处。 | 836 |
| `tibound` | `tibound` | real | `-1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `model.f90` 2处。 | 837 |

## 电阻壁/真空/导体区 / Resistive Wall

真空、导体壁、多区域、wall break、RE killer coil 等电阻参数。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `eta_wall` | `eta_wall` | real | `1e-3` | Resistivity of conducting wall region | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `input.f90` 3处, `output.f90` 1处, `resistive_wall.f90` 1处。 | 840 |
| `eta_wallRZ` | `eta_wallRZ` | real | `-1.` | Resistivity of conducting wall region | -1 表示校验后取 `eta_wall`。 运行时默认：`eta_wallRZ<0` 时改为 `eta_wall`。 | 源码引用 2 处；主要在 `input.f90` 1处, `resistive_wall.f90` 1处。 | 842 |
| `eta_vac` | `eta_vac` | real | `1.` | Resistivity of vacuum region | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `input.f90` 3处, `m3dc1_nint.f90` 1处, `transport.f90` 1处。 | 844 |
| `iwall_breaks` | `iwall_breaks` | integer | `0` | Number of wall break regions | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 846 |
| `eta_break` | `eta_break` | real array | `1.` | Resistivity of wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 848 |
| `wall_break_xmin` | `wall_break_xmin` | real array | `0.` | Minimum x coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 850 |
| `wall_break_xmax` | `wall_break_xmax` | real array | `0.` | Maximum x coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 852 |
| `wall_break_zmin` | `wall_break_zmin` | real array | `0.` | Minimum z coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 854 |
| `wall_break_zmax` | `wall_break_zmax` | real array | `0.` | Maximum z coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 856 |
| `wall_break_phimin` | `wall_break_phimin` | real array | `0.` | Minimum phi coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 858 |
| `wall_break_phimax` | `wall_break_phimax` | real array | `0.` | Maximum phi coordinate for wall break | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 860 |
| `iwall_regions` | `iwall_regions` | integer | `0` | Number of resistive wall regions | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `resistive_wall.f90` 5处, `input.f90` 2处, `output.f90` 2处。 | 862 |
| `wall_region_eta` | `wall_region_eta` | real array | `1e-3` | Resistivity of each wall region | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`20`。 | 源码引用 3 处；主要在 `input.f90` 1处, `output.f90` 1处, `resistive_wall.f90` 1处。 | 864 |
| `wall_region_etaRZ` | `wall_region_etaRZ` | real array | `-1.` | Poloidal Resistivity of each wall region | -1 表示校验后逐区域取对应 `wall_region_eta(i)`。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 运行时默认：每个 `wall_region_etaRZ(i)<0` 时改为对应 `wall_region_eta(i)`。 数组长度/上限：`20`。 | 源码引用 4 处；主要在 `input.f90` 2处, `output.f90` 1处, `resistive_wall.f90` 1处。 | 866 |
| `eta_zone` | `eta_zone` | real array | `0.` | Resistivity of mesh zone | 托卡马克：为 `zone_type(i)=2` 的导体 zone 指定标量电阻率，正值优先于全局 `eta_wall`；适合显式第一壁/导体区域。仿星器：数值优先级相同，但只有用户事先设计了与 VMEC/bloat 映射后物理位置一致的导体 zone 才有物理意义。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 4 处；主要在 `resistive_wall.f90` 4处。 | 868 |
| `etaRZ_zone` | `etaRZ_zone` | real array | `0.` | Poloidal resistivity of mesh zone | 托卡马克：为导体 zone 指定极向电阻率，正值优先于 `eta_zone`，否则回退到全局 `eta_wallRZ`。仿星器：用法相同，但程序不会检查该 zone 是否真的对应物理导体壁。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 870 |
| `wall_region_filename` | `wall_region_filename` | character(len=256) array | `""` | Resistivity of each wall region | 字符数组；每个 wall region 轮廓点文件名。 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 数组长度/上限：`20`。 | 源码引用 1 处；主要在 `resistive_wall.f90` 1处。 | 873 |
| `eta_rekc` | `eta_rekc` | real | `0.` | Resistivity of runaway-electron killer coil (REKC) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `resistive_wall.f90` 6处。 | 875 |
| `ntor_rekc` | `ntor_rekc` | integer | `0` | Toroidal mode number of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 877 |
| `mpol_rekc` | `mpol_rekc` | integer | `0` | Poloidal mode number of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `resistive_wall.f90` 6处。 | 879 |
| `isym_rekc` | `isym_rekc` | integer | `0` | if nonzero, a double helix | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 881 |
| `phi_rekc` | `phi_rekc` | real | `0.` | Toroidal angle of fixed point of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 883 |
| `theta_rekc` | `theta_rekc` | real | `0.` | Poloidal angle of fixed point of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `resistive_wall.f90` 6处。 | 885 |
| `sigma_rekc` | `sigma_rekc` | real | `0.` | Angular half-width of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `resistive_wall.f90` 6处。 | 887 |
| `rzero_rekc` | `rzero_rekc` | real | `0.` | R0 for computing theta of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 889 |
| `zzero_rekc` | `zzero_rekc` | real | `0.` | Z0 for computing theta of REKC | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `resistive_wall.f90` 2处。 | 891 |

## 时间推进 / Time Step

时间积分、分裂/非分裂推进、可变时间步、矩阵/预条件器重算及线性增长率停止条件。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `ntimemax` | `ntimemax` | integer | `20` | Total number of timesteps | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `kprad_test.f90` 2处, `newpar.f90` 2处。 | 470 |
| `integrator` | `integrator` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `input.f90` 1处, `ludef_t.f90` 1处, `ludef_t_gpu.f90` 1处, `newpar.f90` 1处。 | 472 |
| `isplitstep` | `isplitstep` | integer | `1` | 0: Unsplit time step;  1: Split time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 57 处；主要在 `ludef_t.f90` 17处, `ludef_t_gpu.f90` 15处, `input.f90` 11处, `time_step.f90` 8处。 | 473 |
| `iteratephi` | `iteratephi` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `input.f90` 2处, `time_step_split.f90` 1处, `time_step_unsplit.f90` 1处。 | 475 |
| `imp_mod` | `imp_mod` | integer | `1` | Type of split step.  0: Standard;  1: Caramana | 源码当前默认 1。0: standard/theta implicit；1: Caramana split-step 形式。 运行时默认：`isplitstep=0` 时校验阶段强制 `imp_mod=0`。 | 源码引用 20 处；主要在 `ludef_t.f90` 9处, `ludef_t_gpu.f90` 9处, `electrostatic_potential.f90` 1处, `input.f90` 1处。 | 476 |
| `caramana_fac` | `caramana_fac` | real | `1.` | Coefficient for the explicit term in Caramana method. 1: Caramana; 0: implicit | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `ludef_t.f90` 3处。 | 478 |
| `idiff` | `idiff` | integer | `0` | only solve for difference in B,p | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 48 处；主要在 `model.f90` 14处, `ludef_t.f90` 13处, `ludef_t_gpu.f90` 13处, `time_step_split.f90` 5处。 | 480 |
| `idifv` | `idifv` | integer | `0` | only solve for difference in v | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `ludef_t.f90` 3处, `ludef_t_gpu.f90` 3处, `time_step_split.f90` 1处。 | 481 |
| `irecalc_eta` | `irecalc_eta` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `time_step_split.f90` 2处。 | 482 |
| `iconst_eta` | `iconst_eta` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 483 |
| `itime_independent` | `itime_independent` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 45 处；主要在 `ludef_t.f90` 22处, `ludef_t_gpu.f90` 19处, `input.f90` 2处, `output.f90` 1处。 | 484 |
| `thimp` | `thimp` | real | `0.5` | Implicitness of timestep (.5<thimp<1) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 445 处；主要在 `ludef_t.f90` 310处, `ludef_t_gpu.f90` 113处, `kprad_m3dc1.f90` 16处, `input.f90` 3处。 | 485 |
| `thimpsm` | `thimpsm` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `newvar.f90` 2处。 | 487 |
| `harned_mikic` | `harned_mikic` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `harned_mikic.f90` 8处, `ludef_t.f90` 2处。 | 488 |
| `isources` | `isources` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 2处。 | 489 |
| `nskip` | `nskip` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `time_step.f90` 1处。 | 490 |
| `pskip` | `pskip` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 源码当前默认 0；官方文档写 1。控制预条件器重算/复用相关周期。 | 源码引用 4 处；主要在 `time_step_split.f90` 4处。 | 491 |
| `iskippc` | `iskippc` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `get_pc_skip_count.f90` 2处。 | 492 |
| `dt` | `dt` | real | `0.1` | Size of time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1498 处；主要在 `ludef_t.f90` 1014处, `ludef_t_gpu.f90` 334处, `bootstrap.f90` 36处, `electrostatic_potential.f90` 20处。 | 493 |
| `ddt` | `ddt` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 495 |
| `frequency` | `frequency` | real | `0.` | Frequency in time-independent calculations | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 25 处；主要在 `ludef_t.f90` 9处, `ludef_t_gpu.f90` 9处, `input.f90` 4处, `init_circle.f90` 1处。 | 497 |
| `gamma_gr_stop` | `gamma_gr_stop` | integer | `0` | Stop linear simulation when growth rate gamma is converged | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `output.f90` 1处。 | 500 |
| `nt_gamma_gr` | `nt_gamma_gr` | integer | `10` | Number of time steps considered for gamma convergence check | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `output.f90` 3处。 | 501 |
| `gamma_gr_stop_std` | `gamma_gr_stop_std` | real | `0.01` | Standard deviation under which gamma is considered converged | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `output.f90` 1处。 | 502 |
| `dtmin` | `dtmin` | real | `4.0` | minimum time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `time_step.f90` 1处。 | 507 |
| `dtmax` | `dtmax` | real | `40.` | maximum time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `time_step.f90` 1处。 | 508 |
| `dtkecrit` | `dtkecrit` | real | `0.0` | ekin limit on timestep | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `time_step.f90` 4处, `newpar.f90` 1处。 | 509 |
| `dtfrac` | `dtfrac` | real | `0.1` | fractional change of time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `time_step.f90` 3处。 | 510 |
| `max_repeat` | `max_repeat` | integer | `1` | maximum number of times a time step can be attempted | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `time_step.f90` 1处。 | 511 |
| `ksp_max` | `ksp_max` | integer | `10000` | maximum number of ksp iterations without repeating time step | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `time_step.f90` 2处。 | 513 |
| `ksp_min` | `ksp_min` | integer | `500` | time step is increased if max ksp iterations is less than this | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `time_step.f90` 2处。 | 515 |
| `ksp_warn` | `ksp_warn` | integer | `1000` | time step is reduced if max ksp iterations exceeds this | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `time_step.f90` 2处。 | 517 |

## 数值选项 / Numerical Options

积分点数、守恒/规整化、物理量 floor、线性模拟重标定等数值控制。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `jadv` | `jadv` | integer | `1` | Use Del*(psi) eqn. instead of psi eqn. | 1 使用环向电流密度方程代替极向磁通方程；官方文档旧表写 0，但当前源码默认是 1。 | 源码引用 174 处；主要在 `metricterms_new_gpu.f90` 56处, `metricterms_new.f90` 42处, `ludef_t.f90` 11处, `electric_field.f90` 8处。 | 521 |
| `int_pts_main` | `int_pts_main` | integer | `25` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 91 处；主要在 `gradshafranov.f90` 13处, `init_common.f90` 12处, `particle.f90` 11处, `particle_com.f90` 8处。 | 524 |
| `int_pts_aux` | `int_pts_aux` | integer | `25` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `auxiliary_fields.f90` 5处, `input.f90` 3处, `diagnostics.f90` 1处, `transport.f90` 1处。 | 525 |
| `int_pts_diag` | `int_pts_diag` | integer | `25` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 14 处；主要在 `diagnostics.f90` 6处, `input.f90` 3处, `gradshafranov.f90` 2处, `init_basicq.f90` 1处。 | 526 |
| `int_pts_tor` | `int_pts_tor` | integer | `5` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 76 处；主要在 `init_common.f90` 12处, `particle.f90` 11处, `particle_com.f90` 8处, `diagnostics.f90` 6处。 | 527 |
| `max_ke` | `max_ke` | real | `1.` | Value of ke at which linear sims are rescaled；(ignore if 0) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `time_step.f90` 1处。 | 528 |
| `equilibrate` | `equilibrate` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `newpar.f90` 3处, `gradshafranov.f90` 1处, `kprad_m3dc1.f90` 1处, `m3dc1_nint.f90` 1处。 | 530 |
| `regular` | `regular` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 21 处；主要在 `transport.f90` 7处, `ludef_t.f90` 4处, `init_vmec.f90` 3处, `init_common.f90` 2处。 | 531 |
| `iset_pe_floor` | `iset_pe_floor` | integer | `0` | 1: Do not let pe drop below pe_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `m3dc1_nint.f90` 3处, `input.f90` 1处。 | 532 |
| `pe_floor` | `pe_floor` | real | `0.` | Minimum allowed value for pe when iset_pe_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `m3dc1_nint.f90` 5处, `input.f90` 1处。 | 534 |
| `iset_pi_floor` | `iset_pi_floor` | integer | `0` | 1: Do not let pi drop below pi_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `m3dc1_nint.f90` 3处, `input.f90` 1处。 | 536 |
| `pi_floor` | `pi_floor` | real | `0.` | Minimum allowed value for pi when iset_pi_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `m3dc1_nint.f90` 5处, `input.f90` 1处。 | 538 |
| `iset_ne_floor` | `iset_ne_floor` | integer | `0` | 1: Do not let ne drop below ne_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `m3dc1_nint.f90` 1处。 | 540 |
| `ne_floor` | `ne_floor` | real | `0.` | Minimum allowed value for ne when iset_ne_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `input.f90` 1处。 | 542 |
| `iset_ni_floor` | `iset_ni_floor` | integer | `0` | 1: Do not let ni drop below ni_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `m3dc1_nint.f90` 1处。 | 544 |
| `ni_floor` | `ni_floor` | real | `0.` | Minimum allowed value for ni when iset_ni_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `input.f90` 1处。 | 546 |
| `iset_te_floor` | `iset_te_floor` | integer | `0` | 1: Do not let Te drop below te_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `m3dc1_nint.f90` 1处。 | 548 |
| `te_floor` | `te_floor` | real | `0.` | Minimum allowed value for Te when iset_te_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `input.f90` 1处。 | 550 |
| `iset_ti_floor` | `iset_ti_floor` | integer | `0` | 1: Do not let Ti drop below ti_floor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `m3dc1_nint.f90` 1处。 | 552 |
| `ti_floor` | `ti_floor` | real | `0.` | Minimum allowed value for Ti when iset_ti_floor=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `m3dc1_nint.f90` 4处, `input.f90` 1处。 | 554 |
| `iprecompute_metric` | `iprecompute_metric` | integer | `0` | 1: precompute full metric tensor | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 13 处；主要在 `newpar.f90` 4处, `element.f90` 1处, `error_estimate.f90` 1处, `gradshafranov.f90` 1处。 | 556 |

## 线性求解器 / Solver

M3D-C1 内部线性求解器通用控制。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `solver_tol` | `solver_tol` | real | `1e-9` | solver tolerance | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `scorec_matrix.f90` 4处。 | 1238 |
| `solver_type` | `solver_type` | integer | `0` | Solver type | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `scorec_matrix.f90` 2处。 | 1240 |
| `num_iter` | `num_iter` | integer | `100` | Maximum number of iterations | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 27 处；主要在 `scorec_matrix.f90` 18处, `m3dc1_scorec.cc` 8处, `m3dc1_scorec.h` 1处。 | 1241 |
| `isolve_with_guess` | `isolve_with_guess` | integer | `0` | newsolve with nonzero initial guess | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 15 处；主要在 `kprad_m3dc1.f90` 8处, `time_step_split.f90` 7处。 | 1242 |

## Trilinos 选项 / Trilinos Options

Trilinos 编译/运行路径下的 Krylov 与预条件器选项。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `krylov_solver` | `krylov_solver` | character(len=50) | `gmres` | Krylov solver | 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 6 处；主要在 `m3dc1_scorec.cc` 3处, `scorec_matrix.f90` 2处, `m3dc1_scorec.h` 1处。 | 1245 |
| `preconditioner` | `preconditioner` | character(len=50) | `dom_decomp` | Preconditioner | 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 30 处；主要在 `m3dc1_matrix.cc` 12处, `PETScInterface.cpp` 8处, `m3dc1_scorec.cc` 5处, `input.f90` 2处。 | 1247 |
| `sub_dom_solver` | `sub_dom_solver` | character(len=50) | `ilu` | Subdomain solver in preconditioner | 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1250 |
| `subdomain_overlap` | `subdomain_overlap` | integer | `1` | subdomain overlap | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `scorec_matrix.f90` 2处。 | 1252 |
| `graph_fill` | `graph_fill` | integer | `0` | graph fill level | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1254 |
| `drop_tolerance` | `ilu_drop_tol` | real | `0.0` | ILU drop tolerance | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1256 |
| `ilu_fill_level` | `ilu_fill` | real | `1.0` | ILU fill level | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1258 |
| `ilu_omega` | `ilu_omega` | real | `1.0` | Relaxation parameter for rILU | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1260 |
| `poly_ord` | `poly_ord` | integer | `1` | Polynomial order for certain preconditioners | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `scorec_matrix.f90` 2处, `m3dc1_scorec.cc` 2处, `m3dc1_scorec.h` 1处。 | 1262 |

## 网格自适应 / Mesh Adaptation

SCOREC/SPR 网格自适应控制；部分参数仅在启用对应库/流程时有效。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `iadapt` | `iadapt` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `newpar.f90` 5处, `input.f90` 1处, `time_step_split.f90` 1处, `time_step_unsplit.f90` 1处。 | 1130 |
| `ispradapt` | `ispradapt` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 17 处；主要在 `newpar.f90` 7处, `auxiliary_fields.f90` 4处, `gradshafranov.f90` 2处, `adapt.f90` 1处。 | 1132 |
| `isprntime` | `isprntime` | integer | `10` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1133 |
| `isprweight` | `isprweight` | real | `0.1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1134 |
| `isprmaxsize` | `isprmaxsize` | real | `0.05` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1135 |
| `isprrefinelevel` | `isprrefinelevel` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1136 |
| `isprcoarsenlevel` | `isprcoarsenlevel` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1137 |
| `iadapt_writevtk` | `iadapt_writevtk` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `adapt.f90` 2处, `newpar.f90` 1处。 | 1140 |
| `iadapt_writesmb` | `iadapt_writesmb` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1143 |
| `iadapt_useH1` | `iadapt_useH1` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `error_estimate.f90` 5处。 | 1144 |
| `iadapt_removeEquiv` | `iadapt_removeEquiv` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `error_estimate.f90` 1处。 | 1145 |
| `adapt_target_error` | `adapt_target_error` | real | `0.0001` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `m3dc1_scorec.cc` 4处, `adapt.f90` 3处。 | 1146 |
| `adapt_ke` | `adapt_ke` | real | `0.0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1147 |
| `iadapt_ntime` | `iadapt_ntime` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `adapt.f90` 3处。 | 1148 |
| `iadapt_max_node` | `iadapt_max_node` | integer | `10000` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `adapt.f90` 2处, `m3dc1_scorec.cc` 2处。 | 1149 |
| `adapt_control` | `adapt_control` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `adapt.f90` 2处, `m3dc1_scorec.cc` 1处。 | 1150 |
| `iadapt_order_p` | `iadapt_order_p` | real | `3.0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1151 |
| `iadaptFaceNumber` | `iadaptFaceNumber` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `m3dc1_scorec.cc` 5处, `adapt.f90` 2处, `m3dc1_scorec.h` 1处。 | 1152 |
| `iadapt_snap` | `iadapt_snap` | integer | `1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `scorec_mesh.f90` 1处。 | 1153 |
| `adapt_factor` | `adapt_factor` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 1155 |
| `adapt_hmin` | `adapt_hmin` | real | `0.001` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1156 |
| `adapt_hmax` | `adapt_hmax` | real | `0.1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1157 |
| `adapt_hmin_rel` | `adapt_hmin_rel` | real | `0.5` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1158 |
| `adapt_hmax_rel` | `adapt_hmax_rel` | real | `2.0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1159 |
| `adapt_smooth` | `adapt_smooth` | real | `2./3. (约 0.6667)` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 1160 |
| `adapt_psin_vacuum` | `adapt_psin_vacuum` | real | `-1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1161 |
| `adapt_psin_wall` | `adapt_psin_wall` | real | `-1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1163 |
| `iadapt_pack_rationals` | `iadapt_pack_rationals` | integer | `0` | Number of mode-rational surfaces to pack mesh around | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `adapt.f90` 4处。 | 1165 |
| `adapt_pack_factor` | `adapt_pack_factor` | real | `0.02` | Width of Lorentzian (in psi_N) for rational mesh packing | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `adapt.f90` 2处。 | 1167 |
| `adapt_coil_delta` | `adapt_coil_delta` | real | `0.` | Parameter for packing mesh around coil locations | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `adapt.f90` 3处。 | 1169 |
| `adapt_pellet_length` | `adapt_pellet_length` | real | `0.` | Length of pellet path to pack mesh along | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `adapt.f90` 1处。 | 1171 |
| `adapt_pellet_delta` | `adapt_pellet_delta` | real | `0.` | Parameter for packing mesh along pellet path | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `adapt.f90` 6处。 | 1173 |

## 源项/汇项 / Sources/Sinks

回路电压/电流控制、pellet、束源、电流驱动、高斯热源、粒子源/汇、ionization 等。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `iheat_sink` | `iheat_sink` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `ludef_t.f90` 2处, `input.f90` 1处, `transport.f90` 1处。 | 243 |
| `vloop` | `vloop` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 19 处；主要在 `newpar.f90` 5处, `restart_hdf5.f90` 3处, `mackenbach_profiles.f90` 2处, `electric_field.f90` 1处。 | 896 |
| `vloopRZ` | `vloopRZ` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `model.f90` 1处。 | 897 |
| `tcur` | `tcur` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `newpar.f90` 3处, `control.f90` 2处, `input.f90` 1处, `mackenbach_profiles.f90` 1处。 | 898 |
| `vloop_freq` | `vloop_freq` | real | `0.` | Loop voltage frequency | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 899 |
| `tcuri` | `tcuri` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `control.f90` 2处, `newpar.f90` 2处。 | 902 |
| `tcurf` | `tcurf` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `control.f90` 2处, `newpar.f90` 2处。 | 903 |
| `tcur_t0` | `tcur_t0` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `control.f90` 2处, `newpar.f90` 1处。 | 904 |
| `tcur_tw` | `tcur_tw` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `control.f90` 2处, `newpar.f90` 1处。 | 905 |
| `control_p` | `control_p` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 907 |
| `control_i` | `control_i` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 908 |
| `control_d` | `control_d` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 909 |
| `control_type` | `control_type` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | -1 不启用电流控制；0 旧算法；1 标准 PID，配合 `control_p/i/d`。 | 源码引用 2 处；主要在 `newpar.f90` 1处, `restart_hdf5.f90` 1处。 | 910 |
| `ipellet` | `ipellet` | integer | `0` | 1 = include a gaussian pellet source | 源码用法：在 `pellet.f90` 中选择密度源分布；正值为持续源，负值用于初始扰动；双位数分布按 `Lor_vol` 数值归一化。 | 源码引用 27 处；主要在 `init_common.f90` 5处, `output.f90` 5处, `pellet.f90` 5处, `input.f90` 3处。 | 914 |
| `irestart_pellet` | `irestart_pellet` | integer | `0` | 1 = read some pellet restart parameters from C1input | restart 时仍从 C1input 覆盖部分 pellet 参数，如 pellet_rate、pellet_var_tor、pellet_var、cloud_pel、pellet_mix、cauchy_fraction。 | 源码引用 3 处；主要在 `restart_hdf5.f90` 3处。 | 916 |
| `ipellet_z` | `ipellet_z` | integer | `0` | Atomic number of pellet (0 = main ion species) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 12 处；主要在 `input.f90` 4处, `kprad_m3dc1.f90` 3处, `init_common.f90` 2处, `pellet.f90` 2处。 | 918 |
| `iread_pellet` | `iread_pellet` | integer | `0` | 1: read pellet info from pellet.dat | 0 用标量 pellet_* 定义单 pellet；1 读 `pellet.dat`，每行一个 pellet，列为 r,phi,z,rate,var,var_tor,velr,velphi,velz,r_p,cloud_pel,pellet_mix,cauchy_fraction。 | 源码引用 1 处；主要在 `pellet.f90` 1处。 | 920 |
| `pellet_r` | `pellet_r_scl` | real | `0.` | Initial radial position of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 33 处；主要在 `pellet.f90` 23处, `restart_hdf5.f90` 4处, `adapt.f90` 2处, `output.f90` 2处。 | 922 |
| `pellet_phi` | `pellet_phi_scl` | real | `0.` | Initial toroidal position of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 30 处；主要在 `pellet.f90` 21处, `restart_hdf5.f90` 3处, `adapt.f90` 2处, `output.f90` 2处。 | 924 |
| `pellet_z` | `pellet_z_scl` | real | `0.` | Initial vertical position of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 24 处；主要在 `pellet.f90` 16处, `restart_hdf5.f90` 3处, `output.f90` 2处, `adapt.f90` 1处。 | 926 |
| `pellet_rate` | `pellet_rate_scl` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 29 处；主要在 `pellet.f90` 14处, `newpar.f90` 3处, `transport.f90` 3处, `init_common.f90` 2处。 | 928 |
| `pellet_var` | `pellet_var_scl` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 36 处；主要在 `pellet.f90` 29处, `output.f90` 2处, `restart_hdf5.f90` 2处, `transport.f90` 2处。 | 929 |
| `pellet_var_tor` | `pellet_var_tor_scl` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 源码用法：读入后若 <=0 会自动补值：`ipellet=15` 用 `pellet_var/pellet_r`，其它分支用 `pellet_var`。 | 源码引用 13 处；主要在 `pellet.f90` 11处, `output.f90` 1处, `restart_hdf5.f90` 1处。 | 930 |
| `pellet_velr` | `pellet_velr_scl` | real | `0.` | Initial radial velocity of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 11 处；主要在 `pellet.f90` 5处, `restart_hdf5.f90` 4处, `output.f90` 2处。 | 931 |
| `pellet_velphi` | `pellet_velphi_scl` | real | `0.` | Initial toroidal velocity of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `pellet.f90` 5处, `restart_hdf5.f90` 3处, `output.f90` 2处。 | 933 |
| `pellet_velz` | `pellet_velz_scl` | real | `0.` | Initial vertical velocity of the pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 14 处；主要在 `pellet.f90` 7处, `restart_hdf5.f90` 3处, `adapt.f90` 2处, `output.f90` 2处。 | 935 |
| `ipellet_abl` | `ipellet_abl` | integer | `0` | 1 = include an ablation model | 源码用法：选择 pellet ablation 模型；1/2 lithium，3 neon，43 carbon/Sergeev06。`ipellet_z=0` 时会由模型推断默认 Z。 | 源码引用 20 处；主要在 `pellet.f90` 10处, `diagnostics.f90` 5处, `transport.f90` 2处, `input.f90` 1处。 | 937 |
| `ipellet_fixed_dep` | `ipellet_fixed_dep` | integer | `0` | 1 = use fixed input pellet_var when ipellet_abl=1 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `pellet.f90` 2处。 | 939 |
| `r_p` | `r_p_scl` | real | `1.e-3` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 34 处；主要在 `pellet.f90` 25处, `restart_hdf5.f90` 3处, `diagnostics.f90` 2处, `output.f90` 2处。 | 941 |
| `cloud_pel` | `cloud_pel_scl` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `pellet.f90` 5处, `output.f90` 1处, `restart_hdf5.f90` 1处。 | 942 |
| `pellet_mix` | `pellet_mix_scl` | real | `0.` | Molar fraction of deuterium in pellet | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 27 处；主要在 `pellet.f90` 17处, `init_common.f90` 4处, `transport.f90` 3处, `input.f90` 1处。 | 943 |
| `temin_abl` | `temin_abl` | real | `0.` | Min. Temp. at which ablation turns on | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `pellet.f90` 1处。 | 945 |
| `cauchy_fraction` | `cauchy_fraction_scl` | real | `0.` | For ipellet=14, fraction of distribution that is Cauchy, vs von Mises | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `pellet.f90` 5处, `output.f90` 1处, `restart_hdf5.f90` 1处。 | 947 |
| `abl_fac` | `abl_fac` | real | `1.` | Factor multiplying calculated ablation rate | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `pellet.f90` 3处。 | 950 |
| `ibeam` | `ibeam` | integer | `0` | GE 1: Include neutral beam source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `input.f90` 5处, `transport.f90` 4处。 | 955 |
| `beam_x` | `beam_x` | real | `0.` | R-coordinate of beam center | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `neutral_beam.f90` 1处。 | 957 |
| `beam_z` | `beam_z` | real | `0.` | Z-coordinate of beam center | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `neutral_beam.f90` 1处。 | 959 |
| `beam_v` | `beam_v` | real | `1.e4` | Beam voltage (in volts) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `neutral_beam.f90` 2处, `mackenbach_profiles.f90` 1处。 | 961 |
| `beam_rate` | `beam_rate` | real | `0.` | Ions/second deposited by beam | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `mackenbach_profiles.f90` 1处, `neutral_beam.f90` 1处。 | 963 |
| `beam_dr` | `beam_dr` | real | `0.1` | Dispersion of beam deposition | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `mackenbach_profiles.f90` 1处, `neutral_beam.f90` 1处。 | 965 |
| `beam_dv` | `beam_dv` | real | `100.` | Dispersion of beam voltage (in volts) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `neutral_beam.f90` 1处。 | 967 |
| `beam_fracpar` | `beam_fracpar` | real | `1.0` | Cosine of beam angle relative to parallel | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 969 |
| `icd_source` | `icd_source` | integer | `0` | 1: Include current drive source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 16 处；主要在 `transport.f90` 5处, `adapt.f90` 2处, `ludef_t.f90` 2处, `ludef_t_gpu.f90` 2处。 | 973 |
| `J_0cd` | `j_0cd` | real | `0.` | amplitude of current drive | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 975 |
| `R_0cd` | `r_0cd` | real | `0.` | R-coordinate of cd maximum | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 977 |
| `Z_0cd` | `z_0cd` | real | `0.` | Z-coordinate of cd maximum | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 979 |
| `W_cd` | `w_cd` | real | `0.` | width of cd gaussian | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `transport.f90` 4处。 | 981 |
| `delta_cd` | `delta_cd` | real | `0.` | shift of cd gaussian | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 983 |
| `ipforce` | `ipforce` | integer | `0` | 1: Include Poloidal momentum source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 22 处；主要在 `ludef_t.f90` 5处, `transport.f90` 5处, `adapt.f90` 4处, `newpar.f90` 4处。 | 987 |
| `dforce` | `dforce` | real | `0.` | half-width of poloidal momentum source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 989 |
| `xforce` | `xforce` | real | `0.` | location [0,1] of poloidal momentum source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 991 |
| `nforce` | `nforce` | integer | `0` | exponent of (1-x) multiplying poloidal mom. source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 993 |
| `aforce` | `aforce` | real | `0.` | magnitude of poloidal momentum source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 995 |
| `igaussian_heat_source` | `igaussian_heat_source` | integer | `0` | Include gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `transport.f90` 1处。 | 1000 |
| `ghs_x` | `ghs_x` | real | `0.` | R coordinate of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 3处。 | 1002 |
| `ghs_z` | `ghs_z` | real | `0.` | Z coordinate of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 1004 |
| `ghs_phi` | `ghs_phi` | real | `0.` | Phi coordinate of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `transport.f90` 4处。 | 1006 |
| `ghs_rate` | `ghs_rate` | real | `0.` | Amplitude of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 3处。 | 1008 |
| `ghs_var` | `ghs_var` | real | `1.` | Variance of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `transport.f90` 4处。 | 1010 |
| `ghs_var_tor` | `ghs_var_tor` | real | `0.` | Toroidal variance of gaussian heat source | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `transport.f90` 7处。 | 1012 |
| `ionization` | `ionization` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `input.f90` 4处, `diagnostics.f90` 1处, `transport.f90` 1处。 | 1015 |
| `ionization_rate` | `ionization_rate` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1016 |
| `coolrate` | `coolrate` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `ludef_t.f90` 4处, `init_basicq.f90` 1处, `transport.f90` 1处。 | 1017 |
| `ionization_temp` | `ionization_temp` | real | `0.01` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 3处。 | 1018 |
| `ionization_depth` | `ionization_depth` | real | `0.01` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1019 |
| `isink` | `isink` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 2处, `input.f90` 1处。 | 1021 |
| `sink1_x` | `sink1_x` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1022 |
| `sink1_z` | `sink1_z` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1023 |
| `sink1_rate` | `sink1_rate` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1024 |
| `sink1_var` | `sink1_var` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 1025 |
| `sink2_x` | `sink2_x` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1026 |
| `sink2_z` | `sink2_z` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1027 |
| `sink2_rate` | `sink2_rate` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1028 |
| `sink2_var` | `sink2_var` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `transport.f90` 2处。 | 1029 |
| `iarc_source` | `iarc_source` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `transport.f90` 2处, `input.f90` 1处。 | 1031 |
| `arc_source_alpha` | `arc_source_alpha` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1032 |
| `arc_source_eta` | `arc_source_eta` | real | `0.01` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1033 |
| `idenfloor` | `idenfloor` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `transport.f90` 1处。 | 1035 |
| `alphadenfloor` | `alphadenfloor` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 1036 |
| `n_target` | `n_target` | real | `1.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1038 |
| `n_control_p` | `n_control_p` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1039 |
| `n_control_i` | `n_control_i` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1040 |
| `n_control_d` | `n_control_d` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1041 |
| `n_control_type` | `n_control_type` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | -1 不启用密度控制；0 旧算法；1 标准 PID，配合 `n_control_p/i/d`。 | 源码引用 2 处；主要在 `newpar.f90` 1处, `pellet.f90` 1处。 | 1042 |

## PRAD 简单辐射模型 / PRAD Options

简单单杂质辐射模型。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `iprad` | `iprad` | integer | `0` | 1: Teng's PRad module with one impurity species | 1 启用 Teng PRAD 单杂质辐射模型；当前 PRAD 表中 C/Ar/Fe 常用。 | 源码引用 3 处；主要在 `input.f90` 2处, `transport.f90` 1处。 | 252 |
| `prad_z` | `prad_z` | integer | `1` | Z of impurity species in PRad module | PRAD 杂质电荷数；源码警告只实现 6、18、26。 | 源码引用 4 处；主要在 `input.f90` 3处, `transport.f90` 1处。 | 254 |
| `prad_fz` | `prad_fz` | real | `1.` | Density of impurity species in PRad module, as fraction of ne | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 256 |
| `iread_prad` | `iread_prad` | integer | `0` | 1: Read impurity density from profile_nz in units of 10^20 / m^3 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `transport.f90` 1处。 | 259 |

## KPRAD 辐射/杂质模型 / KPRAD Options

KPRAD 杂质电离/复合/辐射与中性粒子演化控制。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `ikprad` | `ikprad` | integer | `0` | 1: KPRad module with one impurity species | 0 关闭；1 使用 KPRAD；-1 需 USEADAS 编译，使用 ADAS 数据。 源码用法：0 关闭；1 使用内置 KPRAD polynomial fit；-1 在 `USEADAS` 编译时读 ADAS ADF11，否则报错。 | 源码引用 53 处；主要在 `auxiliary_fields.f90` 15处, `kprad_m3dc1.f90` 10处, `input.f90` 6处, `output.f90` 6处。 | 264 |
| `kprad_z` | `kprad_z` | integer | `1` | Z of impurity species in KPRad module | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 54 处；主要在 `kprad_m3dc1.f90` 37处, `auxiliary_fields.f90` 5处, `output.f90` 4处, `diagnostics.f90` 2处。 | 266 |
| `ikprad_evolve_neutrals` | `ikprad_evolve_neutrals` | integer | `0` | Model for advection/diffusion of neutrals | 0 中性粒子不对流不扩散；1 推荐：同其它电荷态对流扩散；2 只扩散不对流。 | 源码引用 2 处；主要在 `kprad_m3dc1.f90` 2处。 | 268 |
| `kprad_fz` | `kprad_fz` | real | `0.` | Density of neutral impurity species in KPRad module, as fraction of ne | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `kprad_m3dc1.f90` 1处。 | 270 |
| `kprad_nz` | `kprad_nz` | real | `0.` | Density of neutral impurity species in KPRAD module | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `kprad_m3dc1.f90` 1处。 | 273 |
| `iread_lp_source` | `iread_lp_source` | integer | `0` | Read source from Lagrangian Particle code | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 9 处；主要在 `kprad_m3dc1.f90` 5处, `input.f90` 3处, `transport.f90` 1处。 | 276 |
| `ikprad_min_option` | `ikprad_min_option` | integer | `1` | Control behavior for KPRAD minimum density & temperature | 1 低 ne/Te 时无辐射/电离/复合；2 推荐：允许复合但无辐射/电离；3 按 subcycling 中 ne/Te 判断无辐射/电离/复合。 | 源码引用 7 处；主要在 `kprad.f90` 5处, `kprad_m3dc1.f90` 2处。 | 279 |
| `kprad_nemin` | `kprad_nemin` | real | `1e-12` | Minimum elec. density for KPRAD evolution | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `kprad.f90` 5处, `kprad_m3dc1.f90` 2处。 | 281 |
| `kprad_temin` | `kprad_temin` | real | `2e-7` | Minimum elec. temperature for KPRAD evolution | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 7 处；主要在 `kprad.f90` 5处, `kprad_m3dc1.f90` 2处。 | 283 |
| `ikprad_max_dt` | `ikprad_max_dt` | integer | `0` | Use maximum value of dt for KPRAD ionization | 0 用 MHD dt；1 推荐用 dt/(kprad_z+1)；也可配合 `kprad_max_dt` 显式限制。 | 源码引用 1 处；主要在 `kprad.f90` 1处。 | 285 |
| `kprad_max_dt` | `kprad_max_dt` | real | `-1.` | Specify maximum value of dt for KPRAD ionization | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `kprad.f90` 3处。 | 287 |
| `ikprad_evolve_internal` | `ikprad_evolve_internal` | integer | `0` | Internally evolve ne and Te within KPRAD ionization | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `kprad.f90` 4处。 | 289 |
| `kprad_n0_denm_fac` | `kprad_n0_denm_fac` | real | `1.` | Scaling factor for neutral impurity diffusion | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `kprad_m3dc1.f90` 1处。 | 291 |
| `adas_adf11` | `adas_adf11` | character(len=256) | `""` | Path to ADAS folder with ADF11 data | 字符串值可写成 `name = value` 或带引号形式；解析器会去掉首尾引号。 条件编译：`ifdef USEADAS`。 | 源码引用 2 处；主要在 `adas_m3dc1.f90` 2处。 | 294 |

## 粒子模拟选项 / Particle Simulation Options

仅在 USEPARTICLES 编译时注册。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `kinetic_fast_ion` | `kinetic_fast_ion` | integer | `1` | 1: Enable fast ion PIC | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 19 处；主要在 `particle.f90` 6处, `particle_com.f90` 5处, `gradshafranov.f90` 3处, `init_common.f90` 2处。 | 1266 |
| `kinetic_thermal_ion` | `kinetic_thermal_ion` | integer | `0` | 1: Enable thermal ion PIC and density coupling between MHD and PIC | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 28 处；主要在 `particle.f90` 9处, `particle_com.f90` 8处, `ludef_t.f90` 4处, `gradshafranov.f90` 3处。 | 1268 |
| `igyroaverage` | `igyroaverage` | integer | `0` | 1: Enable gyro-averaging for PIC simulation | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 10 处；主要在 `particle.f90` 5处, `particle_com.f90` 5处。 | 1270 |
| `particle_linear` | `particle_linear` | integer | `-1` | 1: Solve linear delta-f equation. 0: Include nonlinear terms in delta-f | 运行时默认：`particle_linear=-1` 时改为当前 `linear`。 条件编译：`ifdef USEPARTICLES`。 | 源码引用 5 处；主要在 `particle.f90` 2处, `particle_com.f90` 2处, `input.f90` 1处。 | 1272 |
| `particle_substeps` | `particle_substeps` | integer | `40` | Number of substeps for particle pushing in one subcycle | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 8 处；主要在 `particle.f90` 4处, `particle_com.f90` 4处。 | 1274 |
| `particle_subcycles` | `particle_subcycles` | integer | `1` | Number of subcycles for particle pushing in one MHD timestep | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 7 处；主要在 `particle.f90` 3处, `particle_com.f90` 3处, `input.f90` 1处。 | 1276 |
| `particle_couple` | `particle_couple` | integer | `0` | -1: No coupling (test particle). 0: Pressure coupling. 1: Current coupling | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 27 处；主要在 `ludef_t.f90` 21处, `gradshafranov.f90` 2处, `init_common.f90` 2处, `particle.f90` 2处。 | 1278 |
| `particle_nodelete` | `particle_nodelete` | integer | `0` | Do not call delete_particle, keep particles' order | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1280 |
| `iconst_f0` | `iconst_f0` | integer | `0` | Use a constant f0 for delta-f equation | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1282 |
| `ifullf` | `ifullf` | integer | `0` | Do full-f simulation | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 6 处；主要在 `particle.f90` 5处, `input.f90` 1处。 | 1284 |
| `fast_ion_mass` | `fast_ion_mass` | real | `0.` | Fast ion mass (in units of m_p) | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 6 处；主要在 `gradshafranov.f90` 3处, `input.f90` 1处, `particle.f90` 1处, `particle_com.f90` 1处。 | 1286 |
| `fast_ion_z` | `fast_ion_z` | real | `0.` | Zeff of fast ion | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 3 处；主要在 `input.f90` 1处, `particle.f90` 1处, `particle_com.f90` 1处。 | 1288 |
| `fast_ion_dist` | `fast_ion_dist` | integer | `1` | Type of fast ion distribution function. 0: Read 3D distribution from file. 1: Maxwellian. 2. slowing-down. | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 18 处；主要在 `particle.f90` 8处, `particle_com.f90` 8处, `gradshafranov.f90` 1处, `init_common.f90` 1处。 | 1290 |
| `fast_ion_max_energy` | `fast_ion_max_energy` | real | `1000.` | Maximum energy of fast ion for slowing-down distribution | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 5 处；主要在 `particle.f90` 2处, `particle_com.f90` 2处, `gradshafranov.f90` 1处。 | 1293 |
| `num_par_max` | `num_par_max` | integer | `4000000` | Maximum number of particles | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 11 处；主要在 `particle.f90` 6处, `particle_com.f90` 5处。 | 1295 |
| `num_par_scale` | `num_par_scale` | real array | `1.` | Scaling factor for particle number initialization | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 条件编译：`ifdef USEPARTICLES`。 数组长度/上限：`2`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1297 |
| `kinetic_nrmfac_scale` | `kinetic_nrmfac_scale` | real array | `1.` | Scaling factor of the normalization term in particle phase space integration | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 条件编译：`ifdef USEPARTICLES`。 数组长度/上限：`2`。 | 源码引用 4 处；主要在 `particle.f90` 2处, `particle_com.f90` 2处。 | 1299 |
| `ikinetic_vpar` | `ikinetic_vpar` | integer | `0` | 1: Synchronize particle parallel flow to MHD | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1301 |
| `kinetic_rhomax` | `kinetic_rhomax` | real | `1.` | Maximum rho for kinetic particle | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1303 |
| `vpar_reduce` | `vpar_reduce` | real | `0.` | Factor of parallel flow reduction for every timestep | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 6 处；主要在 `particle.f90` 3处, `particle_com.f90` 3处。 | 1305 |
| `idiamagnetic_advection` | `idiamagnetic_advection` | integer | `0` | 1: Enable diamagnetic velocity advection term in momentum equation | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 9 处；主要在 `ludef_t.f90` 7处, `m3dc1_nint.f90` 1处, `particle.f90` 1处。 | 1307 |
| `imode_filter` | `imode_filter` | integer | `0` | Number of toroidal mode to be filtered | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 3 处；主要在 `particle.f90` 3处。 | 1309 |
| `mode_filter_ntor` | `mode_filter_ntor` | integer array | `0` | Toroidal mode number to be filtered | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 条件编译：`ifdef USEPARTICLES`。 数组长度/上限：`100`。 | 源码引用 1 处；主要在 `particle.f90` 1处。 | 1311 |
| `smooth_par` | `smooth_par` | real | `1.e-8` | Smoothing factor for particle pressure | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 4 处；主要在 `particle.f90` 2处, `particle_com.f90` 2处。 | 1313 |
| `smooth_dens_parallel` | `smooth_dens_parallel` | real | `0.` | Smoothing factor for electron density in parallel direction, used for calculating parallel electric field | 条件编译：`ifdef USEPARTICLES`。 | 源码引用 2 处；主要在 `particle.f90` 1处, `particle_com.f90` 1处。 | 1315 |

## 诊断 / Diagnostics

X-ray、磁探针、磁通环等诊断的几何参数。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `xray_detector_enabled` | `xray_detector_enabled` | integer | `0` | 1: enable xray detector | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 5 处；主要在 `output.f90` 3处, `auxiliary_fields.f90` 2处。 | 1086 |
| `xray_r0` | `xray_r0` | real | `0.` | R coordinate of xray detector | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `auxiliary_fields.f90` 1处, `diagnostics.f90` 1处。 | 1088 |
| `xray_phi0` | `xray_phi0` | real | `0.` | Phi coordinate of xray detector | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `auxiliary_fields.f90` 1处, `diagnostics.f90` 1处。 | 1090 |
| `xray_z0` | `xray_z0` | real | `0.` | Z coordinate of xray detector | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `auxiliary_fields.f90` 1处, `diagnostics.f90` 1处。 | 1092 |
| `xray_theta` | `xray_theta` | real | `0.` | Angle of xray detector chord (degrees) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `auxiliary_fields.f90` 1处, `diagnostics.f90` 1处。 | 1094 |
| `xray_sigma` | `xray_sigma` | real | `1.` | Spread of xray detector chord (degrees) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `auxiliary_fields.f90` 1处, `diagnostics.f90` 1处。 | 1096 |
| `imag_probes` | `imag_probes` | integer | `0` | Number of magnetic probes | 磁探针数量；对应数组用 `mag_probe_x(i)` 等一基索引给出。 | 源码引用 7 处；主要在 `output.f90` 6处, `diagnostics.f90` 1处。 | 1099 |
| `mag_probe_x` | `mag_probe_x` | real array | `0.` | X-coordinate of magnetic probes | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 5 处；主要在 `diagnostics.f90` 5处。 | 1101 |
| `mag_probe_phi` | `mag_probe_phi` | real array | `0.` | Phi-coordinate of magnetic probes | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 4 处；主要在 `diagnostics.f90` 4处。 | 1103 |
| `mag_probe_z` | `mag_probe_z` | real array | `0.` | Z-coordinate of magnetic probes | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 4 处；主要在 `diagnostics.f90` 4处。 | 1105 |
| `mag_probe_nx` | `mag_probe_nx` | real array | `0.` | X-component of magnetic probe normal | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 3 处；主要在 `diagnostics.f90` 3处。 | 1107 |
| `mag_probe_nphi` | `mag_probe_nphi` | real array | `0.` | Phi-component of magnetic probe normal | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 3 处；主要在 `diagnostics.f90` 3处。 | 1109 |
| `mag_probe_nz` | `mag_probe_nz` | real array | `0.` | Z-component of magnetic probe normal | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 3 处；主要在 `diagnostics.f90` 3处。 | 1111 |
| `iflux_loops` | `iflux_loops` | integer | `0` | Number of flux loops | 磁通环数量；对应数组用 `flux_loop_x(i)`、`flux_loop_z(i)` 一基索引给出。 | 源码引用 7 处；主要在 `output.f90` 6处, `diagnostics.f90` 1处。 | 1114 |
| `flux_loop_x` | `flux_loop_x` | real array | `0.` | X-coordinate of flux loop | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 1 处；主要在 `diagnostics.f90` 1处。 | 1116 |
| `flux_loop_z` | `flux_loop_z` | real array | `0.` | Z-coordinate of flux loop | 数组参数在 C1input 中使用 Fortran 一基索引，例如 `name(1)=...`；未赋值元素保持默认值。 数组长度/上限：`100`。 | 源码引用 1 处；主要在 `diagnostics.f90` 1处。 | 1118 |
| `ifixed_temax` | `ifixed_temax` | integer | `0` | if nonzero, evaluate temax at xmag0,zmag0 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `newpar.f90` 3处。 | 1121 |

## 输出与重启 / Output

HDF5/标量/辅助变量输出、重启读写、调试打印和 Slurm 超时写时间片。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `iprint` | `iprint` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 465 处；主要在 `gradshafranov.f90` 64处, `newpar.f90` 50处, `diagnostics.f90` 41处, `transport.f90` 32处。 | 1046 |
| `ntimepr` | `ntimepr` | integer | `1` | Number of time steps per field output | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `input.f90` 2处, `newpar.f90` 1处, `output.f90` 1处, `particle.f90` 1处。 | 1047 |
| `ntimers` | `ntimers` | integer | `0` | Number of time steps per restart output | 0 表示校验后取 `ntimepr`；否则为 restart 输出周期。 运行时默认：`ntimers<=0` 时源码把它设为 `ntimepr`。 | 源码引用 1 处；主要在 `input.f90` 1处。 | 1049 |
| `ifout` | `ifout` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | -1 表示校验后按编译维度默认：3D 输出 f，2D 不输出；也可显式 0/1。 运行时默认：`ifout=-1` 在 `validate_input` 中改为 `i3d`：3D 默认输出 f 场，2D 默认不输出。 | 源码引用 7 处；主要在 `output.f90` 4处, `input.f90` 1处, `newpar.f90` 1处, `newvar.f90` 1处。 | 1051 |
| `icalc_scalars` | `icalc_scalars` | integer | `1` | 1: Calculate scalar diagnostics | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 1处, `newpar.f90` 1处。 | 1052 |
| `ike_only` | `ike_only` | integer | `0` | 1: Only calculate ke scalar diagnostic | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `diagnostics.f90` 2处。 | 1054 |
| `ike_harmonics` | `ike_harmonics` | integer | `0` | Number of Fourier harmonics of ke to be calculated and output | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 3 处；主要在 `diagnostics.f90` 2处, `output.f90` 1处。 | 1056 |
| `ibh_harmonics` | `ibh_harmonics` | integer | `0` | Number of Fourier harmonics of magnetic perturbation to be calculated and output | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `input.f90` 3处, `diagnostics.f90` 2处, `output.f90` 1处。 | 1058 |
| `irestart` | `irestart` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 0 从头启动；1 从 HDF5 restart；2 用 restart 初始化 GS；3 用 2D real restart 初始化 2D complex。 | 源码引用 26 处；主要在 `output.f90` 11处, `newpar.f90` 4处, `adapt.f90` 3处, `hdf5_output.f90` 2处。 | 1060 |
| `itimer` | `itimer` | integer | `0` | 1: Output internal timer data | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 77 处；主要在 `time_step_split.f90` 31处, `time_step.f90` 12处, `newpar.f90` 9处, `ludef_t.f90` 7处。 | 1061 |
| `iwrite_transport_coeffs` | `iwrite_transport_coeffs` | integer | `1` | 1: Output transport coefficient fields | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `output.f90` 2处。 | 1063 |
| `iwrite_aux_vars` | `iwrite_aux_vars` | integer | `1` | 1: Output auxiliary variable fields | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 4 处；主要在 `output.f90` 3处, `newpar.f90` 1处。 | 1065 |
| `iwrite_adjacency` | `iwrite_adjacency` | integer | `1` | 1: Output mesh adjacency info | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `output.f90` 1处。 | 1067 |
| `iwrite_quad_points` | `iwrite_quad_points` | integer | `0` | 1: Output integration quadrature points | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `output.f90` 2处。 | 1069 |
| `itemp_plot` | `itemp_plot` | integer | `0` | 1: Output additional temperature plots | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 10 处；主要在 `auxiliary_fields.f90` 8处, `output.f90` 2处。 | 1071 |
| `ibdgp` | `ibdgp` | integer | `0` | ne.0: bdgp plot contains only partial results | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `electric_field.f90` 1处。 | 1073 |
| `idouble_out` | `idouble_out` | integer | `0` | 1: Use double-precision floating points in output | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 6 处；主要在 `hdf5_output.f90` 4处, `particle.f90` 1处, `particle_com.f90` 1处。 | 1075 |
| `irestart_slice` | `irestart_slice` | integer | `-1` | Field output slice from which to restart | -1 使用最后一个 time slice；否则从指定 `time_nnn.h5` restart。 | 源码引用 3 处；主要在 `restart_hdf5.f90` 3处。 | 1077 |
| `iveldif` | `iveldif` | integer | `0` | ne.0: veldif plot contains only partial results | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `electric_field.f90` 1处。 | 1080 |
| `write_ts_on_job_timeout` | `write_ts_on_job_timeout` | integer | `0` | 1: Write time slice and stop code before job hits timeout or is preempted | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `newpar.f90` 1处。 | 1082 |

## 杂项物理参数 / Miscellaneous

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `gam` | `gam` | real | `5./3. (约 1.6667)` | Ratio of specific heats | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 482 处；主要在 `metricterms_new_gpu.f90` 251处, `metricterms_new.f90` 113处, `temperature_plots.f90` 29处, `ludef_t.f90` 22处。 | 381 |
| `db` | `db` | real | `-1.` | Collisionless ion skin depth (overrides db_fac) | 源码默认 -1，表示按物理归一化自动计算 ion skin depth 并乘以 `db_fac`；若显式给非负值则覆盖。 运行时默认：`db<0` 时源码按 `b0_norm/n0_norm/l0_norm/ion_mass` 计算物理 ion skin depth，再乘 `db_fac`；显式给非负 `db` 会覆盖该自动计算。 | 源码引用 396 处；主要在 `ludef_t.f90` 291处, `electrostatic_potential.f90` 25处, `particle.f90` 17处, `particle_com.f90` 11处。 | 383 |
| `db_fac` | `db_fac` | real | `0.` | Factor multiplying physical value of ion skin depth | `db<0` 时乘在物理 ion skin depth 上；默认 0 等价于关闭 two-fluid skin-depth 贡献。 | 源码引用 3 处；主要在 `input.f90` 3处。 | 385 |
| `mass_ratio` | `mass_ratio` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 8 处；主要在 `metricterms_new.f90` 4处, `metricterms_new_gpu.f90` 4处。 | 387 |
| `lambdae` | `lambdae` | real | `0.` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 未发现除注册/声明外的源码引用；可能是废弃参数、条件编译路径参数，或仅由外部工具/库间接使用。 | 388 |
| `z_ion` | `z_ion` | real | `1.` | Z effective | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 39 处；主要在 `gradshafranov.f90` 14处, `input.f90` 9处, `mackenbach_profiles.f90` 3处, `auxiliary_fields.f90` 2处。 | 389 |
| `ion_mass` | `ion_mass` | real | `1.` | Ion mass (in units of m_p) | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 20 处；主要在 `gradshafranov.f90` 6处, `init_conds.f90` 2处, `input.f90` 2处, `neutral_beam.f90` 2处。 | 390 |
| `lambda_coulomb` | `lambda_coulomb` | real | `17.` | Coulomb logarithm | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 2 处；主要在 `input.f90` 2处。 | 392 |
| `thermal_force_coeff` | `thermal_force_coeff` | real | `0.` | Coefficient of thermal force | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 源码引用 1 处；主要在 `gradshafranov.f90` 1处。 | 394 |
| `ntor` | `ntor` | integer | `0` | Toroidal mode number | 2D/complex 线性模拟的环向模数；RMP 等也会使用。 | 源码引用 64 处；主要在 `coils.f90` 18处, `rmp.f90` 13处, `nintegrate_mod.f90` 9处, `read_schaffer_field.f90` 7处。 | 1124 |
| `mpol` | `mpol` | integer | `0` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 若干测试/外场/REKC 设置中使用的极向模数。 | 源码引用 16 处；主要在 `rmp.f90` 6处, `init_common.f90` 4处, `init_circle.f90` 1处, `init_conds.f90` 1处。 | 1126 |

## 已废弃兼容参数 / Deprecated

仍可被解析以兼容旧输入，但新算例不建议使用。

| 参数 | 内部变量 | 类型 | 默认值 | 含义 | 使用方法/注意 | 源码使用摘要 | 注册行 |
|---|---|---|---|---|---|---|---:|
| `ibform` | `idum` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1320 |
| `igs_method` | `idum` | integer | `-1` | 源码 `add_var_*` 注册说明为空；请结合所在逻辑组和下方源码使用位置判断。 | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1321 |
| `iwrite_restart` | `idum` | integer | `0` | 1: Write restart files | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1322 |
| `zeff` | `dum` | real | `0.` | zeff is deprecated.  Use z_ion instead. | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `dum`，未见模型计算使用。 | 1324 |
| `ivform` | `idum` | integer | `1` | ivform is deprecated.  Only ivform=1 is now implemented. | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1326 |
| `iwrite_adios` | `idum` | integer | `0` | iwrite_adios is deprecated. | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1328 |
| `iglobalout` | `idum` | integer | `0` | iglobalout is deprecated | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1330 |
| `iglobalin` | `idum` | integer | `0` | iglobalin is deprecated | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1332 |
| `iread_adios` | `idum` | integer | `0` | iread_adios is deprecated | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1334 |
| `iread_hdf5` | `idum` | integer | `1` | iread_hdf5 is deprecated | 按需在 `C1input` 中写 `name = value`；未设置则使用默认值。 | 兼容旧输入：读入到 dummy 变量 `idum`，未见模型计算使用。 | 1336 |

## 附录 A：主程序相关的辅助输入文件

| 文件/前缀 | 触发参数 | 用途 |
|---|---|---|
| `geqdsk` | `iread_eqdsk` | EFIT g-file；读入磁通/边界/剖面，具体选项见 `iread_eqdsk`。 |
| `dskbal` | `iread_dskbal` | 读入 BAL 平衡。 |
| `fixed` | `iread_jsolver` | 读入 Jsolver 平衡。 |
| `profile_ne` | `iread_ne` | 电子密度剖面。 |
| `profile_te` | `iread_te` | 电子温度剖面。 |
| `profile_p` | `iread_p` | 压力剖面。 |
| `profile_f` | `iread_f` | GS 求解用 F=R*B_phi vs Psi_N。 |
| `profile_j` | `iread_j` | basicj 平衡用环向电流密度。 |
| `profile_bscale` | `iread_bscale` | F 或 toroidal field 缩放剖面。 |
| `profile_pscale` | `iread_pscale` | 压力及 p' 缩放剖面。 |
| `profile_kappa` | `ikappafunc=10/11` | 热扩散/热导剖面，10 为 m^2/s，11 为归一化。 |
| `profile_denm` | `idenmfunc=10/11` | 粒子扩散剖面，10 为 m^2/s，11 为归一化。 |
| `profile_nz` | `iread_prad` | PRAD impurity density，单位 10^20/m^3。 |
| `rmp_coil.dat`, `rmp_current.dat` | `irmp=1` | RMP window-pane coil 位置、电流和相位。 |
| `pellet.dat` | `iread_pellet=1` | 多 pellet 表格输入。 |
| `cloud.txt` | `iread_lp_source>0` | Lagrangian particle code source，开发中。 |
| `FIELDLINES`/`MGRID`/`fieldlines*`/`mgrid*` | `type_ext_field=1/2` | stellarator total/external field。 |
| `geometry.nc` 或 `vmec_filename` | `iread_vmec=1` | VMEC 几何。 |
| `plane_positions` | `iread_planes=1` | 自定义环向平面位置。 |
| `C1.h5`, `time_nnn.h5` | `irestart=1`, `irestart_slice` | HDF5 restart 文件。 |

## 附录 B：mesh 生成器与转换工具输入

这些不是主程序 `C1input` 的 `&inputnl` 参数，而是 `doc/mesh-gen.tex` 中描述的 mesh 工具输入文件。常见键包括：

| 工具 | 输入格式/参数 | 说明 |
|---|---|---|
| `m3dc1_mfmgen` / `create_mesh.sh input` | `inType`, `outFile`, `meshSize`, `modelFile`, `meshFile`, `bdryFile`, `faceBdry` 等 | ASCII key-value 输入；生成 `.dmg/.smb/.vtk` 等模型/网格文件。具体示例见各 `unstructured/templates/*/*_mesh/input`。 |
| `polar_meshgen` | `inFile`, `meshSize` 等 | `POLAR`/jsolver 相关几何转 mesh；`meshSize` 缺省约 0.05。 |
| `simToM3dc1` | SimModeler model/mesh 与 inner/outer model face 等 | 把 SimModeler 数据转换为 M3D-C1 所需 mesh/model。 |

## 附录 C：官方 `doc/` 覆盖范围

本整理扫描了当前 master 的 `doc/` 目录。与 `C1input` 参数直接相关的主要文件是 `inputs.tex`、`running_jobs.tex`、`units.tex`、`mesh-gen.tex`、`petsc_option.tex`、`physics-model.tex`、`output.tex`；其它文档主要提供安装、构建、后处理、版本协作和教程背景。

| 文件 | 与本参数整理的关系 |
|---|---|
| `M3DC1.tex` | LaTeX 主文件。 |
| `M3DC1_License.tex` | 许可证。 |
| `app-paraview.tex` | ParaView 后处理背景。 |
| `building.tex` | 构建系统背景。 |
| `color.tex` | LaTeX 样式/颜色定义。 |
| `doc.tex` | 合并生成后的文档文本，内容与各章节有重复。 |
| `github.tex` | GitHub 工作流背景。 |
| `idl-postproc.tex` | IDL 后处理背景。 |
| `inputs.tex` | 官方参数表，提供大多数参数的使用说明；存在少量旧名/错拼名，本文已按源码校正。 |
| `installation.tex` | 安装/编译背景。 |
| `mesh-adapt.tex` | 网格自适应背景。 |
| `mesh-gen.tex` | mesh 生成器输入、`C1input` 中 mesh/model 文件名、`nplanes`、SimModeler/VMEC 相关背景。 |
| `numerical_methods.tex` | 数值方法背景，补充 `jadv` 等参数解释。 |
| `output.tex` | HDF5、time slice、`ntimepr`、后处理输出背景。 |
| `petsc_option.tex` | PETSc options 与 `nplanes`/bjacobi block 的配套关系。 |
| `physics-model.tex` | MHD/two-fluid/temperature/impurity/radiation 物理模型背景。 |
| `running_jobs.tex` | 2D/3D、linear/nonlinear、bootstrap、restart、output 周期等运行方式说明。 |
| `tutorials.tex` | 教程索引，提供典型算例入口。 |
| `units.tex` | 归一化单位说明，对 `b0_norm/n0_norm/l0_norm/ion_mass` 的解释有用。 |
