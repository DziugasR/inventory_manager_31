from PyQt5.QtCore import QObject
from functools import partial

# Import UI, Backend, and potentially other necessary modules
from frontend.ui.generate_ideas_dialog import GenerateIdeasDialog
from backend.generate_ideas_backend import GenerateIdeasBackend
# Assuming AddComponentDialog is needed for mapping, adjust import path
try:
    from frontend.ui.add_component_dialog import AddComponentDialog
except ImportError:
    # Handle case where AddComponentDialog might not be available
    # Provide a dummy mapping or raise an error if essential
    print("Warning: AddComponentDialog not found, type mapping may be incomplete.")
    AddComponentDialog = None


class GenerateIdeasController(QObject):
    def __init__(self, components, parent=None):
        super().__init__()
        self.components = components # Original list of component objects
        self.view = GenerateIdeasDialog(parent)
        self.backend = GenerateIdeasBackend()

        # State managed by controller
        self.project_quantities = {} # {part_number: project_quantity}

        # Pre-calculate type mapping if possible
        self._type_mapping = self._get_type_mapping()

        self._connect_signals()
        self._initialize_view()

    def _get_type_mapping(self):
        """Helper to get the backend-to-UI type name mapping."""
        if AddComponentDialog:
             try:
                 temp_dialog = AddComponentDialog()
                 mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
                 del temp_dialog
                 return mapping
             except Exception as e:
                 print(f"Error getting type mapping from AddComponentDialog: {e}")
        return {} # Return empty if dialog not found or error

    def _connect_signals(self):
        """Connect signals from the view to controller slots."""
        self.view.checkbox_state_changed.connect(self._handle_checkbox_change)
        self.view.quantity_changed.connect(self._handle_quantity_change)
        self.view.generate_requested.connect(self._handle_generate_request)

    def _initialize_view(self):
        """Populate the view with initial data."""
        self.view.populate_table(self.components, self._type_mapping)
        # Initially clear controls (view might hold old state if reused)
        self.view.clear_quantity_controls()

    def show(self):
        """Shows the dialog modally."""
        self.view.exec_()

    # --- Slots for UI Signals ---

    def _handle_checkbox_change(self, row_index, is_checked):
        """Handles checkbox state changes from the view."""
        if 0 <= row_index < len(self.components):
            component = self.components[row_index]
            part_number = component.part_number

            if is_checked:
                # Add quantity control
                available_qty = component.quantity
                ui_type = self._type_mapping.get(component.component_type, component.component_type)
                value_str = component.value or ""

                # Determine initial quantity for the spinbox
                initial_proj_qty = self.project_quantities.get(part_number, 1) # Default to 1 if new
                initial_proj_qty = min(initial_proj_qty, available_qty)
                initial_proj_qty = max(1, initial_proj_qty) if available_qty > 0 else 0

                # Update controller state first
                self.project_quantities[part_number] = initial_proj_qty

                # Tell the view to add the UI element
                self.view.add_quantity_control(
                    part_number, ui_type, value_str, available_qty, initial_proj_qty
                )
            else:
                # Remove quantity control
                if part_number in self.project_quantities:
                    del self.project_quantities[part_number] # Update controller state

                # Tell the view to remove the UI element
                self.view.remove_quantity_control(part_number)

    def _handle_quantity_change(self, part_number, new_quantity):
        """Handles quantity spinbox changes from the view."""
        if part_number in self.project_quantities: # Only update if it's supposed to be tracked
            self.project_quantities[part_number] = new_quantity
            # print(f"Controller updated project quantity for {part_number}: {new_quantity}") # Debug

    def _handle_generate_request(self):
        """Handles the generate button click from the view."""
        print("\nController: Generate request received.") # Debug message

        # Prepare data for the backend
        data_for_backend = []
        # Get current spinbox values to ensure consistency, fallback to stored dict
        current_spinbox_values = self.view.get_spinbox_values()

        for component in self.components:
             part_number = component.part_number
             # Check if it's currently selected via the spinbox values reported by UI
             if part_number in current_spinbox_values:
                 project_qty = current_spinbox_values[part_number]
                 ui_type = self._type_mapping.get(component.component_type, component.component_type)
                 value = component.value or "N/A"

                 data_for_backend.append({
                     "part_number": part_number,
                     "type": ui_type,
                     "value": value,
                     "project_quantity": project_qty,
                     # Add other component details if backend needs them
                     "original_object": component # Pass original if needed
                 })

        if not data_for_backend:
            print("Controller: No components selected for generation.")
            # Optionally show a message in the UI via a new view method
            return

        # Call the backend to process
        self.backend.process_ideas(data_for_backend)

        # Future: Handle results from backend and update view if necessary
        # For now, backend just prints. Maybe close dialog?
        # self.view.accept() # or self.view.close()