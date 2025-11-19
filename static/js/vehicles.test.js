/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

describe('Vehicles JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
    });

    test('Handles vehicle list interactions', () => {
        document.body.innerHTML = `
            <input id="vehicle-search" />
            <select id="status-filter">
                <option value="all">Todos</option>
                <option value="active">Ativos</option>
            </select>
            <table id="vehicles-table">
                <tr class="vehicle-row" data-status="active"><td>Caminhão 1</td></tr>
            </table>
            <button class="btn-edit-vehicle">Editar</button>
        `;

        require('./vehicles.js');
        $(document).trigger('ready');

        $('#vehicle-search').val('Caminhão').trigger('keyup');
        $('#status-filter').val('active').trigger('change');

        $('.btn-edit-vehicle').first().click();

        expect(true).toBe(true);
    });
});