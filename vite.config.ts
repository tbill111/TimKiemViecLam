import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    // Tách thư viện lớn thành chunk riêng để tránh cảnh báo chunk > 500 kB
    rolldownOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return undefined;
          // pdf.js chỉ nạp khi đọc CV, nên tách riêng để không làm nặng lần tải đầu
          if (id.includes('pdfjs-dist')) return 'pdf';
          if (id.includes('recharts') || id.includes('d3-') || id.includes('victory-vendor')) return 'charts';
          if (id.includes('react-dom') || id.includes('react-router') || id.includes('/react/')) return 'react-vendor';
          return 'vendor';
        },
      },
    },
  },
})
