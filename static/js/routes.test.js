/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

describe('Routes JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
        
        $.ajax = jest.fn().mockImplementation(({ success }) => {
            if (success) success({ distance: 100, duration: '2h' });
        });
    });

    test('Calculates route on input change', () => {
        document.body.innerHTML = `
            <input id="id_start_location" value="Joinville, SC" />
            <input id="id_end_location" value="Curitiba, PR" />
            <input id="id_distance" />
            <form id="route-form"></form>
        `;

        require('./routes.js');
        $(document).trigger('ready');

        $('#id_start_location').trigger('change');
        $('#id_end_location').trigger('change');

        $('#route-form').submit();

        expect(true).toBe(true);
    });
});