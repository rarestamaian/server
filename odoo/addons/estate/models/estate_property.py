from odoo import models, fields, api
import datetime
# from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
import string
import random
import time
import logging
import os
# from datetime import datetime
import redis
import json
import hashlib

_logger = logging.getLogger(__name__)

# Create a Redis client instance
redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Table that describes a real estate property!"
    _order = "id desc"
    # _auto = False

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=lambda self: datetime.date.today() + datetime.timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    score = fields.Integer(default=0)
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        string="Garden Orientation",
        help="Select the orientation of the garden."
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled')
        ],
        required=True,
        copy=False,
        default='new',
        string="State",
        help="The state of the property",
        index=True
    )

    active = fields.Boolean(
        default=True,
        string="Active",
        help="Indicates if the property is active or archived",
        index=True
    )

    property_type_id = fields.Many2one(comodel_name="estate.property.type", string="Property Type",
                                       ondelete="restrict")

    salesPerson_id = fields.Many2one('res.users', string='Salesperson', index=True,
                                     default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Buyer', index=True, copy=False)
    tag_ids = fields.Many2many('estate.property.tag', string='Tags')
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Offers')

    total_area = fields.Integer(compute="_compute_total_area")
    best_price = fields.Integer(compute="_compute_max_offer_price")

    _sql_constraints = [
        (
            '_expected_price_positive',
            'CHECK(expected_price > 0)',
            'The expected price MUST be positive.'
        ),
        (
            '_selling_price_positive',
            'CHECK(selling_price >= 0)',
            'The selling price MUST be 0 or positive.'
        ),
    ]
    

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price_percentage(self):
        for record in self:
            if (not float_is_zero(record.selling_price, precision_rounding=0.01)
                    and float_compare(record.selling_price, record.expected_price * 0.9, precision_rounding=0.01) < 0):
                raise ValidationError("The selling price cannot be lower than 90% of the expected price")

    @api.depends("offer_ids.price")
    def _compute_max_offer_price(self):
        for record in self:
            # record.best_price = max(id.price for id in record.offer_ids)
            record.best_price = max(record.offer_ids.mapped("price"), default=0)

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden == True:
            self.garden_area = 10
            self.garden_orientation = 'north'
            self.score = 7
        else:
            self.garden_area = 0
            self.garden_orientation = False
            self.score = 0
            # u can return a warning if u want
        # return {'warning': {
        #     'title': ("Warning"),
        #     'message': ('This option is not supported for Authorize.net')}}

    def action_cancel_property(self):
        for record in self:
            if record.state != 'sold':
                record.state = 'cancelled'
            else:
                raise UserError("Sold properties cannot be cancelled. edited")

    def action_sold_property(self):
        for record in self:
            if record.state != 'cancelled':
                record.state = 'sold'
            else:
                raise UserError("Cancelled properties cannot be sold.")

    @api.constrains('score')
    def _check_score(self):
        for record in self:
            if not (1 <= record.score <= 10):
                raise ValidationError("The score must be between 1 and 10.")


    def generate_daily_report(self):
        """Generate and save the daily property report."""
        try:
            report_dir = '/opt/odoo/server/odoo/addons/estate'
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            properties = self.env['estate.property'].sudo().search([('active', '=', False)], limit=100)
            _logger.info(f"Fetched properties: {properties}")
            if not properties:
                _logger.warning("No properties found to generate the report.")
                return

            report_filename = f"daily_property_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            file_path = os.path.join(report_dir, report_filename)
            if not file_path:
                _logger.error("File path is not set correctly.")
                return
            with open(file_path, 'w') as f:
                f.write("Daily Property Report\n")
                f.write("=" * 30 + "\n")
                for property in properties:
                    f.write(f"Property Name: {property.name}\n")
                    f.write(f"Status: {property.postcode}\n")
                    f.write(f"Offer Deadline: {property.bedrooms}\n")
                    f.write("-" * 30 + "\n")
        except Exception as e:
            _logger.info(f"Generated file: {e}")

# logic applied during normal record deletion not when the module is uninstalled
    @api.ondelete(at_uninstall=False)
    def _prevent_deletion(self):
        for record in self:
            if record.state not in ('new', 'cancelled'):
                    # use _ if u need translation: _("You cannot delete a property unless its state is 'New' or 'Cancelled'.")
                raise UserError("You cannot delete a property unless its state is 'New' or 'Cancelled'.")


    def serialize_obj(self, obj):
        """Used to convert date and datetime objects to string"""
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()  # Convert to ISO 8601 string format
        raise TypeError(f"Object of type {obj.__class__.__name__} is not serializable")


    def _generate_cache_key(self, model_name, *args, **kwargs):
        """Generates a unique cache key based on model name, positional arguments, and keyword arguments."""
        key_data = {"model_name": model_name, "args": [], "kwargs": {}}
        for arg in args:
            key_data["args"].append(arg)
        for k, v in sorted(kwargs.items()):  # Sort to ensure consistent order
            key_data["kwargs"][k] = v
        # Use hashlib to create a hash key for the data
        return "odoo::" + hashlib.md5(json.dumps(key_data, sort_keys=True, default=self.serialize_obj).encode()).hexdigest()


    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        """Override the method from the web module, models.py - used when retrieving the records"""
        _logger.info("web_search_read called for estate.property")
        # _logger.info(f"Domain: {domain}, Specification: {specification}, Offset: {offset}, Limit: {limit}, Order: {order}")
        cache_key = self._generate_cache_key(self._name, domain, specification, offset, limit, order, count_limit)
        cached_result = redis_client.get(cache_key)
        if cached_result:
            _logger.info(f"Cache triggered web_search_read for domain: {domain}, specification: {specification}, offset: {offset}, limit: {limit}, oder: {order}, count_limit: {count_limit}")
            return json.loads(cached_result)
        res = super(EstateProperty, self).web_search_read(domain, specification, offset, limit, order, count_limit)
        redis_client.setex(cache_key, 3600, json.dumps(res, default=self.serialize_obj))
        # _logger.info(f"res: {res}")
        _logger.info(f"Cache miss web_search_read for domain: {domain}, specification: {specification}, offset: {offset}, limit: {limit}, oder: {order}, count_limit: {count_limit}")
        return res
    
    @api.model
    def search_count(self, domain,  limit=None):
        """Override the method from the odoo root, server/odoo/models.py - used when counting the nr of records"""
        _logger.info("overriden - search_count called for estate.property")
        cache_key = self._generate_cache_key(self._name, domain, limit) # limit is necessary - it s default to 10k when entering the page but it must change when navigation backward based on the real count number without limit- hash must be different so include all params not just domain
        # Check if the result is already cached
        cached_count = redis_client.get(cache_key)
        if cached_count:
            _logger.info(f"Cache hit search_count for domain: {domain} with count: {cached_count}, int cached_count: {int(cached_count)} hash key: {cache_key}")
            return int(cached_count)
        # If not cached, compute the count and cache it
        count = super(EstateProperty, self).search_count(domain, limit=limit)
        redis_client.setex(cache_key, 3600, count)  # Cache for 1 hour
        _logger.info(f"Cache miss search_count for domain: {domain}. Count computed: {count}, hash key: {cache_key}, limit:{limit}")
        return count


    def create(self, vals):
        _logger.info("overriden - create called for estate.property")
        res = super(EstateProperty, self).create(vals)
        total_nr = redis_client.get("odoo::12e4c58826ec60be7791dffc924bd223") # this is the hash for property count without filters
        _logger.info(f"total nr: {total_nr}")
        redis_client.flushdb()
        if total_nr:
            total_nr = int(total_nr)
            total_nr += 1
            redis_client.setex("odoo::12e4c58826ec60be7791dffc924bd223", 3600, total_nr)  # Cache for 1 hour
        return res


    def write(self, vals):
        _logger.info("overriden - write/edit called for estate.property")
        redis_client.flushdb()
        return super(EstateProperty, self).write(vals)
    

    def unlink(self):
        _logger.info("overriden - unlink called for estate.property")
        res = super(EstateProperty, self).unlink()
        total_nr = redis_client.get("odoo::12e4c58826ec60be7791dffc924bd223") # this is the hash for property count without filters
        redis_client.flushdb()
        if total_nr:
            total_nr = int(total_nr)
            total_nr -= 1
            redis_client.setex("odoo::12e4c58826ec60be7791dffc924bd223", 3600, total_nr)  # Cache for 1 hour
        return res  


    # @api.model
    # def action_insert_properties(self, *args, **kwargs):
    #     start_time = time.time()
    #     property_types = self.env['estate.property.type'].search([])  # Get all property types
    #     property_tags = self.env['estate.property.tag'].search([])  # Get all property tags
    #     property_data = []
    #     batch_size = 1000
    #     for i in range(9000000, 10000001):
    #         letters = random.choices(string.ascii_uppercase, k=2)  # Two random uppercase letters
    #         digits = random.choices(string.digits, k=3)  # Three random digits
    #         last_letters = random.choices(string.ascii_uppercase, k=2)  # Two more random uppercase letters
    #         postcode = f"{''.join(letters)}-{''.join(digits)}-{''.join(last_letters)}"
    #         property_type = property_types[i % len(property_types)]
    #         tags = random.sample(property_tags, 2) if len(property_tags) >= 2 else property_tags
    #
    #         property_data.append(
    #             {
    #                 'name': f'Property {i}',
    #                 'expected_price': 4 + i % 1000000,
    #                 'description': f'This is property {i}',
    #                 'postcode': postcode,
    #                 'living_area': i % 100,
    #                 'facades': i%4,
    #                 'bedrooms': 1 + i%6,
    #                 'garage': True if i % 2 == 0 else False,
    #                 'garden': True if i % 2 != 0 else False,
    #                 'garden_area': 20 if i % 2 != 0 else 0,
    #                 'garden_orientation': 'north' if i % 2 != 0 else None,
    #                 'state': 'new',
    #                 'property_type_id': property_type.id,  # Link property type
    #                 'tag_ids': [(6, 0, [tag.id for tag in tags])],
    #             }
    #         )
    #         if len(property_data) >= batch_size:
    #             self.env['estate.property'].create(property_data)
    #             property_data = []
    #             print(f'{i} records inserted')
    #
    #     if len(property_data) >= batch_size:
    #         self.env['estate.property'].create(property_data)
    #         property_data = []  # Clear the list after batch inser
    #
    #     end_time = time.time()
    #     time_taken = end_time - start_time
    #     print(f'Time taken for inserting 10,000 records: {time_taken} seconds')

