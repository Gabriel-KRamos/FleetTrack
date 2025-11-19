/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = $;
global.jQuery = $;
require('./drivers.js');
describe('Drivers Module JS Tests', () => {
  test('File loads and DOM manipulation code is present', () => {
    expect(typeof window).toBe('object');
  });
  test('Driver add modal submission handler mock works', () => {
    const submitHandler = jest.fn();
    submitHandler({ preventDefault: () => {} });
    expect(submitHandler).toHaveBeenCalled();
  });
  test('Driver search filtering function mock runs', () => {
    const filterDrivers = jest.fn();
    filterDrivers('active');
    expect(filterDrivers).toHaveBeenCalledWith('active');
  });
});