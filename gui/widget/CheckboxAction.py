from gui.widget.Action import Action



class CheckboxAction(Action):
    def __init__(self, icon=None, text=None, action=None, checked=False, parent=None):
        super().__init__(icon, text, action, parent)

        if action is not None:
            self.toggled.connect(lambda x: checked)

        self.setCheckable(True)
        self.setChecked(checked)
