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
        artificial_offset = self._get_artificial_offset()

        self.vs_id = vs_id if vs_id is not None else max_id + offset
        self.vt_id = vt_id if vt_id is not None else max_id + offset + 1
        self.artificial_node_id = start_artificial_id if start_artificial_id is not None else self.vt_id + artificial_offset

        self.vS = ArtificialNode(id=self.vs_id, label="vS")
        self.vT = ArtificialNode(id=self.vt_id, label="vT")
        self.edges_added = []

    def _get_max_id(self):
        all_ids = [node.id for node in self.processor.ts_nodes]
        if hasattr(self.processor, "graph") and hasattr(self.processor.graph, "nodes"):
            all_ids += list(self.processor.graph.nodes.keys())
        return max(all_ids) if all_ids else 1000

    def _get_offset(self):
        node_count = len(set(node.id for node in self.processor.ts_nodes))
        return max(1000, node_count * 10)

    def _get_artificial_offset(self):
        node_count = len(set(node.id for node in self.processor.ts_nodes))
        return max(100, node_count * 2)

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

    def _add_artificial_edges(self, node1, node2, lower, upper, F, U):
        edges_artificial = [
            self.create_artificial_edge(self.vS, node1, lower, F - U, 0),
            self.create_artificial_edge(node1, node2, lower, upper, 0),
            self.create_artificial_edge(node2, self.vT, lower, F - U, 0)
        ]
        self.processor.ts_edges.extend(edges_artificial)
        self.edges_added.extend(edges_artificial)
    
    def _remove_and_replace_edge(self, u, v, node1, node2, lower, upper, cost):
        removed = self.processor.remove_edge_by_id(u, v)
        if not removed:
            print(f"⚠️  Không tìm thấy cung gốc ({u} → {v}) để loại bỏ")
        edges_replacement = [
            self.create_artificial_edge(self.processor.graph.nodes[u], node1, lower, upper, cost),
            self.create_artificial_edge(node2, self.processor.graph.nodes[v], lower, upper, 0)
        ]
        self.processor.ts_edges.extend(edges_replacement)
        self.edges_added.extend(edges_replacement)

    def print_artificial_edges(self):
        print("\n=== 📤 Danh sách các cung ảo đã được tạo ===")
        for edge in self.edges_added:
            u = edge.start_node.id
            v = edge.end_node.id
            low = getattr(edge, 'lower', self.DEFAULT_LOWER)
            up = getattr(edge, 'upper', self.DEFAULT_UPPER)
            cost = getattr(edge, 'weight', 1)
            print(f"a {u} {v} {low} {up} {cost}")
        print(f"→ Tổng số cung ảo được thêm: {len(self.edges_added)}")
    
    # ==== Các hàm được gọi trong run() ====
    def add_artificial_source_sink_nodes(self):
        self.processor.ts_nodes.extend([self.vS, self.vT])
        self.processor.graph.nodes[self.vS.id] = self.vS
        self.processor.graph.nodes[self.vT.id] = self.vT

    def ask_upper_bound(self):
        U_input = input("Nhập U (upper bound mỗi nhánh phụ, mặc định = 1): ")
        return int(U_input) if U_input.strip() else 1

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

            self._add_artificial_edges(node1, node2, lower, upper, F, U)
            self._remove_and_replace_edge(u, v, node1, node2, lower, upper, cost)

    def write_to_dimacs_file(self, filename="TSG1.txt"):
        F = self.pipeline.max_flow_value
        U = self.ask_upper_bound()  # hoặc truyền U vào hàm nếu cần
        supply = F - U

        with open(filename, "w") as f:
            # Nếu có dòng p min ... thì ghi trước
            if hasattr(self.processor, "dimacs_header"):
                f.write(self.processor.dimacs_header + "\n")
            # Ghi supply/demand cho vS và vT
            f.write(f"n {self.vS.id} {supply}\n")
            f.write(f"n {self.vT.id} {-supply}\n")
            # Ghi các cung
            for e in self.processor.ts_edges:
                if hasattr(e, 'start_node') and hasattr(e, 'end_node'):
                    u = e.start_node.id
                    v = e.end_node.id
                    low = getattr(e, 'lower', self.DEFAULT_LOWER)
                    up = getattr(e, 'upper', self.DEFAULT_UPPER)
                    cost = getattr(e, 'weight', 1)
                    f.write(f"a {u} {v} {low} {up} {cost}\n")
        print(f"✅ File {filename} đã được tạo thành công.")

    def write_to_dimacs_file_from_tsg(self, tsg_path=None, out_path="TSG1.txt"):
        # Nếu không truyền tsg_path thì tự động lấy file TSG.txt ở thư mục cha
        if tsg_path is None:
            tsg_path = (Path(__file__).parent.parent / "TSG.txt").resolve()
        else:
            tsg_path = Path(tsg_path).resolve()

        F = self.pipeline.max_flow_value
        U = self.ask_upper_bound()
        supply = F - U

        # Đọc toàn bộ file TSG.txt
        with open(tsg_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Tìm vị trí dòng a đầu tiên
        first_a_idx = next((i for i, line in enumerate(lines) if line.startswith("a ")), len(lines))

        # Tách các dòng trước và sau dòng a đầu tiên
        before_a = lines[:first_a_idx]
        after_a = lines[first_a_idx:]

        # Xử lý các dòng n: cập nhật hoặc thêm vS/vT
        vs_id = self.vS.id
        vt_id = self.vT.id
        found_vs = found_vt = False
        new_n_lines = []
        other_lines = []
        for line in before_a:
            if line.startswith("n "):
                parts = line.strip().split()
                if len(parts) >= 3:
                    if int(parts[1]) == vs_id:
                        new_n_lines.append(f"n {vs_id} {supply}\n")
                        found_vs = True
                        continue
                    elif int(parts[1]) == vt_id:
                        new_n_lines.append(f"n {vt_id} {-supply}\n")
                        found_vt = True
                        continue
            new_n_lines.append(line) if line.startswith("n ") else other_lines.append(line)
        # Nếu chưa có thì thêm vào
        if not found_vs:
            new_n_lines.append(f"n {vs_id} {supply}\n")
        if not found_vt:
            new_n_lines.append(f"n {vt_id} {-supply}\n")

        # Ghi lại phần đầu file: các dòng khác + các dòng n (đã cập nhật)
        output_lines = []
        output_lines.extend(other_lines)
        output_lines.extend(new_n_lines)
        output_lines.extend(after_a)

        # Lấy danh sách các cung gốc đã có trong file
        original_edges = set()
        for line in lines:
            if line.startswith("a "):
                parts = line.strip().split()
                if len(parts) >= 3:
                    u, v = int(parts[1]), int(parts[2])
                    original_edges.add((u, v))

        # Thêm các cung ảo mới vào cuối file
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)
            for e in self.processor.ts_edges:
                if hasattr(e, 'start_node') and hasattr(e, 'end_node'):
                    u = e.start_node.id
                    v = e.end_node.id
                    if (u, v) not in original_edges:
                        low = getattr(e, 'lower', self.DEFAULT_LOWER)
                        up = getattr(e, 'upper', self.DEFAULT_UPPER)
                        cost = getattr(e, 'weight', 1)
                        f.write(f"a {u} {v} {low} {up} {cost}\n")
        print("-------------------------------------------------------------------------------------------------------")
        print(f"✅ File {out_path} đã được cập nhật đúng thứ tự và bổ sung các cung ảo mới từ {tsg_path}.")

    def run(self, U, gamma):
        self.add_artificial_source_sink_nodes()
        self.add_exit_edge_vs_to_vt(U, gamma)
        V = self.collect_omega_in_edges()
        self.insert_artificial_nodes_and_edges(V, U)
        self.write_to_dimacs_file_from_tsg()