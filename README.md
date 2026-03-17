## p5r-nego-extractor

解析 Persona 5 Royal (P5R / 女神异闻录5皇家版) 的 `TALK_*.BF.msg/.msg.h/.flow` 文件，输出交涉对话结果（反应）表。预构建结果参见 [Release](https://github.com/etnAtker/p5r-nego-extractor/releases/latest)。

> 本项目完全由codex实现，可能有致命错误和缺陷，请见谅。

### 依赖

本项目使用 [uv](https://github.com/astral-sh/uv) 管理和运行 Python 依赖。

- Python ≥ 3.11
- `openpyxl`

### 常量映射

目前的人格映射为 `0=懦弱 / 1=性急 / 2=开朗 / 3=阴沉`，反应的映射为 `1=喜欢 / 2=反感 / 3=一般`。

> 注意，现在的映射均没有直接性的依据，而是猜测后实际验证的结果。若有直接依据标明指向错误，请提 Issue 说明。下面说明为何选择这种映射。

#### 人格映射

尚无直接的映射证据，但通过解包的UNIT.TBL中找到了每个怪的性格定义（同样是数字0/1/2/3），通过对比这个怪实际在游戏中是什么性格，得出了当前映射。

#### 反应映射

通过解包 `BASE/BATTLE/EVENT/BCD/HOLD_UP/ICON` 下的EPL文件，可以看出：

- `BES_H_01.EPL` 为“音符”即“喜欢”；
- `BES_H_02.EPL` 为“青筋”即“讨厌”；
- `BES_H_03.EPL` 为“流汗”即“一般”。

同时也在游戏中抽样验证了此种映射的正确性。

如需自行解包 `EPL` 文件进行验证，可运行：

```bash
uv run python extract_hold_up_gfs.py \
  --epl-dir /path/to/epl/icon \
  --output-dir /path/to/output
```

脚本会扫描 `epl-dir` 下的 `EPL` 文件，输出每个 `EPL` 中最大的 `GFS0` 子块，并生成 `manifest.tsv` 方便对照。将解包结果用 [GFD-Studio](https://github.com/tge-was-taken/GFD-Studio) 打开，即可看到图标。

> 另，对话交涉的详细机制参见：[对话交涉](https://wiki.biligame.com/persona/P5R/%E5%AF%B9%E8%AF%9D%E4%BA%A4%E6%B6%89)

### 使用

在本脚本运行之前，需要先使用 [Atlus-Script-Tools](https://github.com/tge-was-taken/Atlus-Script-Tools) 对TALK下的`.bf`文件进行解包。然后运行本程序：

```bash
uv run python cli.py \
  --input-dir /path/to/TALK_dir \
  --output-dir /path/to/output \
  [--scripts TALK_01JIGAKU TALK_02YOUNGMEN ...]
```

省略 `--scripts` 时会自动处理 `input-dir` 下全部 `TALK_*.BF.msg`。运行结束后在 `output/talk_negotiation_tables.xlsx` 中查看。

### 开发提示

- 入口：`cli.py`  
- 解析模块：同目录下的 `msg_parser.py`、`flow_parser.py`  
- 导出逻辑：`pipeline.py`（合并单元格、列宽、样式）  
