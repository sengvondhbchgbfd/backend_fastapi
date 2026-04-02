from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.schema import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    StockMovementCreate, StockMovementResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
)
from app.services.inventory_service import (
    SupplierService,
    CustomerService,
    CategoryService,
    ProductService,
    StockMovementService,
    InvoiceService,
)
from app.dependencies import get_db
from app.utils.auth import require_login, require_manager

# ---------------------------------------------------------------------------
# One router per resource
# ---------------------------------------------------------------------------


supplier_router       = APIRouter(prefix="/suppliers",       tags=["Suppliers"])
customer_router       = APIRouter(prefix="/customers",       tags=["Customers"])
category_router       = APIRouter(prefix="/categories",      tags=["Categories"])
product_router        = APIRouter(prefix="/products",        tags=["Products"])
stock_movement_router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])
invoice_router        = APIRouter(prefix="/invoices",        tags=["Invoices"])


# ===========================================================================
# SUPPLIERS
# ===========================================================================

@supplier_router.get("/", response_model=list[SupplierResponse], summary="List suppliers")
async def list_suppliers(current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await SupplierService(db).get_all(current_user["company_id"])



@supplier_router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await SupplierService(db).get_by_id(supplier_id, current_user["company_id"])



@supplier_router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(data: SupplierCreate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await SupplierService(db).create(data, current_user["company_id"])





@supplier_router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: int, data: SupplierUpdate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await SupplierService(db).update(supplier_id, data, current_user["company_id"])

@supplier_router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await SupplierService(db).delete(supplier_id, current_user["company_id"])


# ===========================================================================
# CUSTOMERS
# ===========================================================================

@customer_router.get("/", response_model=list[CustomerResponse], summary="List customers")
async def list_customers(current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CustomerService(db).get_all(current_user["company_id"])

@customer_router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CustomerService(db).get_by_id(customer_id, current_user["company_id"])



@customer_router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(data: CustomerCreate, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CustomerService(db).create(data, current_user["company_id"])




@customer_router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, data: CustomerUpdate, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CustomerService(db).update(customer_id, data, current_user["company_id"])

@customer_router.delete("/{customer_id}")
async def delete_customer(customer_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await CustomerService(db).delete(customer_id, current_user["company_id"])


# ===========================================================================
# CATEGORIES
# ===========================================================================

@category_router.get("/", response_model=list[CategoryResponse], summary="List categories")
async def list_categories(current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CategoryService(db).get_all(current_user["company_id"])

@category_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await CategoryService(db).get_by_id(category_id, current_user["company_id"])

@category_router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await CategoryService(db).create(data, current_user["company_id"])

@category_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, data: CategoryUpdate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await CategoryService(db).update(category_id, data, current_user["company_id"])

@category_router.delete("/{category_id}")
async def delete_category(category_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await CategoryService(db).delete(category_id, current_user["company_id"])


# ===========================================================================
# PRODUCTS
# ===========================================================================

@product_router.get("/", response_model=list[ProductResponse], summary="List products")
async def list_products(
    category_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    db: AsyncSession = Depends(get_db)
):
    return await ProductService(db).get_all(current_user["company_id"], category_id)

@product_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await ProductService(db).get_by_id(product_id, current_user["company_id"])

@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await ProductService(db).create(data, current_user["company_id"])

@product_router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, data: ProductUpdate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await ProductService(db).update(product_id, data, current_user["company_id"])

@product_router.delete("/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await ProductService(db).delete(product_id, current_user["company_id"])


# ===========================================================================
# STOCK MOVEMENTS
# ===========================================================================

@stock_movement_router.get("/", response_model=list[StockMovementResponse], summary="List stock movements")
async def list_movements(
    product_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    db: AsyncSession = Depends(get_db)
):
    return await StockMovementService(db).get_all(current_user["company_id"], product_id)

@stock_movement_router.get("/{movement_id}", response_model=StockMovementResponse)
async def get_movement(movement_id: int, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await StockMovementService(db).get_by_id(movement_id, current_user["company_id"])

@stock_movement_router.post("/", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED,
    summary="Create stock movement — auto updates product stock_quantity")

async def create_movement(data: StockMovementCreate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await StockMovementService(db).create(data, current_user["company_id"])

@stock_movement_router.delete("/{movement_id}")
async def delete_movement(movement_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await StockMovementService(db).delete(movement_id, current_user["company_id"])


# ===========================================================================
# INVOICES
# ===========================================================================

@invoice_router.get("/", response_model=list[InvoiceResponse], summary="List invoices")
async def list_invoices(
    customer_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    db: AsyncSession = Depends(get_db)
):
    return await InvoiceService(db).get_all(current_user["company_id"], customer_id)

@invoice_router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await InvoiceService(db).get_by_id(invoice_id, current_user["company_id"])

@invoice_router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED,
    summary="Create invoice — auto deducts product stock")
async def create_invoice(data: InvoiceCreate, current_user: dict = Depends(require_login), db: AsyncSession = Depends(get_db)):
    return await InvoiceService(db).create(data, current_user["company_id"])

@invoice_router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: int, data: InvoiceUpdate, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await InvoiceService(db).update(invoice_id, data, current_user["company_id"])

@invoice_router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, current_user: dict = Depends(require_manager), db: AsyncSession = Depends(get_db)):
    return await InvoiceService(db).delete(invoice_id, current_user["company_id"])