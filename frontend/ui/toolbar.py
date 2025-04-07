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
        - tools_menu                                # New
        - export_xls_action, import_xls_action, chatgpt_action # New
        - tools_menu_action                         # New
        - view_menu                                 # New
        - table_size_action, dark_mode_action       # New
        - view_menu_action                          # New
        # - help_action (Removed)

    Args:
        main_window: The QMainWindow instance (e.g., InventoryUI) to add the toolbar to.
    """
    # --- Toolbar --- START
    main_window.toolbar = QToolBar("Main Toolbar", main_window) # Parent is main_window
    main_window.addToolBar(Qt.TopToolBarArea, main_window.toolbar)  # Add toolbar to the top

    # --- File Menu Dropdown --- (Unchanged)
    # 1. Create the QMenu
    main_window.file_menu = QMenu("File", main_window)
    # 2. Create Actions
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
    main_window.file_menu.addSeparator()
    main_window.file_menu.addAction(main_window.exit_action)
    # 4. Create the main Action/Button FOR the toolbar
    main_window.file_menu_action = QAction("File", main_window)
    # 5. Associate the QMenu
    main_window.file_menu_action.setMenu(main_window.file_menu)
    # 6. Add the main Action to the toolbar
    main_window.toolbar.addAction(main_window.file_menu_action)
    # 7. Set the popup mode
    file_tool_button = main_window.toolbar.widgetForAction(main_window.file_menu_action)
    if isinstance(file_tool_button, QToolButton):
        file_tool_button.setPopupMode(QToolButton.InstantPopup)

    # --- Edit Menu Dropdown --- (Unchanged)
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

    # --- Tools Menu Dropdown --- (New)
    main_window.tools_menu = QMenu("Tools", main_window)
    # Actions within the Tools menu
    main_window.export_xls_action = QAction("Export .xls", main_window)
    main_window.import_xls_action = QAction("Import .xls", main_window)
    main_window.chatgpt_action = QAction("ChatGPT", main_window)
    # Add actions to the menu
    main_window.tools_menu.addAction(main_window.export_xls_action)
    main_window.tools_menu.addAction(main_window.import_xls_action)
    main_window.tools_menu.addSeparator()
    main_window.tools_menu.addAction(main_window.chatgpt_action)
    # Main action for the toolbar
    main_window.tools_menu_action = QAction("Tools", main_window)
    main_window.tools_menu_action.setMenu(main_window.tools_menu)
    main_window.toolbar.addAction(main_window.tools_menu_action)
    # Set popup mode for the toolbar button
    tools_tool_button = main_window.toolbar.widgetForAction(main_window.tools_menu_action)
    if isinstance(tools_tool_button, QToolButton):
        tools_tool_button.setPopupMode(QToolButton.InstantPopup)

    # --- View Menu Dropdown --- (New)
    main_window.view_menu = QMenu("View", main_window)
    # Actions within the View menu
    main_window.table_size_action = QAction("Table Size...", main_window)
    main_window.dark_mode_action = QAction("Dark Mode", main_window)
    # Add actions to the menu
    main_window.view_menu.addAction(main_window.table_size_action)
    main_window.view_menu.addAction(main_window.dark_mode_action)
    # Main action for the toolbar
    main_window.view_menu_action = QAction("View", main_window)
    main_window.view_menu_action.setMenu(main_window.view_menu)
    main_window.toolbar.addAction(main_window.view_menu_action)
    # Set popup mode for the toolbar button
    view_tool_button = main_window.toolbar.widgetForAction(main_window.view_menu_action)
    if isinstance(view_tool_button, QToolButton):
        view_tool_button.setPopupMode(QToolButton.InstantPopup)

    # --- Help Action Removed ---
    # main_window.help_action = QAction("Help", main_window) # Removed
    # main_window.toolbar.addAction(main_window.help_action) # Removed

    # --- Toolbar --- END