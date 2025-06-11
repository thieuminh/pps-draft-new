from controller.time_window_generator import TimeWindowGenerator

class CustomNWriter(TimeWindowGenerator):
    def append_n_lines(self, n_lines_pos, n_lines_neg):
        # Thêm các dòng n cho started_nodes
        for start in getattr(self, "started_nodes", []):
            n_lines_pos.append(f"n {start} 1\n")
        # Thêm các dòng n cho target nodes
        for target in self.get_targets():
            target_id = target.id
            n_lines_neg.append(f"n {target_id} -1\n")