from fastapi import HTTPException, UploadFile, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.dependencies import get_db, get_redis_client
import redis.asyncio as redis
from app.services.communication.notifications_service import NotificationService
from app.repositories.inventory.inventory_repository import (
    SupplierRepository,
    CustomerRepository,
    CategoryRepository,
    ProductRepository,
    StockMovementRepository,
    InvoiceRepository,
    InvoiceAttachmentRepository,
)
from app.models.invoices import Invoice
from app.schemas.schema import (
    SupplierCreate, SupplierUpdate,
    CustomerCreate, CustomerUpdate,
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    StockMovementCreate,
    InvoiceCreate, InvoiceUpdate,
)
from app.models.supplier import Supplier

from app.services.storage import CloudinaryStorage
storage = CloudinaryStorage()

# ===========================================================================
# SUPPLIER SERVICE Encapsulation  class
# ===========================================================================


class SupplierService:
    def __init__(
        self, 
        db: AsyncSession,
        repo = SupplierRepository
    ):
        self.repo = repo

    async def get_all(self, company_id: int):
        return await self.repo.get_all(company_id)
    






    async def get_by_id(self, supplier_id: int, company_id: int) -> Supplier:
        obj = await self.repo.get_by_id(supplier_id, company_id)
        if not obj:
            raise HTTPException(404, f"Supplier id={supplier_id} not found.")
        return obj








    async def create(self, data: SupplierCreate, company_id: int, avatar: UploadFile | None = None):
        payload = {**data.model_dump(), "company_id": company_id}

        if avatar:
            result = await storage.upload_image(avatar, folder=f"suppliers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.repo.create(payload)

    


    
    async def update(
        self,
        supplier_id: int,
        data: SupplierUpdate,
        company_id: int,
        avatar: UploadFile | None = None,
    ) -> Supplier:
        obj = await self.get_by_id(supplier_id, company_id)
        payload = data.model_dump(exclude_none=True)
        if avatar:
            if obj.avatar_public_id:
                await storage.delete_asset(obj.avatar_public_id)
            result = await storage.upload_image(avatar, folder=f"suppliers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]   

        return await self.repo.update(obj, payload)



    async def delete_avatar(self, supplier_id: int, company_id: int):
        """Remove avatar from Cloudinary and clear DB fields."""
        obj = await self.get_by_id(supplier_id, company_id)
        if not obj.avatar_public_id:
            raise HTTPException(404, "Supplier has no avatar.")

        await storage.delete_asset(obj.avatar_public_id)
        return await self.repo.update(obj, {"avatar_url": None, "avatar_public_id": None})




    async def delete(self, supplier_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(supplier_id, company_id)
        # Clean up Cloudinary avatar before deleting the record
        if obj.avatar_public_id:
            await storage.delete_asset(obj.avatar_public_id)

        await self.repo.delete(obj)
        return {"message": f"Supplier '{obj.name}' deleted."}


# ===========================================================================
# FACTORY
# ===========================================================================


async def get_supplier_service(
    db: AsyncSession = Depends(get_db)
) -> SupplierService:
    return SupplierService(
        db = db,
        repo = SupplierRepository(db),
    )





# ===========================================================================
# CUSTOMER SERVICE
# ===========================================================================

class CustomerService:
    def __init__(
        self, 
        db: AsyncSession,
        custom_repo: CustomerRepository,
        ):
        self.custom_repo = custom_repo

    async def get_all(self, company_id: int):
        return await self.custom_repo.get_all(company_id)

    async def get_by_id(self, customer_id: int, company_id: int):
        obj = await self.custom_repo.get_by_id(customer_id, company_id)
        if not obj:
            raise HTTPException(404, f"Customer id={customer_id} not found.")
        return obj

    async def create(self, data: CustomerCreate, company_id: int, avatar: UploadFile | None = None):
        payload = {**data.model_dump(), "company_id": company_id}

        if avatar:
            result = await storage.upload_image(avatar, folder=f"customers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.custom_repo.create(payload)

    async def update(
        self,
        customer_id: int,
        data: CustomerUpdate,
        company_id: int,
        avatar: UploadFile | None = None,
    ):
        obj = await self.get_by_id(customer_id, company_id)
        payload = data.model_dump(exclude_none=True)

        if avatar:
            if obj.avatar_public_id:
                await storage.delete_asset(obj.avatar_public_id)

            result = await storage.upload_image(avatar, folder=f"customers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.custom_repo.update(obj, payload)
    
    async def delete_avatar(self, customer_id: int, company_id: int):
        obj = await self.get_by_id(customer_id, company_id)
        if not obj.avatar_public_id:
            raise HTTPException(404, "Customer has no avatar.")

        await storage.delete_asset(obj.avatar_public_id)
        return await self.custom_repo.update(obj, {"avatar_url": None, "avatar_public_id": None})

    async def delete(self, customer_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(customer_id, company_id)

        if obj.avatar_public_id:
            await storage.delete_asset(obj.avatar_public_id)

        await self.custom_repo.delete(obj)
        return {"message": f"Customer '{obj.name}' deleted."}


# ===========================================================================
# FACTORY
# ===========================================================================

async def get_customer_service(
        db:  AsyncSession = Depends(get_db)
) -> CustomerService:
    return CustomerService(
        db = db,
        custom_repo = CustomerRepository(db)
    )


# ===========================================================================
# CATEGORY SERVICE
# ===========================================================================
class CategoryService:
    def __init__(
        self,
        db: AsyncSession, 
        cate_repo: CategoryRepository
        ):
        self.cate_repo = cate_repo



    async def get_all(self, company_id: int):
        return await self.cate_repo.get_all(company_id)




    async def get_by_id(self, category_id: int, company_id: int):
        obj = await self.cate_repo.get_by_id(category_id, company_id)
        if not obj:
            raise HTTPException(404, f"Category id={category_id} not found.")
        return obj


    async def create(self, data: CategoryCreate, company_id: int, image: UploadFile | None = None):
        payload = {**data.model_dump(), "company_id": company_id}

        if image:
            result = await storage.upload_image(image, folder=f"categories/{company_id}")
            payload["image_url"]       = result["secure_url"]
            payload["image_public_id"] = result["public_id"]

        return await self.cate_repo.create(payload)
    

    async def update(
        self,
        category_id: int,
        data: CategoryUpdate,
        company_id: int,
        image: UploadFile | None = None,
    ):
        obj = await self.get_by_id(category_id, company_id)
        payload = data.model_dump(exclude_none=True)

        if image:
            if obj.image_public_id:
                await storage.delete_asset(obj.image_public_id)

            result = await storage.upload_image(image, folder=f"categories/{company_id}")
            payload["image_url"]       = result["secure_url"]
            payload["image_public_id"] = result["public_id"]

        return await self.cate_repo.update(obj, payload)



    async def delete_image(self, category_id: int, company_id: int):
        obj = await self.get_by_id(category_id, company_id)
        if not obj.image_public_id:
            raise HTTPException(404, "Category has no image.")

        await storage.delete_asset(obj.image_public_id)
        return await self.cate_repo.update(obj, {"image_url": None, "image_public_id": None})




    async def delete(self, category_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(category_id, company_id)
        if obj.image_public_id:
            await storage.delete_asset(obj.image_public_id)
        await self.cate_repo.delete(obj)
        return {"message": f"Category '{obj.category_name}' deleted."}
    



# ===========================================================================
# FACTORY
# ===========================================================================

async def get_category_service(
        db: AsyncSession = Depends(get_db)
) -> CategoryService:
    return CategoryService(
        db = db,
        cate_repo=CategoryRepository(db)
    )




# ===========================================================================
# PRODUCT SERVICE
# ===========================================================================

class ProductService:
    def __init__(
        self, 
        db: AsyncSession,
        product_repo: ProductRepository,
        ):
        self.product_repo=product_repo

    async def get_all(self, company_id: int, category_id: int | None = None):
        return await self.product_repo.get_all(company_id, category_id)

    async def get_by_id(self, product_id: int, company_id: int):
        obj = await self.product_repo.get_by_id(product_id, company_id)
        if not obj:
            raise HTTPException(404, f"Product id={product_id} not found.")
        return obj

    async def create(self, data: ProductCreate, company_id: int):
        """Create product (no image here — images are added via add_image)."""
        return await self.product_repo.create({**data.model_dump(), "company_id": company_id})

    async def update(self, product_id: int, data: ProductUpdate, company_id: int):
        obj = await self.get_by_id(product_id, company_id)
        return await self.product_repo.update(obj, data.model_dump(exclude_none=True))

    # -------------------------------------------------------------------------
    # Product Images  (product_images table — multi-image)
    # -------------------------------------------------------------------------
    async def add_image(
        self,
        product_id: int,
        company_id: int,
        image: UploadFile,
        is_primary: bool = False,
        sort_order: int = 0,
    ):
        """Upload a new image and attach it to the product."""
        await self.get_by_id(product_id, company_id)   # ensure product exists

        result = await storage.upload_image(image, folder=f"products/{company_id}/{product_id}")

        return await self.product_repo.create_image({
            "company_id":  company_id,
            "product_id":  product_id,
            "image_url":   result["secure_url"],
            "public_id":   result["public_id"],
            "is_primary":  is_primary,
            "sort_order":  sort_order,
        })

    async def set_primary_image(self, product_id: int, image_id: int, company_id: int):
        """
        Mark one image as primary and demote all others.
        Raises 404 if the image doesn't belong to this product/company.
        """
        img = await self.product_repo.get_image_by_id(image_id, product_id, company_id)
        if not img:
            raise HTTPException(404, f"Product image id={image_id} not found.")

        await self.product_repo.clear_primary_flags(product_id, company_id)
        return await self.product_repo.update_image(img, {"is_primary": True})

    async def delete_image(self, product_id: int, image_id: int, company_id: int) -> dict:
        """Delete a single product image from Cloudinary and the DB."""
        img = await self.product_repo.get_image_by_id(image_id, product_id, company_id)
        if not img:
            raise HTTPException(404, f"Product image id={image_id} not found.")

        await storage.delete_asset(img.public_id)
        await self.product_repo.delete_image(img)
        return {"message": f"Product image id={image_id} deleted."}

    async def delete(self, product_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(product_id, company_id)

        # Delete all Cloudinary images for this product
        images = await self.product_repo.get_all_images(product_id, company_id)
        for img in images:
            await storage.delete_asset(img.public_id)

        await self.product_repo.delete(obj)
        return {"message": f"Product '{obj.name}' deleted."}
    
# ===========================================================================
# FACTORY
# ===========================================================================

async def get_product_service(
    db:  AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
)-> ProductService:
    return ProductService(
        db     = db,
        product_repo  =   ProductRepository(db),
        redis_client  = redis_client
    )

# ===========================================================================
# STOCK MOVEMENT SERVICE
# ===========================================================================

class StockMovementService:
    def __init__(
        self, 
        db: AsyncSession,
        repo_stock: StockMovementRepository,
        product_repo: ProductRepository,
        redis_client: redis.Redis,
    ):
        self.repo_stock = repo_stock  
        self.product_repo = product_repo

        self.notify = NotificationService(
            db=db,
            redis_client=redis_client
        )

    async def get_all(self, company_id: int, product_id: int | None = None):
        return await self.repo_stock.get_all(company_id, product_id)
    
    async def get_by_id(self, movement_id: int, company_id: int):
        obj = await self.repo_stock.get_by_id(movement_id, company_id)
        if not obj:
            raise HTTPException(404, f"Movement id={movement_id} not found.")
        return obj
    
    async def create(self, data: StockMovementCreate, company_id: int):
        product = await self.product_repo.get_by_id(data.product_id, company_id)
        if not product:
            raise HTTPException(404, f"Product id={data.product_id} not found.")

        opening_balance = product.stock_quantity
        new_balance     = opening_balance + data.qty_in - data.qty_out

        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Current balance: {opening_balance}",
            )

        movement = await self.repo_stock.create({
            **data.model_dump(),
            "company_id":       company_id,
            "opening_balance":  opening_balance,
            "balance_quantity": new_balance,
        })

        await self.product_repo.update_stock(product, data.qty_in - data.qty_out)
        return movement

    async def deletes(self, movement_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(movement_id, company_id)
        await self.repo_stock.deleted(obj)
        return {"message": f"Movement id={movement_id} deleted."}

# ===========================================================================
# FACTORY
# ===========================================================================

async def get_stock_service(
    db:       AsyncSession =  Depends(get_db),
    redis_client:  redis.Redis = Depends(get_redis_client),

    ) -> StockMovementService:
    return StockMovementService(
        db            = db,
        repo_stock    = StockMovementRepository(db),
        product_repo  =   ProductRepository(db),
        redis_client  = redis_client,
    )

# ===========================================================================
# INVOICE SERVICE
# ===========================================================================

class InvoiceService:
    def __init__(
            self, 
            db: AsyncSession,
            repo:     InvoiceRepository,
            product_repo: ProductRepository,
            invoice_attach_repo: InvoiceAttachmentRepository,
            redis_client: redis.Redis,
            ):
            self.repo         = repo
            self.product_repo = product_repo
            self.invoice_attach_repo = invoice_attach_repo
            self.notify       = NotificationService(
                db             = db,
                redis_client  = redis_client,
            )
    # -----------------------------------------------------------------------
    # GET all
    # -----------------------------------------------------------------------
    async def get_all(self, company_id: int, customer_id: int) -> list[Invoice]:
        return await self.repo.get_all(company_id, customer_id)
    
    # -----------------------------------------------------------------------
    # GET by id
    # -----------------------------------------------------------------------
    async def get_by_id(self, invoice_id: int, company_id: int) -> Invoice:
        obj = await self.repo.get_by_id(invoice_id, company_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Invoice id={invoice_id} not found.',
            )
        return obj
    # -----------------------------------------------------------------------
    # GET by user_id
    # -----------------------------------------------------------------------
    async def create(self, data: InvoiceCreate, company_id: int):
        invoice = await self.repo.create({
            "company_id":   company_id,
            "customer_id":  data.customer_id,
            "staff_id":     data.staff_id,
            "total_amount": data.total_amount,
            "discount":     data.discount,
            "tax":          data.tax,
            "payment_type": data.payment_type,
        })

        for item in data.items:
            await self.repo.create_item({
                "company_id":  company_id,
                "invoice_id":  invoice.invoice_id,
                "product_id":  item.product_id,
                "quantity":    item.quantity,
                "unit_price":  item.unit_price,
                "total_price": Decimal(str(item.quantity)) * item.unit_price,
            })
            product = await self.product_repo.get_by_id(item.product_id, company_id)
            if product:
                await self.product_repo.update_stock(product, -item.quantity)

        return await self.repo.commit_and_refresh(invoice)


    async def update(self, invoice_id: int, data: InvoiceUpdate, company_id: int):
        obj = await self.get_by_id(invoice_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    # -------------------------------------------------------------------------
    # Invoice Attachments  (invoice_attachments table)
    # -------------------------------------------------------------------------

    async def add_attachment(
        self,
        invoice_id: int,
        company_id: int,
        file: UploadFile,
        file_type: str | None = None,
    ):
        """Upload a file attachment and link it to the invoice."""
        await self.get_by_id(invoice_id, company_id)   

        result = await storage.upload_image(file, folder=f"invoices/{company_id}/{invoice_id}")

        return await self.invoice_attach_repo.create({
            "company_id":  company_id,
            "invoice_id":  invoice_id,
            "file_url":    result["secure_url"],
            "public_id":   result["public_id"],
            "file_name":   file.filename,
            "file_type":   file_type or file.content_type,
        })
    



    async def delete_attachment(self, invoice_id: int, attachment_id: int, company_id: int) -> dict:
        """Delete a single invoice attachment from Cloudinary and the DB."""
        att = await self.invoice_attach_repo.get_by_id(attachment_id, invoice_id, company_id)
        if not att:
            raise HTTPException(404, f"Attachment id={attachment_id} not found.")

        await storage.delete_asset(att.public_id)

        await self.invoice_attach_repo.delete_all_by_invoice(att)

        return {"message": f"Attachment id={attachment_id} deleted."}
    






    async def delete(self, invoice_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(invoice_id, company_id)

        # Delete all Cloudinary attachments for this invoice
        attachments = await self.invoice_attach_repo.get_all(invoice_id, company_id)
        for att in attachments:
            await storage.delete_asset(att.public_id)

        await self.repo.delete(obj)
        return {"message": f"Invoice id={invoice_id} deleted."}

# ===========================================================================
# FACTORY
# ===========================================================================

async def get_Invoice_service(
        db:       AsyncSession =  Depends(get_db),
        redis_client:  redis.Redis = Depends(get_redis_client),
)-> InvoiceService:
    return InvoiceService(
        db           = db,
        repo         = InvoiceRepository(db),
        product_repo = ProductRepository(db),
        invoice_attach_repo = InvoiceAttachmentRepository(db),
        redis_client = redis_client,
    )

















