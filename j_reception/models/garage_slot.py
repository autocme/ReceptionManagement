# -*- coding: utf-8 -*-
"""
Garage Slot model for managing garage slot assignments
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class GarageSlot(models.Model):
    """
    Model to manage garage slots for renters
    """
    _name = 'garage.slot'
    _description = 'Garage Slot'
    _order = 'gs_number'

    gs_renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        ondelete='cascade',
        help='The renter who owns this garage slot'
    )
    gs_description = fields.Char(
        string='Description',
        required=True,
        placeholder='e.g., Underground Level 1, Slot A-15',
        help='Description of the garage slot (e.g., Underground Level 1, Slot A-15)'
    )
    gs_number = fields.Char(
        string='Number',
        required=True,
        placeholder='e.g., A-15',
        help='Garage slot number or identifier'
    )

    @api.constrains('gs_number', 'gs_renter_id')
    def _check_unique_garage_number(self):
        """
        Ensure garage slot numbers are unique within the same renter
        """
        for record in self:
            if record.gs_renter_id:
                existing = self.search([
                    ('gs_number', '=', record.gs_number),
                    ('gs_renter_id', '=', record.gs_renter_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f'Garage slot number "{record.gs_number}" already exists for this renter. '
                        'Please use a different number.'
                    )