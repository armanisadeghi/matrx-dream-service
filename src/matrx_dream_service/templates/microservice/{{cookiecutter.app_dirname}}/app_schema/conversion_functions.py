from matrx_connect.socket.schema import register_conversions


# Define your conversions methods here

def modify_mic_check(value):
    return str(value) + "[Converted by modify_mic_check]"


# Register Conversions

register_conversions({
    "convert_mic_check": modify_mic_check,

    # register more conversions here
})
