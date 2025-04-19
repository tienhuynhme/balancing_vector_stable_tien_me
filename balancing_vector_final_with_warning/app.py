import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm

st.set_page_config(page_title="Cân Bằng Động - Add Mass", layout="centered")
st.title("⚙️ Phân Tích Vector Mất Cân Bằng (Add Mass)")

# Nhập liệu từ máy cân bằng động
m_input = st.number_input("🔸 Khối lượng mất cân bằng đo được (g)", min_value=0.0, value=2.0)
r_input = st.number_input("🔸 Bán kính vị trí mất cân bằng đo được (mm)", min_value=1.0, value=70.0)
M = m_input * r_input

# Nhập bán kính cố định để gắn mass
fixed_r = st.number_input("🔸 Bán kính sử dụng để gắn khối lượng bù (mm)", min_value=1.0, value=50.0)

# Các thông số phân tách vector
angle_step = 18.0
fixed_m = st.number_input("🔸 Khối lượng cố định mỗi vector (g)", min_value=0.01, value=0.5)
theta = st.number_input("🔸 Góc mất cân bằng (°)", min_value=0.0, max_value=360.0, value=45.0)
allowed_error = st.number_input("🔸 Sai số tối đa cho phép (g.mm)", min_value=0.1, value=5.0)

if st.button("🚀 Phân tách & Hiển thị"):
    theta_rad = np.radians(theta)
    Mx, My = M * np.cos(theta_rad), M * np.sin(theta_rad)
    Mi = fixed_m * fixed_r
    n_vectors = 0
    used_angles = set()
    valid_angles = np.radians(np.arange(0, 360, int(angle_step)))
    components = []

    while np.sqrt(Mx**2 + My**2) > allowed_error and n_vectors < 1000:
        best_angle = None
        min_error = float("inf")
        for angle in valid_angles:
            if angle in used_angles:
                continue
            vx, vy = Mi * np.cos(angle), Mi * np.sin(angle)
            error = (Mx - vx)**2 + (My - vy)**2
            if error < min_error:
                min_error = error
                best_angle = angle
        if best_angle is None:
            break
        vx, vy = Mi * np.cos(best_angle), Mi * np.sin(best_angle)
        Mx -= vx
        My -= vy
        components.append((fixed_m, fixed_r, np.degrees(best_angle)))
        used_angles.add(best_angle)
        n_vectors += 1

    st.session_state.components = components
    residual_moment = np.sqrt((Mx_target - Mx)**2 + (My_target - My)**2)
    st.session_state.residual_moment = residual_moment
    if residual_moment > allowed_error:
        st.session_state.limit_warning = True
    else:
        st.session_state.limit_warning = False

if "components" in st.session_state:
    if "limit_warning" in st.session_state and st.session_state.limit_warning:
        st.error("⚠️ Không thể cân bằng đủ vì đã hết góc hợp lệ hoặc khối lượng mỗi vector quá nhỏ.")
        st.info("📉 Sai số còn lại: {:.2f} g.mm".format(st.session_state.residual_moment))
        st.info("💡 Gợi ý: Hãy thử tăng khối lượng mỗi vector hoặc nới rộng sai số cho phép.")
    components = st.session_state.components
    df = pd.DataFrame(components, columns=["Khối lượng (g)", "Bán kính gắn mass (mm)", "Góc (°)"])
    st.subheader("📋 Danh sách vector thành phần:")
    st.dataframe(df.style.format({"Khối lượng (g)": "{:.2f}", "Bán kính gắn mass (mm)": "{:.1f}", "Góc (°)": "{:.1f}"}))
    for m, r, a in components:
        st.markdown(f"- Gắn **{m:.2f} g** tại **góc {a:.1f}°**, bán kính **{r:.1f} mm**")

    check_Mx = sum(m * r * np.cos(np.radians(a)) for m, r, a in components)
    check_My = sum(m * r * np.sin(np.radians(a)) for m, r, a in components)
    total_moment = np.sqrt(check_Mx**2 + check_My**2)
    error = abs(total_moment - M)

    st.markdown("### ✅ Kiểm tra tổng moment")
    st.write(f"• Tổng moment thành phần: {total_moment:.2f} g.mm")
    st.write(f"• Moment gốc nhập vào: {M:.2f} g.mm")
    st.write(f"• Sai số còn lại: {error:.4f} g.mm")

    if len(components) > 1:
        usable_count = st.slider("Chọn số vector bạn có thể thực hiện", 1, len(components), len(components))
        partial_components = components[:usable_count]
        res_x = sum(m * r * np.cos(np.radians(a)) for m, r, a in partial_components)
        res_y = sum(m * r * np.sin(np.radians(a)) for m, r, a in partial_components)
        residual_moment = np.sqrt((M * np.cos(np.radians(theta)) - res_x)**2 + (M * np.sin(np.radians(theta)) - res_y)**2)

        st.markdown("### 📉 Sai số nếu chỉ thực hiện một phần:")
        st.write(f"• Vector lý tưởng: {len(components)}")
        st.write(f"• Vector bạn có thể thực hiện: {usable_count}")
        st.write(f"• Moment còn dư: {residual_moment:.2f} g.mm")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.set_xlim(-M * 1.2, M * 1.2)
    ax.set_ylim(-M * 1.2, M * 1.2)

    circle = plt.Circle((0, 0), fixed_r, color='lightgray', fill=False, linestyle='--')
    ax.add_patch(circle)
    for deg in range(0, 360, int(angle_step)):
        rad = np.radians(deg)
        ax.plot([0, fixed_r * 1.2 * np.cos(rad)], [0, fixed_r * 1.2 * np.sin(rad)], color='lightgray', lw=0.5, linestyle='--')
        ax.text(fixed_r * 1.3 * np.cos(rad), fixed_r * 1.3 * np.sin(rad), f"{deg}°", fontsize=8, ha='center', va='center')

    ax.quiver(0, 0, M * np.cos(np.radians(theta)), M * np.sin(np.radians(theta)),
              angles='xy', scale_units='xy', scale=1, color='red', label="Vector Mất Cân Bằng")

    x, y = 0, 0
    colors = cm.viridis(np.linspace(0, 1, len(components)))
    for i, (mass, r, angle) in enumerate(components):
        angle_rad = np.radians(angle)
        dx, dy = mass * r * np.cos(angle_rad), mass * r * np.sin(angle_rad)
        ax.quiver(x, y, dx, dy, angles='xy', scale_units='xy', scale=1, color=colors[i], alpha=0.8)
        x += dx
        y += dy

    ax.set_title("Mô phỏng vector trên rotor")
    ax.legend()
    st.pyplot(fig)
