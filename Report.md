# Coursework Report: Electronics Inventory Manager

## 1. Introduction

**Goal and Topic:**

The primary goal of this coursework was to design, develop, and implement a functional desktop application demonstrating Object-Oriented Programming (OOP), software design patterns, and core Python development practices. The chosen topic is an **Electronics Inventory Manager**, a tool designed to help electronics hobbyists, students, or small labs keep track of their electronic components.

**Application Description:**

The Electronics Inventory Manager is a graphical user interface (GUI) application built using Python with the PyQt5 framework. It allows users to:

*   Maintain a persistent inventory of electronic components (resistors, capacitors, ICs, etc.) stored in an SQLite database.
*   Add new components with details like part number, type, value, quantity, and optional web links for purchasing and datasheets.
*   Remove quantities of existing components, automatically deleting them when the quantity reaches zero.
*   View the entire inventory in a sortable table.
*   Select components and request project ideas based on the selected parts and quantities, utilizing the OpenAI API (specifically gpt-4o-mini model) for idea generation.
*   Export the current inventory data to a Excel (.xlsx) file.
*   Import inventory data from a structured Excel file, overwriting the existing inventory.

**How to Run (Portable EXE Version):**

1.  **Extract Archive:** Extract the contents of the provided `.zip` file (e.g., `Electronics_component_manager_Džiugas_Ragauskas_EF_24_2.zip`) to a folder on your computer.
2.  **Navigate to Folder:** Open the extracted folder (e.g., `Electronics component manager_Džiugas_Ragauskas_EF_24_2`).
3.  **Configure API Key:**
    *   Open the `.env` file within this folder using a text editor.
    *   Replace the placeholder after `OPENAI_API_KEY=` with your personal OpenAI API key.
    *   Save the `.env` file. (Idea generation requires this key).
4.  **Optional Configuration:** You can edit `config.ini` in the same folder to change the OpenAI model or database path, if needed.
5.  **Run Application:** Double-click the main executable file (e.g., `Electronics Component Manager.exe`) inside the folder.


**How to Run the Program in a IDE:**

1.  **Prerequisites:** Ensure Python 3.10 and `pip` are installed.
2.  **Clone Repository:** Obtain the project code (e.g., `git clone <https://github.com/DziugasR/inventory_manager_31>`).
3.  **Navigate to Directory:** Open a terminal or command prompt and change into the project's root directory.
4.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    .\venv\Scripts\activate   # On Windows
    ```
5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
6.  **Configure API Key:**
    *   Create a file named `.env` in the project's root directory.
    *   Add the following line to the `.env` file, replacing `<your_actual_openai_api_key>` with your key:
        ```
        OPENAI_API_KEY=<your_actual_openai_api_key>
        ```
7.  **Initialize Database:** The application uses SQLAlchemy, which will create the `inventory.db` SQLite database file automatically on the first run if it doesn't exist.
8.  **Run Application:**
    ```bash
    python main.py
    ```

**How to Use the Program:**

1.  **Launch:** Run the application using IDE or portable EXE. The main window will appear, displaying the inventory table (at first will be empty).
2.  **Viewing Data:** In the table colums shows component details. Click column headers to sort alphabetically or numerically (Ascending/Descending). Links in the "Purchase Link" and "Datasheet" columns can be clicked to open in a web browser.
3.  **Adding Components:** Click the "Add Component" button. A dialog appears. Select the component type, fill in the part number (primary specification),value ,quantity, and optional links. Click "OK" to add the component to database.
4.  **Removing Components:**
    *   Select components using the checkboxes in the last column.
    *   Click the "Remove Selected" button.
    *   A dialog will iterate for every selected component, asking how many units to remove. Enter the quantity and click "OK".
    *   Components are deleted from inventory if quantity reaches zero.
5.  **Generating Project Ideas:**
    *   Select components using the checkboxes.
    *   Click the "Generate Ideas" button.
    *   A dialog appears showing selected components. Adjust the quantity to use for the project idea using the spin boxes.
    *   Click the "Generate Ideas" button within this dialog. The application will contact the OpenAI API.
    *   Generated ideas will appear in the text box on the right.
6.  **Exporting Data:** Click the "Export to Excel" button. Choose a location and filename to save the inventory as an `.xlsx` file.
7.  **Importing Data:** Click the "Import from Excel" button. **Warning:** This will **OVERWRITE** the current inventory. Select an `.xlsx` file with the correct column structure ("Part Number", "Type", "Value", "Quantity" are mandatory). The inventory will be reloaded from the file.

## 2. Body/Analysis

This section shows how the application implements the coursework requirements, supported by code examples.

**Functional Requirements Implementation:**

*   **Component Management (Add/Remove/View):**
    *   Viewing is handled by `main_window.py` displaying data fetched by `main_controller.py` using `backend.inventory.get_all_components()` method.
    *   Adding is initiated by `AddComponentDialog` class, data processed by `main_controller._add_new_component` method, which calls `backend.inventory.add_component()` method.
    *   Removing uses `main_controller.handle_remove_components` which calls `backend.inventory.remove_component_quantity()` for each selected item after user input.
    *   Database interaction uses SQLAlchemy models defined in `backend.models.py` and session management in `backend.database.py`.


*   **Data Persistence:** Achieved using an SQLite database (`inventory.db`) managed via SQLAlchemy ORM (`backend.database.py`, `backend.models.py`).
*   *ORM, like SQLAlchemy, is a tool that lets you interact with relational database tables using object-oriented code instead of writing raw SQL queries.*


*   **File Import/Export:** Implemented in `backend.import_export_logic.py` using the `pandas` and `openpyxl` libraries.
    *   *Pandas - Python library used for data manipulation and analysis, offering data structures like DataFrames to easily work with tabular data.* 
    *   *Openpyxl - Python library designed for reading from and writing to Excel 2010+ .xlsx / .xlsm files.*
    *   `export_to_excel` class: Fetches all components, creates a Pandas DataFrame, and writes it to a formatted `.xlsx` file.
    *   `import_from_excel` class: Reads an `.xlsx` file into a DataFrame, validates columns, *deletes existing inventory*, creates new component objects using `ComponentFactory` class, and commits them to the database.


*   **Project Idea Generation:**
    *   **Initiation:** User selects components `frontend.ui.main_window.py`; `MainController` Class in `frontend.controllers.main_controller.py` fetches data, reads model config, and launches `GenerateIdeasController` Class.
    *   **User Input:** `GenerateIdeasDialog` Class in `frontend.ui.generate_ideas_dialog.py` shows parts; user sets project quantities.
    *   **Prompt Creation:** `construct_generation_prompt` method in `backend.generate_ideas_backend.py` creates the API prompt using component data and quantities.
    *   **API Request:** `ChatGPTService` Class in `backend.ChatGPT.py` (using configured model) sends prompt via `ChatGPTWorker` Class in `frontend.controllers.generate_ideas_controller.py` running in a `QThread`.
    *   **Display Results:** `GenerateIdeasController` Class receives response/error and updates the `GenerateIdeasDialog` Class.

# Object-Oriented Programming Pillars Implementation

This section details how the four fundamental pillars of Object-Oriented Programming (OOP) – Inheritance, Abstraction, Polymorphism, and Encapsulation – have been implemented within the Electronics Inventory Manager application.

---

## 1. Inheritance

*   **What it is:** Inheritance is an OOP principle where a new class (the *child* or *subclass*) acquires properties and behaviors from an existing class (the *parent* or *superclass*). This creates an "is-a" relationship (e.g., a `DatabaseError` *is a* `ComponentError`) and promotes code reuse by allowing subclasses to build upon existing functionality.

*   **How it Works (Example 1: Defining Exceptions in `backend/exceptions.py`):**
    1.  A base custom exception `ComponentError` is defined, inheriting directly from Python's built-in `Exception` class.
    2.  More specific exception types, such as `InvalidInputError`, `DatabaseError`, `StockError`, etc., are defined to inherit from `ComponentError`.
    3.  Each subclass calls `super().__init__(self.message)` within its own `__init__` method. This executes the initialization logic of the parent class (`ComponentError` and subsequently `Exception`), ensuring the standard exception setup is performed.

    ```python
    # backend/exceptions.py (Definition)
    class ComponentError(Exception):
        # Base class for component-related exceptions
        def __init__(self, message="Component error occurred"):
            self.message = message
            super().__init__(self.message) # Calls Exception.__init__

    class InvalidInputError(ComponentError):
        # Raised when user input is invalid
        def __init__(self, message="Invalid input provided"):
            self.message = message
            # Calls ComponentError.__init__
            super().__init__(self.message)

    class DatabaseError(ComponentError):
        # Raised for database-related errors
        def __init__(self, message="Database operation failed"):
            self.message = message
            super().__init__(self.message)
    # ... other specific exceptions follow the same pattern ...
    ```

*   **How it Works (Example 2: Using Inherited Exceptions in `frontend/controllers/main_controller.py`):**
    1.  Code that calls potentially problematic backend functions (like adding or removing components) is wrapped in `try...except` blocks.
    2.  Specific `except` clauses can catch the individual custom exception types (`InvalidQuantityError`, `ComponentNotFoundError`, `StockError`, `DatabaseError`, etc.) defined in `exceptions.py`.
    3.  Because all these custom exceptions inherit from `ComponentError`, you *could* also use a single `except ComponentError` block to catch *any* of these specific errors if generic handling was desired, demonstrating code reuse in error handling. However, catching specific errors often allows for more tailored user feedback.
    4.  This structured approach allows the program to handle different error conditions gracefully and provide informative messages to the user via the `_show_message` helper.

    ```python
    # frontend/controllers/main_controller.py (Usage - Simplified from handle_remove_components)
    # ... inside handle_remove_components method ...
    for component_id in component_ids:
        # ... logic to get component details and quantity_to_remove ...
        try:
            # Attempt the backend operation that might fail
            remove_component_quantity(component_id, quantity_to_remove)
            messages.append(f"- {part_number_display}: Removed {quantity_to_remove} units.")
            success_count += 1
        # Catch specific errors inheriting from ComponentError
        except InvalidQuantityError as e:
            messages.append(f"- {part_number_display}: Removal error - {e}")
            failure_count += 1
        except ComponentNotFoundError as e:
            messages.append(f"- {part_number_display}: Removal error - {e}")
            failure_count += 1
        except StockError as e:
            messages.append(f"- {part_number_display}: Removal error - {e}")
            failure_count += 1
        except DatabaseError as e: # Another specific error
            messages.append(f"- {part_number_display}: Removal error - {e}")
            failure_count += 1
        except Exception as e: # Catch any other unexpected errors
             messages.append(f"- {part_number_display}: Unexpected removal error - {e}")
             failure_count += 1
    # ... after loop ...
    # Show summary message to user via self._show_message(...)
    ```

*   **How it Works (Example 3: PyQt Framework Integration):**
    1.  GUI elements inherit from PyQt5 base classes (e.g., `InventoryUI(QMainWindow)`).
    2.  Controllers and workers inherit from `QObject` for signals/slots.
    3.  `super().__init__(...)` initializes the base PyQt functionality.

    ```python
    # frontend/ui/main_window.py
    from PyQt5.QtWidgets import QMainWindow # ... other imports
    class InventoryUI(QMainWindow): # Inherits from QMainWindow
        def __init__(self):
            super().__init__() # Calls QMainWindow.__init__
            # ...

    # frontend/controllers/main_controller.py
    from PyQt5.QtCore import QObject
    class MainController(QObject): # Inherits from QObject
        def __init__(self, view: InventoryUI, openai_model: str):
            super().__init__() # Calls QObject.__init__
            # ...
    ```

*   **Purpose:**
    *   **Code Reuse:** Defines common structure (exceptions, UI base) once in parent classes.
    *   **Organization:** Creates logical hierarchies (specific errors are types of `ComponentError`; UI elements are specialized Qt objects).
    *   **Robust Error Handling:** Allows specific catching of different error types while also providing a common base (`ComponentError`) for more general handling if needed. Improves code clarity and user feedback during errors.
    *   **Framework Integration:** Enables use of PyQt features (windows, signals/slots).
    *   **Extensibility:** Easy to add new specific exceptions or UI elements.

*  **Used Pyqt frawork in project**
   * Window/Dialog Features: From QMainWindow, QDialog (standard controls, show/hide, modality).
   * Signals/Slots: From QObject (for event-based communication).
   * Widget Capabilities: From QWidget (rendering, layout management, basic input).
   * Threading Support: From QObject (moving tasks like API calls to QThread).
   * Object Lifecycle: From QObject (parent-child relationships, memory management).

## 2. Abstraction

*   **What it is:** Abstraction focuses on hiding complex implementation details while exposing only the essential features or interfaces of an object. It emphasizes *what* an object does rather than *how* it does it. This is often achieved using abstract classes and methods, defining a contract that subclasses must fulfill.

*   **How it Works (`backend/models.py`):**
    1.  The `Component` class serves as a base for all specific component types within the data model.
    2.  It defines a method signature `get_specifications(self)` decorated with `@abstractmethod` from Python's `abc` module (implicitly, as it's defined in the base `Component` and implemented in the dynamic subclasses).
    3.  This decorator signifies that `Component` itself does not provide an implementation for this method, but it mandates that any concrete (non-abstract) subclass *must* provide its own implementation.
    4.  The actual implementation is provided dynamically when specific component classes like `Resistor`, `Capacitor`, etc., are created by the `create_component_class` function. This function assigns a concrete `generated_get_specifications` function (tailored by `spec_format_string`) to the `get_specifications` attribute of the newly created subclass.

    ```python
    # backend/models.py
    from abc import abstractmethod # Used conceptually here

    class Component(Base):
        # ... common attributes and __mapper_args__ ...

        @abstractmethod # Declares an interface requirement
        def get_specifications(self):
            # No implementation here in the base class
            pass

    # --- Dynamic creation provides the concrete implementation ---
    def create_component_class(class_name, polymorphic_id, spec_format_string):
        # This inner function BECOMES the implementation in the subclass
        def generated_get_specifications(self):
            # ... logic using spec_format_string to format output ...  
            unit = ""
            parts = spec_format_string.split()

            if len(parts) > 1:
                unit = " " + parts[-1] # Assumes last word is the unit

            return f"{spec_format_string}: {self.value}{unit}" # Example formatting

        class_attributes = {
            "__mapper_args__": {"polymorphic_identity": polymorphic_id},
            # Assigns the concrete function to the name required by the abstract method
            "get_specifications": generated_get_specifications
        }
        new_class = type(class_name, (Component,), class_attributes)
        return new_class

    Resistor = create_component_class(
        class_name="Resistor",
        polymorphic_id="resistor",
        spec_format_string="Resistance Ω"
    )

    Capacitor = create_component_class(
        class_name="Capacitor",
        polymorphic_id="capacitor",
        spec_format_string="Capacitance F"
    ) # Resistor and Capacitor now HAS a get_specifications method
    ```

*   **How it Was Used (Purpose):**
    *   **Interface Definition:** Defines a standard way (`get_specifications`) to retrieve key technical details for any component, regardless of its specific type.
    *   **Decoupling:** Code that needs to display component specifications can interact with any `Component` object through this standard method without needing to know the specific type (Resistor, LED, etc.) or how its specific value is formatted.
    *   **Enforcement:** Ensures that every component type developed (via `create_component_class`) will have the capability to provide its specifications, maintaining consistency across the model.
    *   **Code Generation:** Using `create_component_class` abstracts away the repetitive boilerplate code needed for defining each similar subclass, making the model definition more concise.
---

## 3. Polymorphism

*   **What it is:** Polymorphism, meaning "many forms," allows objects of different classes to be treated as objects of a common superclass. It enables invoking the same method on different objects, resulting in different behaviors specific to each object's actual type.

*   **How it Works (Example: SQLAlchemy Object Loading in `models.py` / `inventory.py`):**
    1.  The `Component` model in `models.py` is configured for Single Table Inheritance using SQLAlchemy's `polymorphic_on` and `polymorphic_identity` arguments within `__mapper_args__`. This tells SQLAlchemy that the `component_type` column in the `components` table determines the specific subclass of `Component` each row represents (e.g., "resistor", "capacitor").
    2.  Specific subclasses (like `Resistor`, `Capacitor`) are defined (dynamically via `create_component_class`) each with their unique `polymorphic_identity`.
    3.  When data is queried from the database using the *base* class, SQLAlchemy automatically handles the polymorphism. For example, in `backend/inventory.py`, the `get_all_components` function queries for `Component`.
    4.  During the loading process, SQLAlchemy inspects the value in the `component_type` column for each row retrieved. Based on this value, it instantiates an object of the corresponding *specific subclass* (`Resistor`, `Capacitor`, `LED`, etc.).
    5.  Therefore, the single query `session.query(Component)` results in a list containing objects of *various specific component types*, all treated initially as `Component` objects but retaining their specialized nature.

    ```python
    # backend/models.py (Polymorphism Setup)
    class Component(Base):
        # ... columns ...
        component_type = Column(String, nullable=False) # Discriminator column
        # ...
        __mapper_args__ = {
            "polymorphic_on": component_type, # Which column decides the type
            "polymorphic_identity": "component" # Identity of the base class
        }
        # ... abstract method ...

    # Dynamically created class with its specific identity
    Resistor = create_component_class(
        class_name="Resistor",
        polymorphic_id="resistor", # Matches value in component_type column
        spec_format_string="Resistance Ω"
    )
    Capacitor = create_component_class(
        class_name="Capacitor",
        polymorphic_id="capacitor", # Matches value in component_type column
        spec_format_string="Capacitance F"
    )
    # ... other types ...

    # backend/inventory.py (Polymorphism in Action during Query)
    from .models import Component
    from .database import get_session

    def get_all_components() -> list[Component]:
        session = get_session()
        try:
            # Querying for the BASE type Component...
            components_list = session.query(Component).order_by(Component.part_number).all()
            # ... but components_list will contain Resistor, Capacitor, etc. objects
            # instantiated by SQLAlchemy based on the 'component_type' column value.
            return components_list
        # ... error handling ...
        finally:
            session.close()
    ```

*   **How it Was Used (Purpose):**
    *   **Simplified Data Handling:** Allows interaction with the database using the general `Component` type, while automatically receiving correctly specialized objects (`Resistor`, `Capacitor`, etc.) without manual type checking after retrieval.
    *   **Uniform Treatment:** Enables code to process collections of components generically. For example, iterating through the list returned by `get_all_components` and calling `comp.get_specifications()` on each element will execute the correct implementation for each specific component type.
    *   **Flexibility:** Makes the system easier to extend with new component types without changing the core data retrieval logic. As long as a new type is registered with its `polymorphic_identity`, SQLAlchemy will handle its instantiation correctly.

---

## 4. Encapsulation

*   **What it is:** Encapsulation involves bundling data (attributes) and the methods that operate on that data within a single unit (a class). It also includes controlling access to an object's internal state. Python uses conventions and name mangling rather than strict access modifiers like some other languages:
    *   **Public:** Attributes and methods accessible from anywhere (no leading underscore). These form the class's intended interface.
    *   **Protected (Convention):** Attributes and methods prefixed with a single underscore (`_`). This *signals* they are intended for internal use within the class or subclasses, but access is *not* technically restricted. It's a hint to developers.
    *   **Private (Name Mangling):** Attributes and methods prefixed with a double underscore (`__`). Python automatically changes the name to `_ClassName__attributeName`, making it harder (but not impossible) to access directly from outside, strongly discouraging external use.

*   **How it Works (Example 1: `backend/ChatGPT.py` - Using Public, Private):**
    1.  The `ChatGPTService` class bundles data like `api_key`, `model_name` (which are **public** attributes, accessible directly) and the internal `openai.OpenAI` client instance `self.client` (also technically public but managed internally).
    2.  It provides **public** methods like `is_ready()` and `get_project_ideas()` as the intended interface.
    3.  It uses a **private** (name-mangled) helper method `__execute_chat_completion`. The double underscore `__` makes Python rename it internally (to `_ChatGPTService__execute_chat_completion`), strongly indicating it's for internal use only and hiding the direct API call details.

    ```python
    # backend/ChatGPT.py
    import openai
    import os
    from typing import Optional # Added import

    class ChatGPTService:
        def __init__(self, config_model_name: Optional[str] = None):
            # Public attributes, though often set internally
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.model_name = config_model_name if config_model_name else 'gpt-4o-mini'
            # Internal state, technically public but intended for class use
            self.client = None
            if self.api_key:
                try:
                    self.client = openai.OpenAI(api_key=self.api_key)
                except Exception as e:
                    print(f"Error initializing OpenAI client: {e}")
                    self.client = None

        # Public interface method
        def is_ready(self):
            # Accesses internal state (self.client)
            # ... (implementation) ...
            return self.client is not None

        # Public interface method
        def get_project_ideas(self, prompt):
            if not self.is_ready():
                return "Error: ..."
            try:
                # Calls the internal ("private") helper method
                response = self.__execute_chat_completion( # Invoked using mangled name internally
                    model=self.model_name,
                    messages=[ {"role": "user", "content": prompt} ],
                    temperature=0.7,
                    max_tokens=1000
                )
                # ... process response ...
                if response.choices:
                    return response.choices[0].message.content.strip()
                else:
                    return "Error: No response choices received from ChatGPT."
            # ... error handling ...
            except Exception as e: # Simplified error handling for snippet
                 print(f"Error during API call: {e}")
                 return f"Error: {e}"


        # "Private" internal helper method (uses name mangling __)
        def __execute_chat_completion(self, model, messages, temperature, max_tokens):
            # Directly uses the internal self.client
            # Name becomes _ChatGPTService__execute_chat_completion externally
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
    ```

*   **How it Works (Example 2: `frontend/ui/main_window.py` - Using Public, Protected Convention):**
    1.  The `InventoryUI` class manages internal state using **protected** convention attributes like `_checkboxes` and `_row_id_map`. The underscore signals these are internal details.
    2.  It has **public** signals like `add_component_requested` which form part of its communication interface.
    3.  It uses **protected** convention helper methods for internal setup and event handling, like `_init_ui`, `_connect_signals`, `_on_remove_clicked`, `_update_buttons_state_on_checkbox`. These structure the class internally but aren't meant for direct calls from unrelated code.
    4.  It also provides **public** methods like `get_checked_ids()` or `display_data()` which *are* intended to be called externally (e.g., by the controller).

    ```python
    # frontend/ui/main_window.py
    import uuid # Added import
    from PyQt5.QtWidgets import QMainWindow, QWidget, QTableWidget, QCheckBox #... other imports
    from PyQt5.QtCore import pyqtSignal, QUrl, Qt # Added imports

    class InventoryUI(QMainWindow):
        # Public signals - part of the interface
        add_component_requested = pyqtSignal()
        remove_components_requested = pyqtSignal(list)
        link_clicked = pyqtSignal(QUrl)
        # ... other signals ...

        def __init__(self):
            super().__init__()
            # "Protected" attributes (internal state, by convention _)
            self._checkboxes = []
            self._row_id_map = {}
            # Calls "protected" helper methods
            self._init_ui()
            self._connect_signals()

        # "Protected" internal setup method (convention _)
        def _init_ui(self):
            # ... setup widgets like self.add_button (public)...
            self.table = QTableWidget() # Public attribute holding a widget

        # "Protected" internal signal connection method (convention _)
        def _connect_signals(self):
            # Connect public widget signal to public signal
            self.add_button.clicked.connect(self.add_component_requested)
            # Connect public widget signal to "protected" internal handler
            self.remove_button.clicked.connect(self._on_remove_clicked)
            # Connect table signal (public) to "protected" internal handler
            self.table.cellClicked.connect(self._handle_cell_click)

        # "Protected" internal event handler (convention _)
        def _on_remove_clicked(self):
            ids_to_remove = self.get_checked_ids() # Calls public helper
            if ids_to_remove:
                self.remove_components_requested.emit(ids_to_remove) # Emits public signal

        # "Protected" internal event handler (convention _)
        def _handle_cell_click(self, row, column):
             # ... logic ...
             # Emits public signal link_clicked if relevant
                 self.link_clicked.emit(link_data)

        # Public helper method - part of intended interface
        def get_checked_ids(self) -> list[uuid.UUID]:
            # Accesses "protected" internal state (_checkboxes, _row_id_map)
            checked_ids = []
            # ... logic ...
            return checked_ids

        # "Protected" internal helper method (convention _)
        def _update_buttons_state_on_checkbox(self):
            # ... logic using get_checked_ids() ...
             pass # Added pass

        # Public method - part of intended interface
        def display_data(self, components: list):
             # ... complex logic using self.table (public), _row_id_map (protected) ...
             pass # Added pass
    ```

*   **How it Was Used (Purpose):**
    *   **Organization:** Groups data and related operations within classes.
    *   **Interface Definition:** **Public** methods and attributes define how other parts of the code should interact with an object.
    *   **Data Hiding/Intent Signaling:** **Protected** (`_`) convention signals that attributes/methods are internal implementation details, discouraging external reliance. **Private** (`__`) name mangling strongly discourages external access to highly internal implementation details.
    *   **Simplified Interface:** Hides complex internal logic behind simpler public methods.
    *   **Maintainability:** Changes to protected/private internals are less likely to break external code if the public interface remains stable.
    * **Clarity:** Conventions (`_`, `__`) clearly communicate the intended scope and usage of class members.
    * **Limited Use of `__private`:** While name mangling (`__`) was used in `ChatGPTService` for a highly internal helper, the **protected** convention (`_`) was generally preferred elsewhere in the project (e.g., in UI and controller classes). This aligns with common Python practice, where the `_` prefix is usually sufficient to signal internal use without the potential complexities name mangling can introduce, such as making debugging or subclass overrides slightly more difficult. Strict privacy wasn't deemed necessary for most internal methods or attributes in this application's context.

# Design Patterns Implementation

Beyond the fundamental OOP pillars, specific design patterns have been employed to address common software design problems, enhance code structure, maintainability, and flexibility. This section details the implementation of key design patterns within the Electronics Inventory Manager application.

---

## 1. Factory Method Pattern

*   **What it is:** The Factory Method pattern defines an interface (or in this case, a static method within a class) for creating objects but lets subclasses (or the method itself based on input) decide which class to instantiate. It promotes loose coupling by separating the client code (which requests an object) from the concrete class creation logic.

*   **How it Works (`backend/component_factory.py`):**
    1.  A `ComponentFactory` class is defined, primarily acting as a holder for the creation logic.
    2.  It contains a private dictionary `_component_types` that maps string identifiers (like "resistor", "capacitor") to the actual *class types* (e.g., `Resistor`, `Capacitor`) which were dynamically created in `models.py`.
    3.  A static method `create_component` acts as the factory method. It takes a `component_type` string and arbitrary keyword arguments (`**kwargs`).
    4.  Inside `create_component`, it looks up the `component_type` string (converted to lowercase) in the `_component_types` dictionary.
    5.  If found, it retrieves the corresponding class type (e.g., `Resistor`) and instantiates it using the provided `kwargs` (e.g., `Resistor(**kwargs)`). This instantiation call effectively creates the specific component object.
    6.  If the type string is not found, it raises a `ValueError`.

    ```python
    # backend/component_factory.py (Excerpt)
    from backend.models import ( # Imports the actual component classes
        Resistor, Capacitor, Inductor, Diode, Transistor, LED, Relay,
        # ... other component classes ...
    )

    class ComponentFactory:
        # Maps string identifiers to the concrete class types
        _component_types = {
            "resistor": Resistor,
            "capacitor": Capacitor,
            "inductor": Inductor,
            "diode": Diode,
            # ... other mappings ...
        }

        @staticmethod # The Factory Method itself
        def create_component(component_type, **kwargs):
            """Creates a component instance based on the type string."""
            component_type = component_type.lower()
            if component_type in ComponentFactory._component_types:
                # Looks up the class and instantiates it
                component_class = ComponentFactory._component_types[component_type]
                return component_class(**kwargs) # e.g., Resistor(part_number=..., ...)
            else:
                raise ValueError(f"Unknown component type: {component_type}")

    # Example Usage (e.g., in backend/inventory.py or backend/import_export_logic.py)
    # part_data = {'component_type': 'resistor', 'part_number': 'R101', 'value': '1k', ...}
    # new_component = ComponentFactory.create_component(**part_data)
    # # new_component is now an instance of the Resistor class
    ```

*   **How it Was Used (Purpose):**
    *   **Decoupling:** Code needing to create components (like the import logic or potentially the add component dialog handling) doesn't need to know the specific class names (`Resistor`, `Capacitor`). It only needs the type string and the `ComponentFactory`.
    *   **Centralized Creation Logic:** The mapping and instantiation logic is centralized in one place (`ComponentFactory`), making it easier to manage and extend. Adding a new component type involves updating `models.py` and adding one entry to the `_component_types` dictionary.
    *   **Flexibility:** Simplifies the process of creating different component types based on dynamic input (like data read from an Excel file or user input).

---

## 2. Model-View-Controller (MVC) / Model-View-Presenter (MVP) Variant

*   **What it is:** MVC and its variants (like MVP, MVVM) are architectural patterns used to separate application logic into three interconnected components:
    *   **Model:** Manages the application's data, logic, and rules (the "backend").
    *   **View:** Represents the user interface (UI) and displays data from the Model.
    *   **Controller/Presenter:** Acts as an intermediary, handling user input from the View, interacting with the Model, and updating the View. This pattern promotes separation of concerns, making the application more modular, testable, and maintainable.

*   **How it Works (Overall Structure):**
    1.  **Model:** Resides primarily in the `backend` directory.
        *   `backend/models.py`: Defines the data structures (Component classes) and their mapping to the database using SQLAlchemy.
        *   `backend/database.py`: Manages database connection and sessions.
        *   `backend/inventory.py`: Contains the core business logic for manipulating components (add, remove, query).
        *   `backend/exceptions.py`: Defines custom exceptions related to data and logic rules.
        *   `backend/import_export_logic.py`, `backend/ChatGPT.py`: Handle specific backend tasks.
    2.  **View:** Resides in the `frontend/ui` directory.
        *   `frontend/ui/main_window.py`: Defines the main application window (`InventoryUI`) with its widgets (table, buttons).
        *   `frontend/ui/add_component_dialog.py`, `frontend/ui/generate_ideas_dialog.py`: Define the dialog windows.
        *   These classes are responsible *only* for displaying information and emitting signals when user interactions occur (button clicks, cell clicks). They generally contain minimal application logic.
    3.  **Controller/Presenter:** Resides in the `frontend/controllers` directory.
        *   `frontend/controllers/main_controller.py`: Orchestrates the main application flow. It listens for signals from the `InventoryUI` (View), calls methods in the `backend/inventory.py` (Model) to fetch or modify data, and then updates the `InventoryUI` (View) with the results.
        *   `frontend/controllers/import_export_controller.py`: Handles the logic specifically for import/export actions, interacting with the View for file dialogs and the Model (`backend/import_export_logic.py`) for the operations.
        *   `frontend/controllers/generate_ideas_controller.py`: Manages the "Generate Ideas" dialog, coordinating between the dialog (View) and the `backend/ChatGPT.py` service (part of the Model layer).

    ```python
    # frontend/controllers/main_controller.py (Illustrative Interaction)
    class MainController(QObject):
        def __init__(self, view: InventoryUI, openai_model: str):
            super().__init__()
            self._view = view # Reference to the View
            # ... other initializations ...
            self._connect_signals()

        def _connect_signals(self):
            # View signal connected to Controller slot
            self._view.load_data_requested.connect(self.load_inventory_data)
            self._view.remove_components_requested.connect(self.handle_remove_components)
            # ... other connections ...

        # Controller method triggered by View signal
        def load_inventory_data(self):
            try:
                # 1. Controller calls the Model
                components = get_all_components() # From backend.inventory
                # 2. Controller updates the View
                self._view.display_data(components)
            except DatabaseError as e:
                # Controller handles errors and updates View
                self._show_message("Database Error", ...)

        # Controller method triggered by View signal
        def handle_remove_components(self, component_ids: list[uuid.UUID]):
            # ... confirmation logic (interacts with View via QMessageBox) ...
            for component_id in component_ids:
                try:
                    # 1. Controller gets data from Model if needed
                    component = get_component_by_id(component_id)
                    # ... input dialog logic (interacts with View via QInputDialog) ...
                    if ok_and_valid_quantity:
                         # 2. Controller calls Model to perform action
                         remove_component_quantity(component_id, quantity_to_remove)
                         success_count += 1
                # ... error handling ...
            # 3. Controller potentially updates View (reloads data)
            if success_count > 0:
                self.load_inventory_data()
    ```

*   **How it Was Used (Purpose):**
    *   **Separation of Concerns:** Isolates UI code from business logic and data management, making each part easier to understand, develop, and modify independently.
    *   **Maintainability:** Changes in the UI layout (`View`) are less likely to break the backend logic (`Model`), and vice-versa.
    *   **Testability:** While controller tests were noted as complex, this structure *facilitates* testing. The Model (backend logic) can often be tested independently of the UI.
    *   **Modularity:** Different parts of the application (inventory management, idea generation, import/export) have their dedicated controllers and backend logic.

---

## 3. Observer Pattern (via PyQt Signals/Slots)

*   **What it is:** The Observer pattern defines a one-to-many dependency between objects so that when one object (the *Subject* or *Observable*) changes state, all its dependents (*Observers*) are notified and updated automatically. PyQt's signal/slot mechanism is a prime example of this pattern.

*   **How it Works (PyQt Signals/Slots):**
    1.  **Subject (Emitter):** Objects (typically UI widgets like `QPushButton`, `QCheckBox` or custom `QObject`s) define *signals* (e.g., `clicked = pyqtSignal()`). When a specific event occurs (like a button click), the object *emits* the signal.
    2.  **Observer (Receiver):** Other objects (typically Controllers or other UI elements) define *slots* (which are just regular Python methods decorated implicitly or explicitly).
    3.  **Connection:** A connection is established between a signal and a slot using the `connect()` method (e.g., `button.clicked.connect(controller_method)`).
    4.  **Notification:** When the Subject emits the signal, the Qt event loop automatically calls all connected slots (Observers), passing any arguments the signal carries.

    ```python
    # frontend/ui/main_window.py (View defines signals and emits them)
    from PyQt5.QtCore import pyqtSignal
    from PyQt5.QtWidgets import QMainWindow, QPushButton

    class InventoryUI(QMainWindow):
        # Define signals (Subject's notification points)
        add_component_requested = pyqtSignal()
        remove_components_requested = pyqtSignal(list) # Signal carrying data
        # ... other signals ...

        def _init_ui(self):
            # ...
            self.add_button = QPushButton("Add Component")
            self.remove_button = QPushButton("Remove Selected")
            # ...

        def _connect_signals(self):
            # Internal connection (e.g., button click triggers internal handler)
            # The handler might then emit a public signal
            self.remove_button.clicked.connect(self._on_remove_clicked)
            # Direct connection example (if not handled internally first)
            # self.add_button.clicked.connect(self.add_component_requested) # Connect button's signal to custom signal

        # Internal handler that emits the public signal
        def _on_remove_clicked(self):
            ids_to_remove = self.get_checked_ids()
            if ids_to_remove:
                # Emit the signal to notify external observers (the Controller)
                self.remove_components_requested.emit(ids_to_remove)

    # frontend/controllers/main_controller.py (Controller connects to signals)
    from PyQt5.QtCore import QObject

    class MainController(QObject): # Acts as an Observer
        def __init__(self, view: InventoryUI, openai_model: str):
            super().__init__()
            self._view = view
            self._connect_signals()

        def _connect_signals(self):
            # Connect View's signal to Controller's slot (method)
            self._view.add_component_requested.connect(self.open_add_component_dialog)
            self._view.remove_components_requested.connect(self.handle_remove_components)
            # ... other connections ...

        # Slot (method) executed when add_component_requested signal is emitted
        def open_add_component_dialog(self):
            print("Add component requested!")
            # ... logic to open dialog ...

        # Slot (method) executed when remove_components_requested signal is emitted
        def handle_remove_components(self, component_ids: list[uuid.UUID]): # Receives data from signal
            print(f"Remove components requested for IDs: {component_ids}")
            # ... logic to handle removal ...
    ```

*   **How it Was Used (Purpose):**
    *   **Decoupling:** The View (`InventoryUI`) doesn't need to know *anything* about the `MainController`'s internal methods. It just emits signals when events happen. The `MainController` doesn't need detailed knowledge of the View's internal widgets, it just connects to the signals it cares about.
    *   **Event Handling:** Provides a clean and robust mechanism for reacting to user interactions and other events within the application.
    *   **Communication:** Facilitates communication between different components (View-Controller, Controller-Worker, View-View) without creating tight dependencies.
    *   **Extensibility:** New observers (slots) can be connected to existing signals without modifying the signal emitter (Subject).


# Composition and Aggregation Usage

Besides inheritance ("is-a" relationship), object relationships also involve "has-a" relationships, which are modeled using Composition and Aggregation.

---

## 1. Composition

*   **What it is:** Composition represents a strong "has-a" relationship where one object (the "whole") *owns* or is *composed of* other objects (the "parts"). The lifecycle of the "parts" is typically tied to the lifecycle of the "whole" – if the whole object is destroyed, its internal parts are usually destroyed too.

*   **How it Works:** The "whole" object creates instances of the "part" objects, often within its own `__init__` method or setup routines. These parts are usually internal details necessary for the whole object to function.

*   **How it Was Used (Example: UI Elements):**
    *   GUI windows and dialogs are *composed of* their widgets (buttons, tables, text boxes, etc.).
    *   In `frontend/ui/main_window.py`, the `InventoryUI` class creates its `QTableWidget`, `QPushButton` instances, etc., within its `_init_ui` method. These widgets are essential parts *of* the window and don't exist independently. When the `InventoryUI` window is closed, these child widgets are automatically destroyed by the Qt framework.

    ```python
    # frontend/ui/main_window.py (Excerpt - Simplified)
    class InventoryUI(QMainWindow):
        def __init__(self):
            super().__init__()
            # ...
            self._init_ui() # Calls the method that creates the parts

        def _init_ui(self):
            self.central_widget = QWidget(self) # Creates a part
            self.layout = QVBoxLayout(self.central_widget) # Creates a part

            # ... button layout ...
            self.add_button = QPushButton("Add Component") # Creates a part
            self.remove_button = QPushButton("Remove Selected") # Creates a part
            # ... other buttons created as parts ...

            self.table = QTableWidget() # Creates the main table part
            self.layout.addWidget(self.table) # Adds the part to the layout
            # ...
    ```
*   **How it Was Used (Example: Controller Structure):**
    *   The `MainController` creates and owns the `ImportExportController`. The `ImportExportController` is part of the `MainController`'s overall functionality.

    ```python
    # frontend/controllers/main_controller.py (Excerpt)
    class MainController(QObject):
        def __init__(self, view: InventoryUI, openai_model: str):
            super().__init__()
            self._view = view
            # Creates and owns the ImportExportController instance
            self._import_export_controller = ImportExportController(self._view, self)
            # ...
    ```

*   **Purpose:** To build complex objects or functionalities by assembling simpler parts. It helps manage complexity by encapsulating parts within the whole and ensures that components that logically belong together are managed together.

---

## 2. Aggregation

*   **What it is:** Aggregation represents a weaker "has-a" relationship where one object (the "aggregate") *uses* or *references* another independent object (the "part"). The lifecycle of the "part" object is *not* tied to the aggregate object. The part can exist independently, and the aggregate object simply holds a reference to it.

*   **How it Works:** The aggregate object typically receives a reference to the already existing part object through its constructor or a setter method. It uses the part's functionality but doesn't own it.

*   **How it Was Used (Example: Controller-View Relationship):**
    *   The `MainController` *aggregates* the `InventoryUI` (the View). The View object is created externally (in `main.py`) and passed *into* the `MainController`'s constructor.
    *   The `MainController` holds a reference (`self._view`) and interacts with the View (calling methods like `display_data`, connecting to its signals), but it doesn't *own* the View in the sense of controlling its entire lifecycle from creation to destruction. If the `MainController` instance were somehow replaced, the `InventoryUI` window could potentially persist (though in this app they are tightly linked at the top level).

    ```python
    # main.py (Excerpt - Where objects are created)
    # ...
    app = QApplication(sys.argv)
    view = InventoryUI() # View created independently
    # View instance is passed to the Controller
    controller = MainController(view, openai_model=openai_model)
    controller.show_view()
    # ...

    # frontend/controllers/main_controller.py (Excerpt - Controller holds reference)
    class MainController(QObject):
        def __init__(self, view: InventoryUI, openai_model: str): # Receives View reference
            super().__init__()
            self._view = view # Holds the reference (Aggregation)
            self._openai_model = openai_model
            # ... interacts with self._view ...
    ```
*   **How it Was Used (Example: Controller-Controller Relationship):**
    *   The `ImportExportController` *aggregates* the `MainController`. It receives a reference to the `MainController` in its constructor and uses it (e.g., to show messages via `_main_controller._show_message`). It doesn't own the `MainController`.

    ```python
    # frontend/controllers/import_export_controller.py (Excerpt)
    class ImportExportController(QObject):
        def __init__(self, view: InventoryUI, main_controller): # Receives MainController
            super().__init__()
            self._view = view # Aggregates view
            self._main_controller = main_controller # Aggregates main_controller
        # ... uses self._main_controller._show_message(...) ...
    ```

*   **Purpose:** To allow objects to collaborate and use each other's functionality without being tightly bound by ownership or lifecycle dependencies. This promotes flexibility and allows objects (like Views or Services) to be potentially shared or referenced by multiple other objects.

# File Reading and Writing

The application utilizes file operations for configuration, styling, and core data persistence via import/export functionality, fulfilling the requirement to save and load program state/data.

---

## 1. Data Import/Export (Excel)

*   **Requirement Fulfillment:** Directly addresses the requirement to implement functions for importing and exporting application data (the component inventory).
*   **File Type Chosen:** Microsoft Excel (`.xlsx`) format was selected for its widespread usability and ability to handle structured tabular data effectively.
*   **Implementation (`backend/import_export_logic.py`):**
    *   **Exporting:**
        1.  Uses the `pandas` library to create a DataFrame from the current component inventory fetched from the database.
        2.  Uses the `openpyxl` engine with `pandas.ExcelWriter` to write the DataFrame to a user-specified `.xlsx` file.
        3.  Applies basic formatting (bold headers, background color, auto-column width adjustment) using `openpyxl` for better readability.
        ```python
        # backend/import_export_logic.py (Export Snippet)
        import pandas as pd
        from pandas import ExcelWriter
        # ... other imports ...

        def export_to_excel(filename: str) -> bool:
            # ... fetch components_data from database ...
            df = pd.DataFrame(components_data, columns=EXCEL_COLUMNS)
            with ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Inventory', index=False)
                # ... formatting code using writer.book, writer.sheets ...
            return True
        ```
    *   **Importing:**
        1.  Uses `pandas.read_excel` (with `openpyxl` engine) to read data from a user-selected `.xlsx` file into a DataFrame.
        2.  Validates the presence of required columns ("Part Number", "Type", "Value", "Quantity").
        3.  Iterates through the DataFrame rows, validating data types and values (e.g., quantity >= 0).
        4.  **Crucially, this operation first deletes all existing components from the database before adding the imported ones**, effectively overwriting the current inventory.
        5.  Uses the `ComponentFactory` to create new component objects from the validated row data and adds them to the database session.
        ```python
        # backend/import_export_logic.py (Import Snippet)
        import pandas as pd
        # ... other imports ...

        def import_from_excel(filename: str) -> bool:
            df = pd.read_excel(filename, engine='openpyxl')
            # ... validate columns ...
            components_to_add = []
            for index, row in df.iterrows():
                # ... read and validate data from row (part_number, type, value, qty) ...
                components_to_add.append({ ... })
            # ... database operations ...
            session = get_session()
            session.query(Component).delete() # Overwrite existing data
            for comp_data in components_to_add:
                 component = ComponentFactory.create_component(...)
                 session.add(component)
            session.commit()
            return True
        ```
*   **Purpose:** Provides users with a convenient way to back up their inventory, edit it externally using standard spreadsheet software, and share it or transfer it between application instances.

---

## 2. Configuration and Style Files (Reading)

*   **Implementation:**
    *   `main.py`: Reads the `config.ini` file using Python's `configparser` module to load settings like the database path and OpenAI model name. It also uses `dotenv` to load the API key from the `.env` file.
    *   `frontend/ui/utils.py`: Reads the `button_styles.qss` file (a text file) to load custom stylesheet rules for the PyQt application interface.
*   **Purpose:** Demonstrates reading different file types (INI, ENV, QSS/TXT) to configure application behavior and appearance, loading program state and settings from external sources.

# Unit Testing

*   **Implementation:** The project includes a dedicated `tests` directory containing unit tests, primarily utilizing Python's built-in `unittest` framework. An in-memory SQLite database is used during testing to isolate tests from the development database.

*   **Scope:** These tests focus primarily on verifying the correctness of individual functions and classes within the backend logic. This includes testing data validation in models, core inventory operations (add, remove quantity logic), utility functions, and critically, the `ComponentFactory`.

*   **Example: Testing `ComponentFactory` (`tests/test_component_factory.py`):**
    *   **Testing Creation of All Known Types:** Ensures the factory can correctly instantiate every component type defined in `models.py` and that the created objects have the expected attributes and specific type after being saved and retrieved from the test database.
        ```python
        # tests/test_component_factory.py (Inside TestComponentFactory class)
        def test_all_component_types_creation(self):
            # ... setup default data ...
            failed_types = []
            # Loop through all types registered in the factory
            for component_type, component_class in ComponentFactory._component_types.items():
                try:
                    # ... create unique part number ...
                    # Attempt to create the component via the factory
                    component = ComponentFactory.create_component(component_type, **test_data)
                    self.session.add(component)
                    self.session.commit()
                    # Retrieve to verify persistence and type
                    retrieved = self.session.query(Component).filter_by(part_number=part_number).first()

                    self.assertIsNotNone(retrieved, f"{component_type} not found")
                    self.assertEqual(retrieved.component_type, component_type)
                    # Check if the retrieved object is an instance of the expected specific class
                    self.assertIsInstance(retrieved, component_class)
                    # Check if the abstract method implementation works
                    specs = retrieved.get_specifications()
                    self.assertIsNotNone(specs)
                except Exception as e:
                    failed_types.append(f"{component_type}: {e}") # Collect failures
                    self.session.rollback()
            # Fail test if any types caused an error during creation/verification
            self.assertFalse(failed_types, f"Component types failed: {', '.join(failed_types)}")
        ```
    *   **Testing Handling of Unknown Types:** Verifies that the factory raises a `ValueError` as expected when asked to create a component type it doesn't recognize.
        ```python
        # tests/test_component_factory.py (Inside TestComponentFactory class)
        def test_error_on_unknown_component_type(self):
            # Asserts that the specified exception is raised
            with self.assertRaises(ValueError):
                ComponentFactory.create_component("nonexistent_type", part_number="TEST-X", value="1", quantity=1)
        ```
    *   **Testing Dynamic Registration:** Confirms that new component types can be dynamically created and registered with the factory at runtime, and subsequently instantiated correctly.
        ```python
        # tests/test_component_factory.py (Inside TestComponentFactory class)
        def test_register_new_component_type(self):
            from backend.models import create_component_class # Import helper
            # Dynamically create a new component class for testing
            TestComp = create_component_class(
                class_name="TestComp", polymorphic_id="test_comp", spec_format_string="Test Value X"
            )
            # Register this new type with the factory
            ComponentFactory.register_component("test_comp", TestComp)
            # Attempt to create an instance of the newly registered type
            component = ComponentFactory.create_component("test_comp", part_number="TEST-CUSTOM", ...)
            # ... add, commit, retrieve ...
            retrieved = self.session.query(Component).filter_by(part_number="TEST-CUSTOM").first()
            self.assertIsNotNone(retrieved)
            # Verify it's an instance of the dynamically created TestComp class
            self.assertIsInstance(retrieved, TestComp)
            self.assertEqual(retrieved.component_type, "test_comp")
        ```

*   **Limitations:** The controller classes (`frontend/controllers`) are not covered by unit tests. This is due to the complexity of testing components that interact heavily with GUI elements and manage application state triggered by user actions, which typically requires more involved testing strategies (like integration or functional testing) or mocking entire frameworks.

*   **Purpose:** The existing unit tests serve to ensure that fundamental backend operations (especially component creation via the factory) behave as expected, catch regressions (accidental breakages) during development, and provide a degree of confidence in the reliability of the core data manipulation logic.

*   **Code Style (PEP8):** Code generally follows PEP8 guidelines for readability.
## 3. Results and Summary

**Results:**

*   The application successfully provides a graphical interface for managing an electronic component inventory stored persistently in a local database.
*   It integrates core CRUD (Create, Read, Update, Delete) functionalities for components through user-friendly dialogs and table interactions.
*   Data exchange with external files is enabled through robust Excel import/export functionality.
*   Value-added functionality is provided by integrating the OpenAI API to generate project ideas based on available inventory, enhancing the tool's utility.
*   The project demonstrates the practical application of OOP principles, a key design pattern (Factory Method), and separation of concerns in a desktop application context.

**Conclusions:**

*   The project successfully demonstrates the application of the four pillars of OOP (Inheritance, Abstraction, Encapsulation, Polymorphism) to model the application's domain effectively.
*   The Factory Method design pattern was successfully implemented to decouple component instantiation logic, improving maintainability.
*   Experience was gained in integrating disparate technologies: PyQt5 for the GUI, SQLAlchemy for database ORM, Pandas for file I/O, and the OpenAI API for special functions.
*   The development process highlighted the importance of asynchronous operations (using `QThread`) in GUI applications to maintain responsiveness during long-running tasks like API calls.
*   The project underscored the challenges associated with unit testing components tightly coupled with a GUI framework like PyQt5, emphasizing the need for mocking or specialized testing tools.

**Potential Extensions:**

*   **User Accounts:** Implement user login and potentially different permission levels.
*   **Project Association:** Allow users to create "projects" and link specific components from the inventory to these projects, tracking usage.
*   **Low Stock Notifications:** Implement visual cues or notifications when component quantities fall below a user-defined threshold.
*   **Component Images:** Add functionality to associate image files with component entries.
*   **Advanced Search/Filtering:** Implement more sophisticated searching capabilities within the inventory table (e.g., filtering by value range, multiple criteria).
*   **Multiple inventory tables:** Implement multiple inventory tables for different component inventorization needs.


## 4. Resources, References List

**Key Libraries Used:**

*   **PyQt5:** GUI Framework
*   **SQLAlchemy:** Database ORM Toolkit
*   **OpenAI Python Library:** Interface for OpenAI API
*   **Pandas:** Data manipulation and Excel I/O
*   **python-dotenv:** Loading environment variables (for API key)
*   **openpyxl:** Reading/Writing Excel `.xlsx` files (used by Pandas)

**Key Libraries Used, documentation:**

*   **Python 3.10 Documentation:** [https://docs.python.org/3.10/](https://docs.python.org/3.10/) - Official documentation for the Python language version used.
*   **PyQt5 Reference Guide:** [https://www.riverbankcomputing.com/static/Docs/PyQt5/](https://www.riverbankcomputing.com/static/Docs/PyQt5/) - Documentation for the GUI framework.
*   **SQLAlchemy Documentation:** [https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/) - Official documentation for the Database ORM Toolkit (using version 2.0 style).
*   **OpenAI API Reference (Python):** [https://platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference) & [https://github.com/openai/openai-python](https://github.com/openai/openai-python) - Documentation and library for the OpenAI API.
*   **Pandas Documentation:** [https://pandas.pydata.org/pandas-docs/stable/](https://pandas.pydata.org/pandas-docs/stable/) - Documentation for data manipulation and Excel I/O.
*   **python-dotenv Documentation:** [https://github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) - For loading environment variables (like API key).
*   **openpyxl Documentation:** [https://openpyxl.readthedocs.io/en/stable/](https://openpyxl.readthedocs.io/en/stable/) - For reading/Writing Excel `.xlsx` files (used by Pandas).
*   **PEP 8 -- Style Guide for Python Code:** [https://peps.python.org/pep-0008/](https://peps.python.org/pep-0008/) - Official Python style guide.
*   **unittest — Unit testing framework:** [https://docs.python.org/3/library/unittest.html](https://docs.python.org/3/library/unittest.html) - Python's built-in testing framework.
*   **Markdown Guide:** [https://www.markdownguide.org/basic-syntax/](https://www.markdownguide.org/basic-syntax/) - A general guide to Markdown syntax used for this report.