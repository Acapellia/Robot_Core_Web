import logging
import os
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("PCDMapParser")


class PCDParseError(Exception):
    """PCD 텍스트 파싱 실패 시 발생하는 예외"""
    pass


def parse_ascii_pcd(pcd_text: str) -> np.ndarray:
    """ALLMAPDATA에서 디코딩된 PCD(ASCII) 텍스트를 (N, 3) x/y/z 좌표 배열로 변환한다."""
    lines = pcd_text.splitlines()

    fields = []
    data_format = None
    num_points = 0
    data_start_idx = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        upper = stripped.upper()
        if upper.startswith("FIELDS"):
            fields = stripped.split()[1:]
        elif upper.startswith("POINTS"):
            num_points = int(stripped.split()[1])
        elif upper.startswith("DATA"):
            data_format = stripped.split()[1].lower()
            data_start_idx = idx + 1
            break

    if data_start_idx is None:
        raise PCDParseError("PCD 헤더에서 DATA 섹션을 찾을 수 없습니다.")

    if data_format != "ascii":
        raise PCDParseError(f"지원하지 않는 PCD DATA 형식입니다 (ascii만 지원): {data_format}")

    try:
        x_idx, y_idx, z_idx = fields.index("x"), fields.index("y"), fields.index("z")
    except ValueError:
        raise PCDParseError(f"PCD FIELDS에 x/y/z 좌표가 없습니다: {fields}")

    data_lines = lines[data_start_idx:data_start_idx + num_points] if num_points else lines[data_start_idx:]

    points = []
    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        tokens = stripped.split()
        if len(tokens) <= max(x_idx, y_idx, z_idx):
            continue
        try:
            points.append((float(tokens[x_idx]), float(tokens[y_idx]), float(tokens[z_idx])))
        except ValueError:
            continue

    if not points:
        raise PCDParseError("PCD 데이터에서 유효한 포인트를 파싱하지 못했습니다.")

    return np.asarray(points, dtype=np.float64)


def filter_floor_ceiling(points: np.ndarray, bin_size: float = 0.05) -> np.ndarray:
    """Z축 높이 분포(히스토그램)에서 바닥/천장 피크를 감지해 제외한다 (main.py의 필터링 로직 참고)."""
    z_values = points[:, 2]
    min_z, max_z = np.min(z_values), np.max(z_values)

    bins = np.arange(min_z, max_z + (bin_size * 1.5), bin_size)
    counts, bin_edges = np.histogram(z_values, bins=bins)
    mean_count = np.mean(counts)
    significant_peaks = np.where(counts > mean_count * 2)[0]

    z_min_limit, z_max_limit = min_z, max_z
    if len(significant_peaks) > 0:
        floor_bin_idx = significant_peaks[0]
        z_min_limit = bin_edges[floor_bin_idx + 1] + 0.02

        safe_distance_bins = int(2.0 / bin_size)
        ceiling_candidates = [idx for idx in significant_peaks if idx > floor_bin_idx + safe_distance_bins]
        if ceiling_candidates:
            ceiling_bin_idx = ceiling_candidates[-1]
            z_max_limit = bin_edges[ceiling_bin_idx] - 0.02

    keep_mask = (z_values >= z_min_limit) & (z_values <= z_max_limit)
    filtered = points[keep_mask]

    return filtered if len(filtered) > 0 else points


def render_topview_image(points: np.ndarray, pixel_size: float = 0.05, padding: int = 5) -> np.ndarray:
    """포인트 클라우드(x, y)를 위에서 내려본 2D 흑백 탑뷰 이미지로 투영한다 (main.py의 render_and_set_topview 참고)."""
    x, y = points[:, 0], points[:, 1]
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    img_w = max(int((x_max - x_min) / pixel_size) + padding * 2, 10)
    img_h = max(int((y_max - y_min) / pixel_size) + padding * 2, 10)

    image = np.full((img_h, img_w, 3), 255, dtype=np.uint8)

    x_range = (x_max - x_min) or 1.0
    y_range = (y_max - y_min) or 1.0

    img_x = ((x - x_min) / x_range * (img_w - padding * 2) + padding).astype(np.int32)
    img_y = (((y_max - y) / y_range) * (img_h - padding * 2) + padding).astype(np.int32)

    valid_mask = (img_x >= 0) & (img_x < img_w) & (img_y >= 0) & (img_y < img_h)
    image[img_y[valid_mask], img_x[valid_mask]] = [0, 0, 0]

    return image


def save_image(image: np.ndarray, save_path: str) -> str:
    out_dir = os.path.dirname(save_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    Image.fromarray(image, mode="RGB").save(save_path)
    return save_path


class PCDMapParser:
    """ALLMAPDATA로 수신된 PCD 데이터를 2D 탑뷰 이미지로 변환하고 파일로 저장하는 역할을 담당"""

    DEFAULT_OUTPUT_DIR = "pcd_datas"
    DEFAULT_PIXEL_SIZE = 0.05
    DEFAULT_PADDING = 5

    @classmethod
    def parse_and_save(
        cls,
        pcd_text: str,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        pixel_size: Optional[float] = None,
        padding: Optional[int] = None,
    ) -> Optional[str]:
        """PCD 텍스트를 파싱해 탑뷰 이미지를 생성하고 저장한 뒤, 저장된 파일 경로를 반환한다.
        파싱/생성에 실패하면 None을 반환한다 (allmapdata 처리 파이프라인 전체를 중단시키지 않음)."""
        try:
            points = parse_ascii_pcd(pcd_text)
            filtered_points = filter_floor_ceiling(points)
            image = render_topview_image(
                filtered_points,
                pixel_size=pixel_size or cls.DEFAULT_PIXEL_SIZE,
                padding=padding if padding is not None else cls.DEFAULT_PADDING,
            )

            base_name = os.path.splitext(os.path.basename(filename))[0] if filename else "map"
            save_path = os.path.join(output_dir or cls.DEFAULT_OUTPUT_DIR, f"topview-{base_name}.png")

            return save_image(image, save_path)
        except PCDParseError as e:
            logger.warning(f"[PCDMapParser] '{filename}' PCD 파싱 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"[PCDMapParser] '{filename}' 탑뷰 이미지 생성/저장 실패: {e}")
            return None
