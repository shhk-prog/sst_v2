"""Coding dataset helpers (Python filter, optional output cleaning)."""

from __future__ import annotations

import re


def extract_code_from_output(output: str) -> str:
    """最初の fenced code block の中身のみ返す。無ければ strip した全文。"""
    match = re.search(r"```[\w]*\n(.*?)```", output, re.DOTALL)
    if match:
        return match.group(1).rstrip()
    return output.strip()


def strip_tail_after_codeblock(output: str) -> str:
    """fence がある場合のみブロック以降の解説 tail を削除（緩和クリーニング）。"""
    match = re.search(r"(```[\w]*\n.*?```)", output, re.DOTALL)
    if match:
        return match.group(1).rstrip()
    return output.strip()


def process_output(output_raw: str, *, clean_output: bool, clean_mode: str = "block_only") -> str:
    """
    clean_output=False: 生の solution をそのまま使用（Phase 2a 推奨）
    clean_mode='aggressive': extract_code_from_output（ブロック内のみ）
    clean_mode='tail_only': fence + 中身 + 閉じ fence まで（後続解説のみ削除）
    """
    if not clean_output:
        return output_raw.strip()
    if clean_mode == "tail_only":
        return strip_tail_after_codeblock(output_raw)
    return extract_code_from_output(output_raw)


def is_python_sample(instruction: str, output: str) -> bool:
    """HumanEval / MBPP 向けに Python っぽいサンプルかをヒューリスティック判定。"""
    combined = f"{instruction}\n{output}"
    lower = combined.lower()

    non_python_markers = [
        r"```java\b",
        r"```cpp\b",
        r"```c\+\+\b",
        r"```swift\b",
        r"```kotlin\b",
        r"```go\b",
        r"```rust\b",
        r"```ruby\b",
        r"```php\b",
        r"```csharp\b",
        r"```cs\b",
    ]
    if any(re.search(p, lower) for p in non_python_markers):
        return False

    if "#include" in output or "using namespace std" in output:
        return False
    if re.search(r"\bpublic\s+(class|static|void)\s+", output) and not re.search(
        r"\bdef \w+\(", output
    ):
        return False

    python_markers = [
        r"```python\b",
        r"\bdef \w+\(",
        r"\bimport \w+",
        r"from typing import",
        r"\bself\.",
        r"@pytest",
        r"if __name__ == ['\"]__main__['\"]",
    ]
    return any(re.search(p, combined) for p in python_markers)
