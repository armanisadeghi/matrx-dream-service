from matrx_connect.socket.schema import register_schema

schema = {
    "definitions": {
        "MIC_CHECK_DEFINITION": {
            "mic_check_message": {
                "REQUIRED": False,
                "DEFAULT": "{{cookiecutter.app_primary_service_name}} Service mic check",
                "VALIDATION": "validate_mic_check_min_length",
                "DATA_TYPE": "string",
                "CONVERSION": "convert_mic_check",
                "REFERENCE": None,
                "COMPONENT": "input",
                "COMPONENT_PROPS": {},
                "DESCRIPTION": "Test message for {{cookiecutter.app_primary_service_name}} service connectivity",
                "ICON_NAME": "Mic"
            }
        },
    },
    "tasks": {
        "{{cookiecutter.app_primary_service_name}}_SERVICE": {
            "MIC_CHECK": {"$ref": "definitions/MIC_CHECK_DEFINITION"}
        }
    }
}

register_schema(schema)
