import { unzipSync, strFromU8 } from 'fflate';
import { skillAliases, skillCatalog } from '../data/skillCatalog';

/** Giới hạn kích thước tệp CV đọc trên trình duyệt. */
export const MAX_CV_SIZE = 5 * 1024 * 1024;

export interface CvExtraction {
  /** Kỹ năng chuẩn tìm thấy, theo thứ tự xuất hiện trong CV. */
  skills: string[];
  githubUrl?: string;
  linkedinUrl?: string;
  email?: string;
}

// ============================================================
// ĐỌC VĂN BẢN TỪ TỆP (chạy hoàn toàn trên trình duyệt)
// ============================================================

/**
 * Đọc văn bản từ tệp CV. Hỗ trợ PDF (có lớp chữ), DOCX và TXT.
 * Tệp không được gửi đi đâu.
 */
export async function readCvText(file: File): Promise<string> {
  if (file.size > MAX_CV_SIZE) throw new Error('Tệp lớn hơn 5 MB.');
  const name = file.name.toLowerCase();
  if (name.endsWith('.pdf')) return readPdf(file);
  if (name.endsWith('.docx')) return readDocx(file);
  if (name.endsWith('.txt')) return file.text();
  throw new Error('Chỉ hỗ trợ tệp PDF, DOCX hoặc TXT.');
}

async function readPdf(file: File): Promise<string> {
  // Nạp pdf.js khi cần để không làm nặng lần tải trang đầu
  const pdfjs = await import('pdfjs-dist');
  const worker = await import('pdfjs-dist/build/pdf.worker.min.mjs?url');
  pdfjs.GlobalWorkerOptions.workerSrc = worker.default;

  const doc = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
  const pages: string[] = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const content = await (await doc.getPage(i)).getTextContent();
    pages.push(content.items.map((item) => ('str' in item ? item.str : '')).join(' '));
  }
  return pages.join('\n');
}

async function readDocx(file: File): Promise<string> {
  const entries = unzipSync(new Uint8Array(await file.arrayBuffer()), {
    filter: (f) => f.name === 'word/document.xml',
  });
  const xml = entries['word/document.xml'];
  if (!xml) throw new Error('Tệp DOCX không hợp lệ.');
  return strFromU8(xml)
    .replace(/<w:tab\/>/g, ' ')
    .replace(/<\/w:p>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

// ============================================================
// TRÍCH XUẤT KỸ NĂNG VÀ LIÊN KẾT
// ============================================================

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Tìm vị trí xuất hiện đầu tiên của từ khóa như một từ độc lập ("Git" không khớp "GitHub"). */
function firstIndexOf(text: string, term: string): number {
  const re = new RegExp(`(?<![\\p{L}\\p{N}])${escapeRegExp(term.toLowerCase())}(?![\\p{L}\\p{N}])`, 'u');
  return re.exec(text)?.index ?? -1;
}

const withProtocol = (url: string) => (/^https?:\/\//i.test(url) ? url : `https://${url}`);

/**
 * Dò kỹ năng theo danh mục từ khóa (tên chuẩn và từ đồng nghĩa) cùng các liên kết trong CV.
 * Đây là trích xuất theo từ điển, không phải mô hình AI.
 */
export function extractFromCv(text: string): CvExtraction {
  const lower = text.normalize('NFC').toLowerCase();

  const found: { skill: string; index: number }[] = [];
  for (const skill of skillCatalog) {
    const base = skill.replace(/\s+cơ bản$/, '');
    const terms = [skill, ...(skillAliases[skill] ?? []), ...(base !== skill ? [base] : [])];
    const positions = terms.map((t) => firstIndexOf(lower, t)).filter((i) => i >= 0);
    if (positions.length > 0) found.push({ skill, index: Math.min(...positions) });
  }

  const github = text.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/[A-Za-z0-9_.-]+/i)?.[0];
  const linkedin = text.match(/(?:https?:\/\/)?(?:[a-z]{2,3}\.)?linkedin\.com\/in\/[A-Za-z0-9_%-]+/i)?.[0];
  const email = text.match(/[\w.+-]+@[\w-]+\.[\w.-]+/)?.[0];

  return {
    skills: found.sort((a, b) => a.index - b.index).map((f) => f.skill),
    githubUrl: github ? withProtocol(github) : undefined,
    linkedinUrl: linkedin ? withProtocol(linkedin) : undefined,
    email,
  };
}
