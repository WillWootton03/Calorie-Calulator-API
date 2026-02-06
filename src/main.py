from fastapi import FastAPI, HTTPException, Depends, Form
from src.models.models import User
from contextlib import asynccontextmanager

from src.database import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.database import Base, engine

import uuid

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan():
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

# DONE: Calculate BMR using the Miflin St. Jeor Equation
# DONE: Calculate Starting TDEE using a multiplier ((Sedentary = 1.2), (1-3 days light activity Light Active = 1.375), 
# (moderate excersize 3-5 days Moderate Active = 1.55), (hard excersize 6-7 days / week 1.725), 
# (hard excersize or physical labor every day 1.9) )
# DONE: Based on base calorie intake, and timeframe in days calcualte calories to eat in order to reach goal
# DONE: Based on weekly weight if weight is within 2 pounds of weight 2 weeks ago, lower or up calories by 200
# DONE: warning if calories are below 1500 and user is male or 1200 and user is female

def calorie_warnings(caloric_intake: int, sex: str):
    """ Simple warning for consuming too little calories

    Args:
        caloric_intake (int): the calculated amount of calories to be consumed
        sex (Sex): Male or female changes the minimum reccommended calorie count
    """

    # Warning for dangerously low caloric intakes
    if caloric_intake <= 800:
        print('WARNING!! The minimum reccommended caloric intake is 800, you are currently consuming a dangerously low ' \
                'amount of calories')
        
    # Warning for dangerously low caloric intakes for men or women
    if sex == 'male':
        if caloric_intake < 1500:
            print('WARNING!! The Recommended minimum for caloric intake for you is 1500, you are currently consuming a low ' \
                    'amount of calories')
    else:
        if caloric_intake < 1200:
            print('WARNING!! The Recommended minimum for caloric intake for you is 1200, you are currently consuming a low ' \
                    'amount of calories')

def kg_to_lbs(weight_kg: float):
    """Simple visual change to go from calculation measurement to visual

    Args:
        weight_kg (float): a persons calculated kg weight

    Returns:
        weight_lbs (float): a persons converted weight from kg to pounds rounded 2 decimal places
    """
    return round(weight_kg * 2.205, 2)

def lbs_to_kg(weight_lbs: float):
    """Simple conversion metric to deal with pounds to kg for storage

    Args:
        weight_lbs (float): Input weight lbs to convert to kgs
    
    Returns:
        weight_kg (float): retirns weight in kg for for calculations
        
    """
    
    return round(weight_lbs / 2.205, 2)

@app.get("/calculate_bmr")
def calculate_bmr(_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generate a base daily caloric rate based on the Mifflin St. Jeor Equation to determine an estimate
    for daily caloric burn. Can round height and weight since it is an early estimate of calories.

    Args:
        id (uuid) = reference to user to edit
        db (Session) = reference to db that is used
        ADDITION (int) = value to add or remove from calories based on sex as defined in the equation

    Returns: 
        bmr (int) = The amount of calories that need to be consumed to maintain body weight if person is 
                    completely inactive and does absoultely nothing throughout day
    """
    stmt = select(User).where(User.id == _id)
    user = db.execute(stmt).scalars().one()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid User")
    
    ADDITION = -1
    # For formula 2 different values are added to the main forumla, which is decided in this switch
    if user.sex == 'male':
        ADDITION = 5
    else:
        ADDITION = -161

    bmr = round(((user.weight * 10) + (user.height * 6.25) - (user.age * 5 ) + ADDITION))
    user.bmr = bmr

    db.commit()

    return {"Success" : True, "bmr" : bmr }

@app.get("/calculate_tdee")
def calculate_tdee( _id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Calculate the Total Energy Expenditure for a person based on their bmr and activity level.
    Gives an estimated amount of calories to be consumed for a day
    
    Args:
        id (uuid) = reference to user to edit
        db (Session) = reference to db that is used
    
    Returns:
        calories (float): calculated estimate for a person to eat to maintain weight
    """
    stmt = select(User).where(User.id == _id)
    user = db.execute(stmt).scalars().one()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User")
    
    active_level = -1.0

    # Verifies bmr was a usable input
    if user.bmr < 1:
        raise ValueError

    # matches tdee calculation based on active level
    match user.activity_level:
        case 'no_active':
            active_level = 1.2
        case 'light_active':
            active_level = 1.375
        case 'moderate_active':
            active_level = 1.55
        case 'high_active':
            active_level = 1.725
        case 'extra_active':
            active_level = 1.9
        
    # Checks to make sure active_level was set
    if active_level == -1.0:
        raise ValueError
    

    # Return estimated calorie count based on tdee and bmr
    # rounds to nearest 5 to make calorie count look better
    base_calorie_intake = (int(user.bmr * active_level) // 5) * 5
    user.base_calorie_intake = base_calorie_intake

    db.commit()

    return {"Success" : True, "base_calorie_intake" : base_calorie_intake}

@app.get("/daily_calories")
def calculate_calories(days: int, _id: uuid.UUID, db: Session = Depends(get_db)):
    """Generate a caloric intake based on weight loss goals over time, also print warning if calories are too low

    Args:
        id (uuid) = reference to user to edit
        db (Session) = reference to db that is used

    Returns:
        daily_intake (int): returns the reccommended intake of calories to reach goal weight by date
    """

    stmt = select(User).where(User.id == _id)
    user = db.execute(stmt).scalar_one()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid User")


    curr_weight = kg_to_lbs(user.weight)
    targ_weight = kg_to_lbs(user.target_weight)

    # If user wants to gain weight 
    if targ_weight > curr_weight:
        total_cals = (targ_weight - curr_weight) * 3000
        new_cals = ((user.base_calorie_intake + (total_cals / days)) // 5) * 5
    # User wants to lose weight
    else:
        total_cals = (curr_weight - targ_weight) * 3000
        new_cals = ((user.base_calorie_intake - (total_cals / days)) // 5) * 5

    # Warning if calories are dangerously low
    calorie_warnings(new_cals, user.sex)


    user.calorie_intake = new_cals
    db.commit()

    return {"Success" : True, "calorie_intake" : new_cals}

@app.post("/add_daily_check_in")
def daily_checkin(weight: float = Form(...), id: uuid.UUID = Form(...), db: Session = Depends(get_db)):
    """Used to add a single weight check in for each day

    Args:
        weight (float): The weight to be added to weight_checks
        id (uuid) = reference to user to edit
        db (Session) = reference to db that is used

    """
    stmt = select(User).where(User.id == id)
    user = db.execute(stmt).scalar_one()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid User")

    # update list of weight_check 
    user.weight_check.append(weight)
    flag_modified(user, 'weight_check')
    db.commit()

    # Check if it has been 2 weeks since starting, and checks if todays weight check is the start of a new week
    if len(user.weight_check) >= 14 and len(user.weight_check) % 7 == 0:
        # Based on wether you want to gain or lose weight determine if you are within 1kg of weight from 2 weeks ago and prompt a potential increase or decrease in calories
        if user.calorie_intake > user.base_calorie_intake:
        # If the last weight inputted is within 2 pounds of the weight input from 2 weeks ago
            if (user.weight_check[-1] < user.weight_check[-14] + 1):
                weekly_check(user.id, db)
        else:
            if (user.weight_check[-1] > user.weight_check[-14] - 1): 
                weekly_check(user.id, db)
        

@app.get("/weekly_check")
def weekly_check(_id: uuid.UUID, db: Session = Depends(get_db)):
    """Daily weight check in to determine how user's weight journey is going. If its a weekly check in and it is determines
        user's weight has been stagnant for 2 week, user is asked if they want to increase or decrease calories

    Args:
        id (uuid) = reference to user to edit
        db (Session) = reference to db that is used

    Returns:
        calorie_intake (int): Will remain the same, unless its a weekly check and the user has been stagnant at weight
    """
    stmt = select(User).where(User.id == _id)
    user = db.execute(stmt).scalar_one()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid User")
    
    # Check if user is trying to gain or lose weight
    if user.calorie_intake > user.base_calorie_intake:
        # asks if user wishes to increase calories after stagnating
        inp = input('It seems you have been at a similar weight for 2 weeks would you like to up your calories (y/n)?')
        if inp.strip().lower() == 'y':
            user.calorie_intake += 200
            db.commit()
    else:
        # Prints warnings if calories will be too low, then asks if user wants to lower
        calorie_warnings(user.calorie_intake - 200, user.sex)
        inp = input('It seems you have been at a similar weight for 2 weeks would you like to lower your calories (y/n)?')
        if inp.strip().lower() == 'y':
            user.calorie_intake -= 200
            db.commit()
    # if not a weekly check in, or user does not want to change their calories, then calorie_intake stays the same
    return {"Success": True, "calorie_intake" : user.calorie_intake}


