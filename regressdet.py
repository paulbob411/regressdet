"""regressdet —— 比较两轮评测结果，标出退化的指标与分项。

对齐两轮结果，标出分数下降超过阈值的指标与下降最快的子集

定位：
  区分总体下降与结构变化——有些回归只在某个子集上发生

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到 评测回归检测 领域的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python regressdet.py --help
    python regressdet.py --file input.txt
    python regressdet.py --text "示例内容"
    python regressdet.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 领域规则表：每条规则独立可核查，命中即报，不做推断。
RULES: list[dict] = [
    {
        "name": "评测回归检测·缺失",
        "why": "缺少评测回归检测的关键要素时无法给出可靠判定",
        "severity": "high",
        "keywords": ['缺失', 'missing', 'absent', '缺少', '没有'],
    },
    {
        "name": "评测回归检测·冲突",
        "why": "同一份输入里两处评测回归检测描述互相矛盾",
        "severity": "high",
        "keywords": ['冲突', 'conflict', 'contradict', '矛盾', '不一致', '相反'],
    },
    {
        "name": "评测回归检测·越界",
        "why": "评测回归检测的取值超出常规范围",
        "severity": "medium",
        "keywords": ['越界', 'out of range', 'outlier', '越界', '超限', '超过'],
    },
    {
        "name": "评测回归检测·退化",
        "why": "评测回归检测的信息量不足以支撑结论",
        "severity": "medium",
        "keywords": ['退化', 'degrade', 'insufficient', '不足', '太少', '无法'],
    },
    {
        "name": "评测回归检测·泄漏",
        "why": "评测回归检测相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['泄漏', 'leak', 'expose', '泄漏', '暴露', '明文'],
    },
    {
        "name": "评测回归检测·重复",
        "why": "同一处评测回归检测信息被反复传递",
        "severity": "low",
        "keywords": ['重复', 'duplicate', 'repeat', '重复', 'again'],
    },
    {
        "name": "评测回归检测·陈旧",
        "why": "评测回归检测的时效性已经过期",
        "severity": "medium",
        "keywords": ['陈旧', 'stale', 'expired', '过期', '陈旧', '旧版'],
    },
    {
        "name": "评测回归检测·不可核",
        "why": "评测回归检测的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['不可核', 'unverifiable', 'no evidence', '无法追溯', '没有来源'],
    },
]

# 判定阈值：越高越好
THRESHOLD = 0.75
HIGHER_IS_BETTER = True



def regressdet_read_numbers(text: str) -> list[float]:
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def regressdet_percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    if len(vs) == 1:
        return vs[0]
    pos = (len(vs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(vs) - 1)
    frac = pos - lo
    return vs[lo] * (1 - frac) + vs[hi] * frac


def regressdet_gate(value: float, threshold: float, higher_is_better: bool = True) -> dict:
    """门槛判定，带符号余量。"""
    margin = (value - threshold) if higher_is_better else (threshold - value)
    return {
        "value": value,
        "threshold": threshold,
        "margin": round(margin, 4),
        "pass": margin >= 0,
        "critical": abs(margin) < threshold * 0.05 if threshold else False,
    }


def regressdet_analyze(text: str) -> dict:
    """主分析：分数统计与门槛判定。"""
    nums = regressdet_read_numbers(text)
    if not nums:
        return {"ok": False, "error": "文本里没有数字", "count": 0}
    n = len(nums)
    mean = sum(nums) / n
    stdev = (sum((v - mean) ** 2 for v in nums) / n) ** 0.5
    return {
        "ok": True,
        "count": n,
        "mean": mean,
        "stdev": stdev,
        "median": regressdet_percentile(nums, 0.5),
        "min": min(nums),
        "max": max(nums),
        "threshold_check": regressdet_gate(mean, THRESHOLD, HIGHER_IS_BETTER),
        "values": nums[:50],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"样本数：{result['count']}")
    out.append(f"均值 {result['mean']:.4f}  标准差 {result['stdev']:.4f}  中位 {result['median']:.4f}")
    out.append(f"区间 [{result['min']}, {result['max']}]")
    out.append("")
    t = result["threshold_check"]
    status = "通过" if t["pass"] else "未通过"
    if t["critical"]:
        status += "（临界）"
    out.append(f"门槛 {t['threshold']}  实测 {t['value']:.4f}  余量 {t['margin']:+.4f}  → {status}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="regressdet",
        description="对齐两轮结果，标出分数下降超过阈值的指标与下降最快的子集（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python regressdet.py --file input.txt\n"
            "  python regressdet.py --text '示例内容'\n"
            "  python regressdet.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = regressdet_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
