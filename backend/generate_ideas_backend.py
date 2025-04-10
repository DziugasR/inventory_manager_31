class GenerateIdeasBackend:
    def __init__(self):
        # Initialize any backend resources if needed (e.g., API clients)
        pass

    def process_ideas(self, selected_data):
        print("\n--- [Backend] Generating Ideas Based On Selected Components ---")

        if not selected_data:
            print("[Backend] No components data received.")
            print("-----------------------------------------------------------\n")
            return

        for item in selected_data:
            # Access data using dictionary keys
            part_number = item.get("part_number", "N/A")
            item_type = item.get("type", "N/A")
            item_value = item.get("value", "N/A")
            project_quantity = item.get("project_quantity", "?")

            print(f"  - Part: {part_number}, Type: {item_type}, Value: {item_value}, Project Qty: {project_quantity}")

        print("-----------------------------------------------------------\n")