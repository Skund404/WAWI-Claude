# services/dto/__init__.py
# Data Transfer Objects package initialization

from services.dto.customer_dto import CustomerDTO
from services.dto.material_dto import (
    MaterialDTO,
    LeatherDTO,
    HardwareDTO,
    SuppliesDTO,
    create_material_dto
)
from services.dto.project_dto import ProjectDTO, ProjectComponentDTO, ProjectStatusHistoryDTO
from services.dto.inventory_dto import InventoryDTO, InventoryTransactionDTO, LocationHistoryDTO
from services.dto.sales_dto import SalesDTO, SalesItemDTO
from services.dto.picking_list_dto import PickingListDTO, PickingListItemDTO
from services.dto.tool_list_dto import ToolListDTO, ToolListItemDTO