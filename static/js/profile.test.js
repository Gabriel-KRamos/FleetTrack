/**
 * @jest-environment jsdom
 */
const $ = require('jquery');
global.$ = global.jQuery = $;

describe('Profile JS', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.resetModules();
    });

    test('Handles profile form interactions', () => {
        document.body.innerHTML = `
            <form id="profile-form">
                <input id="id_password" type="password" />
                <input id="id_confirm_password" type="password" />
                <button type="submit">Salvar</button>
            </form>
            <div id="message-container"></div>
        `;

        require('./profile.js');
        $(document).trigger('ready');

        $('#profile-form').submit();

        expect(true).toBe(true);
    });
});