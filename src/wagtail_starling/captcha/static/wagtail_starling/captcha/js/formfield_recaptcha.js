/**
 * Show/hide reCAPTCHA v3 score threshold field based on field type selection
 * This script runs in Wagtail admin for FormField inline panels
 */

(function() {
    'use strict';

    function toggleScoreThresholdField(fieldTypeSelect) {
        console.log('[reCAPTCHA] toggleScoreThresholdField called for:', fieldTypeSelect);

        // Find the parent container (various possible structures)
        const container = fieldTypeSelect.closest('[data-inline-panel-child]') ||
                         fieldTypeSelect.closest('[data-contentpath]') ||
                         fieldTypeSelect.closest('.inline-child') ||
                         fieldTypeSelect.closest('.object') ||
                         fieldTypeSelect.closest('li') ||
                         fieldTypeSelect.closest('[id*="inline"]');

        if (!container) {
            console.warn('[reCAPTCHA] Could not find container for field type select');
            return;
        }

        console.log('[reCAPTCHA] Found container:', container);

        // Find the score threshold field within the same container
        // Try multiple selectors for the INPUT element
        const scoreThresholdInput = container.querySelector('[id$="recaptcha_score_threshold"]') ||
                                   container.querySelector('[name$="recaptcha_score_threshold"]') ||
                                   container.querySelector('input[type="number"][name*="recaptcha"]');

        if (!scoreThresholdInput) {
            console.log('[reCAPTCHA] Score threshold input not found in this container');
            return;
        }

        console.log('[reCAPTCHA] Found score threshold input:', scoreThresholdInput);

        // Find the parent field wrapper that contains BOTH label and input
        // This is usually the outermost container for the entire field
        let fieldWrapper = scoreThresholdInput.closest('[data-contentpath]') ||
                          scoreThresholdInput.closest('[data-field]') ||
                          scoreThresholdInput.closest('.w-field') ||
                          scoreThresholdInput.closest('.field') ||
                          scoreThresholdInput.closest('li[data-contentpath]');

        // If still not found, look for parent with both label and input
        if (!fieldWrapper || !fieldWrapper.querySelector('label')) {
            fieldWrapper = scoreThresholdInput.parentElement;
            let attempts = 0;
            while (fieldWrapper && fieldWrapper !== container && attempts < 10) {
                // Check if this element contains a label
                const hasLabel = fieldWrapper.querySelector('label');
                if (hasLabel) {
                    break;
                }
                fieldWrapper = fieldWrapper.parentElement;
                attempts++;
            }
        }

        console.log('[reCAPTCHA] Found field wrapper:', fieldWrapper);

        // Show/hide based on field type
        const selectedType = fieldTypeSelect.value;
        console.log('[reCAPTCHA] Selected field type:', selectedType);

        if (selectedType === 'recaptcha_v3') {
            console.log('[reCAPTCHA] Showing score threshold field (label + input)');
            if (fieldWrapper) {
                fieldWrapper.style.display = '';
                fieldWrapper.style.visibility = 'visible';
            }
        } else {
            console.log('[reCAPTCHA] Hiding score threshold field (label + input)');
            if (fieldWrapper) {
                fieldWrapper.style.display = 'none';
                fieldWrapper.style.visibility = 'hidden';
            }
        }
    }

    function initializeFormFields() {
        console.log('[reCAPTCHA] Initializing form fields...');

        // Find all field type selects in the page
        const fieldTypeSelects = document.querySelectorAll('[id$="field_type"], [name$="field_type"], select[name*="field_type"]');

        console.log('[reCAPTCHA] Found', fieldTypeSelects.length, 'field type selects');

        fieldTypeSelects.forEach(function(select) {
            console.log('[reCAPTCHA] Processing select:', select);

            // Set initial state
            toggleScoreThresholdField(select);

            // Remove existing listener if any to prevent duplicates
            select.removeEventListener('change', handleFieldTypeChange);

            // Listen for changes
            select.addEventListener('change', handleFieldTypeChange);
        });
    }

    function handleFieldTypeChange() {
        console.log('[reCAPTCHA] Field type changed');
        toggleScoreThresholdField(this);
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[reCAPTCHA] DOMContentLoaded event');
            initializeFormFields();
        });
    } else {
        console.log('[reCAPTCHA] Document already loaded');
        initializeFormFields();
    }

    // Re-initialize when new inline panels are added (Wagtail dynamic forms)
    document.addEventListener('wagtail:init', function() {
        console.log('[reCAPTCHA] wagtail:init event');
        setTimeout(initializeFormFields, 100);
    });

    // For older Wagtail versions or additional compatibility
    if (window.$ && $.fn.on) {
        $(document).on('formset:added', function() {
            console.log('[reCAPTCHA] formset:added event');
            setTimeout(initializeFormFields, 200);
        });
    }

    // Also listen to Wagtail's specific events
    document.addEventListener('wagtail:panel-init', function() {
        console.log('[reCAPTCHA] wagtail:panel-init event');
        setTimeout(initializeFormFields, 100);
    });

    console.log('[reCAPTCHA] Script loaded and initialized');
})();
