import open3d as o3d
import numpy as np
import os
import matplotlib.pyplot as plt # 이미지 생성을 위한 라이브러리 추가

def auto_remove_floor_and_ceiling(input_path, output_path, bin_size=0.05, peak_ratio=0.1, output_image_path=None):
    """
    Z축 분포(히스토그램)를 분석하여 바닥과 천장을 자동으로 감지하고 제거하는 함수
    
    :param input_path: 입력 PCD 파일 경로
    :param output_path: 출력 PCD 파일 경로
    :param bin_size: 히스토그램 구간 크기 (0.05 = 5cm 단위로 높이 분석)
    :param peak_ratio: 천장으로 인정하기 위한 최소 포인트 비율 (전체 평균 빈도수 대비 배수)
    :param output_image_path: 결과 탑뷰 이미지를 저장할 경로 (None이면 생성 안 함)
    """
    if not os.path.exists(input_path):
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_path}")
        return

    print(f"\n[{os.path.basename(input_path)}] 처리 시작...")
    pcd = o3d.io.read_point_cloud(input_path)
    
    if not pcd.has_points():
        print("오류: 포인트 클라우드가 비어 있습니다.")
        return

    points = np.asarray(pcd.points)
    z_values = points[:, 2]
    
    # --- 1. Z축 데이터의 히스토그램 생성 ---
    min_z, max_z = np.min(z_values), np.max(z_values)
    
    # bins 배열 생성시 max_z까지 포함되도록 마지막 안전장치 추가
    bins = np.arange(min_z, max_z + (bin_size * 1.5), bin_size) 
    counts, bin_edges = np.histogram(z_values, bins=bins)
    
    # --- 2. 자동 바닥/천장 감지 로직 ---
    mean_count = np.mean(counts)
    # 데이터 밀도가 평균의 2배 이상인 곳을 잠재적 평면(바닥/천장)으로 간주
    significant_peaks = np.where(counts > mean_count * 2)[0] 
    
    z_min_limit = min_z # 기본값
    z_max_limit = max_z # 기본값 (천장 없음 가정)

    if len(significant_peaks) > 0:
        # 바닥(Floor) 자동 탐지: 가장 낮은 위치에 있는 유의미한 피크
        floor_bin_idx = significant_peaks[0]
        # 바닥 피크의 '끝나는 지점' 바로 위를 기준으로 설정 (마진 2cm 추가)
        z_min_limit = bin_edges[floor_bin_idx + 1] + 0.02 
        
        # 천장(Ceiling) 자동 탐지: 야외 환경 고려
        # 바닥 피크와 최소 1.5m 이상 떨어진 위쪽 영역에서만 천장 후보 검색
        safe_distance_bins = int(1.5 / bin_size) 
        ceiling_candidates = [idx for idx in significant_peaks if idx > floor_bin_idx + safe_distance_bins] 
        
        if ceiling_candidates:
            # 가장 높은 곳에 있는 피크를 천장으로 판정
            ceiling_bin_idx = ceiling_candidates[-1]
            # 천장 피크가 시작되는 지점 바로 아래를 자르기 기준으로 설정 (마진 2cm 차감)
            z_max_limit = bin_edges[ceiling_bin_idx] - 0.02
            print(f"-> 천장 감지됨: {bin_edges[ceiling_bin_idx]:.2f}m 부근")
        else:
            print("-> 천장이 없는 야외 환경으로 추정됩니다. (천장 제거 스킵)")
    else:
        print("-> 명확한 바닥/천장 분포를 찾지 못했습니다. 원본 높이를 유지합니다.")

    # 최종 필터링 범위 출력
    print(f"[필터링 결과] Z범위: {z_min_limit:.2f}m ~ {z_max_limit:.2f}m")

    # --- 3. 포인트 필터링 ---
    keep_indices = np.where((z_values >= z_min_limit) & (z_values <= z_max_limit))[0]
    filtered_pcd = pcd.select_by_index(keep_indices)
    
    print(f"-> 포인트 수 변화: {len(points)} -> {len(filtered_pcd.points)}")
    
    # --- 4. PCD 결과 저장 ---
    o3d.io.write_point_cloud(output_path, filtered_pcd)
    print(f"-> PCD 저장 완료: {output_path}")

    # --- 5. 탑뷰 이미지 생성 및 저장 (추가된 기능) ---
    if output_image_path:
        create_topview_image(filtered_pcd, output_image_path)

def create_topview_image(pcd, save_path, pixel_size=0.05):
    """
    포인트 클라우드로부터 탑뷰(Projection) 이미지를 생성하여 저장하는 함수
    
    :param pcd: open3d 포인트 클라우드 객체
    :param save_path: 이미지를 저장할 경로
    :param pixel_size: 픽셀 하나가 나타내는 실제 거리(m). 값이 작을수록 고해상도 (예: 0.05 = 5cm)
    """
    print(f"-> 탑뷰 이미지 생성 중...")
    
    points = np.asarray(pcd.points)
    if len(points) == 0:
        print("   경고: 포인트가 없어 이미지를 생성할 수 없습니다.")
        return

    # X, Y 좌표만 추출
    x = points[:, 0]
    y = points[:, 1]

    # 좌표의 최솟값, 최댓값 구하기
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    # 이미지 크기 계산 (미터 단위를 픽셀 단위로 변환)
    # 이미지 테두리에 여백(Padding)을 5픽셀 정도 둠
    padding = 5
    width = int((x_max - x_min) / pixel_size) + padding * 2
    height = int((y_max - y_min) / pixel_size) + padding * 2

    # 안전장치: 이미지 크기가 너무 작거나 크면 조절
    width = max(width, 10)
    height = max(height, 10)
    
    if width * height > 50000000: # 50MP 이상일 경우 해상도 강제 낮춤
        print("   경고: 데이터 범위가 너무 넓어 해상도를 낮추어 이미지를 생성합니다.")
        return create_topview_image(pcd, save_path, pixel_size * 2)

    # 포인트들을 이미지 좌표계로 변환 (정규화)
    # X, Y 값을 0~1 사이로 만들고 이미지 크기를 곱함
    img_x = ((x - x_min) / (x_max - x_min) * (width - padding * 2) + padding).astype(np.int32)
    # Y축은 반전시켜야 일반적인 지도 형태가 됨 (이미지 좌표는 위가 0, 아래가 H)
    img_y = (((y_max - y) / (y_max - y_min)) * (height - padding * 2) + padding).astype(np.int32)

    # 이미지 좌표 범위 유효성 체크 (가끔 정밀도 문제로 범위를 벗어나는 것 방지)
    valid_mask = (img_x >= 0) & (img_x < width) & (img_y >= 0) & (img_y < height)
    img_x = img_x[valid_mask]
    img_y = img_y[valid_mask]

    # 2D 이미지 배열 생성 (흰색 배경: 255)
    image = np.full((height, width), 255, dtype=np.uint8)

    # 포인트가 있는 위치를 검은색(0)으로 칠함
    image[img_y, img_x] = 0

    # matplotlib를 이용해 이미지 저장 (plt.imshow를 쓰면 축 정보를 포함할 수 있으나, 여기선 순수 이미지만 저장)
    # cmap='gray'는 흑백 이미지를 의미
    plt.imsave(save_path, image, cmap='gray')
    print(f"-> 탑뷰 이미지 저장 완료: {save_path}")


# --- 사용 예시 ---
if __name__ == "__main__":
    # 데이터 경로 설정 (기존 사용자의 경로 유지)
    base_dir = "./pcd_datas"
    file_name = "map-21514416240"
    
    input_file = os.path.join(base_dir, f"{file_name}.pcd")          # 원본 PCD
    output_file = os.path.join(base_dir, f"fixed-{file_name}.pcd")    # 결과 PCD
    output_image = os.path.join(base_dir, f"topview-{file_name}.png") # 결과 탑뷰 이미지 (PNG)

    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"디렉토리 생성됨: {base_dir}")
        print("테스트를 위해 해당 디렉토리에 PCD 파일을 넣어주세요.")

    # 함수 실행 (마지막 인자로 이미지 저장 경로를 전달)
    auto_remove_floor_and_ceiling(input_file, output_file, bin_size=0.05, output_image_path=output_image)