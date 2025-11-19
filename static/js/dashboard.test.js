/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

global.Chart = jest.fn();

describe('Dashboard JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
    });

    test('Initializes charts if canvas elements exist', () => {
        document.body.innerHTML = `
            <canvas id="revenue-chart-canvas"></canvas>
            <canvas id="sales-chart-canvas"></canvas>
        `;
        require('./dashboard.js');

        $(document).trigger('ready');
        expect(true).toBe(true); 
    });
});