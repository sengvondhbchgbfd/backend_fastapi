from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.exceptions.exceptions import NotFoundException

from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.category import Category
from app.models.products.product import Product
from app.models.products.product_image import ProductImage
from app.models.products.stock_movement import StockMovement
from app.models.invoices.invoice import Invoice
from app.models.invoices.invoice_item import InvoiceItem
from app.models.invoices.invoice_attachments import InvoiceAttachment


# ===========================================================================
# SUPPLIER
# ===========================================================================

class SupplierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

        

    async def get_all(self, company_id: int) -> list[Supplier]:
        r = await self.db.execute(
            select(Supplier)
            .where(Supplier.company_id == company_id)
            .order_by(Supplier.name)
        )
        return r.scalars().all()
    



    async def get_by_id(self, supplier_id: int, company_id: int) -> Supplier | None:
        r = await self.db.execute(
            select(Supplier).where(
                Supplier.supplier_id == supplier_id,
                Supplier.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()
    

    
    
    async def get_by_id(self, supplier_id: int, company_id: int) -> Supplier:
        r = await self.db.execute(
            select(Supplier).where(
                Supplier.supplier_id == supplier_id,
                Supplier.company_id  == company_id,
            )
        )
        obj = r.scalar_one_or_none()
        if obj is None:
            raise NotFoundException(f"Supplier {supplier_id} not found")
        return obj
    






    async def create(self, data: dict) -> Supplier:
        obj = Supplier(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Supplier, data: dict) -> Supplier:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    



    async def delete(self, obj: Supplier) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# CUSTOMER
# ===========================================================================

class CustomerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int) -> list[Customer]:
        r = await self.db.execute(
            select(Customer)
            .where(Customer.company_id == company_id)
            .order_by(Customer.name)
        )
        return r.scalars().all()

    async def get_by_id(self, customer_id: int, company_id: int) -> Customer | None:
        r = await self.db.execute(
            select(Customer).where(
                Customer.customer_id == customer_id,
                Customer.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Customer:
        obj = Customer(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Customer, data: dict) -> Customer:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Customer) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# CATEGORY
# ===========================================================================

class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int) -> list[Category]:
        r = await self.db.execute(
            select(Category)
            .where(Category.company_id == company_id)
            .order_by(Category.category_name)
        )
        return r.scalars().all()

    async def get_by_id(self, category_id: int, company_id: int) -> Category | None:
        r = await self.db.execute(
            select(Category).where(
                Category.category_id == category_id,
                Category.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Category:
        obj = Category(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Category, data: dict) -> Category:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Category) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# PRODUCT
# ===========================================================================

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int, category_id: int | None = None) -> list[Product]:
        query = (
            select(Product)
            .where(Product.company_id == company_id)
            .order_by(Product.name)
        )
        if category_id:
            query = query.where(Product.category_id == category_id)
        r = await self.db.execute(query)
        return r.scalars().all()

    async def get_by_id(self, product_id: int, company_id: int) -> Product | None:
        r = await self.db.execute(
            select(Product).where(
                Product.product_id == product_id,
                Product.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Product:
        obj = Product(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Product, data: dict) -> Product:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Product) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    async def update_stock(self, product: Product, qty_change: int) -> Product:
        product.stock_quantity += qty_change
        await self.db.commit()
        await self.db.refresh(product)
        return product

    # --- product_images ---

    async def get_all_images(self, product_id: int, company_id: int) -> list[ProductImage]:
        r = await self.db.execute(
            select(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
            .order_by(ProductImage.sort_order)
        )
        return r.scalars().all()

    async def get_image_by_id(self, image_id: int, product_id: int, company_id: int) -> ProductImage | None:
        r = await self.db.execute(
            select(ProductImage).where(
                ProductImage.image_id   == image_id,
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create_image(self, data: dict) -> ProductImage:
        obj = ProductImage(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update_image(self, obj: ProductImage, data: dict) -> ProductImage:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def clear_primary_flags(self, product_id: int, company_id: int) -> None:
        """Set is_primary=False on all images for this product before promoting a new one."""
        await self.db.execute(
            update(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
            .values(is_primary=False)
        )
        await self.db.commit()

    async def delete_image(self, obj: ProductImage) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# STOCK MOVEMENT
# ===========================================================================




class StockMovementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_all(self, company_id: int, product_id: int | None = None) -> list[StockMovement]:
        query = (
            select(StockMovement)
            .where(StockMovement.company_id == company_id)
            .order_by(StockMovement.date.desc())
        )
        if product_id:
            query = query.where(StockMovement.product_id == product_id)
        r = await self.db.execute(query)
        return r.scalars().all()
    
    async def get_by_id(self, movement_id: int, company_id: int) -> StockMovement | None:
        r = await self.db.execute(
            select(StockMovement).where(
                StockMovement.movement_id == movement_id,
                StockMovement.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()
    
    async def create(self, data: dict) -> StockMovement:
        obj = StockMovement(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def deleted(self, obj: StockMovement) -> None:
        await self.db.delete(obj)
        await self.db.commit()





# ===========================================================================
# INVOICE
# ===========================================================================

class InvoiceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int, customer_id: int | None = None) -> list[Invoice]:
        query = (
            select(Invoice)
            .where(Invoice.company_id == company_id)
            .order_by(Invoice.created_at.desc())
        )
        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)
        r = await self.db.execute(query)
        return r.scalars().all()

    async def get_by_id(self, invoice_id: int, company_id: int) -> Invoice | None:
        r = await self.db.execute(
            select(Invoice).where(
                Invoice.invoice_id == invoice_id,
                Invoice.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Invoice:
        obj = Invoice(**data)
        self.db.add(obj)
        await self.db.flush()   # get invoice_id without committing (items added next)
        return obj

    async def create_item(self, data: dict) -> InvoiceItem:
        obj = InvoiceItem(**data)
        self.db.add(obj)
        return obj              # caller does commit_and_refresh after all items

    async def commit_and_refresh(self, obj: Invoice) -> Invoice:
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Invoice, data: dict) -> Invoice:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Invoice) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# INVOICE ATTACHMENT
# ===========================================================================

class InvoiceAttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_all(self, invoice_id: int, company_id: int) -> list[InvoiceAttachment]:
        r = await self.db.execute(
            select(InvoiceAttachment)
            .where(
                InvoiceAttachment.invoice_id == invoice_id,
                InvoiceAttachment.company_id == company_id,
            )
            .order_by(InvoiceAttachment.created_at.desc())
        )
        return r.scalars().all()


    async def get_by_id(
        self, attachment_id: int, invoice_id: int, company_id: int
    ) -> InvoiceAttachment | None:
        r = await self.db.execute(
            select(InvoiceAttachment).where(
                InvoiceAttachment.attachment_id == attachment_id,
                InvoiceAttachment.invoice_id    == invoice_id,
                InvoiceAttachment.company_id    == company_id,
            )
        )
        return r.scalar_one_or_none()
    


    async def create(self, data: dict) -> InvoiceAttachment:
        obj = InvoiceAttachment(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj




    async def delete(self, obj: InvoiceAttachment) -> None:
        await self.db.delete(obj)
        await self.db.commit()




    async def delete_all_by_invoice(self, invoice_id: int, company_id: int) -> list[str]:
        """
        Fetches all public_ids for Cloudinary cleanup, then bulk-deletes all
        attachment rows. Called by the service before deleting an invoice.
        """
        attachments = await self.get_all(invoice_id, company_id)
        public_ids  = [a.public_id for a in attachments]
        for att in attachments:
            await self.db.delete(att)
        await self.db.commit()
        return public_ids
    

    