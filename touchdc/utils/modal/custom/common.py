"""Common mixins for custom dialogs"""

class OptionMixin:
    def normalize_option(self, op):
        if len(op) == 2:
            label, code = op
            detail = None
        else:
            label, code, detail = op
        return label, code, detail