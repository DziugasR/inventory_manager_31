class ComponentFactory:
    _component_types = {}

    @staticmethod
    def create_component(component_type, **kwargs):
        component_type = component_type.lower()
        if component_type in ComponentFactory._component_types:
            component_class = ComponentFactory._component_types[component_type]
            return component_class(**kwargs)
        else:
            raise ValueError(f"Unknown component type: '{component_type}'. It has not been registered with the factory.")

    @staticmethod
    def register_component(name, cls):
        name = name.lower()
        print(f"DEBUG: ComponentFactory registering '{name}' with class {cls.__name__}")
        ComponentFactory._component_types[name] = cls