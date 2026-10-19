class SharedState:
    """Agent 间共享状态 + 消息通信记录（黑板模式 Blackboard）。

    - publish: Agent 把处理结果写入共享状态，下游 Agent 可读取 -> 实现消息互通
    - read:   Agent 读取上游写入的状态，完成信息传递
    - history: 记录完整的 Agent 间通信链路，用于状态追踪/日志
    """

    def __init__(self):
        self._store = {}
        self._comm_log = []

    def publish(self, key, value, sender):
        self._store[key] = value
        self._comm_log.append(
            {"from": sender, "key": key, "chars": len(value)}
        )
        print(f"    [通信] {sender} -> 状态 '{key}' (写入 {len(value)} 字符)")

    def read(self, key, default=""):
        return self._store.get(key, default)

    def history(self):
        return self._comm_log

    def snapshot(self):
        return dict(self._store)
