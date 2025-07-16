# -*- coding: utf-8 -*-
"""
Facilities model for managing building facilities
"""

from odoo import models, fields


class Facilities(models.Model):
    """
    Model to manage building facilities
    """
    _name = 'facilities'
    _description = 'Facilities'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        placeholder='e.g., Conference Room, Gym, Pool',
        help='Name of the facility'
    )