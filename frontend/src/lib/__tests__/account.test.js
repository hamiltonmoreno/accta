import { isMemberAccount } from '../account';

describe('isMemberAccount', () => {
  test('conta sem account_type é tratada como membro', () => {
    expect(isMemberAccount({ name: 'X' })).toBe(true);
  });
  test("account_type 'member' é membro", () => {
    expect(isMemberAccount({ account_type: 'member' })).toBe(true);
  });
  test("account_type 'technical' NÃO é membro", () => {
    expect(isMemberAccount({ account_type: 'technical' })).toBe(false);
  });
  test('user nulo não é membro', () => {
    expect(isMemberAccount(null)).toBe(true); // missing ⇒ member (default), null tratado como ausência
  });
});
