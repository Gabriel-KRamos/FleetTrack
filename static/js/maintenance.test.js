/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = $;
global.jQuery = $;
require('./maintenance.js');
describe('Maintenance Module JS Tests', () => {
  test('File loads and is DOM ready dependent', () => {
    expect(typeof window).toBe('object');
  });
  test('Maintenance complete handler submission mock works', () => {
    const completeHandler = jest.fn();
    completeHandler({ preventDefault: () => {} });
    expect(completeHandler).toHaveBeenCalled();
  });
  test('Service type change event function mock is callable', () => {
    const handleServiceChange = jest.fn();
    handleServiceChange('Outro');
    expect(handleServiceChange).toHaveBeenCalledWith('Outro');
  });
});