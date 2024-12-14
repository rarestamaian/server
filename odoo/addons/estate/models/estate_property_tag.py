from odoo import models, fields


class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Table that describes a property tag"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer(string="Color")
    _sql_constraints = [
        (
            'unique_property_tag_name',
            'UNIQUE(name)',
            'The tag name must be unique.'
        )
    ]


