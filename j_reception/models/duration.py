# -*- coding: utf-8 -*-
"""
Duration model for managing booking durations
"""

from odoo import models, fields


class Duration(models.Model):
    """
    Model to manage booking durations
    """
    _name = 'duration'
    _description = 'Duration'
    _order = 'minutes'

    name = fields.Char(
        string='Name',
        required=True,
        placeholder='e.g., 30 Minutes, 1 Hour',
        help='Display name for the duration'
    )
    minutes = fields.Integer(
        string='Minutes',
        required=True,
        placeholder='e.g., 30, 60, 90',
        help='Duration in minutes'
    )