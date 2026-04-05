from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.config import settings
from app.models import ExchangeRate, ExchangeRateSource
from app.schemas import ExchangeRateResponse

router = APIRouter(prefix="/currency", tags=["currency"])

TENANT_ID = 1


async def _fetch_frankfurter_rate(currency: str, rate_date: date) -> Decimal:
    """Fetch exchange rate from Frankfurter API and convert to GBP rate."""
    url = settings.FRANKFURTER_API_URL
    params = {
        "from": currency,
        "to": "GBP",
        "date": str(rate_date),
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch exchange rate from Frankfurter API: {response.status_code}",
        )

    data = response.json()

    # Frankfurter v2 returns rates nested under the date key or directly
    # Handle both formats
    rates = data.get("rates", {})
    if isinstance(rates, dict):
        # Could be {date: {GBP: rate}} or {GBP: rate}
        if "GBP" in rates:
            return Decimal(str(rates["GBP"]))
        # Try nested date format
        for date_key, date_rates in rates.items():
            if isinstance(date_rates, dict) and "GBP" in date_rates:
                return Decimal(str(date_rates["GBP"]))

    raise HTTPException(
        status_code=502,
        detail="Unexpected response format from Frankfurter API",
    )


@router.get("/rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    currency: str,
    rate_date: date,
    db: Session = Depends(get_db),
):
    """
    Get exchange rate for a currency to GBP on a specific date.
    Checks the local cache first, then fetches from Frankfurter API.
    """
    currency = currency.upper()

    if currency == "GBP":
        return ExchangeRateResponse(
            currency="GBP",
            date=rate_date,
            rate_to_gbp=Decimal("1.0"),
            source="local",
        )

    # Check cache
    cached = (
        db.query(ExchangeRate)
        .filter(
            ExchangeRate.currency == currency,
            ExchangeRate.date == rate_date,
        )
        .first()
    )

    if cached is not None:
        return ExchangeRateResponse(
            currency=cached.currency,
            date=cached.date,
            rate_to_gbp=cached.rate_to_gbp,
            source=str(cached.source.value) if hasattr(cached.source, "value") else str(cached.source),
        )

    # Fetch from Frankfurter API
    rate_to_gbp = await _fetch_frankfurter_rate(currency, rate_date)

    # Cache the result
    new_rate = ExchangeRate(
        currency=currency,
        date=rate_date,
        rate_to_gbp=rate_to_gbp,
        source=ExchangeRateSource.frankfurter,
    )
    db.add(new_rate)
    db.commit()
    db.refresh(new_rate)

    return ExchangeRateResponse(
        currency=new_rate.currency,
        date=new_rate.date,
        rate_to_gbp=new_rate.rate_to_gbp,
        source="frankfurter",
    )


@router.get("/rates")
def list_cached_rates(
    currency: str = None,
    db: Session = Depends(get_db),
):
    """List all cached exchange rates, optionally filtered by currency."""
    query = db.query(ExchangeRate)

    if currency is not None:
        query = query.filter(ExchangeRate.currency == currency.upper())

    rates = query.order_by(ExchangeRate.date.desc()).limit(100).all()

    return [
        ExchangeRateResponse(
            currency=r.currency,
            date=r.date,
            rate_to_gbp=r.rate_to_gbp,
            source=str(r.source.value) if hasattr(r.source, "value") else str(r.source),
        )
        for r in rates
    ]
