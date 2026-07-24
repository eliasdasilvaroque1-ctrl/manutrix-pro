import { api } from './api';

export const CORPORATE_DOCUMENT_ACCEPT = '.pdf,.docx,.xlsx,.png,.jpg,.jpeg';
export const CORPORATE_DOCUMENT_MAX_SIZE = 25 * 1024 * 1024;

const ALLOWED_EXTENSIONS = new Set(['pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg']);

export const formatFileSize = (bytes = 0) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const validateCorporateDocumentFile = (file) => {
  if (!file) throw new Error('Selecione um arquivo.');

  const extension = file.name?.split('.').pop()?.toLowerCase();
  if (!extension || !ALLOWED_EXTENSIONS.has(extension)) {
    throw new Error('Formato não permitido. Use PDF, DOCX, XLSX, PNG ou JPG.');
  }

  if (file.size === 0) throw new Error('O arquivo está vazio.');
  if (file.size > CORPORATE_DOCUMENT_MAX_SIZE) {
    throw new Error('O arquivo excede o limite de 25 MB.');
  }

  return file;
};

export const normalizeDocumentFileEndpoint = (fileUrl = '') => (
  fileUrl.startsWith('/api/') ? fileUrl.slice(4) : fileUrl
);

export const uploadCorporateDocumentFile = async (documentId, file, onProgress) => {
  validateCorporateDocumentFile(file);

  const data = new FormData();
  data.append('file', file);

  const response = await api.post(`/documentos-corporativos/${documentId}/upload`, data, {
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });

  return response.data;
};

export const downloadCorporateDocumentFile = async (fileUrl, fileName) => {
  if (!fileUrl) throw new Error('Arquivo não disponível.');

  const response = await api.get(normalizeDocumentFileEndpoint(fileUrl), {
    responseType: 'blob',
    timeout: 120000,
  });
  const blob = response.data instanceof Blob ? response.data : new Blob([response.data]);
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = objectUrl;
  link.download = fileName || 'documento';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
};
