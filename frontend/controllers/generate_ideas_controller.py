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

        self.project_quantities = {}
        self._type_mapping = self._get_type_mapping()
        self._worker_thread = None
        self._worker = None # Keep reference to worker too

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
        self.view.checkbox_state_changed.connect(self._handle_checkbox_change)
        self.view.quantity_changed.connect(self._handle_quantity_change)
        self.view.generate_requested.connect(self._handle_generate_request)
         # Optional: Connect view finished signal for cleanup
        # self.view.finished.connect(self.cleanup)


    def _initialize_view(self):
        self.view.populate_table(self.components, self._type_mapping)
        self.view.clear_quantity_controls()

    def show(self):
        self.view.exec_()

    def _handle_checkbox_change(self, row_index, is_checked):
        if 0 <= row_index < len(self.components):
            component = self.components[row_index]
            part_number = component.part_number
            if is_checked:
                available_qty = component.quantity
                ui_type = self._type_mapping.get(component.component_type, component.component_type)
                value_str = component.value or ""
                initial_proj_qty = self.project_quantities.get(part_number, 1)
                initial_proj_qty = min(initial_proj_qty, available_qty)
                initial_proj_qty = max(1, initial_proj_qty) if available_qty > 0 else 0
                self.project_quantities[part_number] = initial_proj_qty
                self.view.add_quantity_control(
                    part_number, ui_type, value_str, available_qty, initial_proj_qty
                )
            else:
                if part_number in self.project_quantities:
                    del self.project_quantities[part_number]
                self.view.remove_quantity_control(part_number)

    def _handle_quantity_change(self, part_number, new_quantity):
        if part_number in self.project_quantities:
            self.project_quantities[part_number] = new_quantity

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

        for component in self.components:
             part_number = component.part_number
             if part_number in current_spinbox_values:
                 project_qty = current_spinbox_values[part_number]
                 ui_type = self._type_mapping.get(component.component_type, component.component_type)
                 value = component.value or "N/A"
                 component_details.append(f"  - {part_number} (Type: {ui_type}, Value: {value}): Quantity {project_qty}")

        if not component_details:
            print("Controller: No components selected for generation.")
            self.view.set_response_text("Please select components and adjust quantities first.")
            return

        prompt = "Generate electronics project ideas based on the following available components and their exact selected quantities:\n\n"
        prompt += "\n".join(component_details)
        prompt += "\n\nPlease provide a few specific project ideas with brief descriptions."
        prompt += "\n\nWrite like an experienced engineer/lecturer, who knows what they are talking about. Strictly avoid unnecessary rambling and too much adjectives."

        self.view.show_processing(True)

        # *** Revised Thread Setup and Connections ***
        self._worker_thread = QThread()
        self._worker = ChatGPTWorker(self.chatgpt_service, prompt)
        self._worker.moveToThread(self._worker_thread)

        # Connections:
        # 1. When thread starts, run the worker's task
        self._worker_thread.started.connect(self._worker.run)
        # 2. When worker emits finished signal, handle the result
        self._worker.finished.connect(self._handle_chatgpt_result)
        # 3. After handling result OR worker finishes, tell the thread event loop to quit
        self._worker.finished.connect(self._worker_thread.quit)
        # 4. When the thread *actually* finishes, schedule worker and thread for deletion
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        # 5. Clean up controller references when thread finishes
        self._worker_thread.finished.connect(self._on_thread_finished)


        self._worker_thread.start()

    def _handle_chatgpt_result(self, result):
        print("Controller: Received result from worker.")
        # Check if view still exists (might have been closed)
        if self.view:
             self.view.set_response_text(result)
             self.view.show_processing(False)
        else:
             print("Controller: View no longer exists, cannot display result.")


    def _on_thread_finished(self):
        """Slot called when the thread finishes to clean up references."""
        print("Controller: Worker thread finished.")
        self._worker_thread = None
        self._worker = None

    def cleanup(self):
         # Call this if the dialog can be closed externally while processing
         if self._worker_thread and self._worker_thread.isRunning():
              print("Controller: Requesting worker thread to quit during cleanup...")
              self._worker_thread.quit()
              self._worker_thread.wait(1000) # Give it a moment
         # Clean up view if necessary, though Dialog usually handles itself
         # if self.view:
         #    self.view.deleteLater()
         #    self.view = None