def get_maxflow_conditions():
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
    return conditions

def get_virtual_upper_bound():
    U_input = input("Nhập U (upper bound mỗi nhánh phụ, mặc định = 1): ")
    return int(U_input) if U_input.strip() else 1

def get_virtual_gamma():
    gamma_input = input("Nhập gamma (cost vS→vT, mặc định = 1230919231): ")
    return int(gamma_input) if gamma_input.strip() else 1230919231