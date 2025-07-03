from matrx_connect.socket.schema import register_validations


# Define your validation methods here

def validate_min_mic_check_message(value):
    if not len(value) > 50:
        raise ValueError("Value of of Mic check message must be greater than 50")


# Register Validations

register_validations({
    "validate_mic_check_min_length": validate_min_mic_check_message,

    # register more validations here
})
