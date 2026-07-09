import os
import sys
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np

class UbuntuPointMapViewer:
    def __init__(self, pcd_path):
        self.pcd_path = pcd_path
        self.pixel_size = 0.05
        self.padding = 5

        # 1. PCD 데이터 로드 및 필터링
        self.load_and_filter_pcd()

        # 2. Open3D 내장 GUI 어플리케이션 초기화
        gui.Application.instance.initialize()
        
        # 메인 윈도우 생성
        self.window = gui.Application.instance.create_window("3D & Topview Integrated Viewer", 1400, 800)
        
        # [해결책] 창이 닫힐 때 C++ 엔진을 안전하게 먼저 죽이도록 이벤트 등록
        self.window.set_on_close(self.on_window_close)
        
        # 3. UI 레이아웃 및 뷰어 배치
        self.init_ui()

    def load_and_filter_pcd(self):
        print(f"[{os.path.basename(self.pcd_path)}] 필터링 중...")
        self.original_pcd = o3d.io.read_point_cloud(self.pcd_path)
        points = np.asarray(self.original_pcd.points)
        z_values = points[:, 2]

        min_z, max_z = np.min(z_values), np.max(z_values)
        bins = np.arange(min_z, max_z + (0.05 * 1.5), 0.05)
        counts, bin_edges = np.histogram(z_values, bins=bins)
        mean_count = np.mean(counts)
        significant_peaks = np.where(counts > mean_count * 2)[0]
        
        z_min_limit, z_max_limit = min_z, max_z
        if len(significant_peaks) > 0:
            floor_bin_idx = significant_peaks[0]
            z_min_limit = bin_edges[floor_bin_idx + 1] + 0.02
            
            # 천장 위치 계산(최소 바닥으로부터 2미터)
            safe_distance_bins = int(2.0 / 0.05)
            ceiling_candidates = [idx for idx in significant_peaks if idx > floor_bin_idx + safe_distance_bins]
            if ceiling_candidates:
                ceiling_bin_idx = ceiling_candidates[-1]
                z_max_limit = bin_edges[ceiling_bin_idx] - 0.02

        keep_indices = np.where((z_values >= z_min_limit) & (z_values <= z_max_limit))[0]
        self.filtered_pcd = self.original_pcd.select_by_index(keep_indices)

        # 필터링으로 제외된 바닥 포인트들을 별도 보관 (클릭 지점의 실제 바닥 높이 조회용)
        floor_indices = np.where(z_values < z_min_limit)[0]
        self.floor_points = points[floor_indices]
        self.floor_z_fallback = np.median(self.floor_points[:, 2]) if len(self.floor_points) > 0 else z_min_limit

        if not self.filtered_pcd.has_colors():
            self.filtered_pcd.paint_uniform_color([0.6, 0.6, 0.6])

        # 3D 마커(빨간 구체)
        self.marker = o3d.geometry.TriangleMesh.create_sphere(radius=0.2)
        self.marker.paint_uniform_color([1.0, 0.0, 0.0])
        
        self.filtered_points = np.asarray(self.filtered_pcd.points)
        self.x_min, self.x_max = np.min(self.filtered_points[:, 0]), np.max(self.filtered_points[:, 0])
        self.y_min, self.y_max = np.min(self.filtered_points[:, 1]), np.max(self.filtered_points[:, 1])
        self.z_max = np.max(self.filtered_points[:, 2])

    def init_ui(self):
        # --- [왼쪽] 내장 3D Scene 뷰어 위젯 ---
        self.scene_widget = gui.SceneWidget()
        self.scene_widget.scene = rendering.Open3DScene(self.window.renderer)
        self.scene_widget.scene.set_background([0.1, 0.1, 0.1, 1.0])

        # 포인트 클라우드 추가
        mat_pcd = rendering.MaterialRecord()
        mat_pcd.point_size = 2.0
        self.scene_widget.scene.add_geometry("pcd_data", self.filtered_pcd, mat_pcd)

        # 마커 추가 (법선 경고를 피하기 위해 unlit 셰이더 사용)
        self.mat_marker = rendering.MaterialRecord()
        self.mat_marker.shader = "defaultUnlit" # 조명 연산을 안 하므로 경고가 안 뜸 (unlitLine은 LineSet 전용이라 TriangleMesh에 쓰면 렌더링이 깨짐)
        self.scene_widget.scene.add_geometry("marker", self.marker, self.mat_marker,
                                              add_downsampled_copy_for_fast_rendering=False)

        bounds = self.filtered_pcd.get_axis_aligned_bounding_box()
        self.scene_widget.setup_camera(60, bounds, bounds.get_center())

        # --- [오른쪽] 2D 탑뷰 이미지 위젯 ---
        self.topview_widget = gui.ImageWidget()
        self.render_and_set_topview()
        self.topview_widget.set_on_mouse(self.on_topview_mouse_event)

        # [해결책] Open3D의 알려진 버그: SceneWidget을 Horiz/Vert 같은 레이아웃
        # 컨테이너의 자식으로 넣으면 클릭 시 렌더링이 사라짐(github.com/isl-org/Open3D
        # issues #5343, #5768, #7317). 레이아웃 대신 window에 직접 자식으로 추가하고
        # on_layout에서 frame을 수동으로 배치해야 함.
        self.window.add_child(self.scene_widget)
        self.window.add_child(self.topview_widget)
        self.window.set_on_layout(self._on_layout)

    def _on_layout(self, layout_context):
        r = self.window.content_rect
        margin = 10
        gap = 10
        content_h = r.height - margin * 2

        # ImageWidget은 프레임 크기에 맞춰 이미지를 늘려서 그리므로, 프레임을
        # 원본 해상도(img_w x img_h)와 다르게 주면 클릭 좌표 -> 이미지 좌표
        # 변환이 어긋난다. 클릭 정확도를 위해 원본 해상도 그대로 표시한다.
        topview_w = self.img_w
        topview_h = self.img_h
        scene_w = max(100, r.width - margin * 2 - gap - topview_w)

        self.scene_widget.frame = gui.Rect(r.x + margin, r.y + margin, scene_w, content_h)
        self.topview_widget.frame = gui.Rect(r.x + margin + scene_w + gap, r.y + margin, topview_w, topview_h)

    def render_and_set_topview(self):
        # 이미지(캔버스) 크기 결정
        x, y = self.filtered_points[:, 0], self.filtered_points[:, 1]
        self.img_w = int((self.x_max - self.x_min) / self.pixel_size) + self.padding * 2
        self.img_h = int((self.y_max - self.y_min) / self.pixel_size) + self.padding * 2
        
        img_data = np.full((self.img_h, self.img_w, 3), 255, dtype=np.uint8)

        # 3D 좌표를 2D 픽셀 좌표로 변환 (정규화 및 스케일링)
        img_x = ((x - self.x_min) / (self.x_max - self.x_min) * (self.img_w - self.padding * 2) + self.padding).astype(np.int32)
        img_y = (((self.y_max - y) / (self.y_max - self.y_min)) * (self.img_h - self.padding * 2) + self.padding).astype(np.int32)

        # 이미지에 점 찍기 및 예외 처리
        valid_mask = (img_x >= 0) & (img_x < self.img_w) & (img_y >= 0) & (img_y < self.img_h)
        img_data[img_y[valid_mask], img_x[valid_mask]] = [0, 0, 0]

        # 클릭 마커를 매번 이 원본 위에 새로 그리기 위해 보관해둔다
        self.topview_base_img = img_data
        self.topview_widget.update_image(o3d.geometry.Image(self.topview_base_img))

    def _lookup_floor_z(self, world_x, world_y):
        if len(self.floor_points) == 0:
            return self.floor_z_fallback

        dist_sq = (self.floor_points[:, 0] - world_x) ** 2 + (self.floor_points[:, 1] - world_y) ** 2
        for radius in (0.2, 0.5, 1.0, 2.0):
            nearby_mask = dist_sq <= radius ** 2
            if np.any(nearby_mask):
                return np.mean(self.floor_points[nearby_mask, 2])

        return self.floor_z_fallback

    def _update_topview_marker(self, img_x, img_y):
        marked_img = self.topview_base_img.copy()
        radius = 4
        y0, y1 = max(0, img_y - radius), min(self.img_h, img_y + radius + 1)
        x0, x1 = max(0, img_x - radius), min(self.img_w, img_x + radius + 1)
        marked_img[y0:y1, x0:x1] = [255, 0, 0]
        self.topview_widget.update_image(o3d.geometry.Image(marked_img))

    def on_topview_mouse_event(self, event):
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_button_down(gui.MouseButton.LEFT):
            widget_w = self.topview_widget.frame.width
            widget_h = self.topview_widget.frame.height

            # 위젯 내 실제 클릭 좌표 계산
            click_x = event.x - self.topview_widget.frame.x
            click_y = event.y - self.topview_widget.frame.y

            # 위젯 크기와 원본 이미지 크기 비율 맞추기 (스케일링)
            raw_img_x = int((click_x / widget_w) * self.img_w)
            raw_img_y = int((click_y / widget_h) * self.img_h)
            raw_img_x = int(np.clip(raw_img_x, 0, self.img_w - 1))
            raw_img_y = int(np.clip(raw_img_y, 0, self.img_h - 1))

            # 2D 픽셀 좌표 → 3D 세계 좌표 (X, Y) 역산
            world_x = ((raw_img_x - self.padding) / (self.img_w - self.padding * 2)) * (self.x_max - self.x_min) + self.x_min
            world_y = self.y_max - ((raw_img_y - self.padding) / (self.img_h - self.padding * 2)) * (self.y_max - self.y_min)

            # 클릭한 X, Y 지점의 실제 바닥 높이(Z)를 필터링 전 원본 바닥 포인트에서 조회
            world_z = self._lookup_floor_z(world_x, world_y)

            print(f"[클릭] 이미지 좌표 (X: {raw_img_x}, Y: {raw_img_y}) -> 3D 좌표 (X: {world_x:.2f}, Y: {world_y:.2f}, Z: {world_z:.2f})")

            # topview 이미지에도 클릭 위치에 마커 표시
            self._update_topview_marker(raw_img_x, raw_img_y)

            # 마커 객체의 위치 이동 (지오메트리를 재생성하지 않고 변환 행렬만 갱신)
            # 마커는 포인트클라우드 최고 높이보다 살짝 위에 띄워서 주변 포인트에 가려지지 않게 함
            marker_z = self.z_max + 0.3
            transform = np.eye(4)
            transform[:3, 3] = [world_x, world_y, marker_z]
            self.scene_widget.scene.set_geometry_transform("marker", transform)

            # 화면 리프레시
            self.scene_widget.force_redraw()
            return True

        return False

    def on_window_close(self):
        """ [해결책] 창이 닫힐 때 파이썬 프로세스를 정상 탈출시키는 함수 """
        print("시각화 윈도우를 닫는 중...")
        gui.Application.instance.quit() # Open3D의 내부 UI 루프를 안전하게 종료
        return True # 창 닫기를 승인함

    def run(self):
        gui.Application.instance.run()

if __name__ == "__main__":
    pcd_file_path = "./pcd_datas/map-21514416240.pcd"
    
    if not os.path.exists(pcd_file_path):
        print(f"오류: PCD 파일이 없습니다. 경로를 확인하세요: {pcd_file_path}")
    else:
        viewer = UbuntuPointMapViewer(pcd_file_path)
        viewer.run()