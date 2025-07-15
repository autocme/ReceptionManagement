# -*- coding: utf-8 -*-
"""
Reception Invitation model for managing building invitations
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re


class ReceptionInvitation(models.Model):
    """
    Model for managing building invitations
    """
    _name = 'reception.invitation'
    _description = 'Reception Invitation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ri_sequence desc'

    ri_sequence = fields.Char(
        string='Sequence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique sequence number for the invitation'
    )
    ri_officer_id = fields.Many2one(
        'res.users',
        string='Officer',
        required=True,
        default=lambda self: self.env.user,
        domain=lambda self: [('id', 'in', self.env['building.renter'].search([]).mapped('br_officer_id.id'))],
        placeholder='Select the officer',
        help='The user responsible for this invitation',
        tracking=True
    )
    ri_renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        readonly=True,
        help='The renter associated with this invitation',
        tracking=True
    )
    ri_subject = fields.Char(
        string='Subject',
        required=True,
        placeholder='Enter invitation subject',
        help='Subject of the invitation'
    )
    ri_state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('attended', 'Attended'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True, copy=False,
       help='Current state of the invitation')
    ri_invitation_datetime = fields.Datetime(
        string='Date',
        required=True,
        placeholder='Set invitation date and time',
        help='Scheduled date and time for the invitation',
        tracking=True
    )
    ri_guest_partner_id = fields.Many2one(
        'res.partner',
        string='Guest',
        required=True,
        domain=lambda self: [('create_uid', '=', self.env.user.id)],
        placeholder='Select the guest',
        help='The guest partner for this invitation'
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the invitation'
    )

    @api.depends('ri_sequence', 'ri_guest_partner_id', 'ri_renter_id')
    def _compute_name(self):
        """
        Compute the display name for the invitation
        """
        for record in self:
            if record.ri_sequence != '/':
                renter_name = record.ri_renter_id.name if record.ri_renter_id else 'Unknown'
                guest_name = record.ri_guest_partner_id.name if record.ri_guest_partner_id else 'Unknown'
                record.name = f"{record.ri_sequence} - {guest_name} ({renter_name})"
            else:
                record.name = 'Draft Invitation'

    @api.onchange('ri_officer_id')
    def _onchange_officer_id(self):
        """
        Auto-populate renter when officer changes
        """
        if self.ri_officer_id:
            renter = self.env['building.renter'].search([
                ('br_officer_id', '=', self.ri_officer_id.id)
            ], limit=1)
            if renter:
                self.ri_renter_id = renter.id
            if not renter:
                self.ri_renter_id = False


    @api.model
    def default_get(self, fields_list):
        """
        Set default values for renter based on current user
        """
        res = super(ReceptionInvitation, self).default_get(fields_list)
        if 'ri_renter_id' in fields_list:
            current_user = self.env.user
            
            # For administrators, don't set default renter - let them choose officer first
            if current_user.has_group('j_reception.group_j_reception_admin'):
                # If context has default_ri_officer_id, use it to find renter
                if self.env.context.get('default_ri_officer_id'):
                    officer_id = self.env.context['default_ri_officer_id']
                    renter = self.env['building.renter'].search([
                        ('br_officer_id', '=', officer_id)
                    ], limit=1)
                    if renter:
                        res['ri_renter_id'] = renter.id
                # If admin has no default officer in context, try to find their own renter
                else:
                    renter = self.env['building.renter'].search([
                        ('br_officer_id', '=', current_user.id)
                    ], limit=1)
                    if renter:
                        res['ri_renter_id'] = renter.id
            else:
                # For non-admin users, set default renter based on current user
                renter = self.env['building.renter'].search([
                    ('br_officer_id', '=', current_user.id)
                ], limit=1)
                if renter:
                    res['ri_renter_id'] = renter.id
        return res

    @api.constrains('ri_officer_id', 'ri_renter_id')
    def _check_officer_renter_relationship(self):
        """
        Ensure officer can only create invitations for their assigned renter
        (except for Reception Administrators who can create for any renter)
        """
        for record in self:
            if record.ri_officer_id and record.ri_renter_id:
                # Skip constraint check for Reception Administrators
                if self.env.user.has_group('j_reception.group_j_reception_admin'):
                    continue
                
                if record.ri_renter_id.br_officer_id.id != record.ri_officer_id.id:
                    raise ValidationError(
                        f"You can only create invitations for renters you are assigned to. "
                        f"You are not the officer for '{record.ri_renter_id.name}'."
                    )

    @api.model
    def create(self, vals):
        """
        Override create to generate sequence
        """
        if vals.get('ri_sequence', _('New')) == _('New'):
            vals['ri_sequence'] = self.env['ir.sequence'].next_by_code('reception.invitation') or _('New')
        
        invitation = super(ReceptionInvitation, self).create(vals)
        
        return invitation

    def write(self, vals):
        """
        Override write to handle datetime changes and state changes
        """
        datetime_changed = False
        state_changed = False
        
        for record in self:
            if 'ri_invitation_datetime' in vals and vals['ri_invitation_datetime'] != record.ri_invitation_datetime:
                datetime_changed = True
            if 'ri_state' in vals and vals['ri_state'] != record.ri_state:
                state_changed = True
        
        result = super(ReceptionInvitation, self).write(vals)
        
        # Send datetime change notification
        if datetime_changed:
            for record in self:
                record._send_datetime_change_email()
        
        # Send initial invitation email when state changes to scheduled
        if state_changed and vals.get('ri_state') == 'scheduled':
            for record in self:
                record._send_invitation_email()
        
        # Send attendance notification
        if state_changed and vals.get('ri_state') == 'attended':
            for record in self:
                record._send_attendance_notification()
        
        return result

    def _send_invitation_email(self):
        """
        Send initial invitation email to guest
        """
        template = self.env.ref('j_reception.email_template_new_invitation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_datetime_change_email(self):
        """
        Send email notification when invitation datetime changes
        """
        template = self.env.ref('j_reception.email_template_datetime_change', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_attendance_notification(self):
        """
        Send notification to responsible user when guest attends
        """
        template = self.env.ref('j_reception.email_template_attendance_notification', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_confirm(self):
        """
        Action to confirm invitation (draft -> scheduled)
        """
        self.write({'ri_state': 'scheduled'})

    def action_mark_attended(self):
        """
        Action to mark invitation as attended
        """
        self.write({'ri_state': 'attended'})

    def action_mark_cancelled(self):
        """
        Action to mark invitation as cancelled
        """
        self.write({'ri_state': 'cancelled'})



    @api.constrains('ri_invitation_datetime')
    def _check_future_datetime(self):
        """
        Validate that invitation datetime is in the future (for new invitations)
        """
        for record in self:
            if record.ri_invitation_datetime and record.ri_state in ['draft', 'scheduled']:
                if record.ri_invitation_datetime <= fields.Datetime.now():
                    raise ValidationError('Invitation date and time must be in the future.')

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