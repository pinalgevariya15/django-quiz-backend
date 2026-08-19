from rest_framework.views import exception_handler

def map_error_message(message_str):
    """
    Translates standard dry/technical DRF validation messages 
    and system status messages into clean, human-friendly English.
    """
    message_str = message_str.strip()
    
    # Auth & Permission mappings
    if "credentials were not provided" in message_str or "not valid for any token type" in message_str:
        return "Authentication token is missing, invalid, or expired. Please log in."
    if "must contain two space-delimited values" in message_str:
        return "Authentication failed. Please format the header value as 'Bearer <token>' (e.g., prefix your token with 'Bearer ')."
    if "do not have permission" in message_str:
        return "Access denied. Only administrators are authorized to perform this action."
    if "not found" in message_str.lower():
        return "The requested resource could not be found."
    if "method" in message_str.lower() and "not allowed" in message_str.lower():
        return "This action is not supported for this endpoint."
        
    # Common validation constraints translations
    translations = {
        "This field may not be blank.": "This field cannot be empty.",
        "This field may not be null.": "This field cannot be empty.",
        "This field is required.": "This field is required.",
        "Enter a valid email address.": "Please enter a valid email address.",
        "User with this email already exists.": "This email is already registered.",
        "A user with that email already exists.": "This email is already registered.",
        "Given token not valid for any token type": "Authentication token is missing, invalid, or expired. Please log in."
    }
    
    if message_str in translations:
        return translations[message_str]
        
    # Formatting length constraints
    if "at least" in message_str and "characters" in message_str:
        return message_str.replace("Ensure this value has at least", "Must be at least")
    if "at most" in message_str and "characters" in message_str:
        return message_str.replace("Ensure this value has at most", "Must be at most")
        
    return message_str


def custom_exception_handler(exc, context):
    """
    Custom exception handler to format all DRF errors into the envelope:
    {
        "status": false,
        "message": "error description",
        "data": null
    }
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_data = response.data
        message = "An error occurred."
        
        if isinstance(error_data, dict):
            if 'detail' in error_data:
                message = map_error_message(str(error_data['detail']))
            else:
                # Extract the first error message dynamically from field validations
                first_key = next(iter(error_data))
                first_val = error_data[first_key]
                if isinstance(first_val, list) and len(first_val) > 0:
                    raw_msg = str(first_val[0])
                elif isinstance(first_val, str):
                    raw_msg = first_val
                else:
                    raw_msg = str(first_val)
                    
                mapped_msg = map_error_message(raw_msg)
                
                # Format field validations cleanly, e.g. "Email: Please enter a valid email address."
                if first_key not in ['non_field_errors', 'detail']:
                    if first_key in ['uidb64', 'token']:
                        message = "The password reset link is invalid or expired."
                    elif first_key == 'code':
                        message = mapped_msg
                    else:
                        field_name = first_key.replace('_', ' ').capitalize()
                        message = f"{field_name}: {mapped_msg}"
                else:
                    message = mapped_msg
                    
        elif isinstance(error_data, list) and len(error_data) > 0:
            message = map_error_message(str(error_data[0]))
        elif isinstance(error_data, str):
            message = map_error_message(error_data)
            
        response.data = {
            "status": False,
            "message": message,
            "data": None
        }
        
    return response
