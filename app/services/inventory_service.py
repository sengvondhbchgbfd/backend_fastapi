from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date

from app.repositories.inventory_repository import (
    SupplierRepository,
    CustomerRepository,
    CategoryRepository,
    ProductRepository,
    StockMovementRepository,
    InvoiceRepository,
)
from app.schemas.schema import (
    SupplierCreate, SupplierUpdate,
    CustomerCreate, CustomerUpdate,
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    StockMovementCreate,
    InvoiceCreate, InvoiceUpdate,
)


# ===========================================================================
# SUPPLIER SERVICE
# ===========================================================================

class SupplierService:
    def __init__(self, db: AsyncSession):
        self.repo = SupplierRepository(db)

    async def get_all(self, company_id: int): return await self.repo.get_all(company_id)

    async def get_by_id(self, supplier_id: int, company_id: int):
        obj = await self.repo.get_by_id(supplier_id, company_id)
        if not obj: raise HTTPException(404, f"Supplier id={supplier_id} not found.")
        return obj
    
    async def create(self, data: SupplierCreate, company_id: int):
        return await self.repo.create({**data.model_dump(), "company_id": company_id})

    async def update(self, supplier_id: int, data: SupplierUpdate, company_id: int):
        obj = await self.get_by_id(supplier_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, supplier_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(supplier_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Supplier '{obj.name}' deleted."}

# ===========================================================================
# CUSTOMER SERVICE
# ===========================================================================

class CustomerService:
    def __init__(self, db: AsyncSession):
        self.repo = CustomerRepository(db)

    async def get_all(self, company_id: int): return await self.repo.get_all(company_id)

    async def get_by_id(self, customer_id: int, company_id: int):
        obj = await self.repo.get_by_id(customer_id, company_id)
        if not obj: raise HTTPException(404, f"Customer id={customer_id} not found.")
        return obj

    async def create(self, data: CustomerCreate, company_id: int):
        return await self.repo.create({**data.model_dump(), "company_id": company_id})




    async def update(self, customer_id: int, data: CustomerUpdate, company_id: int):
        obj = await self.get_by_id(customer_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, customer_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(customer_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Customer '{obj.name}' deleted."}


# ===========================================================================
# CATEGORY SERVICE
# ===========================================================================

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def get_all(self, company_id: int): return await self.repo.get_all(company_id)

    async def get_by_id(self, category_id: int, company_id: int):
        obj = await self.repo.get_by_id(category_id, company_id)
        if not obj: raise HTTPException(404, f"Category id={category_id} not found.")
        return obj

    async def create(self, data: CategoryCreate, company_id: int):
        return await self.repo.create({**data.model_dump(), "company_id": company_id})

    async def update(self, category_id: int, data: CategoryUpdate, company_id: int):
        obj = await self.get_by_id(category_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, category_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(category_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Category '{obj.category_name}' deleted."}


# ===========================================================================
# PRODUCT SERVICE
# ===========================================================================

class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)

    async def get_all(self, company_id: int, category_id: int | None = None):
        return await self.repo.get_all(company_id, category_id)

    async def get_by_id(self, product_id: int, company_id: int):
        obj = await self.repo.get_by_id(product_id, company_id)
        if not obj: raise HTTPException(404, f"Product id={product_id} not found.")
        return obj

    async def create(self, data: ProductCreate, company_id: int):
        return await self.repo.create({**data.model_dump(), "company_id": company_id})

    async def update(self, product_id: int, data: ProductUpdate, company_id: int):
        obj = await self.get_by_id(product_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, product_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(product_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Product '{obj.name}' deleted."}


# ===========================================================================
# STOCK MOVEMENT SERVICE
# ===========================================================================

class StockMovementService:
    def __init__(self, db: AsyncSession):
        self.repo         = StockMovementRepository(db)
        self.product_repo = ProductRepository(db)

    async def get_all(self, company_id: int, product_id: int | None = None):
        return await self.repo.get_all(company_id, product_id)

    async def get_by_id(self, movement_id: int, company_id: int):
        obj = await self.repo.get_by_id(movement_id, company_id)
        if not obj: raise HTTPException(404, f"Movement id={movement_id} not found.")
        return obj



    async def create(self, data: StockMovementCreate, company_id: int):
        # Verify product exists
        product = await self.product_repo.get_by_id(data.product_id, company_id)
        if not product:
            raise HTTPException(404, f"Product id={data.product_id} not found.")
        
        # opening_balance = stock BEFORE this movement
        
        opening_balance = product.stock_quantity


        # use product.stock_quantity not get_balance() — already accurate
        new_balance = opening_balance + data.qty_in - data.qty_out

        if new_balance < 0:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current balance: {opening_balance}",
        )

        # Save movement
        movement = await self.repo.create({
            **data.model_dump(),
            "company_id":       company_id,
            "opening_balance": opening_balance,
            "balance_quantity": new_balance,
        })

        # Update product stock_quantity
        await self.product_repo.update_stock(
            product,
            data.qty_in - data.qty_out,
        )
        return movement
    



    async def delete(self, movement_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(movement_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Movement id={movement_id} deleted."}


# ===========================================================================
# INVOICE SERVICE
# ===========================================================================

class InvoiceService:
    def __init__(self, db: AsyncSession):
        self.repo         = InvoiceRepository(db)
        self.product_repo = ProductRepository(db)

    async def get_all(self, company_id: int, customer_id: int | None = None):
        return await self.repo.get_all(company_id, customer_id)

    async def get_by_id(self, invoice_id: int, company_id: int):
        obj = await self.repo.get_by_id(invoice_id, company_id)
        if not obj: raise HTTPException(404, f"Invoice id={invoice_id} not found.")
        return obj

    async def create(self, data: InvoiceCreate, company_id: int):
        # Create invoice
        invoice = await self.repo.create({
            "company_id":   company_id,
            "customer_id":  data.customer_id,
            "staff_id":     data.staff_id,
            "total_amount": data.total_amount,
            "discount":     data.discount,
            "tax":          data.tax,
            "payment_type": data.payment_type,
        })

        # Create invoice items + deduct stock
        for item in data.items:
            await self.repo.create_item({
                "company_id":  company_id,
                "invoice_id":  invoice.invoice_id,
                "product_id":  item.product_id,
                "quantity":    item.quantity,
                "unit_price":  item.unit_price,
                "total_price": Decimal(str(item.quantity)) * item.unit_price,
            })
            # Deduct from stock
            product = await self.product_repo.get_by_id(item.product_id, company_id)
            if product:
                await self.product_repo.update_stock(product, -item.quantity)

        return await self.repo.commit_and_refresh(invoice)

    async def update(self, invoice_id: int, data: InvoiceUpdate, company_id: int):
        obj = await self.get_by_id(invoice_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, invoice_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(invoice_id, company_id)
        await self.repo.delete(obj)
        return {"message": f"Invoice id={invoice_id} deleted."}