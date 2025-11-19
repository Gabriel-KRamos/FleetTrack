/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

describe('Drivers JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
    });

    test('Handles driver search and modal interactions', () => {
        // 1. Setup DOM: Campo de busca, tabela e modal
        document.body.innerHTML = `
            <input id="driver-search" type="text" />
            <table id="drivers-table">
                <tbody>
                    <tr class="driver-row" data-name="João"><td>João</td></tr>
                    <tr class="driver-row" data-name="Maria"><td>Maria</td></tr>
                </tbody>
            </table>
            <button id="btn-add-driver">Adicionar</button>
            <div id="driverModal" class="modal"></div>
            <form id="driver-form"></form>
        `;

        require('./drivers.js');
        $(document).trigger('ready');

        $('#driver-search').val('João').trigger('keyup');
        
        $('#btn-add-driver').click();

        $('#driver-form').submit();

        expect($('#driver-search').val()).toBe('João');
    });
});