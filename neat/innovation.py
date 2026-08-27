"""Innovation tracking - the mechanism that makes NEAT crossover possible."""

class InnovationTracker:
    def __init__(self, start_node_id: int, start_innovation: int = 0):
        self._node_counter = start_node_id
        self._innovation_counter = start_innovation
        self._connection_cache: dict[tuple[int, int], int] = {}
        self._split_cache: dict[int, int] = {}  # connection innovation -> new hidden node id

    def next_node_id(self) -> int:
        nid = self._node_counter
        self._node_counter += 1
        return nid

    def get_connection_innovation(self, in_node: int, out_node: int) -> int:
        key = (in_node, out_node)
        if key not in self._connection_cache:
            self._connection_cache[key] = self._innovation_counter
            self._innovation_counter += 1
        return self._connection_cache[key]

    def get_node_id_for_split(self, connection_innovation: int) -> int:
        if connection_innovation not in self._split_cache:
            self._split_cache[connection_innovation] = self.next_node_id()
        return self._split_cache[connection_innovation]

    def reset_generation_cache(self) -> None:
        self._connection_cache.clear()
        self._split_cache.clear()
