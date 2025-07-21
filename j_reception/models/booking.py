# -*- coding: utf-8 -*-
"""
Booking model for managing facility bookings
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz


class Booking(models.Model):
    """
    Model to manage facility bookings
    """
    _name = 'booking'
    _description = 'Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'booking_datetime desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the booking'
    )
    facility_id = fields.Many2one(
        'facilities',
        string='Facility',
        required=True,
        placeholder='Select the facility',
        help='The facility being booked',
        tracking=True
    )
    duration_id = fields.Many2one(
        'duration',
        string='Duration',
        required=True,
        placeholder='Select the duration',
        help='Duration of the booking',
        tracking=True
    )
    booking_datetime = fields.Datetime(
        string='Booking Date',
        required=True,
        placeholder='Select date and time',
        help='Date and time of the booking',
        tracking=True
    )
    officer_id = fields.Many2one(
        'res.users',
        string='Officer',
        required=True,
        default=lambda self: self.env.user,
        help='The officer responsible for this booking'
    )
    renter_id = fields.Many2one(
        'building.renter',
        string='Tenant',
        required=True,
        readonly=True,
        compute='_compute_renter_id',
        placeholder='Select the tenant',
        help='The tenant making the booking',
        tracking=True
    )

    @api.depends('facility_id', 'booking_datetime', 'renter_id')
    def _compute_name(self):
        """
        Compute the display name for the booking
        """
        for record in self:
            if record.facility_id and record.booking_datetime and record.renter_id:
                # Convert UTC datetime to user's timezone for display
                user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                booking_date_local = pytz.utc.localize(record.booking_datetime).astimezone(user_tz)
                booking_date = booking_date_local.strftime('%Y-%m-%d %H:%M')
                record.name = f"{record.facility_id.name} - {booking_date} ({record.renter_id.name})"
            else:
                record.name = 'Draft Booking'

    @api.depends('officer_id')
    def _compute_renter_id(self):
        """
        Compute the renter_id based on the officer relationship
        """
        for record in self:
            if record.officer_id:
                renter = self.env['building.renter'].search([('officer_id', '=', record.officer_id.id)], limit=1)
                record.renter_id = renter.id if renter else False
            else:
                record.renter_id = False

    @api.constrains('facility_id', 'booking_datetime', 'duration_id')
    def _check_booking_conflict(self):
        """
        Ensure no booking conflicts for the same facility
        """
        for record in self:
            if record.facility_id and record.booking_datetime and record.duration_id:
                # Calculate end time
                end_time = record.booking_datetime + timedelta(minutes=record.duration_id.minutes)
                
                # Check for overlapping bookings
                existing_bookings = self.search([
                    ('facility_id', '=', record.facility_id.id),
                    ('id', '!=', record.id)
                ])
                
                for booking in existing_bookings:
                    existing_end_time = booking.booking_datetime + timedelta(minutes=booking.duration_id.minutes)
                    
                    # Check if times overlap
                    if (record.booking_datetime < existing_end_time and 
                        end_time > booking.booking_datetime):
                        # Convert times to user's timezone for error message
                        user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                        booking_start_local = pytz.utc.localize(booking.booking_datetime).astimezone(user_tz)
                        booking_end_local = pytz.utc.localize(existing_end_time).astimezone(user_tz)
                        
                        raise ValidationError(
                            f"The facility '{record.facility_id.name}' is already booked "
                            f"from {booking_start_local.strftime('%Y-%m-%d %H:%M')} "
                            f"to {booking_end_local.strftime('%Y-%m-%d %H:%M')}. "
                            f"Please choose a different time."
                        )

    @api.constrains('renter_id', 'booking_datetime', 'duration_id')
    def _check_daily_booking_limit(self):
        """
        Check if tenant exceeds daily booking limit
        """
        for record in self:
            if record.renter_id and record.booking_datetime and record.duration_id:
                # Get daily booking limit from settings
                daily_limit = int(self.env['ir.config_parameter'].sudo().get_param('j_reception.daily_booking_limit', 0))
                
                if daily_limit > 0:
                    # Get start and end of the booking day
                    booking_date = record.booking_datetime.date()
                    day_start = datetime.combine(booking_date, datetime.min.time())
                    day_end = datetime.combine(booking_date, datetime.max.time())
                    
                    # Find all bookings for this renter on the same day
                    same_day_bookings = self.search([
                        ('renter_id', '=', record.renter_id.id),
                        ('booking_datetime', '>=', day_start),
                        ('booking_datetime', '<=', day_end),
                        ('id', '!=', record.id)
                    ])
                    
                    # Calculate total minutes booked
                    total_minutes = sum(booking.duration_id.minutes for booking in same_day_bookings)
                    total_minutes += record.duration_id.minutes
                    
                    if total_minutes > daily_limit:
                        raise ValidationError(
                            f"Daily booking limit exceeded. "
                            f"You can only book {daily_limit} minutes per day. "
                            f"Currently booked: {total_minutes - record.duration_id.minutes} minutes. "
                            f"Trying to book: {record.duration_id.minutes} minutes."
                        )

    @api.constrains('booking_datetime')
    def _check_future_datetime(self):
        """
        Ensure booking is in the future
        """
        for record in self:
            if record.booking_datetime:
                # Get current time in UTC (same as what's stored in booking_datetime)
                now_utc = fields.Datetime.now()
                
                # Add a 1 minute buffer to avoid immediate expiration
                if record.booking_datetime <= now_utc:
                    # Convert times to user's timezone for error message
                    user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                    booking_local = pytz.utc.localize(record.booking_datetime).astimezone(user_tz)
                    now_local = pytz.utc.localize(now_utc).astimezone(user_tz)
                    
                    raise ValidationError(
                        f"Booking time must be in the future. "
                        f"Selected time: {booking_local.strftime('%Y-%m-%d %H:%M')} "
                        f"Current time: {now_local.strftime('%Y-%m-%d %H:%M')} "
                        f"Please select a future date and time."
                    )