from controller.NodeGenerator import ArtificialNode
from model.Edge import ArtificialEdge
from pathlib import Path
import random

class ExitEdge(ArtificialEdge):
    def __init__(self, vS, vT, lower, upper, weight, temporary=True):
        super().__init__(vS, vT, lower, upper, weight, temporary=temporary)

class ArtificialNodeInserter:
    DEFAULT_LOWER = 0
    DEFAULT_UPPER = 1
    DEFAULT_GAMMA = 1230919231

    def __init__(self, processor, vs_id=None, vt_id=None, start_artificial_id=None):
        self.processor = processor
        self.pipeline = processor.pipeline

        max_id = self._get_max_id()
        offset = self._get_offset()

        self.vs_id = vs_id if vs_id is not None else max_id + offset
        self.vt_id = vt_id if vt_id is not None else max_id + offset + 1
        self.artificial_node_id = start_artificial_id if start_artificial_id is not None else random.randint(self.vt_id + 10, self.vt_id + 1000)

        self.vS = ArtificialNode(id=self.vs_id, label="vS")
        self.vT = ArtificialNode(id=self.vt_id, label="vT")
        self.edges_added = []

    def _get_max_id(self): # Lấy ID lớn nhất từ bộ nhớ
        all_ids = [node.id for node in self.processor.ts_nodes]
        if hasattr(self.processor, "graph") and hasattr(self.processor.graph, "nodes"):
            all_ids += list(self.processor.graph.nodes.keys())
        return max(all_ids) if all_ids else 1000

    def _get_offset(self):
        node_count = len(set(node.id for node in self.processor.ts_nodes))
        return max(1000, node_count * 10)

    # ==== Các hàm tiện ích, phụ trợ ==== #
    def create_artificial_edge(self, start, end, lower, upper, weight, temporary=True):
        return ArtificialEdge(start, end, lower, upper, weight, temporary=temporary)

    def find_original_edge(self, u, v):
        for e in self.processor.ts_edges:
            if getattr(e, 'start_node', None) and getattr(e, 'end_node', None):
                if e.start_node.id == u and e.end_node.id == v:
                    return e
        return None

    def create_artificial_nodes(self, idx):
        node1 = ArtificialNode(id=self.artificial_node_id, label=f"virt_{idx}_1")
        node2 = ArtificialNode(id=self.artificial_node_id + 1, label=f"virt_{idx}_2")
        self.artificial_node_id += 2
        self.processor.ts_nodes.extend([node1, node2])
        self.processor.graph.nodes[node1.id] = node1
        self.processor.graph.nodes[node2.id] = node2
        return node1, node2

    def add_artificial_edges(self, node1, node2, lower, upper, F, U):
        edges_artificial = [
            self.create_artificial_edge(self.vS, node1, lower, F - U, 0),
            self.create_artificial_edge(node1, node2, lower, upper, 0),
            self.create_artificial_edge(node2, self.vT, lower, F - U, 0)
        ]
        self.processor.ts_edges.extend(edges_artificial)
        self.edges_added.extend(edges_artificial)
    
    def remove_and_replace_edge(self, u, v, node1, node2, lower, upper, cost):
        removed = self.processor.remove_edge_by_id(u, v)
        if not removed:
            print(f"⚠️  Không tìm thấy cung gốc ({u} → {v}) để loại bỏ")
        edges_replacement = [
            self.create_artificial_edge(self.processor.graph.nodes[u], node1, lower, upper, cost),
            self.create_artificial_edge(node2, self.processor.graph.nodes[v], lower, upper, 0)
        ]
        self.processor.ts_edges.extend(edges_replacement)
        self.edges_added.extend(edges_replacement)
    
    def generate_p_line(self):
        max_node_id = 0
        num_edges = 0
        for edge in self.processor.ts_edges:
            if edge is not None and hasattr(edge, 'start_node') and hasattr(edge, 'end_node'):
                max_node_id = max(max_node_id, edge.start_node.id, edge.end_node.id)
                num_edges += 1
        return f"p min {max_node_id} {num_edges}\n"
    
    def generate_node_lines(self, supply=None):
        pos_lines = [f"n {s} 1\n" for s in self.processor.started_nodes]
        neg_lines = [f"n {t.id} -1\n" for t in self.processor.target_nodes]

        if supply is not None:
            pos_lines.append(f"n {self.vS.id} {supply}\n")
            neg_lines.append(f"n {self.vT.id} {-supply}\n")

        return pos_lines, neg_lines

    def write_edges(self, file_handle):
        H = getattr(self.processor, 'H', None)
        M = getattr(self.processor, 'M', None)
        for edge in self.processor.ts_edges:
            if edge is not None and hasattr(edge, 'start_node') and hasattr(edge, 'end_node'):
                u = edge.start_node.id
                v = edge.end_node.id
                low = getattr(edge, 'lower', self.DEFAULT_LOWER)
                up = getattr(edge, 'upper', self.DEFAULT_UPPER)
                cost = getattr(edge, 'weight', 1)
                if H is not None and M is not None and cost == H * H:
                    time = u // M - (1 if u % M == 0 else 0)
                    if time >= H:
                        file_handle.write(f"c Exceed {cost} {cost // M} as {u} // {M} - (1 if {u} % {M} == 0 else 0)\n")
                file_handle.write(f"a {u} {v} {low} {up} {cost}\n")

    def write_to_dimacs(self, tsg_path=None, U=None):
        if tsg_path is None:
            tsg_path = (Path(__file__).parent.parent / "TSG.txt").resolve()
        else:
            tsg_path = Path(tsg_path).resolve()

        supply = self.pipeline.max_flow_value - U if U is not None else None
        pos_lines, neg_lines = self.generate_node_lines(supply)
        p_line = self.generate_p_line()

        with open(tsg_path, "w", encoding="utf-8") as f:
            f.write(p_line)
            for line in pos_lines + neg_lines:
                f.write(line)
            self.write_edges(f)
    
    # ==== Các hàm được gọi trong run() ====
    def add_artificial_source_sink_nodes(self):
        self.processor.ts_nodes.extend([self.vS, self.vT])
        self.processor.graph.nodes[self.vS.id] = self.vS
        self.processor.graph.nodes[self.vT.id] = self.vT

    def ask_gamma(self):
        gamma_input = input("Nhập gamma (cost vS→vT, mặc định = 1230919231): ")
        return int(gamma_input) if gamma_input.strip() else self.DEFAULT_GAMMA
    
    def add_exit_edge_vs_to_vt(self, U, gamma):
        F = self.pipeline.max_flow_value
        edge = ExitEdge(self.vS, self.vT, self.DEFAULT_LOWER, max(F - U, 0), gamma)
        self.processor.ts_edges.append(edge)
        self.edges_added.append(edge)

    def collect_omega_in_edges(self):
        """Lọc tất cả các cung có điểm đầu nằm trong tập omega_in."""
        omega_in = self.pipeline.omega_in
        omega_edges = self.pipeline.omega_edges
        V = [edge for edge in omega_edges if edge.start_node.id in {n.id for n in omega_in}]
        return V

    def insert_artificial_nodes_and_edges(self, V, U):
        F = self.pipeline.max_flow_value
        for idx, edge in enumerate(V):
            u, v = edge.start_node.id, edge.end_node.id
            cost = edge.weight

            orig_edge = self.find_original_edge(u, v)
            lower = getattr(orig_edge, 'lower', self.DEFAULT_LOWER) if orig_edge else self.DEFAULT_LOWER
            upper = getattr(orig_edge, 'upper', self.DEFAULT_UPPER) if orig_edge else self.DEFAULT_UPPER

            node1, node2 = self.create_artificial_nodes(idx)

            self.add_artificial_edges(node1, node2, lower, upper, F, U)
            self.remove_and_replace_edge(u, v, node1, node2, lower, upper, cost)
    
    def write_to_dimacs_file(self, U, tsg_path=None):
        self.write_to_dimacs(tsg_path=tsg_path, U=U)

    def write_to_dimacs_file_from_tsg(self, tsg_path=None):
        self.write_to_dimacs(tsg_path=tsg_path)

    def run(self, U, gamma):
        self.add_artificial_source_sink_nodes()
        self.add_exit_edge_vs_to_vt(U, gamma)
        V = self.collect_omega_in_edges()
        self.insert_artificial_nodes_and_edges(V, U)
        self.write_to_dimacs_file(U)