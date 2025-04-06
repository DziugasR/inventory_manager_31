from PyQt5.QtWidgets import QToolBar, QMenu, QAction, QToolButton
from PyQt5.QtCore import Qt

def setup_toolbar(main_window):
    """
    Initializes and configures the main toolbar for the given main_window.

    Sets the following attributes on main_window:
        - toolbar
        - file_menu
        - new_action, open_action, save_action, save_as_action, exit_action
        - file_menu_action
        - edit_menu
        - copy_action, paste_action, find_action
        - edit_menu_action
        - help_action

    Args:
        main_window: The QMainWindow instance (e.g., InventoryUI) to add the toolbar to.
    """
    # --- Toolbar --- START (Copied from original _init_ui)
    main_window.toolbar = QToolBar("Main Toolbar", main_window) # Parent is main_window
    main_window.addToolBar(Qt.TopToolBarArea, main_window.toolbar)  # Add toolbar to the top

    # --- File Menu Dropdown ---
    # 1. Create the QMenu (Parent is main_window)
    main_window.file_menu = QMenu("File", main_window)

    # 2. Create Actions for the menu items (Parent is main_window)
    main_window.new_action = QAction("New Inventory...", main_window)
    main_window.open_action = QAction("Open Inventory...", main_window)
    main_window.save_action = QAction("Save Inventory", main_window)
    main_window.save_as_action = QAction("Save Inventory As...", main_window)
    main_window.exit_action = QAction("Exit", main_window)

    # 3. Add Actions to the QMenu
    main_window.file_menu.addAction(main_window.new_action)
    main_window.file_menu.addAction(main_window.open_action)
    main_window.file_menu.addAction(main_window.save_action)
    main_window.file_menu.addAction(main_window.save_as_action)
    main_window.file_menu.addSeparator()  # Add a visual separator line
    main_window.file_menu.addAction(main_window.exit_action)

    # 4. Create the main Action/Button FOR the toolbar (Parent is main_window)
    main_window.file_menu_action = QAction("File", main_window)

    # 5. Associate the QMenu with the main toolbar Action
    main_window.file_menu_action.setMenu(main_window.file_menu)

    # 6. Add the main Action (which now has a menu) to the toolbar
    main_window.toolbar.addAction(main_window.file_menu_action)

    # 7. Set the popup mode for the button associated with the action
    file_tool_button = main_window.toolbar.widgetForAction(main_window.file_menu_action)
    if isinstance(file_tool_button, QToolButton):
        file_tool_button.setPopupMode(QToolButton.InstantPopup)  # Or MenuButtonPopup for split button

    # --- Edit Menu Dropdown (Example) ---
    main_window.edit_menu = QMenu("Edit", main_window)
    main_window.copy_action = QAction("Copy Row", main_window)
    main_window.paste_action = QAction("Paste Row", main_window)
    main_window.find_action = QAction("Find...", main_window)

    main_window.edit_menu.addAction(main_window.copy_action)
    main_window.edit_menu.addAction(main_window.paste_action)
    main_window.edit_menu.addSeparator()
    main_window.edit_menu.addAction(main_window.find_action)

    main_window.edit_menu_action = QAction("Edit", main_window)
    main_window.edit_menu_action.setMenu(main_window.edit_menu)
    main_window.toolbar.addAction(main_window.edit_menu_action)

    edit_tool_button = main_window.toolbar.widgetForAction(main_window.edit_menu_action)
    if isinstance(edit_tool_button, QToolButton):
        edit_tool_button.setPopupMode(QToolButton.InstantPopup)

    # --- Simple Action (Button) still possible ---
    main_window.help_action = QAction("Help", main_window)
    main_window.toolbar.addAction(main_window.help_action)

    # --- Toolbar --- END