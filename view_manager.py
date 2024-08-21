from oled import OLED

class ViewManager:
    
    def __init__(self):
        self.view_stack = []

    def btn_enter_pressed(self):
        if self.view_stack:
            next_view = self.view_stack[len(self.view_stack)-1].close(enter=True)
            if next_view:
                self.view_stack.append(next_view)

    def btn_cancel_pressed(self):
        if self.view_stack:
            if len(self.view_stack) > 1:
                self.view_stack.pop().close(enter=False)

    def btn_left_pressed(self):
        if self.view_stack:
            self.view_stack[len(self.view_stack)-1].previous_view()

    def btn_right_pressed(self):
        if self.view_stack:
           self.view_stack[len(self.view_stack)-1].next_view()

    def oled_update(self):
        if self.view_stack:
            self.view_stack[len(self.view_stack)-1].update()
    
    def open_view(self,view):
        self.view_stack.append(view)
