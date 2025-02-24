

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


@dataclass
class MaterialConfig:
    """Configuration for material calculations."""
    material_type: MaterialType
    wastage_factor: float
    minimum_order_quantity: float
    unit_cost_multiplier: float

    @dataclass
    class ComponentConfig:
        """Configuration for component calculations."""
        component_type: ComponentType
        complexity_factor: float
        labor_multiplier: float


class ModelConfiguration:
    """Configuration management for model calculations."""
    _material_configs: Dict[MaterialType, MaterialConfig] = {}
    _component_configs: Dict[ComponentType, ComponentConfig] = {}

    @classmethod
    def register_material_config(cls, config: MaterialConfig) -> None:
        """Register configuration for a material type."""
        cls._material_configs[config.material_type] = config

        @classmethod
        def register_component_config(cls, config: ComponentConfig) -> None:
            """Register configuration for a component type."""
            cls._component_configs[config.component_type] = config

            @classmethod
            def get_material_config(cls, material_type: MaterialType) -> Optional[
                    MaterialConfig]:
                """Get configuration for a material type."""
                return cls._material_configs.get(material_type)

                @classmethod
                def get_component_config(cls, component_type: ComponentType) -> Optional[
                        ComponentConfig]:
                    """Get configuration for a component type."""
                    return cls._component_configs.get(component_type)

                    @classmethod
                    def initialize_default_configs(cls) -> None:
                        """Initialize default configurations."""
                        for material_type in MaterialType:
                            cls.register_material_config(MaterialConfig(
                                material_type=material_type, wastage_factor=0.1, minimum_order_quantity=1.0, unit_cost_multiplier=1.0))
                            for component_type in ComponentType:
                                cls.register_component_config(ComponentConfig(
                                    component_type=component_type, complexity_factor=1.0, labor_multiplier=1.0))
