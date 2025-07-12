# -*- coding: utf-8 -*-
"""
Renter model for managing building rental information
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class GarageSlot(models.Model):
    """
    Model to manage garage slots for renters
    """
    _name = 'garage.slot'
    _description = 'Garage Slot'
    _order = 'gs_number'

    # Fields with prefix 'gs_' (Garage Slot)
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

    @api.constrains('gs_number')
    def _check_unique_garage_number(self):
        """
        Ensure garage slot numbers are unique within the same renter
        """
        for record in self:
            existing = self.search([
                ('gs_renter_id', '=', record.gs_renter_id.id),
                ('gs_number', '=', record.gs_number),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Garage slot number must be unique for each renter.'))


class ScheduledPayment(models.Model):
    """
    Model to manage scheduled payments for renters
    """
    _name = 'scheduled.payment'
    _description = 'Scheduled Payment'
    _order = 'sp_due_date'

    # Fields with prefix 'sp_' (Scheduled Payment)
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

    @api.constrains('sp_amount')
    def _check_amount_positive(self):
        """
        Ensure payment amount is positive
        """
        for record in self:
            if record.sp_amount <= 0:
                raise ValidationError(_('Payment amount must be positive.'))


class BuildingRenter(models.Model):
    """
    Main model for managing renter information
    """
    _name = 'building.renter'
    _description = 'Building Renter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Fields with prefix 'br_' (Building Renter)
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the renter'
    )
    br_company_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True,
        domain=[('is_company', '=', True)],
        placeholder='Select the company associated with this renter',
        help='The company associated with this renter',
        tracking=True
    )
    br_communications_officer_id = fields.Many2one(
        'res.partner',
        string='Communications Officer',
        required=True,
        placeholder='Select the communications officer',
        help='The person responsible for communications with this renter',
        tracking=True
    )
    br_garage_slot_ids = fields.One2many(
        'garage.slot',
        'gs_renter_id',
        string='Garage Slots',
        help='List of garage slots assigned to this renter'
    )
    br_scheduled_payment_ids = fields.One2many(
        'scheduled.payment',
        'sp_renter_id',
        string='Scheduled Payments',
        help='List of scheduled payments for this renter'
    )
    br_invitation_count = fields.Integer(
        string='Invitation Count',
        compute='_compute_invitation_count',
        help='Number of invitations created for this renter'
    )

    @api.depends('br_company_id')
    def _compute_name(self):
        """
        Compute the display name based on company
        """
        for record in self:
            record.name = record.br_company_id.name if record.br_company_id else 'New Renter'

    @api.depends('br_company_id')
    def _compute_invitation_count(self):
        """
        Compute the number of invitations for this renter
        """
        for record in self:
            record.br_invitation_count = self.env['reception.invitation'].search_count([
                ('ri_renter_id', '=', record.id)
            ])

    def action_view_invitations(self):
        """
        Action to view invitations for this renter
        """
        self.ensure_one()
        action = self.env.ref('j_reception.action_reception_invitation_tree').read()[0]
        action['domain'] = [('ri_renter_id', '=', self.id)]
        action['context'] = {
            'default_ri_renter_id': self.id,
            'search_default_ri_renter_id': self.id,
        }
        return action

    @api.model
    def check_due_payments(self):
        """
        Cron method to check for due payments and send notifications
        """
        today = fields.Date.today()
        due_payments = self.env['scheduled.payment'].search([
            ('sp_due_date', '<=', today),
            ('sp_is_notified', '=', False)
        ])
        
        for payment in due_payments:
            # Send email to communications officer
            template = self.env.ref('j_reception.email_template_payment_due')
            if template and payment.sp_renter_id.br_communications_officer_id.email:
                template.send_mail(
                    payment.id,
                    force_send=True,
                    email_values={
                        'email_to': payment.sp_renter_id.br_communications_officer_id.email,
                    }
                )
                payment.sp_is_notified = True
