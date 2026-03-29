"""MCP tool definitions for flight search — wraps fli's Python API directly."""

from typing import Any, Optional

from fastmcp import FastMCP

flights_mcp = FastMCP("flights")


@flights_mcp.tool()
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    departure_window: Optional[str] = None,
    airlines: Optional[list[str]] = None,
    cabin_class: str = "ECONOMY",
    max_stops: str = "ANY",
    sort_by: str = "CHEAPEST",
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    max_price: Optional[int] = None,
    max_duration: Optional[int] = None,
    layover_airports: Optional[list[str]] = None,
    max_layover_duration: Optional[int] = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Search for flights between two airports on a specific date.

    Args:
        origin: Departure airport IATA code (e.g., 'JFK', 'LIS')
        destination: Arrival airport IATA code (e.g., 'LHR', 'BCN')
        departure_date: Travel date (YYYY-MM-DD)
        return_date: Return date for round-trip (YYYY-MM-DD), omit for one-way
        departure_window: Departure time window in 'HH-HH' 24h format (e.g., '6-20')
        airlines: Filter by airline IATA codes (e.g., ['BA', 'TP'])
        cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
        max_stops: ANY, NON_STOP, ONE_STOP, or TWO_PLUS_STOPS
        sort_by: CHEAPEST, DURATION, DEPARTURE_TIME, or ARRIVAL_TIME
        adults: Number of adult passengers (default: 1)
        children: Number of child passengers (default: 0)
        infants_in_seat: Number of infants in seat (default: 0)
        infants_on_lap: Number of infants on lap (default: 0)
        max_price: Maximum price in USD (omit for no limit)
        max_duration: Maximum total flight duration in minutes (omit for no limit)
        layover_airports: Restrict layovers to these airports (IATA codes)
        max_layover_duration: Maximum layover duration in minutes
        top_n: For round trips, how many outbound flights to search returns for (default: 5)
    """
    from fli.core import (
        build_flight_segments,
        build_time_restrictions,
        parse_airlines,
        parse_cabin_class,
        parse_max_stops,
        parse_sort_by,
        resolve_airport,
    )
    from fli.models import (
        FlightSearchFilters,
        LayoverRestrictions,
        PassengerInfo,
        PriceLimit,
        TripType,
    )
    from fli.search import SearchFlights

    origin_ap = resolve_airport(origin)
    dest_ap = resolve_airport(destination)
    seat = parse_cabin_class(cabin_class)
    stops = parse_max_stops(max_stops)
    sort = parse_sort_by(sort_by)
    airline_list = parse_airlines(airlines)
    time_r = build_time_restrictions(departure_window) if departure_window else None

    segments, trip_type = build_flight_segments(
        origin=origin_ap,
        destination=dest_ap,
        departure_date=departure_date,
        return_date=return_date,
        time_restrictions=time_r,
    )

    price_limit = PriceLimit(max_price=max_price) if max_price else None

    layover_r = None
    if layover_airports or max_layover_duration:
        layover_r = LayoverRestrictions(
            airports=[resolve_airport(a) for a in layover_airports] if layover_airports else None,
            max_duration=max_layover_duration,
        )

    filters = FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
        ),
        flight_segments=segments,
        stops=stops,
        seat_type=seat,
        airlines=airline_list,
        sort_by=sort,
        price_limit=price_limit,
        max_duration=max_duration,
        layover_restrictions=layover_r,
    )

    client = SearchFlights()
    results = client.search(filters, top_n=top_n)

    if not results:
        return {"flights": [], "count": 0, "trip_type": trip_type.name}

    is_rt = trip_type == TripType.ROUND_TRIP

    def serialize_leg(leg):
        return {
            "airline": str(leg.airline.name),
            "flight_number": leg.flight_number,
            "departure_airport": str(leg.departure_airport.name),
            "arrival_airport": str(leg.arrival_airport.name),
            "departure_time": str(leg.departure_datetime),
            "arrival_time": str(leg.arrival_datetime),
            "duration_min": leg.duration,
        }

    flights = []
    for f in results:
        if is_rt and isinstance(f, tuple):
            out, ret = f
            flights.append({
                "price": out.price + ret.price,
                "outbound_legs": [serialize_leg(l) for l in out.legs],
                "return_legs": [serialize_leg(l) for l in ret.legs],
            })
        else:
            flights.append({
                "price": f.price,
                "duration_min": f.duration,
                "stops": f.stops,
                "legs": [serialize_leg(l) for l in f.legs],
            })

    return {"flights": flights, "count": len(flights), "trip_type": trip_type.name}


@flights_mcp.tool()
def search_dates(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    trip_duration: int = 3,
    is_round_trip: bool = False,
    airlines: Optional[list[str]] = None,
    cabin_class: str = "ECONOMY",
    max_stops: str = "ANY",
    departure_window: Optional[str] = None,
    sort_by_price: bool = True,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
) -> dict[str, Any]:
    """Find the cheapest travel dates between two airports within a date range.

    Args:
        origin: Departure airport IATA code (e.g., 'LIS')
        destination: Arrival airport IATA code (e.g., 'BCN')
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)
        trip_duration: Trip duration in days (for round-trip, default: 3)
        is_round_trip: Search for round-trip flights (default: false)
        airlines: Filter by airline IATA codes (e.g., ['TP', 'BA'])
        cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
        max_stops: ANY, NON_STOP, ONE_STOP, or TWO_PLUS_STOPS
        departure_window: Departure time window in 'HH-HH' 24h format (e.g., '6-20')
        sort_by_price: Sort results by price lowest-first (default: true)
        adults: Number of adult passengers (default: 1)
        children: Number of child passengers (default: 0)
        infants_in_seat: Number of infants in seat (default: 0)
        infants_on_lap: Number of infants on lap (default: 0)
    """
    from fli.core import (
        build_date_search_segments,
        build_time_restrictions,
        parse_airlines,
        parse_cabin_class,
        parse_max_stops,
        resolve_airport,
    )
    from fli.models import DateSearchFilters, PassengerInfo
    from fli.search import SearchDates

    origin_ap = resolve_airport(origin)
    dest_ap = resolve_airport(destination)
    seat = parse_cabin_class(cabin_class)
    stops = parse_max_stops(max_stops)
    airline_list = parse_airlines(airlines)
    time_r = build_time_restrictions(departure_window) if departure_window else None

    segments, trip_type = build_date_search_segments(
        origin=origin_ap,
        destination=dest_ap,
        start_date=start_date,
        trip_duration=trip_duration,
        is_round_trip=is_round_trip,
        time_restrictions=time_r,
    )

    filters = DateSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
        ),
        flight_segments=segments,
        stops=stops,
        seat_type=seat,
        airlines=airline_list,
        from_date=start_date,
        to_date=end_date,
        duration=trip_duration if is_round_trip else None,
    )

    client = SearchDates()
    dates = client.search(filters)

    if not dates:
        return {"dates": [], "count": 0}

    if sort_by_price:
        dates.sort(key=lambda x: x.price)

    return {
        "dates": [
            {
                "date": d.date,
                "price": d.price,
                "return_date": getattr(d, "return_date", None),
            }
            for d in dates
        ],
        "count": len(dates),
        "trip_type": trip_type.name,
    }
