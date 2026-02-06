from src.main import lbs_to_kg, app, get_db
from src.models.models import User
from fastapi.testclient import TestClient
from sqlalchemy import select

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.database import Base


# Used for testing database only
TEST_ENGINE = create_engine(
    "sqlite:///test.db",
    connect_args={"check_same_thread": False},
)

TestSession = sessionmaker(bind=TEST_ENGINE)
Base.metadata.create_all(TEST_ENGINE)

def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

db = next(override_get_db())

# height in CM
# weight in KG
# activity_level is the activity levels as defined, no_active, light_active, moderate_active, high_active, extra_active
# target_weight is weight to lose
# sex = male or female
# weight_check daily weight check in's

male_user = User(
    weight=91,
    height=178,
    age=26,
    target_weight=80,
    sex='male',
    activity_level='moderate_active',
    weight_check=[91, lbs_to_kg(200), lbs_to_kg(200), lbs_to_kg(199), lbs_to_kg(199), lbs_to_kg(200), lbs_to_kg(199), lbs_to_kg(198),
                      lbs_to_kg(198), lbs_to_kg(197), lbs_to_kg(197), lbs_to_kg(196), lbs_to_kg(196)],
)
female_user = User(
    weight=64,
    height=160,
    age=18,
    target_weight=80,
    sex='female',
    activity_level='high_active',
    weight_check=[64, lbs_to_kg(141), lbs_to_kg(140), lbs_to_kg(142), lbs_to_kg(141), lbs_to_kg(142), lbs_to_kg(143), lbs_to_kg(143),
                      lbs_to_kg(142), lbs_to_kg(143), lbs_to_kg(142), lbs_to_kg(143), lbs_to_kg(144)],
)

db.add_all([male_user, female_user])
db.commit()


## CHECKLIST
# All tests given based on data from other online calorie trackers
# [X] BMR works properly 
# [X] TDEE works properly
# [X] Weight gain calorie tracker accurate
# [X] Weight loss calorie tracker accurate

    
def test_male_user_1_bmr():
    """Tests to make sure bmr is set and that it is same as other online calculators"""
    stmt = select(User).where(User.id == male_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/calculate_bmr",
        params={"_id" : user.id}
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()['bmr'] == 1898
    assert user.bmr == response.json()['bmr']

def test_male_user_1_tdee():
    """Tests to make sure tdee is set and that it is same as other online calculators"""
    stmt = select(User).where(User.id == male_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/calculate_tdee",
        params={"_id" : user.id}
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()["base_calorie_intake"] == 2940
    assert user.base_calorie_intake == response.json()["base_calorie_intake"] 


def test_male_user_1_daily_calories():
    """Tests to make sure tdee is set and that it is same as other online calculators"""
    stmt = select(User).where(User.id == male_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/daily_calories",
        params={"days" : 60, "_id" : user.id }
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()['calorie_intake'] == 1725
    assert user.calorie_intake == response.json()['calorie_intake']


def test_female_user_1_bmr():
    """Tests to make sure bmr is set and that it is same as other online calculators"""
    stmt = select(User).where(User.id == female_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/calculate_bmr",
        params={"_id" : user.id}
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()['bmr'] == 1389
    assert user.bmr == response.json()['bmr']

def test_female_user_1_tdee():
    """Tests to make sure tdee is set and that it is same as other online calculators"""
    stmt = select(User).where(User.id == female_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/calculate_tdee",
        params={"_id" : user.id}
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()["base_calorie_intake"] == 2635
    assert user.base_calorie_intake == response.json()["base_calorie_intake"] 

def test_female_user_1_daily_calories():
    """Tests checking to be sure daily calories lines up with online calculators"""
    stmt = select(User).where(User.id == female_user.id)
    user = db.execute(stmt).scalars().one()
    response = client.get(
        "/daily_calories",
        params={"days" : 60,"_id" : user.id }
    )
    db.refresh(user)
    assert response.status_code == 200
    assert response.json()["calorie_intake"] >= 4385
    assert user.calorie_intake == response.json()["calorie_intake"]

def test_male_user_daily_checkin_decrease():
    """Test that stagnant weight change prompts weekly check properly"""
    stmt = select(User).where(User.id == male_user.id)
    user = db.execute(stmt).scalars().one()
    leng = len(user.weight_check)
    old_intake = user.calorie_intake
    response = client.post(
        "/add_daily_check_in",
        data={"weight" :  float(91), "id" : str(user.id)}
    )
    db.refresh(user)
    print(response.json())
    assert response.status_code == 200
    assert len(user.weight_check) > leng
    assert user.weight_check[-1] == 91
    assert user.calorie_intake == old_intake - 200

def test_female_user_daily_checkin_increase():
    """Test that stagnant weight change prompts weekly check properly"""
    stmt = select(User).where(User.id == female_user.id)
    user = db.execute(stmt).scalars().one()
    leng = len(user.weight_check)
    old_intake = user.calorie_intake
    response = client.post(
        "/add_daily_check_in",
        data={"weight" :  float(64), "id" : str(user.id)}
    )
    db.refresh(user)
    print(response.json())
    assert response.status_code == 200
    assert len(user.weight_check) > leng
    assert user.weight_check[-1] == 64
    assert user.calorie_intake == old_intake + 200

def test_male_user_daily_checkin():
    """Checks basic addition outside of weekly checks for a weight entry"""
    stmt = select(User).where(User.id == male_user.id)
    user = db.execute(stmt).scalars().one()
    leng = len(user.weight_check)
    response = client.post(
        "/add_daily_check_in",
        data={"weight" :  float(89), "id" : str(user.id)}
    )
    db.refresh(user)
    print(response.json())
    assert response.status_code == 200
    assert len(user.weight_check) > leng
    assert user.weight_check[-1] == 89

def test_female_user_daily_checkin():
    """Checks basic addition outside of weekly checks for a weight entry"""
    stmt = select(User).where(User.id == female_user.id)
    user = db.execute(stmt).scalars().one()
    leng = len(user.weight_check)
    response = client.post(
        "/add_daily_check_in",
        data={"weight" :  float(66), "id" : str(user.id)}
    )
    db.refresh(user)
    print(response.json())
    assert response.status_code == 200
    assert len(user.weight_check) > leng
    assert user.weight_check[-1] == 66

