## p5r-nego-extractor

解析 Persona 5 Royal (P5R / 女神异闻录5皇家版) 的 `TALK_*.BF.msg/.msg.h/.flow` 文件，输出交涉对话结果（反应）表。预构建结果参见 [Release](https://github.com/etnAtker/p5r-nego-extractor/releases/latest)。

> 目前人格与反应是基于其他数据和脚本行为的推测，目前人格的映射为 `0=开朗 / 1=懦弱 / 2=性急 / 3=阴沉`，反应的映射为 `1=喜欢 / 2=一般 / 3=反感`。若有确实依据指向不同，请提 Issue 说明。  

> 本项目完全由codex实现，可能有致命错误和缺陷，请见谅。

### 依赖

本项目使用 [uv](https://github.com/astral-sh/uv) 管理和运行 Python 依赖。

- Python ≥ 3.11
- `openpyxl`

### 使用

在本脚本运行之前，需要先使用 [Atlus-Script-Tools](https://github.com/tge-was-taken/Atlus-Script-Tools) 对TALK下的`.bf`文件进行解包

```bash
uv run p5r-nego-extractor \
  --input-dir /path/to/TALK_dir \
  --output-dir /path/to/output \
  [--scripts TALK_01JIGAKU TALK_02YOUNGMEN ...]
```

省略 `--scripts` 时会自动处理 `input-dir` 下全部 `TALK_*.BF.msg`。运行结束后在 `output/talk_negotiation_tables.xlsx` 中查看。

### 开发提示

- 入口：`cli.py`  
- 解析模块：同目录下的 `msg_parser.py`、`flow_parser.py`  
- 导出逻辑：`pipeline.py`（合并单元格、列宽、样式）  
