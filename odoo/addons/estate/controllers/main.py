from odoo import http
from odoo.http import request

class PropertyController(http.Controller):
    @http.route('/user/properties', type='json', auth='user')
    def get_properties(self, user_id, offset=0, limit=50):
        properties = request.env['estate.property'].search_read(
            [('user_id', '=', int(user_id))], ['name'], offset=int(offset), limit=int(limit)
        )
        return properties
