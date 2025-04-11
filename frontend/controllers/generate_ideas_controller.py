from PyQt5.QtCore import QObject, QThread, pyqtSignal

from functools import partial

from frontend.ui.generate_ideas_dialog import GenerateIdeasDialog
from backend.ChatGPT import ChatGPTService

try:
    from frontend.ui.add_component_dialog import AddComponentDialog
except ImportError:
    print("Warning: AddComponentDialog not found, type mapping may be incomplete.")
    AddComponentDialog = None

class ChatGPTWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, chatgpt_service, prompt):
        super().__init__()
        self.chatgpt_service = chatgpt_service
        self.prompt = prompt

    def run(self):
        if self.chatgpt_service:
             result = self.chatgpt_service.get_project_ideas(self.prompt)
             self.finished.emit(result)
        else:
             self.finished.emit("Error: ChatGPT Service not available.")

class GenerateIdeasController(QObject):
    def __init__(self, components, parent=None):
        super().__init__()
        self.components = components
        self.view = GenerateIdeasDialog(parent)
        self.chatgpt_service = ChatGPTService()

        self._type_mapping = self._get_type_mapping()
        self._worker_thread = None
        self._worker = None

        self._connect_signals()
        self._initialize_view()

        if not self.chatgpt_service.is_ready():
             print("Controller Warning: ChatGPT service failed to initialize.")


    def _get_type_mapping(self):
        if AddComponentDialog:
             try:
                 temp_dialog = AddComponentDialog()
                 mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
                 del temp_dialog
                 return mapping
             except Exception as e:
                 print(f"Error getting type mapping from AddComponentDialog: {e}")
        return {}

    def _connect_signals(self):
        self.view.quantity_changed.connect(self._handle_quantity_change)
        self.view.generate_requested.connect(self._handle_generate_request)


    def _initialize_view(self):
        self.view.populate_table(self.components, self._type_mapping)

    def show(self):
        self.view.exec_()

    def _handle_quantity_change(self, part_number, new_quantity):
        pass

    def _handle_generate_request(self):
        print("\nController: Generate request received.")

        if not self.chatgpt_service.is_ready():
             self.view.set_response_text("ChatGPT is not configured. Check API key.")
             return
        if self._worker_thread and self._worker_thread.isRunning():
             print("Controller: Generation already in progress.")
             return

        component_details = []
        current_spinbox_values = self.view.get_spinbox_values()

        print(f"Controller: Current spinbox values from view: {current_spinbox_values}")

        for component in self.components:
             part_number = component.part_number
             project_qty = current_spinbox_values.get(part_number, 0)

             if project_qty > 0:
                 ui_type = self._type_mapping.get(component.component_type, component.component_type)
                 value = component.value or "N/A"
                 component_details.append(f"  - {part_number} (Type: {ui_type}, Value: {value}): Quantity {project_qty}")

        if not component_details:
            print("Controller: No components selected (all quantities are 0).")
            self.view.set_response_text("Please set a quantity greater than 0 for components you want to use.")
            return

        prompt = "You are an experienced electronics engineer/lecturer. Generate specific and practical electronics project ideas utilizing *exactly* the following components and their specified quantities:\n\n"
        prompt += "Available Components:\n"
        prompt += "\n".join(component_details)
        prompt += "\n\nFor each project idea presented, provide the following:\n"
        prompt += "1.  --Project Title:-- A concise name for the project.\n"
        prompt += "2.  --Description:-- A brief explanation of the project's function and purpose.\n"
        prompt += "3.  --Component Usage:-- Clearly explain the *specific role and logical function* of each listed component within that project's design. For example, specify if a resistor is used as a pull-up/pull-down, current-limiting, part of a voltage divider, etc., or how a microcontroller/sensor/transistor is employed.\n\n"
        prompt += "Focus on realistic applications given the components. Ensure your response is technically sound, direct, and strictly avoids unnecessary rambling or excessive adjectives. Present a few distinct ideas."

        print(f"Controller: Sending prompt:\n{prompt}")

        self.view.show_processing(True)

        self._worker_thread = QThread()
        self._worker = ChatGPTWorker(self.chatgpt_service, prompt)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_chatgpt_result)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.finished.connect(self._on_thread_finished)
        self._worker_thread.start()

    def _handle_chatgpt_result(self, result):
        print("Controller: Received result from worker.")
        if self.view:
             self.view.set_response_text(result)
             self.view.show_processing(False)
        else:
             print("Controller: View no longer exists, cannot display result.")


    def _on_thread_finished(self):
        print("Controller: Worker thread finished.")
        self._worker_thread = None
        self._worker = None

    def cleanup(self):
         if self._worker_thread and self._worker_thread.isRunning():
              print("Controller: Requesting worker thread to quit during cleanup...")
              self._worker_thread.quit()
              self._worker_thread.wait(1000)