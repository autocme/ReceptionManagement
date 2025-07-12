# -*- coding: utf-8 -*-
"""
Invitation model for managing building invitations
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class ReceptionInvitation(models.Model):
    """
    Model for managing building invitations
    """
    _name = 'reception.invitation'
    _description = 'Reception Invitation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ri_sequence desc'

    # Fields with prefix 'ri_' (Reception Invitation)
    ri_sequence = fields.Char(
        string='Sequence',
        required=True,
        copy=False,
        readonly=True,
        default='/',
        help='Unique sequence number for the invitation'
    )
    ri_responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        required=True,
        default=lambda self: self.env.user,
        placeholder='Select the responsible user',
        help='The user responsible for this invitation',
        tracking=True
    )
    ri_renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        placeholder='Select the renter for this invitation',
        help='The renter associated with this invitation',
        tracking=True
    )
    ri_state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('attended', 'Attended'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='scheduled', required=True, tracking=True,
       help='Current state of the invitation')
    
    ri_invitation_datetime = fields.Datetime(
        string='Invitation Date & Time',
        required=True,
        placeholder='Set invitation date and time',
        help='Scheduled date and time for the invitation',
        tracking=True
    )
    
    # Guest information fields
    ri_guest_name = fields.Char(
        string='Guest Name',
        required=True,
        placeholder='Enter guest full name',
        help='Full name of the guest'
    )
    ri_guest_email = fields.Char(
        string='Guest Email',
        required=True,
        placeholder='Enter guest email address',
        help='Email address of the guest for notifications'
    )
    ri_guest_phone = fields.Char(
        string='Guest Phone',
        placeholder='Enter guest phone number',
        help='Phone number of the guest'
    )
    
    # Computed fields
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the invitation'
    )

    @api.depends('ri_sequence', 'ri_guest_name')
    def _compute_name(self):
        """
        Compute the display name for the invitation
        """
        for record in self:
            record.name = f"{record.ri_sequence} - {record.ri_guest_name}"

    @api.model
    def create(self, vals):
        """
        Override create to generate sequence and send initial email
        """
        if vals.get('ri_sequence', '/') == '/':
            vals['ri_sequence'] = self.env['ir.sequence'].next_by_code('j_reception.invitation') or '/'
        
        invitation = super(ReceptionInvitation, self).create(vals)
        
        # Send initial email to guest
        invitation._send_invitation_email()
        
        return invitation

    def write(self, vals):
        """
        Override write to handle datetime changes and state changes
        """
        old_datetime = {}
        old_state = {}
        
        # Store old values for comparison
        for record in self:
            old_datetime[record.id] = record.ri_invitation_datetime
            old_state[record.id] = record.ri_state
        
        result = super(ReceptionInvitation, self).write(vals)
        
        # Handle datetime changes
        if 'ri_invitation_datetime' in vals:
            for record in self:
                if old_datetime[record.id] != record.ri_invitation_datetime:
                    record._send_datetime_change_email()
        
        # Handle state changes to attended
        if 'ri_state' in vals:
            for record in self:
                if old_state[record.id] != 'attended' and record.ri_state == 'attended':
                    record._send_attendance_notification()
        
        return result

    def _send_invitation_email(self):
        """
        Send initial invitation email to guest
        """
        self.ensure_one()
        template = self.env.ref('j_reception.email_template_new_invitation', raise_if_not_found=False)
        if template and self.ri_guest_email:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.ri_guest_email,
                }
            )

    def _send_datetime_change_email(self):
        """
        Send email notification when invitation datetime changes
        """
        self.ensure_one()
        template = self.env.ref('j_reception.email_template_datetime_change', raise_if_not_found=False)
        if template and self.ri_guest_email:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.ri_guest_email,
                }
            )

    def _send_attendance_notification(self):
        """
        Send notification to responsible user when guest attends
        """
        self.ensure_one()
        template = self.env.ref('j_reception.email_template_attendance_notification', raise_if_not_found=False)
        if template and self.ri_responsible_user_id.email:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.ri_responsible_user_id.email,
                }
            )

    def action_mark_attended(self):
        """
        Action to mark invitation as attended
        """
        self.ensure_one()
        self.ri_state = 'attended'

    def action_mark_cancelled(self):
        """
        Action to mark invitation as cancelled
        """
        self.ensure_one()
        self.ri_state = 'cancelled'

    @api.constrains('ri_guest_email')
    def _check_email_format(self):
        """
        Validate email format
        """
        for record in self:
            if record.ri_guest_email and '@' not in record.ri_guest_email:
                raise ValidationError(_('Please enter a valid email address.'))

    @api.constrains('ri_invitation_datetime')
    def _check_future_datetime(self):
        """
        Validate that invitation datetime is in the future (for new invitations)
        """
        for record in self:
            if record.ri_state == 'scheduled' and record.ri_invitation_datetime:
                if record.ri_invitation_datetime < fields.Datetime.now():
                    raise ValidationError(_('Invitation date and time must be in the future.'))

    @api.model
    def check_overdue_invitations(self):
        """
        Cron method to check for overdue invitations
        """
        now = fields.Datetime.now()
        overdue_invitations = self.search([
            ('ri_state', '=', 'scheduled'),
            ('ri_invitation_datetime', '<', now)
        ])
        overdue_invitations.write({'ri_state': 'overdue'})
