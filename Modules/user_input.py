import config

def get_maxflow_conditions(use_config_data=False):
    if config.maxflow_conditions is not None or use_config_data:
        return config.maxflow_conditions or [(1, 2, 3, 4)]
    print("Nhập các bộ điều kiện x y a b (Enter dòng trống để kết thúc, mặc định là '1 2 3 4'):")
    conditions = []
    while True:
        line = input("Nhập x y a b: ").strip()
        if not line:
            break
        try:
            x, y, a, b = map(int, line.split())
            conditions.append((x, y, a, b))
        except:
            print("⚠️  Nhập không hợp lệ. Nhập lại theo định dạng: x y a b")
    if not conditions:
        conditions = [(1, 2, 3, 4)]
    config.maxflow_conditions = conditions
    return conditions

def get_artificial_upper_bound(use_config_data=False):
    if config.artificial_upper_bound is not None or use_config_data:
        return config.artificial_upper_bound or 1
    U_input = input("Nhập U (upper bound mỗi nhánh phụ, mặc định = 1): ")
    U = int(U_input) if U_input.strip() else 1
    config.artificial_upper_bound = U
    return U

def get_artificial_gamma(use_config_data=False):
    if config.artificial_gamma is not None or use_config_data:
        return config.artificial_gamma or 1230919231
    gamma_input = input("Nhập gamma (cost vS→vT, mặc định = 1230919231): ")
    gamma = int(gamma_input) if gamma_input.strip() else 1230919231
    config.artificial_gamma = gamma
    return gamma