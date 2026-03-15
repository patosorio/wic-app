"""Commerce routes: orders and Stripe webhook."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.exceptions import CampaignNotActiveError, InsufficientCapacityError
from core.firebase_auth import FirebaseUser, UserRole, require_role

from platform_api.auth.service import get_user_by_firebase_uid
from platform_api.commerce.models import OrderCreateRequest, OrderResponse
from platform_api.commerce.service import (
    create_order,
    get_order,
    handle_stripe_webhook,
)
from platform_api.commerce.stripe_client import construct_webhook_event

router = APIRouter(prefix="/orders", tags=["orders"])
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/", response_model=OrderResponse)
async def post_order(
    body: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: FirebaseUser = Depends(require_role(UserRole.CUSTOMER)),
) -> OrderResponse:
    """Create pre-order. Requires auth. Returns order with client_secret for Stripe Elements."""
    db_user = await get_user_by_firebase_uid(user.uid, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered. Call POST /auth/register first.",
        )
    try:
        order, client_secret = await create_order(
            campaign_id=body.campaign_id,
            customer_id=db_user.id,
            db=db,
        )
    except CampaignNotActiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        )
    except InsufficientCapacityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    response = OrderResponse.model_validate(order)
    response.client_secret = client_secret
    return response


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_route(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: FirebaseUser = Depends(require_role(UserRole.CUSTOMER)),
) -> OrderResponse:
    """Get order by id. Only the customer who placed it can access."""
    db_user = await get_user_by_firebase_uid(user.uid, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered.",
        )
    order = await get_order(order_id, db)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.customer_id != db_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your order",
        )
    return OrderResponse.model_validate(order)


@webhook_router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Stripe webhook endpoint. No auth; verified via Stripe signature.
    When DEV_SKIP_STRIPE, accepts raw JSON for local testing.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = construct_webhook_event(payload, sig_header)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature or payload",
        )

    await handle_stripe_webhook(event, db)
    return {"status": "ok"}
