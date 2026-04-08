from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
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
from app.services.inventory.inventory_service import (
    SupplierService, CustomerService, CategoryService,
    ProductService, StockMovementService, InvoiceService,
)

from app.services.inventory.inventory_service import (
get_Invoice_service, 
get_stock_service, 
get_product_service, 
get_category_service, 
get_customer_service,
get_supplier_service
)
from app.dependencies import get_db
from app.utils.auth import require_login, require_manager

supplier_router       = APIRouter(prefix="/suppliers",       tags=["Suppliers"])
customer_router       = APIRouter(prefix="/customers",       tags=["Customers"])
category_router       = APIRouter(prefix="/categories",      tags=["Categories"])
product_router        = APIRouter(prefix="/products",        tags=["Products"])
stock_movement_router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])
invoice_router        = APIRouter(prefix="/invoices",        tags=["Invoices"])


# ===========================================================================
# SUPPLIERS
# ===========================================================================
@supplier_router.get(
    "/", 
    response_model=list[SupplierResponse]
)
async def list_suppliers(
    current_user: dict = Depends(require_manager), 
    service: SupplierService = Depends(get_supplier_service)
    ):
    company_id = int(current_user["company_id"])
    return await service.get_all(company_id)

@supplier_router.get(
    "/{supplier_id}",
    response_model=SupplierResponse
)
async def get_supplier(
    supplier_id: int, 
    current_user: dict = Depends(require_manager), 
    service: SupplierService = Depends(get_supplier_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_by_id(supplier_id,company_id )

@supplier_router.post(
    "/", 
    response_model=SupplierResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_supplier(
    data: SupplierCreate = Depends(),
    avatar: UploadFile | None = File(None),
    current_user: dict = Depends(require_manager),
    service: SupplierService = Depends(get_supplier_service)
):
    company_id = int(current_user["company_id"])
    return await service.create(data, company_id, avatar)





@supplier_router.patch(
    "/{supplier_id}", 
    response_model=SupplierResponse
)
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate = Depends(),
    avatar: UploadFile | None = File(None),
    current_user: dict = Depends(require_manager),
    service: SupplierService = Depends(get_supplier_service)
):
    company_id = int(current_user["company_id"])
    return await  service.update(supplier_id, data, company_id, avatar)








@supplier_router.delete(
    "/{supplier_id}/avatar", 
    summary="Remove supplier avatar"
)
async def delete_supplier_avatar(
    supplier_id: int, 
    current_user: dict = Depends(require_manager), 
    service: SupplierService = Depends(get_supplier_service)
):
    company_id = int(current_user["company_id"])
    return await service.delete_avatar(supplier_id, company_id)

@supplier_router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int, 
    current_user: dict = Depends(require_manager), 
    service: SupplierService = Depends(get_supplier_service)
):
    company_id = int(current_user["company_id"])
    return await service.delete(supplier_id, company_id)

# ===========================================================================
# CUSTOMERS
# ===========================================================================

@customer_router.get(
    "/", 
    response_model=list[CustomerResponse]
)
async def list_customers(
    current_user: dict = Depends(require_login), 
    service: CustomerService = Depends(get_customer_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_all(company_id)




@customer_router.get(
    "/{customer_id}",
    response_model=CustomerResponse
)
async def get_customer(
    customer_id: int, 
    current_user: dict = Depends(require_login), 
    service: CustomerService = Depends(get_customer_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_by_id(customer_id, company_id)


@customer_router.post(
    "/", 
    response_model=CustomerResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_customer(
    data: CustomerCreate = Depends(),
    avatar: UploadFile | None = File(None),
    current_user: dict = Depends(require_login),
    service: CustomerService = Depends(get_customer_service),
):
    company_id = int(current_user["company_id"])
    return await service.create(data, company_id, avatar)



@customer_router.patch(
    "/{customer_id}", 
    response_model=CustomerResponse
)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate = Depends(),
    avatar: UploadFile | None = File(None),
    current_user: dict = Depends(require_login),
    service: CustomerService = Depends(get_customer_service),
):
    company_id = int(current_user["company_id"])
    return await service.update(customer_id,data, company_id, avatar)



@customer_router.delete(
    "/{customer_id}/avatar", 
    summary="Remove customer avatar"
)
async def delete_customer_avatar(
    customer_id: int, 
    current_user: dict = Depends(require_login), 
    service: CustomerService = Depends(get_customer_service),
):
    company_id = int(current_user["company_id"])
    return await service.delete_avatar(customer_id, company_id)


@customer_router.delete(
    "/{customer_id}"
)
async def delete_customer(
    customer_id: int, 
    current_user: dict = Depends(require_manager), 
    service: CustomerService = Depends(get_customer_service),

):
    company_id = int(current_user["company_id"])    
    return await service.delete(customer_id, company_id)


# ===========================================================================
# CATEGORIES
# ===========================================================================




@category_router.get(
    "/", 
    response_model=list[CategoryResponse]
    )
async def list_categories(
    current_user: dict = Depends(require_login), 
    service: CategoryService = Depends(get_category_service)
    ):
    company_id = int(current_user['company_id'])
    return await service.get_all(company_id)







@category_router.get(
    "/{category_id}", 
    response_model=CategoryResponse
    )
async def get_category(
    category_id: int, 
    current_user: dict = Depends(require_login), 
    service: CategoryService = Depends(get_category_service)
    ):
    company_id = int(current_user['company_id'])
    return await service.get_by_id(category_id, company_id)




@category_router.post(
    "/", 
    response_model=CategoryResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_category(
    data: CategoryCreate = Depends(),
    image: UploadFile | None = File(None),
    current_user: dict = Depends(require_manager),
    service: CategoryService = Depends(get_category_service)
):
    company_id = int(current_user['company_id'])
    return await  service.create(data, company_id, image)




@category_router.patch(
    "/{category_id}", 
    response_model=CategoryResponse
)
async def update_category(
    category_id: int,
    data: CategoryUpdate = Depends(),
    image: UploadFile | None = File(None),
    current_user: dict = Depends(require_manager),
    service: CategoryService = Depends(get_category_service)
):
    company_id = int(current_user['company_id'])
    return await  service.update(category_id, data, company_id, image)


@category_router.delete(
    "/{category_id}/image", 
    summary="Remove category image"
)
async def delete_category_image(
    category_id: int,
    current_user: dict = Depends(require_manager), 
    service: CategoryService = Depends(get_category_service)
):
    company_id = int(current_user['company_id'])
    return await  service.delete_image(category_id, company_id)


@category_router.delete(
        "/{category_id}"
)
async def delete_category(
    category_id: int, 
    current_user: dict = Depends(require_manager), 
    db: AsyncSession = Depends(get_db),
    service: CategoryService = Depends(get_category_service)

):
    company_id = int(current_user['company_id'])
    return await  service.delete(category_id, company_id)


# ===========================================================================
# PRODUCTS
# ===========================================================================


@product_router.get(
    "/", 
    response_model=list[ProductResponse]
    )
async def list_products(
    category_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_all(company_id, category_id)



@product_router.get(
        "/{product_id}", 
        response_model=ProductResponse
    )
async def get_product(
    product_id: int, 
    current_user: dict = Depends(require_login), 
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_by_id(product_id, company_id)


@product_router.post(
    "/", 
    response_model=ProductResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_product(
    data: ProductCreate, 
    current_user: dict = Depends(require_manager), 
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.create(data, company_id)

@product_router.patch(
    "/{product_id}", 
    response_model=ProductResponse
)
async def update_product(
    product_id: int, 
    data: ProductUpdate, 
    current_user: dict = Depends(require_manager), 
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.update(product_id, data, company_id)
# --- Product Images ---

@product_router.post(
    "/{product_id}/images", 
    status_code=status.HTTP_201_CREATED, 
    summary="Upload product image"
)
async def add_product_image(
    product_id: int,
    image: UploadFile = File(...),
    is_primary: bool = Form(False),
    sort_order: int  = Form(0),
    current_user: dict = Depends(require_manager),
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.add_image(product_id, company_id, image, is_primary, sort_order)

@product_router.patch(
    "/{product_id}/images/{image_id}/set-primary", 
    summary="Set primary product image")
async def set_primary_image(
    product_id: int,
    image_id: int,
    current_user: dict = Depends(require_manager),
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.set_primary_image(product_id, image_id, company_id)

@product_router.delete(
    "/{product_id}/images/{image_id}", 
    summary="Delete product image")
async def delete_product_image(
    product_id: int,
    image_id: int,
    current_user: dict = Depends(require_manager),
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await  service.delete_image(product_id, image_id, company_id)


@product_router.delete("/{product_id}")
async def delete_product(
    product_id: int, 
    current_user: dict = Depends(require_manager), 
    service: ProductService = Depends(get_product_service)
):
    company_id = int(current_user["company_id"])
    return await service.delete(product_id, company_id)






# ===========================================================================
# STOCK MOVEMENTS
# ===========================================================================

@stock_movement_router.get(
        "/", 
        response_model=list[StockMovementResponse],
        summary="Products ID")
async def list_movements(
    product_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    service: StockMovementService = Depends(get_stock_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_all(company_id, product_id)

@stock_movement_router.get(
        "/{movement_id}", 
        response_model=StockMovementResponse,
        summary="movement ID"
    )
async def get_movement(
    movement_id: int, 
    current_user: dict = Depends(require_login), 
    service: StockMovementService = Depends(get_stock_service)
    ):
    company_id = int(current_user["company_id"])
    return await service.get_by_id(movement_id, company_id)

@stock_movement_router.post(
    "/", 
    response_model=StockMovementResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create stock movement — auto updates product stock_quantity"
    )
async def create_movement(
    data: StockMovementCreate, 
    current_user: dict = Depends(require_manager), 
    service: StockMovementService = Depends(get_stock_service)
    ):
    company_id = int(current_user['company_id'])
    return await service.create(data, company_id)




@stock_movement_router.delete(
    "/{movement_id}"
    )
async def delete_movement(
    movement_id: int, 
    current_user: dict = Depends(require_manager), 
    service: StockMovementService = Depends(get_stock_service)

    ):
    company_id = int(current_user['company_id'])
    return await service.deletes(movement_id, company_id)



# ===========================================================================
# INVOICES with customer Id
# ===========================================================================

@invoice_router.get(
        "/", 
        response_model=list[InvoiceResponse], 
        summary="[User login only]")


async def list_invoices(
    customer_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_login),
    service: InvoiceService  = Depends(get_Invoice_service)
):
    company_id = int(current_user["company_id"])
    return await service.get_all(
        customer_id,
        company_id, 
        )



# ===========================================================================
# INVOICES  by Id
# ===========================================================================


@invoice_router.get(
    "/{invoice_id}", 
    response_model=InvoiceResponse
    )
async def get_invoice(
    invoice_id: int,
    current_user: dict = Depends(require_login), 
    service: InvoiceService = Depends(get_Invoice_service)
    ):
    company_id = int(current_user["company_id"])
    return await service.get_by_id(invoice_id, company_id)

# ===========================================================================
# INVOICES  CREATE 
# ===========================================================================

@invoice_router.post(
    "/", 
    response_model=InvoiceResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice — auto deducts product stock"
    )
async def create_invoice(
    data: InvoiceCreate, 
    current_user: dict = Depends(require_login), 
    service: InvoiceService = Depends(get_Invoice_service)
    ):
    company_id = int(current_user["company_id"])
    return await service.create(data, company_id)



@invoice_router.patch(
    "/{invoice_id}", 
    response_model=InvoiceResponse
)
async def update_invoice(
    invoice_id: int, 
    data: InvoiceUpdate, 
    current_user: dict = Depends(require_manager), 
    service: InvoiceService = Depends(get_Invoice_service)
    ):
    company_id   = int(current_user["company_id"])
    return await service.update(invoice_id, data, company_id)

# ========================================================================
# --- Invoice Attachments ---
# ========================================================================


@invoice_router.post(
    "/{invoice_id}/attachments", 
    status_code=status.HTTP_201_CREATED, 
    summary="Upload invoice attachment"
)
async def add_invoice_attachment(
    invoice_id: int,
    file: UploadFile = File(...),
    file_type: str | None = Form(None),
    current_user: dict = Depends(require_manager),
    service: InvoiceService = Depends(get_Invoice_service)
):
    company_id = int(current_user["company_id"])     
    return await service.add_attachment( invoice_id, company_id, file, file_type)


@invoice_router.delete(
    "/{invoice_id}/attachments/{attachment_id}", 
    summary="Delete invoice attachment"
    )
async def delete_invoice_attachment(
    invoice_id: int,
    attachment_id: int,
    current_user: dict = Depends(require_manager),
    service: InvoiceService = Depends(get_Invoice_service),
):
    company_id = int(current_user["company_id"])
    return await service.delete_attachment(invoice_id, attachment_id, company_id)


@invoice_router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int, 
    current_user: dict = Depends(require_manager), 
    service: InvoiceService = Depends(get_Invoice_service),
    ):
    company_id = int(current_user["company_id"])
    return await service.delete(invoice_id,  company_id)