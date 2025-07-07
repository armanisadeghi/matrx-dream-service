class TemplateMerger:
    def __init__(self):
        self.merge_config = self._default_config()

    def _default_config(self):
        return {
            "databases": self.replace,
            "env": self.deep_merge,
            "settings": self.deep_merge,
            "dependencies": self.extend,
            "schema": self.replace,
            "files": self.extend,
            "post_create_scripts": self.extend,
        }

    def merge(self, sys: dict, user: dict) -> dict:
        result = {}
        all_fields = set(sys.keys()) | set(user.keys())

        for field in all_fields:
            system_val = sys.get(field)
            user_val = user.get(field)
            merge_func = self.merge_config.get(field, self.replace)
            result[field] = merge_func(system_val, user_val)

        return result

    def replace(self, sys, user):
        """Replace default value with user value, if not null else default value"""
        return user if user is not None else sys

    def extend(self, sys, user):
        """Add to existing values"""
        return (sys or []) + (user or [])

    def deep_merge(self, sys, user):
        if not isinstance(sys, dict):
            sys = {}
        if not isinstance(user, dict):
            return sys

        result = sys.copy()

        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
