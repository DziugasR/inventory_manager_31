def construct_generation_prompt(components, selected_quantities, type_mapping):
    component_details = []
    for component in components:
        part_number = component.part_number
        project_qty = selected_quantities.get(part_number, 0)

        if project_qty > 0:
            ui_type = type_mapping.get(component.component_type, component.component_type)
            value = component.value or "N/A"
            component_details.append(f"  - {part_number} (Type: {ui_type}, Value: {value}): Quantity {project_qty}")

    if not component_details:
        return None

    prompt = "You are an electronics lecturer creating TWO extremely concise project idea using ONLY the components listed if needed you can add more components.\n\n"
    prompt += "Generate TWO specific project using EXACTLY these components and quantities. Build ONLY with these parts.\n\n"
    prompt += "Available Components:\n"
    prompt += "\n".join(component_details)
    prompt += "\n\nUse this strict format (plain text, no markdown headers):\n\n"
    prompt += "--Project Title:--\n"
    prompt += "[Concise Project Name Here]\n\n"
    prompt += "--Description:--\n"
    prompt += "[Couple, concise sentence explaining the project's function.]\n\n"
    prompt += "--Component Usage:--\n"
    prompt += "[List *each* component below, followed by ' - ' and its *brief* role in couple sentences.]\n"
    prompt += "\nFocus on a logical use of the exact parts. Be extremely direct and brief."

    return prompt
