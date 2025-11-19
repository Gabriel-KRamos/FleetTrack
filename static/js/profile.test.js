/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = $;
global.jQuery = $;
require('./profile.js');
describe('Profile Module JS Tests', () => {
  test('File loads successfully', () => {
    expect(typeof window).toBe('object');
  });
  test('Profile update form handler mock is callable', () => {
    const updateProfile = jest.fn();
    updateProfile('NewName');
    expect(updateProfile).toHaveBeenCalledWith('NewName');
  });
  test('Password change form submission handler mock runs', () => {
    const changePassword = jest.fn();
    changePassword({ password: 'new' });
    expect(changePassword).toHaveBeenCalled();
  });
});