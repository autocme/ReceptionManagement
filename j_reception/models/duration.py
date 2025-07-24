# -*- coding: utf-8 -*-
"""
Duration model for managing booking durations
"""

from odoo import models, fields, api, _


class Duration(models.Model):
    """
    Model to manage booking durations
    """
    _name = 'duration'
    _description = 'Duration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'minutes'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=False,
        help='Display name for the duration'
    )
    minutes = fields.Integer(
        string='Minutes',
        required=True,
        placeholder='e.g., 30, 60, 90',
        help='Duration in minutes',
        tracking=True
    )

    # @api.depends('minutes')
    def _compute_name(self):
        """
        Compute the display name based on minutes
        """
        for record in self:
            if record.minutes:
                if record.minutes < 60:
                    record.name = f"{record.minutes} {_('min')}"
                elif record.minutes == 60:
                    record.name = f"1 {_('hour')}"
                elif record.minutes % 60 == 0:
                    hours = record.minutes // 60
                    record.name = f"{hours} {_('hours')}"
                else:
                    hours = record.minutes // 60
                    mins = record.minutes % 60
                    record.name = f"{hours} {_('hour')} {mins} {_('min')}"
            else:
                record.name = _("New Duration")