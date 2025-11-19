/*
================================================================================
Farm Management System - Fix Unconfirmed User Emails
================================================================================
Version: 1.3.2
Created: 2025-11-19

Purpose:
--------
This script fixes users who were created via the admin panel but don't have
their emails confirmed in Supabase Auth. These users cannot receive password
reset emails. This script updates their email confirmation status.

Background:
-----------
Prior to v1.6.0, the create_user function directly inserted into auth.users
without properly setting email confirmation. This prevented Supabase from
sending password reset emails to these users.

Migration Steps:
----------------
This migration needs to be run via Supabase SQL Editor because we need to
update the auth.users table directly, which requires elevated privileges.

IMPORTANT: Run this in your Supabase Dashboard > SQL Editor
================================================================================
*/

-- Update all users in auth.users to have confirmed emails
-- This is safe to run multiple times (idempotent)
-- Note: confirmed_at is a generated column and will be set automatically
UPDATE auth.users
SET
    email_confirmed_at = COALESCE(email_confirmed_at, NOW())
WHERE
    email_confirmed_at IS NULL;

-- Verify the update
SELECT
    id,
    email,
    email_confirmed_at,
    confirmed_at,
    created_at
FROM auth.users
ORDER BY created_at DESC;
