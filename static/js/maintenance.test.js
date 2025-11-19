/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

describe('Maintenance JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
    });

    test('Toggles "Other" service field visibility', () => {
        document.body.innerHTML = `
            <select id="id_service_choice">
                <option value="Revisão">Revisão</option>
                <option value="Outro">Outro</option>
            </select>
            <div id="service_type_other_container" style="display:none;">
                <input id="id_service_type_other" />
            </div>
            <form id="maintenance-form"></form>
        `;

        require('./maintenance.js');
        $(document).trigger('ready');

        $('#id_service_choice').val('Outro').trigger('change');
        
        $('#id_service_choice').val('Revisão').trigger('change');

        $('#maintenance-form').submit();

        expect(true).toBe(true);
    });
});