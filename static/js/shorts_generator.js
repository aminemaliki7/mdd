// shorts.js - JavaScript for Shorts Script Generator

function updateSpeedValue() {
    const speedSlider = document.getElementById("speed");
    const speedValue = document.getElementById("speedValue");
    const value = parseFloat(speedSlider.value);
    
    // Format to one decimal place
    speedValue.textContent = value.toFixed(1);
}

function updateDepthValue() {
    const depthSlider = document.getElementById("depth");
    const depthValue = document.getElementById("depthValue");
    const value = parseInt(depthSlider.value);
    
    depthValue.textContent = value;
}

function updateVoices() {
    const languageSelect = document.getElementById("language");
    const voiceSelect = document.getElementById("voice");
    const selectedLanguage = languageSelect.value;
    
    // Hide all options first
    for (let i = 0; i < voiceSelect.options.length; i++) {
        const option = voiceSelect.options[i];
        const voiceLanguage = option.getAttribute("data-language");
        
        if (voiceLanguage === selectedLanguage) {
            option.style.display = "";
        } else {
            option.style.display = "none";
        }
    }
    
    // Select the first visible option
    for (let i = 0; i < voiceSelect.options.length; i++) {
        const option = voiceSelect.options[i];
        if (option.style.display !== "none") {
            voiceSelect.selectedIndex = i;
            break;
        }
    }
}

$(document).ready(function() {
    // Initialize voice options
    updateVoices();
    updateSpeedValue();
    updateDepthValue();
    
    // Set up modal for script editing
    const editScriptModal = new bootstrap.Modal(document.getElementById('editScriptModal'));
    
    $('#shortsForm').on('submit', function(e) {
        e.preventDefault();
        
        // Show loading spinner
        $('#loadingSpinner').show();
        $('#generateBtn').prop('disabled', true);
        
        // Hide previous output if any
        $('#outputContainer').hide();
        $('#voiceOptions').hide();
        
        // Get form data
        const topic = $('#topic').val();
        
        // Send AJAX request
        $.ajax({
            url: '/generate-shorts-script',
            type: 'POST',
            data: {
                topic: topic
            },
            success: function(response) {
                // Hide loading spinner
                $('#loadingSpinner').hide();
                $('#generateBtn').prop('disabled', false);
                
                // Display script
                $('#scriptOutput').text(response.script);
                $('#outputContainer').fadeIn(300);
            },
            error: function(xhr) {
                // Hide loading spinner
                $('#loadingSpinner').hide();
                $('#generateBtn').prop('disabled', false);
                
                // Show error
                let errorMessage = 'An error occurred while generating the script.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                alert(errorMessage);
            }
        });
    });
    
    // Copy to clipboard functionality
    $('#copyBtn').on('click', function() {
        const scriptText = $('#scriptOutput').text();
        navigator.clipboard.writeText(scriptText).then(function() {
            // Change button text temporarily
            const originalText = $(this).html();
            $(this).html('COPIED!');
            
            setTimeout(function() {
                $('#copyBtn').html(originalText);
            }, 2000);
            
        }.bind(this));
    });
    
    // Toggle voice options display
    $('#showOptionsBtn').on('click', function() {
        const optionsVisible = $('#voiceForm').is(':visible');
        if (optionsVisible) {
            $('#voiceForm').hide();
            $(this).text('SHOW VOICE OPTIONS');
        } else {
            $('#voiceForm').show();
            $(this).text('HIDE VOICE OPTIONS');
        }
    });
    
    // Edit script button
    $('#editScriptBtn').on('click', function() {
        const scriptText = $('#scriptOutput').text();
        $('#editScriptText').val(scriptText);
        editScriptModal.show();
    });
    
    // Save edited script
    $('#saveScriptBtn').on('click', function() {
        const editedScript = $('#editScriptText').val();
        $('#scriptOutput').text(editedScript);
        editScriptModal.hide();
    });
    
    // Handle voice form submission
    $('#voiceForm').on('submit', function(e) {
        // Update the hidden text content field with current script
        $('#text-content').val($('#scriptOutput').text());
        
        // Show generating state
        $('#generateVoiceBtn').prop('disabled', true);
        $('#generateVoiceBtn').html('<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> GENERATING...');
        
        // Form will submit normally (no preventDefault)
        // This allows browser to handle redirect properly
    });
});