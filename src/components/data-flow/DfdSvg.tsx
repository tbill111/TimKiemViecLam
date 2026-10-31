import { flowGeometry, type DfdDiagram, type DfdNode, type FlowTone } from '../../data/dfdLayout';

interface DfdSvgProps {
  diagram: DfdDiagram;
  /** Tiền tố id cho marker, để hai sơ đồ trên cùng trang không trùng id. */
  idPrefix: string;
  ariaLabel: string;
  /** Chiều rộng tối thiểu (px) để chữ không quá nhỏ trên màn hình hẹp. */
  minWidth?: number;
}

const toneStroke: Record<FlowTone, string> = {
  default: '#475569',
  blue: '#2563eb',
  green: '#16a34a',
};

const toneLabel: Record<FlowTone, string> = {
  default: '#334155',
  blue: '#1d4ed8',
  green: '#15803d',
};

const nodeTheme: Record<DfdNode['kind'], { fill: string; stroke: string; text: string }> = {
  entity: { fill: '#eff6ff', stroke: '#2563eb', text: '#1e3a8a' },
  process: { fill: '#fff7ed', stroke: '#ea580c', text: '#9a3412' },
  store: { fill: '#f1f5f9', stroke: '#64748b', text: '#334155' },
};

/**
 * Vẽ một sơ đồ DFD từ dữ liệu bố cục (ký hiệu Gane–Sarson).
 * Đường nối vẽ trước, nhãn và nút vẽ sau để nút che phần đầu mũi tên trong viền.
 */
export default function DfdSvg({ diagram, idPrefix, ariaLabel, minWidth = 720 }: DfdSvgProps) {
  const marker = (tone: FlowTone) => `${idPrefix}-arrow-${tone}`;

  return (
    <svg
      viewBox={`0 0 ${diagram.width} ${diagram.height}`}
      className="w-full"
      style={{ minWidth: `${minWidth}px`, fontFamily: 'Inter, sans-serif' }}
      role="img"
      aria-label={ariaLabel}
    >
      <defs>
        {(Object.keys(toneStroke) as FlowTone[]).map((tone) => (
          <marker key={tone} id={marker(tone)} markerWidth="9" markerHeight="9" refX="8" refY="3.5" orient="auto">
            <path d="M0,0 L0,7 L9,3.5 z" fill={toneStroke[tone]} />
          </marker>
        ))}
      </defs>

      {diagram.flows.map((flow) => {
        const geo = flowGeometry(flow, diagram);
        return (
          <line
            key={`line-${flow.id}`}
            x1={geo.start.x}
            y1={geo.start.y}
            x2={geo.end.x}
            y2={geo.end.y}
            stroke={toneStroke[flow.tone]}
            strokeWidth={1.8}
            markerEnd={`url(#${marker(flow.tone)})`}
          />
        );
      })}

      {diagram.flows.map((flow) => {
        const geo = flowGeometry(flow, diagram);
        return (
          <text
            key={`label-${flow.id}`}
            x={geo.labelX}
            y={geo.labelY}
            textAnchor={geo.anchor}
            fontSize={geo.fontSize}
            fill={toneLabel[flow.tone]}
          >
            {geo.lines.map((line, i) => (
              <tspan key={i} x={geo.labelX} dy={i === 0 ? 0 : geo.lineHeight}>
                {line}
              </tspan>
            ))}
          </text>
        );
      })}

      {diagram.nodes.map((node) => {
        const theme = nodeTheme[node.kind];
        if (node.kind === 'entity') {
          const w = node.w ?? 0;
          const h = node.h ?? 0;
          const x = node.cx - w / 2;
          const y = node.cy - h / 2;
          const titleTop = node.cy - ((node.title.length - 1) * 13) / 2 + 9;
          return (
            <g key={node.id}>
              <rect x={x} y={y} width={w} height={h} rx={6} fill={theme.fill} stroke={theme.stroke} strokeWidth={2} />
              {/* Dấu tác nhân vẽ lặp: vạch chéo ở góc trên bên trái */}
              {node.duplicate && <line x1={x} y1={y + 12} x2={x + 12} y2={y} stroke={theme.stroke} strokeWidth={2} />}
              <text x={node.cx} y={titleTop - 15} textAnchor="middle" fontSize={12} fontWeight={700} fill={theme.text}>
                {node.code}
                {node.duplicate ? '*' : ''}
              </text>
              {node.title.map((line, i) => (
                <text key={line} x={node.cx} y={titleTop + i * 13} textAnchor="middle" fontSize={11.5} fill={theme.text}>
                  {line}
                </text>
              ))}
            </g>
          );
        }
        if (node.kind === 'process') {
          const r = node.r ?? 52;
          const top = node.cy - ((node.title.length + 1) * 13) / 2;
          return (
            <g key={node.id}>
              <circle cx={node.cx} cy={node.cy} r={r} fill={theme.fill} stroke={theme.stroke} strokeWidth={2} />
              <text x={node.cx} y={top + 10} textAnchor="middle" fontSize={12.5} fontWeight={700} fill={theme.text}>
                {node.code}
              </text>
              {node.title.map((line, i) => (
                <text key={line} x={node.cx} y={top + 25 + i * 13} textAnchor="middle" fontSize={11} fill={theme.text}>
                  {line}
                </text>
              ))}
            </g>
          );
        }
        // Kho dữ liệu: hai đường song song, hở hai đầu
        const w = node.w ?? 0;
        const h = node.h ?? 0;
        return (
          <g key={node.id}>
            <line x1={node.cx - w / 2} y1={node.cy - h / 2} x2={node.cx + w / 2} y2={node.cy - h / 2} stroke={theme.stroke} strokeWidth={2} />
            <line x1={node.cx - w / 2} y1={node.cy + h / 2} x2={node.cx + w / 2} y2={node.cy + h / 2} stroke={theme.stroke} strokeWidth={2} />
            <text x={node.cx} y={node.cy + 4} textAnchor="middle" fontSize={11} fill={theme.text}>
              <tspan fontWeight={700}>{node.code}</tspan>
              {' · '}
              {node.title[0]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
