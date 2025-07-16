# -*- coding: utf-8 -*-
{
    'name': 'J Reception - Building Invitations & Rental Management',
    'version': '15.0.2.0.0',
    'category': 'Real Estate',
    'summary': 'Manage building invitations and rental information with automated notifications',
    'description': """
        J Reception Module
        ==================
        This module provides comprehensive management for building invitations and rental information.
        
        Features:
        - Renter management with company details, communications officer, garage slots, and scheduled payments
        - Invitation management with automated email notifications
        - Role-based access control for renters and administrators
        - Settings configuration for geographical location
        - Automated email notifications for various scenarios
    """,
    'author': 'J Reception Team',
    'depends': ['base', 'mail', 'base_setup'],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence.xml',
        'data/email_templates.xml',
        
        # Views
        'views/building_renter_views.xml',
        'views/reception_invitation_views.xml',
        'views/facilities_views.xml',
        'views/duration_views.xml',
        'views/booking_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}