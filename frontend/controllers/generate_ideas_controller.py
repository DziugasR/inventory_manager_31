from PyQt5.QtCore import QObject, QThread, pyqtSignal
from typing import List

from frontend.ui.generate_ideas_dialog import GenerateIdeasDialog
from backend.ChatGPT import ChatGPTService
from backend.generate_ideas_backend import construct_generation_prompt
from backend.type_manager import type_manager
from backend.models import Component


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
    def __init__(self, components: List[Component], openai_model_name: str, api_key: str, parent=None):
        super().__init__()
        self.components = components
        self.view = GenerateIdeasDialog(parent)
        self.chatgpt_service = ChatGPTService(config_model_name=openai_model_name, api_key=api_key)

        self._worker_thread = None
        self._worker = None

        self._connect_signals()
        self._initialize_view()

        if not self.chatgpt_service.is_ready():
            print("Controller Warning: ChatGPT service failed to initialize.")

    def _connect_signals(self):
        self.view.quantity_changed.connect(self._handle_quantity_change)
        self.view.generate_requested.connect(self._handle_generate_request)

    def _initialize_view(self):
        self.view.populate_table(self.components)

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

        current_spinbox_values = self.view.get_spinbox_values()
        print(f"Controller: Current spinbox values from view: {current_spinbox_values}")

        prompt = construct_generation_prompt(
            self.components,
            current_spinbox_values
        )

        if prompt is None:
            print("Controller: No components selected (all quantities are 0).")
            self.view.set_response_text("Please set a quantity greater than 0 for components you want to use.")
            return

        print(f"Controller: Sending prompt (constructed by backend):\n{prompt}")

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