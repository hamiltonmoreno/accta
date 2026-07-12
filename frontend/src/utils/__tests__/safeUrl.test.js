import { safeUrl } from '../safeUrl';

describe('safeUrl (spec 019 M-HREF)', () => {
  it('mantém http(s) URLs', () => {
    expect(safeUrl('https://acme.cv')).toBe('https://acme.cv');
    expect(safeUrl('http://x.pt/a')).toBe('http://x.pt/a');
  });

  it('assume https:// quando falta scheme', () => {
    expect(safeUrl('acme.cv')).toBe('https://acme.cv');
    expect(safeUrl('  www.x.pt  ')).toBe('https://www.x.pt');
  });

  it('bloqueia schemes perigosos → null', () => {
    for (const bad of ['javascript:alert(1)', 'data:text/html,x', 'file:///etc/passwd', 'vbscript:msgbox', 'JavaScript:alert(1)']) {
      expect(safeUrl(bad)).toBeNull();
    }
  });

  it('vazio/não-string → null', () => {
    expect(safeUrl('')).toBeNull();
    expect(safeUrl(null)).toBeNull();
    expect(safeUrl(undefined)).toBeNull();
    expect(safeUrl(123)).toBeNull();
  });
});
