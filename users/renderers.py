from rest_framework.renderers import JSONRenderer

class CustomRenderer(JSONRenderer):
    """
    Custom JSON renderer to format all success responses into the envelope:
    {
        "status": true,
        "message": "message string",
        "data": <payload>
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        request = renderer_context.get('request') if renderer_context else None
        
        # If response is an error status, let the custom exception handler handle it.
        # Check if the status code is an error (status >= 400)
        if response and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)
            
        status_bool = True
        message = "Success"
        payload = data
        
        # Check if the data is already in our custom envelope format
        if isinstance(data, dict):
            if 'status' in data and 'message' in data:
                return super().render(data, accepted_media_type, renderer_context)
                
            # If the view explicitly returned a message and/or data keys
            if 'message' in data and 'data' in data:
                message = data.get('message')
                payload = data.get('data')
            elif 'message' in data and len(data) == 1:
                message = data.get('message')
                payload = None
            elif 'message' in data:
                message = data.pop('message')
                payload = data
                
        # Customize default success messages based on URL or status code
        if response:
            if response.status_code == 201:
                url_path = request.path if request else ""
                if 'register' in url_path:
                    message = "Users Registered successfully"
                else:
                    message = "Created successfully"
            elif response.status_code == 204:
                message = "Deleted successfully"
                payload = None
                
        envelope = {
            "status": status_bool,
            "message": message,
            "data": payload
        }
        
        return super().render(envelope, accepted_media_type, renderer_context)
