# regressdet

**比较两轮评测结果，标出退化的指标与分项。**

`regressdet` —— 对齐两轮结果，标出分数下降超过阈值的指标与下降最快的子集

- 零依赖，Python 3.10+ 标准库即可运行
- 单文件，`regressdet.py` 拷走就能用
- 不联网、不写文件

<!-- ipos:install -->
## 安装

零依赖，Python 3.10+ 即可：

```bash
pip install paulbob411-regressdet
```

装完直接用命令名调用：

```bash
regressdet --help
```

也可以不用安装，直接把 `regressdet.py` 拷走用——它只依赖标准库。

## 为什么需要它

区分总体下降与结构变化——有些回归只在某个子集上发生

它遵守下面几条自己定的规矩：

1. **只报告能定位到具体位置的结论**，不做语义猜测。
2. **规则表公开**，每条命中都能对应到 评测回归检测 领域的一条明示规则。
3. **输入为空或格式不对时明确报错**，不静默返回空结果。

## 用法

```bash
python regressdet.py --file input.txt
python regressdet.py --text "示例内容"
python regressdet.py --file input.txt --json
```

加 `--json` 可以拿到机器可读的结果，便于接到流水线里。

## 已知局限

- 阈值是固定值，不随数据自适应。
- 只判定达标与否，不解释分数来源。

## 跑测试

```bash
python test_regressdet.py
```

测试用独立的断言与临时数据，不污染工作目录。

## 来源与参考

- Python 标准库文档：<https://docs.python.org/3/>
- GitHub 仓库：<https://github.com/paulbob411/regressdet>

---

## 关于作者

paulbob411 做评测回归检测相关的问题。这个工具先替你回答一个具体问题，再谈别的。

- 个人主页：<https://paulbob411.github.io>
- 仓库：<https://github.com/paulbob411/regressdet>

## 许可

MIT，见 [LICENSE](LICENSE)。
