

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


@unique
class ProjectStatus(str, Enum):
    """Represents the current status of a project."""
    PLANNING = 'planning'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ON_HOLD = 'on_hold'
    CANCELLED = 'cancelled'

    @inject(MaterialService)
        def __str__(self):
        return self.value

        @unique
        class SkillLevel(str, Enum):
            """Represents the skill level required for a project or pattern."""
            BEGINNER = 'beginner'
            INTERMEDIATE = 'intermediate'
            ADVANCED = 'advanced'
            EXPERT = 'expert'

            @inject(MaterialService)
                def __str__(self):
                return self.value

                @unique
                class ProjectType(str, Enum):
                    """Represents different types of projects."""
                    LEATHERWORKING = 'leatherworking'
                    CRAFTING = 'crafting'
                    DESIGN = 'design'
                    PROTOTYPE = 'prototype'

                    @inject(MaterialService)
                        def __str__(self):
                        return self.value

                        @unique
                        class ProductionStatus(str, Enum):
                            """Represents the production status of an item."""
                            NOT_STARTED = 'not_started'
                            IN_PROGRESS = 'in_progress'
                            COMPLETED = 'completed'
                            QUALITY_CHECK = 'quality_check'
                            REJECTED = 'rejected'

                            @inject(MaterialService)
                                def __str__(self):
                                return self.value

                                @unique
                                class MaterialType(str, Enum):
                                    """Represents different types of materials."""
                                    LEATHER = 'leather'
                                    FABRIC = 'fabric'
                                    METAL = 'metal'
                                    WOOD = 'wood'
                                    SYNTHETIC = 'synthetic'

                                    @inject(MaterialService)
                                        def __str__(self):
                                        return self.value

                                        @unique
                                        class TransactionType(str, Enum):
                                            """Represents types of inventory transactions."""
                                            PURCHASE = 'purchase'
                                            SALE = 'sale'
                                            TRANSFER = 'transfer'
                                            ADJUSTMENT = 'adjustment'
                                            RETURN = 'return'

                                            @inject(MaterialService)
                                                def __str__(self):
                                                return self.value

                                                @unique
                                                class OrderStatus(str, Enum):
                                                    """Represents the status of an order."""
                                                    PENDING = 'pending'
                                                    PROCESSING = 'processing'
                                                    SHIPPED = 'shipped'
                                                    DELIVERED = 'delivered'
                                                    CANCELLED = 'cancelled'

                                                    @inject(MaterialService)
                                                        def __str__(self):
                                                        return self.value

                                                        @unique
                                                        class PaymentStatus(str, Enum):
                                                            """Represents the payment status."""
                                                            UNPAID = 'unpaid'
                                                            PARTIAL = 'partial'
                                                            PAID = 'paid'
                                                            REFUNDED = 'refunded'

                                                            @inject(MaterialService)
                                                                def __str__(self):
                                                                return self.value

                                                                @unique
                                                                class ShoppingListStatus(str, Enum):
                                                                    """Represents the status of a shopping list."""
                                                                    ACTIVE = 'active'
                                                                    COMPLETED = 'completed'
                                                                    ARCHIVED = 'archived'

                                                                    @inject(MaterialService)
                                                                        def __str__(self):
                                                                        return self.value

                                                                        @unique
                                                                        class StitchType(str, Enum):
                                                                            """Represents different types of stitching."""
                                                                            HAND_STITCH = 'hand_stitch'
                                                                            MACHINE_STITCH = 'machine_stitch'
                                                                            SADDLE_STITCH = 'saddle_stitch'
                                                                            LOCK_STITCH = 'lock_stitch'

                                                                            @inject(MaterialService)
                                                                                def __str__(self):
                                                                                return self.value

                                                                                @unique
                                                                                class EdgeFinishType(str, Enum):
                                                                                    """Represents different types of edge finishing."""
                                                                                    BURNISHED = 'burnished'
                                                                                    PAINTED = 'painted'
                                                                                    SEALED = 'sealed'
                                                                                    RAW = 'raw'

                                                                                    @inject(MaterialService)
                                                                                        def __str__(self):
                                                                                        return self.value

                                                                                        @unique
                                                                                        class ComponentType(str, Enum):
                                                                                            """Represents different types of components."""
                                                                                            HARDWARE = 'hardware'
                                                                                            MATERIAL = 'material'
                                                                                            ACCESSORY = 'accessory'
                                                                                            STRUCTURAL = 'structural'
                                                                                            DECORATIVE = 'decorative'

                                                                                            @inject(MaterialService)
                                                                                                def __str__(self):
                                                                                                return self.value
