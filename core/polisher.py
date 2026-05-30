import requests


class Polisher:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"

    def polish(self, text: str) -> str:
        prompt = f"""你是一个文字校对工具。你必须严格遵守以下规则：

【核心原则】
逐字对比原文，只修改确认是错别字的字，其他一个字都不准动。

【必须遵守的规则】
1. 保留原文所有标点符号（逗号、句号、问号、感叹号等），一个都不能删
2. 保留原文所有口语化表达
3. 保留原文所有语气词（啊、呢、吗、吧、嘛等）
4. 保留原文所有重复词语
5. 不准添加原文没有的内容
6. 不准删除原文有的内容
7. 不准改变句子顺序
8. 不准修改正确的字词

【输出要求】
只输出修改后的文字，不要解释，不要说明，不要添加任何额外内容。

原文：{text}

修改后："""

        resp = requests.post(self.url, json={
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
        })
        resp.raise_for_status()
        return resp.json().get("response", "")
