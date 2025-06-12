from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import math


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class PartyCalculationRequest(BaseModel):
    guests: int
    drinker_type: str  # "light", "medium", "heavy"
    duration: int  # hours
    drink_types: List[str]  # ["beer", "wine", "vodka", "whiskey", "rum"]
    mixers: List[str] = []  # ["soda", "juice", "tonic"]

class DrinkCalculation(BaseModel):
    drink_type: str
    amount: int
    unit: str
    description: str

class PartyCalculationResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drinks: List[DrinkCalculation]
    mixers: List[DrinkCalculation]
    extras: List[DrinkCalculation]  # cups, ice
    total_cost_estimate: float
    fun_message: str


# Calculation Engine
class DrinkCalculator:
    # Base consumption rates per person per hour
    CONSUMPTION_RATES = {
        "light": {"beer": 0.8, "wine": 0.4, "spirits": 0.3},
        "medium": {"beer": 1.5, "wine": 0.7, "spirits": 0.6},
        "heavy": {"beer": 2.5, "wine": 1.0, "spirits": 1.0}
    }
    
    # Standard sizes
    SIZES = {
        "beer": 0.35,  # 350ml bottles
        "wine": 0.15,  # 150ml per glass, 750ml bottle = 5 glasses
        "spirits": 0.04  # 40ml shots
    }
    
    # Mixer ratios (parts mixer per part alcohol)
    MIXER_RATIOS = {
        "vodka": 4,
        "rum": 3,
        "whiskey": 2,
        "gin": 4
    }
    
    # Estimated costs (USD)
    COSTS = {
        "beer": 2.50,  # per bottle
        "wine": 12.00,  # per bottle (750ml)
        "vodka": 25.00,  # per bottle (750ml)
        "whiskey": 30.00,
        "rum": 22.00,
        "gin": 28.00,
        "soda": 1.50,  # per liter
        "juice": 3.00,  # per liter
        "tonic": 2.00,  # per liter
        "cups": 0.05,  # per cup
        "ice": 2.00  # per kg
    }
    
    def calculate_party_needs(self, request: PartyCalculationRequest) -> PartyCalculationResponse:
        drinks = []
        mixers = []
        extras = []
        total_cost = 0
        
        # Calculate drinks
        for drink_type in request.drink_types:
            if drink_type in ["beer", "wine"]:
                result = self._calculate_drink(drink_type, request.guests, request.drinker_type, request.duration)
            else:  # spirits
                result = self._calculate_spirits(drink_type, request.guests, request.drinker_type, request.duration)
            
            drinks.append(result)
            total_cost += result.amount * self.COSTS.get(drink_type, 20)
        
        # Calculate mixers
        spirits_in_request = [d for d in request.drink_types if d in ["vodka", "rum", "whiskey", "gin"]]
        if spirits_in_request and request.mixers:
            for mixer in request.mixers:
                mixer_result = self._calculate_mixers(spirits_in_request, request.guests, request.drinker_type, request.duration, mixer)
                mixers.append(mixer_result)
                total_cost += mixer_result.amount * self.COSTS.get(mixer, 2)
        
        # Calculate extras (cups and ice)
        cups_needed = max(request.guests * 2, 10)  # At least 2 per person, minimum 10
        ice_needed = max(math.ceil(request.guests * 0.5), 2)  # 0.5kg per person, minimum 2kg
        
        extras.append(DrinkCalculation(
            drink_type="cups",
            amount=cups_needed,
            unit="pieces",
            description=f"Disposable cups (accounting for replacements)"
        ))
        
        extras.append(DrinkCalculation(
            drink_type="ice",
            amount=ice_needed,
            unit="kg",
            description=f"Ice for drinks and cooling"
        ))
        
        total_cost += cups_needed * self.COSTS["cups"] + ice_needed * self.COSTS["ice"]
        
        # Generate fun message
        fun_message = self._generate_fun_message(request.guests, request.drinker_type, len(request.drink_types))
        
        return PartyCalculationResponse(
            drinks=drinks,
            mixers=mixers,
            extras=extras,
            total_cost_estimate=round(total_cost, 2),
            fun_message=fun_message
        )
    
    def _calculate_drink(self, drink_type: str, guests: int, intensity: str, duration: int) -> DrinkCalculation:
        rate = self.CONSUMPTION_RATES[intensity][drink_type if drink_type in ["beer", "wine"] else "spirits"]
        total_consumption = guests * rate * duration
        
        if drink_type == "beer":
            bottles = math.ceil(total_consumption)
            return DrinkCalculation(
                drink_type=drink_type,
                amount=bottles,
                unit="bottles (350ml)",
                description=f"Based on {rate} bottles per person per hour"
            )
        elif drink_type == "wine":
            # Wine: 5 glasses per 750ml bottle
            glasses_needed = math.ceil(total_consumption)
            bottles = math.ceil(glasses_needed / 5)
            return DrinkCalculation(
                drink_type=drink_type,
                amount=bottles,
                unit="bottles (750ml)",
                description=f"About {glasses_needed} glasses ({rate} glasses per person per hour)"
            )
    
    def _calculate_spirits(self, spirit_type: str, guests: int, intensity: str, duration: int) -> DrinkCalculation:
        rate = self.CONSUMPTION_RATES[intensity]["spirits"]
        total_shots = guests * rate * duration
        
        # A 750ml bottle contains about 18 shots (40ml each)
        bottles = math.ceil(total_shots / 18)
        
        return DrinkCalculation(
            drink_type=spirit_type,
            amount=bottles,
            unit="bottles (750ml)",
            description=f"About {math.ceil(total_shots)} shots ({rate} shots per person per hour)"
        )
    
    def _calculate_mixers(self, spirits: List[str], guests: int, intensity: str, duration: int, mixer_type: str) -> DrinkCalculation:
        # Calculate total spirits consumption
        total_spirit_consumption = 0
        for spirit in spirits:
            rate = self.CONSUMPTION_RATES[intensity]["spirits"]
            shots = guests * rate * duration
            # Convert shots to liters (40ml per shot)
            liters = shots * 0.04
            ratio = self.MIXER_RATIOS.get(spirit, 3)
            total_spirit_consumption += liters * ratio
        
        liters_needed = math.ceil(total_spirit_consumption)
        
        return DrinkCalculation(
            drink_type=mixer_type,
            amount=liters_needed,
            unit="liters",
            description=f"Mixer for {', '.join(spirits)}"
        )
    
    def _generate_fun_message(self, guests: int, intensity: str, drink_variety: int) -> str:
        messages = [
            f"🎉 Ready to party with {guests} friends!",
            f"🥂 This {intensity}-drinking crew is going to have a blast!",
            f"🍻 {drink_variety} different drinks = one epic party!",
            f"🎈 Time to get this party started - you're all set!",
            f"🎊 Your party is going to be legendary with this setup!"
        ]
        
        if guests > 20:
            messages.append("🏠 That's a BIG party - hope your neighbors are cool!")
        elif guests < 5:
            messages.append("🍸 Intimate gathering = more quality time with friends!")
        
        if intensity == "heavy":
            messages.append("💪 Heavy drinkers detected - you came prepared!")
        elif intensity == "light":
            messages.append("🌱 Light drinking = longer conversations and better memories!")
        
        import random
        return random.choice(messages)


# Initialize calculator
calculator = DrinkCalculator()

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Party Drink Calculator API Ready! 🎉"}

@api_router.post("/calculate", response_model=PartyCalculationResponse)
async def calculate_party_drinks(request: PartyCalculationRequest):
    """Calculate drinks, mixers, and extras needed for a party"""
    try:
        result = calculator.calculate_party_needs(request)
        
        # Save calculation to database
        await db.party_calculations.insert_one(result.dict())
        
        return result
    except Exception as e:
        logging.error(f"Calculation error: {str(e)}")
        raise

@api_router.get("/drink-options")
async def get_drink_options():
    """Get available drink types and mixers"""
    return {
        "drink_types": [
            {"id": "beer", "name": "Beer 🍺", "category": "beer"},
            {"id": "wine", "name": "Wine 🍷", "category": "wine"},
            {"id": "vodka", "name": "Vodka", "category": "spirits"},
            {"id": "whiskey", "name": "Whiskey", "category": "spirits"},
            {"id": "rum", "name": "Rum", "category": "spirits"},
            {"id": "gin", "name": "Gin", "category": "spirits"}
        ],
        "mixers": [
            {"id": "soda", "name": "Soda"},
            {"id": "juice", "name": "Juice"},
            {"id": "tonic", "name": "Tonic Water"}
        ],
        "intensities": [
            {"id": "light", "name": "Light Drinkers", "description": "1-2 drinks per hour"},
            {"id": "medium", "name": "Medium Drinkers", "description": "2-3 drinks per hour"},
            {"id": "heavy", "name": "Heavy Drinkers", "description": "3+ drinks per hour"}
        ]
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
