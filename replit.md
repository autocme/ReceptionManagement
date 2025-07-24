# J Reception - Building Invitations & Rental Management

## Overview

J Reception is an Odoo-based module designed to manage building invitations and rental information. The system provides comprehensive management for building renters, garage slots, scheduled payments, and automated invitation handling with email notifications. It's built as an Odoo 15 module with role-based access control and automated workflow management.

## User Preferences

Preferred communication style: Simple, everyday language.
Default timezone: Asia/Riyadh (when user timezone not available)

## Recent Changes

### Advanced Permissions and Security (July 24, 2025)
- Changed renter field in booking from computed to default value for better performance
- Implemented role-based visibility for renter field (visible to admins always, tenants only for owned bookings)
- Added write method override in booking to restrict tenant edits to owned records only
- Created new financial security group for scheduled payments access
- Fixed duration name translations to work dynamically with user's language context

### Kanban Views and Auto-assignment (July 21, 2025)
- Added kanban view as default for booking model with consistent styling matching other modules
- Implemented auto-assignment of tenant in booking based on current user's officer relationship
- Made duration terms ("min", "hour", "hours") translatable using Odoo translation system
- Added complete chatter functionality to all booking models (booking, facilities, duration)
- Fixed security rules to properly allow tenants to modify their own bookings

### Booking System Implementation (July 15, 2025)
- Added new booking system with facilities, duration, and booking models
- Implemented facility booking with calendar view as default
- Added time conflict detection and daily booking limits
- Enhanced configuration settings with building image and booking limits
- Updated email templates to include building image
- Added comprehensive security rules for booking system
- Fixed officer field relationship from res.partner to res.users
- Improved constraint handling for administrators vs tenants

### Draft State Implementation (July 14, 2025)
- Added 'draft' state as default for invitations with 'confirm' button workflow
- Moved email sending to state change trigger (draft → scheduled)
- Enhanced kanban views for both tenants and invitations with improved styling
- Integrated currency field to scheduled payments model
- Updated payment reminder email template with currency symbols
- Implemented officer field domain filtering
- Changed terminology from "Renter" to "Tenant" in all user-facing views
- Added enhanced kanban views with inline styling for better visual presentation

## System Architecture

### Framework and Platform
- **Base Framework**: Odoo 15 ERP system
- **Architecture Pattern**: Model-View-Controller (MVC) following Odoo's framework
- **Language**: Python 3
- **Module Type**: Odoo addon module with full application capabilities

### Core Dependencies
- **Odoo Base Modules**: `base`, `mail`, `base_setup`
- **Communication**: Built-in Odoo mail system for notifications
- **Security**: Odoo's built-in security framework

## Key Components

### 1. Data Models
- **Building Renter** (`building.renter`): Central model managing renter information
- **Reception Invitation** (`reception.invitation`): Handles invitation scheduling and tracking
- **Garage Slot** (`garage.slot`): Manages garage slot assignments
- **Scheduled Payment** (`scheduled.payment`): Tracks payment schedules
- **Facilities** (`facilities`): Manages building facilities available for booking
- **Duration** (`duration`): Manages booking duration options (30 min, 60 min, etc.)
- **Booking** (`booking`): Handles facility bookings with conflict detection
- **Configuration Settings** (`res.config.settings`): System configuration management

### 2. Business Logic Features
- **Mail Integration**: Inherits from `mail.thread` and `mail.activity.mixin` for communication tracking
- **Sequence Management**: Automated sequence generation for invitations
- **State Management**: Invitation states (scheduled, attended, overdue, cancelled)
- **Role-Based Access**: Security groups for renters and administrators

### 3. User Interface Components
- **Menu Structure**: Organized navigation for different user roles
- **Form Views**: Comprehensive forms for data entry and management
- **List Views**: Efficient data browsing and filtering
- **Configuration Views**: Settings management interface

## Data Flow

### 1. Renter Management
- Renter creation with company association
- Assignment of communications officer
- Garage slot allocation
- Payment schedule setup

### 2. Invitation Process
- Invitation creation with automatic sequence generation
- State tracking throughout invitation lifecycle
- Automated email notifications based on states
- Integration with geographical location settings

### 3. Communication Flow
- Email templates for various notification scenarios
- Mail threading for conversation tracking
- Activity management for follow-ups

## External Dependencies

### 1. Odoo Core Dependencies
- **Base Module**: Core Odoo functionality
- **Mail Module**: Email and communication features
- **Base Setup**: Configuration management

### 2. Email System
- Uses Odoo's built-in email infrastructure
- Custom email templates for notifications
- Geographical location URL integration for invitations

### 3. Security Framework
- Leverages Odoo's security model
- Custom security groups and access rules
- Model-level and record-level security

## Deployment Strategy

### 1. Module Installation
- Standard Odoo module installation process
- Automatic data loading (sequences, email templates)
- Security configuration deployment

### 2. Configuration Requirements
- Email server setup for notifications
- Geographical location URL configuration
- User group assignments

### 3. Data Migration
- Sequence initialization
- Email template deployment
- Security rules activation

### 4. Integration Points
- Partner/Company integration with existing Odoo contacts
- User management integration
- Email system integration

## Technical Architecture Decisions

### 1. Model Design
- **Problem**: Complex relationship management between renters, companies, and facilities
- **Solution**: Normalized data model with proper foreign key relationships
- **Benefits**: Data integrity, scalability, and maintainability

### 2. Communication System
- **Problem**: Need for automated notifications and activity tracking
- **Solution**: Integration with Odoo's mail system using inheritance
- **Benefits**: Consistent UI, built-in functionality, and reliable delivery

### 3. Security Model
- **Problem**: Different access levels for renters vs administrators
- **Solution**: Role-based access control using Odoo security groups
- **Benefits**: Granular permissions, secure data access, and scalability

### 4. State Management
- **Problem**: Tracking invitation lifecycle and status
- **Solution**: State field with defined transitions and automated updates
- **Benefits**: Clear workflow, automated processing, and audit trail