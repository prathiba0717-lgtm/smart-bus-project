from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="Smart Bus Crowd Management Backend",
    version="1.0.0",
    description="Backend API for the Smart Bus Crowd Management mobile application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


IST = timezone(timedelta(hours=5, minutes=30))


class SendOtpRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)


class VerifyOtpRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    otp: str = Field(min_length=4, max_length=6)


class SosRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    bus_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: str = "Emergency assistance required"


class BookingRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    bus_number: str
    seats: List[int]
    payment_method: Literal["Google Pay", "PhonePe", "Paytm", "UPI"]


class LowCrowdAlertRequest(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)
    bus_number: str
    preferred_crowd_level: Literal["low", "medium"] = "low"


class Terminal(BaseModel):
    id: str
    name: str
    city: str
    state: str
    latitude: float
    longitude: float
    type: Literal["major", "city", "district"]
    facilities: List[str]
    platforms: int


class Bus(BaseModel):
    number: str
    route_name: str
    from_terminal_id: str
    to_terminal_id: str
    current_stop_id: str
    arrival_minutes: int
    crowd_level: Literal["low", "medium", "high"]
    crowd_percentage: int
    seats_available: int
    female_safety: Literal["safe", "moderate", "unsafe"]
    passenger_count: int
    capacity: int
    current_location: str
    stops_away: int
    fare: float


class BusPrediction(BaseModel):
    time: str
    crowd_level: Literal["low", "medium", "high"]
    crowd_percentage: int
    seats: int


class Ticket(BaseModel):
    id: str
    mobile: str
    bus_number: str
    route_name: str
    seats: List[int]
    amount: float
    payment_method: str
    date: str
    status: Literal["confirmed", "cancelled", "completed"]


class BusStop(BaseModel):
    id: str
    name: str
    code: str
    city: str
    latitude: float
    longitude: float


class PopularRoute(BaseModel):
    id: str
    from_city: str
    to_city: str
    distance: int
    duration_hours: float
    frequency: str
    popular: bool


TERMINALS: List[Terminal] = [
    Terminal(id="cmbt", name="Chennai Mofussil Bus Terminus (CMBT)", city="Chennai", state="Tamil Nadu", latitude=13.0381, longitude=80.2042, type="major", facilities=["AC Waiting Hall", "Food Court", "ATM", "Restrooms"], platforms=75),
    Terminal(id="koyambedu", name="Koyambedu Bus Terminus", city="Chennai", state="Tamil Nadu", latitude=13.0674, longitude=80.1952, type="major", facilities=["Shopping Complex", "Food Court", "Parking"], platforms=60),
    Terminal(id="tambaram", name="Tambaram Bus Stand", city="Chennai", state="Tamil Nadu", latitude=12.9249, longitude=80.1000, type="city", facilities=["Waiting Area", "Food Stalls"], platforms=20),
    Terminal(id="coimbatore-central", name="Coimbatore Central Bus Stand (Gandhipuram)", city="Coimbatore", state="Tamil Nadu", latitude=11.0183, longitude=76.9674, type="major", facilities=["AC Waiting Hall", "Food Court", "Shopping", "Medical"], platforms=50),
    Terminal(id="madurai-central", name="Mattuthavani Integrated Bus Terminus", city="Madurai", state="Tamil Nadu", latitude=9.9082, longitude=78.0969, type="major", facilities=["AC Waiting Hall", "Food Court", "Parking", "ATM"], platforms=40),
    Terminal(id="bangalore-majestic", name="Kempegowda Bus Station (Majestic)", city="Bangalore", state="Karnataka", latitude=12.9767, longitude=77.5717, type="major", facilities=["AC Waiting Hall", "Food Court", "Shopping", "ATM"], platforms=65),
    Terminal(id="kochi-vytilla", name="Vytilla Mobility Hub", city="Kochi", state="Kerala", latitude=9.9674, longitude=76.3237, type="major", facilities=["AC Waiting Hall", "Food Court", "Metro Connectivity"], platforms=45),
    Terminal(id="hyderabad-mgbs", name="Mahatma Gandhi Bus Station (MGBS)", city="Hyderabad", state="Telangana", latitude=17.3850, longitude=78.4867, type="major", facilities=["AC Waiting Hall", "Food Court", "Metro Connectivity"], platforms=72),
    Terminal(id="puducherry", name="Pondicherry Bus Stand", city="Puducherry", state="Puducherry", latitude=11.9342, longitude=79.8306, type="city", facilities=["Waiting Hall", "Food Stalls"], platforms=18),
]

STOPS: List[BusStop] = [
    BusStop(id="cmbt", name="CMBT (Koyambedu)", code="CMBT001", city="Chennai", latitude=13.0674, longitude=80.1952),
    BusStop(id="koyambedu", name="Koyambedu Metro", code="KYM002", city="Chennai", latitude=13.0682, longitude=80.1940),
    BusStop(id="tnagar", name="T. Nagar Bus Stand", code="TNG003", city="Chennai", latitude=13.0418, longitude=80.2337),
    BusStop(id="adyar", name="Adyar Depot", code="ADY004", city="Chennai", latitude=13.0067, longitude=80.2574),
]

BUSES: List[Bus] = [
    Bus(number="27C", route_name="CMBT - T. Nagar - Adyar", from_terminal_id="cmbt", to_terminal_id="tambaram", current_stop_id="cmbt", arrival_minutes=3, crowd_level="low", crowd_percentage=35, seats_available=18, female_safety="safe", passenger_count=22, capacity=60, current_location="Near Koyambedu Flyover", stops_away=2, fare=35.0),
    Bus(number="45G", route_name="Koyambedu - Anna Nagar - Tambaram", from_terminal_id="koyambedu", to_terminal_id="tambaram", current_stop_id="koyambedu", arrival_minutes=7, crowd_level="medium", crowd_percentage=65, seats_available=8, female_safety="safe", passenger_count=39, capacity=60, current_location="Anna Nagar Roundtana", stops_away=4, fare=42.0),
    Bus(number="23B", route_name="Central - Mount Road - Airport", from_terminal_id="cmbt", to_terminal_id="tambaram", current_stop_id="tnagar", arrival_minutes=12, crowd_level="high", crowd_percentage=92, seats_available=2, female_safety="moderate", passenger_count=55, capacity=60, current_location="Near Mount Road", stops_away=6, fare=50.0),
    Bus(number="5C", route_name="Parry's Corner - Marina - Velachery", from_terminal_id="cmbt", to_terminal_id="tambaram", current_stop_id="adyar", arrival_minutes=15, crowd_level="medium", crowd_percentage=58, seats_available=12, female_safety="safe", passenger_count=35, capacity=60, current_location="Marina Loop Road", stops_away=7, fare=38.0),
    Bus(number="21G", route_name="Thiruvottiyur - Broadway - Guindy", from_terminal_id="cmbt", to_terminal_id="tambaram", current_stop_id="tnagar", arrival_minutes=18, crowd_level="low", crowd_percentage=28, seats_available=25, female_safety="safe", passenger_count=17, capacity=60, current_location="Near Guindy Signal", stops_away=8, fare=34.0),
]

POPULAR_ROUTES: List[PopularRoute] = [
    PopularRoute(id="chn-cbe", from_city="Chennai", to_city="Coimbatore", distance=507, duration_hours=8.0, frequency="50+ daily", popular=True),
    PopularRoute(id="chn-mdu", from_city="Chennai", to_city="Madurai", distance=462, duration_hours=7.5, frequency="40+ daily", popular=True),
    PopularRoute(id="chn-blr", from_city="Chennai", to_city="Bangalore", distance=346, duration_hours=6.0, frequency="100+ daily", popular=True),
    PopularRoute(id="chn-pdy", from_city="Chennai", to_city="Puducherry", distance=162, duration_hours=3.0, frequency="30+ daily", popular=True),
]

BUS_PREDICTIONS: Dict[str, List[BusPrediction]] = {
    "27C": [
        BusPrediction(time="10:45 AM", crowd_level="medium", crowd_percentage=62, seats=10),
        BusPrediction(time="11:15 AM", crowd_level="high", crowd_percentage=88, seats=3),
        BusPrediction(time="11:45 AM", crowd_level="low", crowd_percentage=38, seats=22),
    ],
    "45G": [
        BusPrediction(time="10:55 AM", crowd_level="high", crowd_percentage=74, seats=6),
        BusPrediction(time="11:25 AM", crowd_level="medium", crowd_percentage=59, seats=12),
        BusPrediction(time="11:55 AM", crowd_level="low", crowd_percentage=33, seats=20),
    ],
}

OTP_STORE: Dict[str, str] = {}
TICKETS: List[Ticket] = []
SOS_ALERTS: List[dict] = []
LOW_CROWD_ALERTS: List[dict] = []


def now_ist() -> datetime:
    return datetime.now(IST)


def calculate_distance_km(start: Terminal, end: Terminal) -> int:
    radius = 6371
    d_lat = math.radians(end.latitude - start.latitude)
    d_lon = math.radians(end.longitude - start.longitude)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(start.latitude))
        * math.cos(math.radians(end.latitude))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(radius * c)


def crowd_from_percentage(value: int) -> Literal["low", "medium", "high"]:
    if value < 40:
        return "low"
    if value < 75:
        return "medium"
    return "high"


def find_bus(bus_number: str) -> Bus:
    for bus in BUSES:
        if bus.number == bus_number:
            return bus
    raise HTTPException(status_code=404, detail="Bus not found")


def find_stop(stop_id: str) -> BusStop:
    for stop in STOPS:
        if stop.id == stop_id:
            return stop
    raise HTTPException(status_code=404, detail="Stop not found")


def find_terminal(terminal_id: str) -> Terminal:
    for terminal in TERMINALS:
        if terminal.id == terminal_id:
            return terminal
    raise HTTPException(status_code=404, detail="Terminal not found")


def generate_seat_map(bus_number: str) -> List[dict]:
    random.seed(bus_number)
    bus = find_bus(bus_number)
    seat_map = []
    available_target = bus.seats_available
    available_numbers = set(random.sample(range(1, 41), k=min(available_target, 40)))

    for row in range(1, 11):
        for col in range(1, 5):
            number = (row - 1) * 4 + col
            seat_map.append(
                {
                    "id": f"seat-{number}",
                    "row": row,
                    "number": number,
                    "is_available": number in available_numbers,
                    "type": "window" if col in (1, 4) else "aisle",
                }
            )
    return seat_map


@app.get("/")
def root() -> dict:
    return {
        "message": "Smart Bus Crowd Management backend is running",
        "docs": "/docs",
        "timestamp": now_ist().isoformat(),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "smart-bus-backend", "time": now_ist().isoformat()}


@app.get("/app/bootstrap")
def app_bootstrap() -> dict:
    return {
        "app": {
            "name": "SmartBus Crowd Management",
            "version": "1.0.0",
            "time": now_ist().isoformat(),
        },
        "buses": BUSES,
        "stops": STOPS,
        "terminals": TERMINALS,
        "popular_routes": POPULAR_ROUTES,
        "analytics": analytics_overview(),
    }


@app.post("/auth/send-otp")
def send_otp(payload: SendOtpRequest) -> dict:
    otp = "1234"
    OTP_STORE[payload.mobile] = otp
    return {
        "message": "OTP sent successfully",
        "mobile": payload.mobile,
        "otp_demo": otp,
    }


@app.post("/auth/verify-otp")
def verify_otp(payload: VerifyOtpRequest) -> dict:
    stored_otp = OTP_STORE.get(payload.mobile)
    if stored_otp != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    return {
        "message": "Login successful",
        "user": {
            "id": payload.mobile[-6:],
            "mobile": payload.mobile,
            "name": "SmartBus User",
        },
        "token": f"smartbus-{uuid4()}",
    }


@app.get("/buses")
def list_buses(
    crowd_level: Optional[Literal["low", "medium", "high"]] = None,
    stop_id: Optional[str] = None,
) -> List[Bus]:
    buses = BUSES
    if crowd_level:
        buses = [bus for bus in buses if bus.crowd_level == crowd_level]
    if stop_id:
        buses = [bus for bus in buses if bus.current_stop_id == stop_id]
    return buses


@app.get("/buses/{bus_number}")
def get_bus(bus_number: str) -> Bus:
    return find_bus(bus_number)


@app.get("/buses/{bus_number}/predictions")
def get_bus_predictions(bus_number: str) -> List[BusPrediction]:
    find_bus(bus_number)
    return BUS_PREDICTIONS.get(
        bus_number,
        [
            BusPrediction(time="10:45 AM", crowd_level="medium", crowd_percentage=60, seats=8),
            BusPrediction(time="11:15 AM", crowd_level="high", crowd_percentage=82, seats=4),
            BusPrediction(time="11:45 AM", crowd_level="low", crowd_percentage=36, seats=18),
        ],
    )


@app.get("/buses/{bus_number}/seats")
def get_bus_seats(bus_number: str) -> dict:
    bus = find_bus(bus_number)
    return {
        "bus_number": bus.number,
        "fare_per_seat": bus.fare,
        "seat_layout": generate_seat_map(bus_number),
    }


@app.get("/stops")
def list_stops() -> List[BusStop]:
    return STOPS


@app.get("/stops/{stop_id}")
def get_stop(stop_id: str) -> BusStop:
    return find_stop(stop_id)


@app.get("/stops/{stop_id}/buses")
def get_stop_buses(stop_id: str) -> dict:
    stop = find_stop(stop_id)
    buses = [bus for bus in BUSES if bus.current_stop_id == stop_id]
    return {"stop": stop, "buses": buses}


@app.get("/terminals")
def list_terminals(
    state: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Terminal]:
    terminals = TERMINALS
    if state:
        terminals = [terminal for terminal in terminals if terminal.state.lower() == state.lower()]
    if search:
        query = search.lower()
        terminals = [
            terminal
            for terminal in terminals
            if query in terminal.name.lower()
            or query in terminal.city.lower()
            or query in terminal.state.lower()
        ]
    return terminals


@app.get("/terminals/{terminal_id}")
def get_terminal(terminal_id: str) -> Terminal:
    return find_terminal(terminal_id)


@app.get("/routes/popular")
def get_popular_routes() -> List[PopularRoute]:
    return POPULAR_ROUTES


@app.get("/routes/plan")
def plan_route(
    from_terminal_id: str = Query(...),
    to_terminal_id: str = Query(...),
) -> dict:
    start = find_terminal(from_terminal_id)
    end = find_terminal(to_terminal_id)
    distance = calculate_distance_km(start, end)
    duration_hours = max(1, round(distance / 60))

    recommendations = [
        {
            "type": "comfort",
            "title": "Most Comfortable",
            "description": "AC coach with lower expected crowd around 32%.",
        },
        {
            "type": "time",
            "title": "Fastest Route",
            "description": "Express service with fewer intermediate stops.",
        },
        {
            "type": "crowd",
            "title": "Least Crowded",
            "description": "Late-morning departure usually has better seat availability.",
        },
    ]

    matching_buses = [
        bus
        for bus in BUSES
        if bus.from_terminal_id == from_terminal_id or bus.to_terminal_id == to_terminal_id
    ]

    return {
        "from_terminal": start,
        "to_terminal": end,
        "distance_km": distance,
        "estimated_duration_hours": duration_hours,
        "daily_buses": max(12, len(matching_buses) * 5),
        "recommendations": recommendations,
        "facilities": {
            "from": start.facilities,
            "to": end.facilities,
        },
    }


@app.post("/bookings")
def create_booking(payload: BookingRequest) -> dict:
    bus = find_bus(payload.bus_number)
    if not payload.seats:
        raise HTTPException(status_code=400, detail="At least one seat must be selected")
    if len(set(payload.seats)) != len(payload.seats):
        raise HTTPException(status_code=400, detail="Duplicate seats are not allowed")
    if any(seat < 1 or seat > 40 for seat in payload.seats):
        raise HTTPException(status_code=400, detail="Seat number must be between 1 and 40")
    if len(payload.seats) > bus.seats_available:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    subtotal = len(payload.seats) * bus.fare
    gst = round(subtotal * 0.05, 2)
    amount = round(subtotal + gst, 2)
    ticket_id = f"TN{str(uuid4().int)[-8:]}"

    ticket = Ticket(
        id=ticket_id,
        mobile=payload.mobile,
        bus_number=bus.number,
        route_name=bus.route_name,
        seats=sorted(payload.seats),
        amount=amount,
        payment_method=payload.payment_method,
        date=now_ist().isoformat(),
        status="confirmed",
    )
    TICKETS.append(ticket)

    bus.seats_available -= len(payload.seats)
    bus.passenger_count += len(payload.seats)
    bus.crowd_percentage = min(100, round((bus.passenger_count / bus.capacity) * 100))
    bus.crowd_level = crowd_from_percentage(bus.crowd_percentage)

    return {
        "message": "Booking confirmed",
        "ticket": ticket,
        "fare_breakdown": {
            "subtotal": round(subtotal, 2),
            "gst": gst,
            "total": amount,
        },
    }


@app.get("/tickets")
def list_tickets(mobile: Optional[str] = None) -> List[Ticket]:
    if mobile:
        return [ticket for ticket in TICKETS if ticket.mobile == mobile]
    return TICKETS


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> Ticket:
    for ticket in TICKETS:
        if ticket.id == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail="Ticket not found")


@app.get("/analytics/overview")
def analytics_overview() -> dict:
    average_crowd = round(sum(bus.crowd_percentage for bus in BUSES) / len(BUSES))
    busiest_bus = max(BUSES, key=lambda bus: bus.crowd_percentage)
    least_crowded = min(BUSES, key=lambda bus: bus.crowd_percentage)

    peak_hours = [
        {"hour": "07:00", "crowd_percentage": 78},
        {"hour": "08:00", "crowd_percentage": 92},
        {"hour": "09:00", "crowd_percentage": 85},
        {"hour": "17:00", "crowd_percentage": 88},
        {"hour": "18:00", "crowd_percentage": 95},
        {"hour": "19:00", "crowd_percentage": 81},
    ]

    weekly_trend = [
        {"day": "Mon", "crowd_percentage": 82},
        {"day": "Tue", "crowd_percentage": 76},
        {"day": "Wed", "crowd_percentage": 79},
        {"day": "Thu", "crowd_percentage": 74},
        {"day": "Fri", "crowd_percentage": 89},
        {"day": "Sat", "crowd_percentage": 63},
        {"day": "Sun", "crowd_percentage": 51},
    ]

    return {
        "average_crowd_percentage": average_crowd,
        "busiest_bus": busiest_bus,
        "least_crowded_bus": least_crowded,
        "peak_hours": peak_hours,
        "weekly_trend": weekly_trend,
        "best_travel_window": "10:30 AM - 12:00 PM",
    }


@app.post("/sos")
def create_sos_alert(payload: SosRequest) -> dict:
    alert = {
        "id": str(uuid4()),
        "mobile": payload.mobile,
        "bus_number": payload.bus_number,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "message": payload.message,
        "status": "sent",
        "created_at": now_ist().isoformat(),
        "helpline": "1800-425-1111",
    }
    SOS_ALERTS.append(alert)
    return {"message": "Emergency alert sent successfully", "alert": alert}


@app.post("/notifications/low-crowd")
def create_low_crowd_alert(payload: LowCrowdAlertRequest) -> dict:
    bus = find_bus(payload.bus_number)
    alert = {
        "id": str(uuid4()),
        "mobile": payload.mobile,
        "bus_number": payload.bus_number,
        "route_name": bus.route_name,
        "preferred_crowd_level": payload.preferred_crowd_level,
        "created_at": now_ist().isoformat(),
        "status": "active",
    }
    LOW_CROWD_ALERTS.append(alert)
    return {
        "message": "Low crowd notification enabled",
        "alert": alert,
    }


@app.get("/dashboard/summary")
def dashboard_summary() -> dict:
    return {
        "app_name": "SmartBus Crowd Management",
        "active_buses": len(BUSES),
        "tracked_terminals": len(TERMINALS),
        "tracked_stops": len(STOPS),
        "total_bookings": len(TICKETS),
        "low_crowd_alerts": len(LOW_CROWD_ALERTS),
        "open_sos_alerts": len([alert for alert in SOS_ALERTS if alert["status"] == "sent"]),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
