# -*- coding: utf-8 -*-
"""
Scheduled Payment model for managing payment schedules
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ScheduledPayment(models.Model):
    """
    Model to manage scheduled payments for renters
    """
    _name = 'scheduled.payment'
    _description = 'Scheduled Payment'
    _order = 'sp_due_date'

    sp_renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        ondelete='cascade',
        help='The renter associated with this scheduled payment'
    )
    sp_description = fields.Char(
        string='Description',
        required=True,
        placeholder='e.g., Monthly Rent, Maintenance Fee',
        help='Description of the payment (e.g., Monthly Rent, Maintenance Fee)'
    )
    sp_amount = fields.Float(
        string='Amount',
        required=True,
        placeholder='0.00',
        help='Payment amount'
    )
    sp_due_date = fields.Date(
        string='Due Date',
        required=True,
        help='Payment due date'
    )
    sp_is_notified = fields.Boolean(
        string='Notification Sent',
        default=False,
        help='Whether notification email has been sent for this payment'
    )
    sp_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Currency for this payment'
    )

    @api.constrains('sp_amount')
    def _check_amount_positive(self):
        """
        Ensure payment amount is positive
        """
        for record in self:
            if record.sp_amount <= 0:
                raise ValidationError('Payment amount must be positive.')