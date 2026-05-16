from fastapi import APIRouter
from .inventory_router import (
    supplier_router,
    customer_router,
    category_router,
    product_router,
    stock_movement_router,
    invoice_router,
)
from .system_setting_router import system_setting_router
from ..communication.ws_router import ws_router
from ..communication.chat_ws_router import chat_ws_router
from .audit_log_router import audit_router

router_inventory = APIRouter()
router_inventory.include_router(supplier_router)
router_inventory.include_router(customer_router)
router_inventory.include_router(category_router)
router_inventory.include_router(product_router)
router_inventory.include_router(stock_movement_router)
router_inventory.include_router(invoice_router)
router_inventory.include_router(system_setting_router)
router_inventory.include_router(ws_router)
router_inventory.include_router(chat_ws_router)
router_inventory.include_router(audit_router)