jest.mock('./api', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import { api } from './api';
import {
  CORPORATE_DOCUMENT_MAX_SIZE,
  formatFileSize,
  normalizeDocumentFileEndpoint,
  uploadCorporateDocumentFile,
  validateCorporateDocumentFile,
} from './corporateDocuments';

describe('corporate document files', () => {
  beforeEach(() => jest.clearAllMocks());

  it('accepts supported files up to 25 MB', () => {
    const file = new File(['conteudo'], 'procedimento.PDF', { type: 'application/pdf' });
    expect(validateCorporateDocumentFile(file)).toBe(file);
  });

  it('rejects unsupported and oversized files before the request', () => {
    expect(() => validateCorporateDocumentFile(
      new File(['x'], 'script.exe', { type: 'application/octet-stream' })
    )).toThrow('Formato não permitido');

    expect(() => validateCorporateDocumentFile({
      name: 'grande.pdf',
      size: CORPORATE_DOCUMENT_MAX_SIZE + 1,
    })).toThrow('25 MB');
  });

  it('uploads to the corporate document endpoint and reports progress', async () => {
    const file = new File(['conteudo'], 'procedimento.pdf', { type: 'application/pdf' });
    const onProgress = jest.fn();
    api.post.mockImplementation(async (_url, _data, config) => {
      config.onUploadProgress({ loaded: 5, total: 10 });
      return { data: { file_name: file.name, file_size: file.size } };
    });

    const result = await uploadCorporateDocumentFile('doc-123', file, onProgress);

    expect(api.post).toHaveBeenCalledWith(
      '/documentos-corporativos/doc-123/upload',
      expect.any(FormData),
      expect.objectContaining({ onUploadProgress: expect.any(Function) })
    );
    expect(onProgress).toHaveBeenCalledWith(50);
    expect(result.file_name).toBe('procedimento.pdf');
  });

  it('normalizes stored API URLs and formats file sizes', () => {
    expect(normalizeDocumentFileEndpoint('/api/storage/docs/file.pdf')).toBe('/storage/docs/file.pdf');
    expect(normalizeDocumentFileEndpoint('/storage/docs/file.pdf')).toBe('/storage/docs/file.pdf');
    expect(formatFileSize(2 * 1024 * 1024)).toBe('2.0 MB');
  });
});
