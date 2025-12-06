/**
 * ================================================================================
 * Photo Upload Utilities
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Utilities for handling photo uploads to Supabase Storage.
 * Includes validation, compression, and upload functionality.
 * ================================================================================
 */

import supabase from './supabaseClient';

// Constants
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];
const BUCKET_NAME = 'wastage-photos';

/**
 * Validate photo file
 */
export const validatePhoto = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        return {
            valid: false,
            error: `File size exceeds 10MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`,
        };
    }

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
        return {
            valid: false,
            error: `Invalid file type. Allowed types: JPG, JPEG, PNG. Current type: ${file.type}`,
        };
    }

    return { valid: true };
};

/**
 * Generate unique filename
 */
export const generateUniqueFilename = (originalFilename: string): string => {
    const timestamp = Date.now();
    const randomString = Math.random().toString(36).substring(2, 15);
    const extension = originalFilename.split('.').pop();
    return `${timestamp}_${randomString}.${extension}`;
};

/**
 * Upload photo to Supabase Storage
 */
export const uploadPhoto = async (
    file: File,
    path: string
): Promise<{ url: string; path: string; error?: string }> => {
    try {
        // Validate file
        const validation = validatePhoto(file);
        if (!validation.valid) {
            return { url: '', path: '', error: validation.error };
        }

        // Generate unique filename
        const filename = generateUniqueFilename(file.name);
        const fullPath = `${path}/${filename}`;

        // Upload to Supabase Storage
        const { error } = await supabase.storage
            .from(BUCKET_NAME)
            .upload(fullPath, file, {
                cacheControl: '3600',
                upsert: false,
            });

        if (error) {
            console.error('Supabase upload error:', error);
            return { url: '', path: '', error: error.message };
        }

        // Get public URL
        const { data: urlData } = supabase.storage
            .from(BUCKET_NAME)
            .getPublicUrl(fullPath);

        return {
            url: urlData.publicUrl,
            path: fullPath,
        };
    } catch (error: any) {
        console.error('Photo upload error:', error);
        return { url: '', path: '', error: error.message || 'Upload failed' };
    }
};

/**
 * Upload multiple photos
 */
export const uploadPhotos = async (
    files: File[],
    basePath: string
): Promise<{ urls: string[]; paths: string[]; errors: string[] }> => {
    const results = await Promise.all(
        files.map((file) => uploadPhoto(file, basePath))
    );

    return {
        urls: results.map((r) => r.url).filter(Boolean),
        paths: results.map((r) => r.path).filter(Boolean),
        errors: results.map((r) => r.error).filter(Boolean) as string[],
    };
};

/**
 * Delete photo from Supabase Storage
 */
export const deletePhoto = async (path: string): Promise<{ success: boolean; error?: string }> => {
    try {
        const { error } = await supabase.storage.from(BUCKET_NAME).remove([path]);

        if (error) {
            console.error('Supabase delete error:', error);
            return { success: false, error: error.message };
        }

        return { success: true };
    } catch (error: any) {
        console.error('Photo delete error:', error);
        return { success: false, error: error.message || 'Delete failed' };
    }
};

/**
 * Compress image if needed (optional, for future enhancement)
 */
export const compressImage = async (file: File, _maxSizeMB: number = 1): Promise<File> => {
    // For now, just return the original file
    // Can implement compression using canvas API if needed
    return file;
};
