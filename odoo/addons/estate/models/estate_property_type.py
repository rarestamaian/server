from odoo import models, fields, api


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Table that describes a property type"
    _order = "sequence, name"

    sequence = fields.Integer('Sequence', default=1, help="Used to order property types. Lower is better.")
# seq = to sort the types manually, using the handle widget in the type list view
    name = fields.Char(required=True)
    property_ids = fields.One2many(
        comodel_name="estate.property",
        inverse_name="property_type_id",
        string="Estate Properties")

    offer_ids = fields.One2many(
        comodel_name="estate.property.offer",
        inverse_name="property_type_id",
        string="Offers",
    )
    offer_count = fields.Integer(compute="_compute_offer_count", store=True)
    # so now we know how many offers are linked to a property type
    _sql_constraints = [
        (
            'unique_property_type_name',
            'UNIQUE(name)',
            'The type name must be unique.')
    ]

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)