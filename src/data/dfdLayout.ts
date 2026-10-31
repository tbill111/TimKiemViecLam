/**
 * Bố cục sơ đồ DFD (ký hiệu Gane–Sarson): mức 0 (sơ đồ ngữ cảnh) và mức 1.
 * Tách khỏi component để kiểm tra tự động: nhãn luồng không được đè lên đường nối hay nút.
 *
 * Quy ước toạ độ: gốc ở góc trên bên trái, đơn vị px của khung vẽ SVG.
 */

export type NodeKind = 'entity' | 'process' | 'store';
export type LabelSide = 'above' | 'below' | 'left' | 'right';
export type FlowTone = 'default' | 'blue' | 'green';

export interface DfdNode {
  id: string;
  kind: NodeKind;
  /** Mã hiển thị: E1, P1, D1... */
  code: string;
  /** Tên hiển thị, mỗi phần tử là một dòng. */
  title: string[];
  cx: number;
  cy: number;
  /** Chiều rộng và chiều cao cho entity và store. */
  w?: number;
  h?: number;
  /** Bán kính cho process. */
  r?: number;
  /** Tác nhân được vẽ lặp lại để sơ đồ gọn (đánh dấu * theo quy ước DFD). */
  duplicate?: boolean;
}

export interface DfdFlow {
  id: string;
  from: string;
  to: string;
  /** Nhãn luồng dữ liệu, mỗi phần tử là một dòng. */
  label: string[];
  /** Vị trí nhãn so với đường nối. */
  side: LabelSide;
  /** Tinh chỉnh thêm vị trí nhãn (px). */
  dx?: number;
  dy?: number;
  /** Dời cả đường nối theo phương vuông góc (px), dùng cho hai luồng ngược chiều giữa cùng hai nút. */
  offset?: number;
  tone: FlowTone;
}

export interface DfdDiagram {
  width: number;
  height: number;
  nodes: DfdNode[];
  flows: DfdFlow[];
}

export interface Point {
  x: number;
  y: number;
}

export interface FlowGeometry {
  start: Point;
  end: Point;
  labelX: number;
  labelY: number;
  anchor: 'start' | 'middle' | 'end';
  lines: string[];
  lineHeight: number;
  fontSize: number;
}

export const LABEL_FONT_SIZE = 11;
const LABEL_LINE_HEIGHT = 13;

// ============================================================
// DFD MỨC 0 – SƠ ĐỒ NGỮ CẢNH
// ============================================================

export const dfdLevel0: DfdDiagram = {
  width: 900,
  height: 400,
  nodes: [
    { id: 'S0', kind: 'process', code: '0', title: ['Hệ thống', 'SmartCareer'], cx: 450, cy: 200, r: 72 },
    { id: 'E1', kind: 'entity', code: 'E1', title: ['Sinh viên'], cx: 100, cy: 200, w: 150, h: 60 },
    { id: 'E2', kind: 'entity', code: 'E2', title: ['Doanh nghiệp'], cx: 800, cy: 200, w: 150, h: 60 },
    { id: 'E3', kind: 'entity', code: 'E3', title: ['Nguồn tuyển dụng', 'ngoài được phép'], cx: 450, cy: 38, w: 190, h: 56 },
    { id: 'E4', kind: 'entity', code: 'E4', title: ['Nhà trường'], cx: 450, cy: 365, w: 170, h: 50 },
  ],
  flows: [
    { id: 'c01', from: 'E1', to: 'S0', label: ['Hồ sơ, CV,', 'yêu cầu tìm kiếm'], side: 'above', offset: -18, tone: 'default' },
    { id: 'c02', from: 'S0', to: 'E1', label: ['Việc phù hợp,', 'kỹ năng thiếu'], side: 'below', offset: -18, tone: 'green' },
    { id: 'c03', from: 'E2', to: 'S0', label: ['Tin tuyển dụng,', 'trạng thái hồ sơ'], side: 'below', offset: -18, tone: 'default' },
    { id: 'c04', from: 'S0', to: 'E2', label: ['Ứng viên', 'xếp hạng'], side: 'above', offset: -18, tone: 'green' },
    { id: 'c05', from: 'E3', to: 'S0', label: ['Tin tuyển dụng', 'được cấp phép'], side: 'right', tone: 'default' },
    { id: 'c06', from: 'E4', to: 'S0', label: ['Chương trình', 'đào tạo'], side: 'left', offset: -22, tone: 'default' },
    { id: 'c07', from: 'S0', to: 'E4', label: ['Báo cáo', 'kỹ năng'], side: 'right', offset: -22, tone: 'green' },
  ],
};

// ============================================================
// DFD MỨC 1
// ============================================================

export const dfdLevel1: DfdDiagram = {
  width: 1060,
  height: 640,
  nodes: [
    // Tác nhân nguồn (bên trái)
    { id: 'E2', kind: 'entity', code: 'E2', title: ['Doanh nghiệp'], cx: 85, cy: 60, w: 150, h: 56 },
    { id: 'E3', kind: 'entity', code: 'E3', title: ['Nguồn tuyển dụng', 'ngoài được phép'], cx: 85, cy: 175, w: 150, h: 56 },
    { id: 'E4', kind: 'entity', code: 'E4', title: ['Nhà trường'], cx: 85, cy: 330, w: 150, h: 56 },
    { id: 'E1', kind: 'entity', code: 'E1', title: ['Sinh viên'], cx: 85, cy: 520, w: 150, h: 56 },

    // Tiến trình
    { id: 'P1', kind: 'process', code: 'P1', title: ['Tiếp nhận &', 'kiểm tra'], cx: 330, cy: 175, r: 52 },
    { id: 'P2', kind: 'process', code: 'P2', title: ['Làm sạch &', 'chuẩn hóa'], cx: 510, cy: 175, r: 52 },
    { id: 'P3', kind: 'process', code: 'P3', title: ['Lưu trữ &', 'quản lý'], cx: 690, cy: 175, r: 52 },
    { id: 'P4', kind: 'process', code: 'P4', title: ['Phân tích &', 'ghép nối'], cx: 580, cy: 455, r: 52 },
    { id: 'P5', kind: 'process', code: 'P5', title: ['Trả kết quả', '& báo cáo'], cx: 770, cy: 470, r: 52 },

    // Kho dữ liệu
    { id: 'D3', kind: 'store', code: 'D3', title: ['Kỹ năng & khóa học'], cx: 510, cy: 305, w: 180, h: 26 },
    { id: 'D1', kind: 'store', code: 'D1', title: ['Hồ sơ & CV'], cx: 690, cy: 305, w: 140, h: 26 },
    { id: 'D2', kind: 'store', code: 'D2', title: ['Tin tuyển dụng'], cx: 870, cy: 305, w: 160, h: 26 },
    { id: 'D4', kind: 'store', code: 'D4', title: ['Kết quả & hành vi'], cx: 580, cy: 600, w: 180, h: 26 },

    // Tác nhân nhận kết quả (vẽ lặp bên phải)
    { id: 'E1R', kind: 'entity', code: 'E1', title: ['Sinh viên'], cx: 990, cy: 385, w: 130, h: 50, duplicate: true },
    { id: 'E2R', kind: 'entity', code: 'E2', title: ['Doanh nghiệp'], cx: 990, cy: 485, w: 130, h: 50, duplicate: true },
    { id: 'E4R', kind: 'entity', code: 'E4', title: ['Nhà trường'], cx: 990, cy: 585, w: 130, h: 50, duplicate: true },
  ],
  flows: [
    // Thu thập
    { id: 'f01', from: 'E2', to: 'P1', label: ['Tin tuyển dụng'], side: 'above', tone: 'default' },
    { id: 'f02', from: 'E3', to: 'P1', label: ['Dữ liệu đối tác'], side: 'above', tone: 'default' },
    { id: 'f03', from: 'E4', to: 'P1', label: ['Chương trình', 'đào tạo'], side: 'above', tone: 'default' },
    { id: 'f04', from: 'E1', to: 'P1', label: ['Hồ sơ và CV'], side: 'right', tone: 'default' },
    { id: 'f05', from: 'P1', to: 'P2', label: ['Dữ liệu', 'thô'], side: 'above', dy: -8, tone: 'default' },
    { id: 'f06', from: 'D3', to: 'P2', label: ['Từ điển', 'kỹ năng'], side: 'left', offset: -16, tone: 'default' },
    { id: 'f07', from: 'P2', to: 'D3', label: ['Kỹ năng mới,', 'khóa học'], side: 'right', offset: -16, tone: 'default' },
    { id: 'f08', from: 'P2', to: 'P3', label: ['Dữ liệu đã', 'chuẩn hóa'], side: 'above', dy: -10, tone: 'default' },
    { id: 'f09', from: 'P3', to: 'D1', label: ['Lưu hồ sơ'], side: 'left', tone: 'default' },
    { id: 'f10', from: 'P3', to: 'D2', label: ['Lưu tin'], side: 'above', tone: 'default' },
    // Phân tích và trả kết quả
    { id: 'f11', from: 'D1', to: 'P4', label: ['Hồ sơ'], side: 'left', tone: 'default' },
    { id: 'f12', from: 'D2', to: 'P4', label: ['Tin đã chuẩn hóa'], side: 'right', dx: 70, dy: -33, tone: 'default' },
    { id: 'f13', from: 'E1', to: 'P4', label: ['Yêu cầu tìm kiếm'], side: 'above', tone: 'blue' },
    { id: 'f14', from: 'P4', to: 'D4', label: ['Kết quả,', 'hành vi'], side: 'left', tone: 'default' },
    { id: 'f15', from: 'P4', to: 'P5', label: ['Danh sách', 'phù hợp'], side: 'above', tone: 'blue' },
    { id: 'f16', from: 'D4', to: 'P5', label: ['Lịch sử', 'ứng tuyển'], side: 'below', tone: 'default' },
    { id: 'f17', from: 'P5', to: 'E1R', label: ['Việc phù hợp'], side: 'above', tone: 'green' },
    { id: 'f18', from: 'P5', to: 'E2R', label: ['Ứng viên', 'xếp hạng'], side: 'above', tone: 'green' },
    { id: 'f19', from: 'P5', to: 'E4R', label: ['Báo cáo', 'kỹ năng'], side: 'below', tone: 'green' },
  ],
};

// ============================================================
// HÌNH HỌC
// ============================================================

export function findNode(diagram: DfdDiagram, id: string): DfdNode {
  const node = diagram.nodes.find((n) => n.id === id);
  if (!node) throw new Error(`Không tìm thấy nút DFD: ${id}`);
  return node;
}

/** Điểm nằm trên biên của nút, theo hướng từ tâm nút tới `toward`. */
export function boundaryPoint(node: DfdNode, toward: Point): Point {
  const dx = toward.x - node.cx;
  const dy = toward.y - node.cy;
  const len = Math.hypot(dx, dy);
  if (node.kind === 'process') {
    const r = node.r ?? 52;
    return { x: node.cx + (dx / len) * r, y: node.cy + (dy / len) * r };
  }
  const hw = (node.w ?? 0) / 2;
  const hh = (node.h ?? 0) / 2;
  const s = Math.min(dx === 0 ? Infinity : hw / Math.abs(dx), dy === 0 ? Infinity : hh / Math.abs(dy));
  return { x: node.cx + dx * s, y: node.cy + dy * s };
}

/** Ước lượng chiều rộng chữ (px) theo cỡ chữ nhãn. */
export function estimateTextWidth(text: string, fontSize = LABEL_FONT_SIZE): number {
  // Đo thực tế trên trình duyệt: chữ tiếng Việt rộng khoảng 0,63–0,65 lần cỡ chữ mỗi ký tự
  return text.length * fontSize * 0.66;
}

export function flowGeometry(flow: DfdFlow, diagram: DfdDiagram): FlowGeometry {
  const from = findNode(diagram, flow.from);
  const to = findNode(diagram, flow.to);
  let start = boundaryPoint(from, { x: to.cx, y: to.cy });
  let end = boundaryPoint(to, { x: from.cx, y: from.cy });

  // Hướng đơn vị của đường nối; dời song song nếu có `offset`
  const len = Math.hypot(end.x - start.x, end.y - start.y);
  const ux = (end.x - start.x) / len;
  const uy = (end.y - start.y) / len;
  const off = flow.offset ?? 0;
  if (off !== 0) {
    start = { x: start.x - uy * off, y: start.y + ux * off };
    end = { x: end.x - uy * off, y: end.y + ux * off };
  }

  const lines = flow.label;
  const boxW = Math.max(...lines.map((l) => estimateTextWidth(l)));
  const boxH = LABEL_FONT_SIZE + (lines.length - 1) * LABEL_LINE_HEIGHT + 2;

  // Chọn chiều pháp tuyến theo `side`
  let nx = -uy;
  let ny = ux;
  const wantFlip =
    (flow.side === 'above' && ny > 0) ||
    (flow.side === 'below' && ny < 0) ||
    (flow.side === 'left' && nx > 0) ||
    (flow.side === 'right' && nx < 0);
  if (wantFlip) {
    nx = -nx;
    ny = -ny;
  }

  // Dời tâm nhãn ra khỏi đường nối: nửa bề dày khối nhãn theo pháp tuyến + khoảng hở 4px
  const mx = (start.x + end.x) / 2;
  const my = (start.y + end.y) / 2;
  const clearance = (Math.abs(nx) * boxW + Math.abs(ny) * boxH) / 2 + 4;
  const cx = mx + nx * clearance + (flow.dx ?? 0);
  const cy = my + ny * clearance + (flow.dy ?? 0);

  return {
    start,
    end,
    labelX: cx,
    // labelY là baseline của dòng đầu tiên
    labelY: cy - boxH / 2 + LABEL_FONT_SIZE,
    anchor: 'middle',
    lines,
    lineHeight: LABEL_LINE_HEIGHT,
    fontSize: LABEL_FONT_SIZE,
  };
}

/** Hộp bao quanh nhãn (dùng cho kiểm tra và căn chỉnh). */
export function labelBox(geo: FlowGeometry): { x1: number; y1: number; x2: number; y2: number } {
  const widest = Math.max(...geo.lines.map((l) => estimateTextWidth(l, geo.fontSize)));
  const x1 = geo.anchor === 'middle' ? geo.labelX - widest / 2 : geo.anchor === 'end' ? geo.labelX - widest : geo.labelX;
  const top = geo.labelY - geo.fontSize;
  const bottom = geo.labelY + (geo.lines.length - 1) * geo.lineHeight + 2;
  return { x1, y1: top, x2: x1 + widest, y2: bottom };
}
