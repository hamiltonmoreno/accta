import * as ctaPt from '../../content/cta';
import pt from '../locales/pt';
import en from '../locales/en';
import fr from '../locales/fr';
import { PENDING } from '../pending';

const placeholders = (s) => (s.match(/\{\w+\}/g) || []).sort().join(',');

// Compara forma (chaves, comprimento de arrays, tipos) e placeholders; devolve as divergências.
function diff(source, target, path = '') {
  const issues = [];
  if (typeof source === 'string') {
    if (typeof target !== 'string') issues.push(`${path}: em falta`);
    else if (placeholders(source) !== placeholders(target)) issues.push(`${path}: placeholders diferentes`);
    return issues;
  }
  if (Array.isArray(source)) {
    if (!Array.isArray(target) || target.length !== source.length) return [`${path}: array com tamanho diferente`];
    source.forEach((item, i) => issues.push(...diff(item, target[i], `${path}[${i}]`)));
    return issues;
  }
  if (source && typeof source === 'object') {
    if (!target || typeof target !== 'object') return [`${path}: em falta`];
    Object.keys(source).forEach((k) => issues.push(...diff(source[k], target[k], path ? `${path}.${k}` : k)));
    Object.keys(target).forEach((k) => {
      if (!(k in source)) issues.push(`${path ? `${path}.` : ''}${k}: chave órfã`);
    });
    return issues;
  }
  if (source !== target && typeof source !== typeof target) issues.push(`${path}: tipo diferente`);
  return issues;
}

const notPending = (locale) => (issue) => !PENDING[locale].some((key) => issue.startsWith(key));

describe.each([
  ['en', en],
  ['fr', fr],
])('dicionário %s', (locale, dict) => {
  test('tem as mesmas chaves e placeholders que o PT', () => {
    const { cta, ...rest } = dict;
    expect(diff(pt, rest).filter(notPending(locale))).toEqual([]);
  });

  test('cta tem a mesma forma que content/cta', () => {
    const source = { ...ctaPt };
    expect(diff(source, dict.cta, 'cta').filter(notPending(locale))).toEqual([]);
  });
});
