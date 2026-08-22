"""
City Generator: Seeds the initial city with districts, locations, businesses, and citizens.
"""

from __future__ import annotations

import random
import uuid

import structlog
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen, Gender, EducationLevel, TransportPreference
from backend.app.models.city import District, Location, LocationType, Building, BuildingType
from backend.app.models.economy import Business, BusinessType, Employment
from backend.app.models.government import Department, DepartmentType

log = structlog.get_logger()

fake = Faker()

DISTRICTS = [
    {"name": "Downtown", "center_x": 0, "center_y": 0, "radius": 800, "wealth": 0.7, "safety": 0.6},
    {"name": "Westside", "center_x": -1500, "center_y": 0, "radius": 600, "wealth": 0.8, "safety": 0.9},
    {"name": "Eastside", "center_x": 1500, "center_y": 0, "radius": 600, "wealth": 0.4, "safety": 0.5},
    {"name": "Northville", "center_x": 0, "center_y": 1500, "radius": 700, "wealth": 0.6, "safety": 0.7},
    {"name": "Southport", "center_x": 0, "center_y": -1500, "radius": 500, "wealth": 0.5, "safety": 0.6},
    {"name": "Industrial Zone", "center_x": 2000, "center_y": 1000, "radius": 400, "wealth": 0.3, "safety": 0.4},
    {"name": "University District", "center_x": -1000, "center_y": 1200, "radius": 400, "wealth": 0.5, "safety": 0.8},
    {"name": "Harbor District", "center_x": 1000, "center_y": -1200, "radius": 400, "wealth": 0.45, "safety": 0.55},
]

BUSINESS_TEMPLATES = [
    {"name": "General Hospital", "type": BusinessType.HOSPITAL, "max_emp": 50, "salary": 5000},
    {"name": "City Mall", "type": BusinessType.RETAIL, "max_emp": 30, "salary": 2500},
    {"name": "Tech Corp", "type": BusinessType.OFFICE, "max_emp": 100, "salary": 6000},
    {"name": "Fresh Market", "type": BusinessType.GROCERY, "max_emp": 15, "salary": 2200},
    {"name": "The Diner", "type": BusinessType.RESTAURANT, "max_emp": 10, "salary": 2000},
    {"name": "City School", "type": BusinessType.SCHOOL, "max_emp": 25, "salary": 3500},
    {"name": "Iron Works Factory", "type": BusinessType.FACTORY, "max_emp": 40, "salary": 2800},
    {"name": "FitLife Gym", "type": BusinessType.GYM, "max_emp": 8, "salary": 2200},
    {"name": "StarPlex Cinema", "type": BusinessType.ENTERTAINMENT, "max_emp": 12, "salary": 2000},
    {"name": "City Bank", "type": BusinessType.BANK, "max_emp": 20, "salary": 5500},
    {"name": "City Hall", "type": BusinessType.GOVERNMENT, "max_emp": 30, "salary": 4000},
]

PERSONALITY_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

OCCUPATIONS = [
    "software_engineer", "doctor", "teacher", "nurse", "accountant",
    "mechanic", "chef", "police_officer", "firefighter", "salesperson",
    "manager", "researcher", "driver", "artist", "lawyer",
]


async def generate_city(db: AsyncSession, population: int = 100, seed: int = 42) -> dict:
    random.seed(seed)
    Faker.seed(seed)

    stats = {"districts": 0, "locations": 0, "buildings": 0, "businesses": 0, "citizens": 0, "employments": 0}

    # --- Districts ---
    db_districts: list[District] = []
    for d in DISTRICTS:
        district = District(
            name=d["name"],
            center_x=d["center_x"],
            center_y=d["center_y"],
            radius=d["radius"],
            wealth_index=d["wealth"],
            safety_index=d["safety"],
        )
        db.add(district)
        db_districts.append(district)
        stats["districts"] += 1

    await db.flush()

    # --- Locations & Buildings ---
    all_locations: list[Location] = []
    for district in db_districts:
        loc_types = [
            (LocationType.RESIDENTIAL, 4),
            (LocationType.COMMERCIAL, 2),
            (LocationType.ENTERTAINMENT, 1),
        ]
        if district.name == "Industrial Zone":
            loc_types.append((LocationType.INDUSTRIAL, 3))
        if district.name == "University District":
            loc_types.append((LocationType.EDUCATION, 2))
        if district.name == "Downtown":
            loc_types.append((LocationType.GOVERNMENT, 1))
            loc_types.append((LocationType.HEALTHCARE, 1))

        for loc_type, count in loc_types:
            for i in range(count):
                offset_x = random.uniform(-district.radius, district.radius) * 0.8
                offset_y = random.uniform(-district.radius, district.radius) * 0.8
                loc = Location(
                    name=f"{district.name} {loc_type.value.title()} {i+1}",
                    location_type=loc_type,
                    district_id=district.id,
                    x=district.center_x + offset_x,
                    y=district.center_y + offset_y,
                    capacity=random.randint(20, 200),
                )
                db.add(loc)
                all_locations.append(loc)
                stats["locations"] += 1

                building_map = {
                    LocationType.RESIDENTIAL: BuildingType.APARTMENT,
                    LocationType.COMMERCIAL: BuildingType.SHOP,
                    LocationType.INDUSTRIAL: BuildingType.FACTORY,
                    LocationType.GOVERNMENT: BuildingType.GOVERNMENT_BUILDING,
                    LocationType.HEALTHCARE: BuildingType.HOSPITAL,
                    LocationType.EDUCATION: BuildingType.SCHOOL,
                    LocationType.ENTERTAINMENT: BuildingType.RESTAURANT,
                }
                btype = building_map.get(loc_type, BuildingType.OFFICE)
                building = Building(
                    name=f"{loc.name} Building",
                    building_type=btype,
                    location=loc,
                    floors=random.randint(1, 15),
                    rent_cost=random.uniform(300, 2000),
                )
                db.add(building)
                stats["buildings"] += 1

    await db.flush()

    # --- Businesses ---
    commercial_locs = [l for l in all_locations if l.location_type in (
        LocationType.COMMERCIAL, LocationType.INDUSTRIAL, LocationType.HEALTHCARE,
        LocationType.EDUCATION, LocationType.GOVERNMENT
    )]

    businesses: list[Business] = []
    for i, template in enumerate(BUSINESS_TEMPLATES):
        loc = commercial_locs[i % len(commercial_locs)] if commercial_locs else all_locations[0]
        biz = Business(
            name=template["name"],
            business_type=template["type"],
            location_id=loc.id,
            max_employees=template["max_emp"],
            base_salary=template["salary"],
            balance=random.uniform(50000, 500000),
        )
        db.add(biz)
        businesses.append(biz)
        stats["businesses"] += 1

    for district in db_districts:
        for _ in range(random.randint(2, 5)):
            template = random.choice(BUSINESS_TEMPLATES[:6])
            district_locs = [l for l in all_locations if l.district_id == district.id]
            loc = random.choice(district_locs) if district_locs else all_locations[0]
            biz = Business(
                name=f"{fake.company()} {template['name']}",
                business_type=template["type"],
                location_id=loc.id,
                max_employees=random.randint(5, template["max_emp"]),
                base_salary=template["salary"] * random.uniform(0.8, 1.2),
                balance=random.uniform(10000, 200000),
            )
            db.add(biz)
            businesses.append(biz)
            stats["businesses"] += 1

    await db.flush()

    # --- Government Departments ---
    for dept_type in DepartmentType:
        dept = Department(
            name=dept_type.value.replace("_", " ").title(),
            department_type=dept_type,
            budget=random.uniform(50000, 500000),
            efficiency=random.uniform(0.5, 0.9),
        )
        db.add(dept)

    await db.flush()

    # --- Citizens ---
    residential_locs = [l for l in all_locations if l.location_type == LocationType.RESIDENTIAL]
    citizens: list[Citizen] = []

    for _ in range(population):
        gender = random.choice(list(Gender))
        name = fake.name_male() if gender == Gender.MALE else fake.name_female()
        if gender == Gender.NON_BINARY:
            name = fake.name()

        age = random.choices(
            range(18, 85),
            weights=[max(0.1, 1.0 - abs(a - 35) / 50.0) for a in range(18, 85)],
        )[0]

        education = random.choices(
            list(EducationLevel),
            weights=[0.05, 0.3, 0.35, 0.2, 0.1],
        )[0]

        personality = {trait: round(random.uniform(0.1, 0.9), 2) for trait in PERSONALITY_TRAITS}

        home = random.choice(residential_locs) if residential_locs else all_locations[0]

        citizen = Citizen(
            name=name,
            age=age,
            gender=gender,
            education=education,
            personality_traits=personality,
            goals=random.sample(
                ["earn_money", "find_love", "stay_healthy", "get_promoted", "learn_new_skill",
                 "travel", "start_business", "retire_early", "help_community"],
                k=random.randint(1, 3),
            ),
            happiness=round(random.uniform(0.4, 0.9), 2),
            stress=round(random.uniform(0.1, 0.5), 2),
            health=round(random.uniform(0.6, 1.0), 2),
            energy=round(random.uniform(0.5, 1.0), 2),
            hunger=round(random.uniform(0.0, 0.3), 2),
            social_need=round(random.uniform(0.2, 0.7), 2),
            balance=round(random.uniform(500, 50000), 2),
            transport_preference=random.choice(list(TransportPreference)),
            political_opinion=round(random.uniform(0.0, 1.0), 3),
            home_location_id=home.id,
            current_location_id=home.id,
        )
        db.add(citizen)
        citizens.append(citizen)
        stats["citizens"] += 1

    await db.flush()

    # --- Assign employment ---
    employable = [c for c in citizens if c.age >= 18 and c.age < 65]
    random.shuffle(employable)

    employment_rate = 0.85
    to_employ = int(len(employable) * employment_rate)

    biz_idx = 0
    for citizen in employable[:to_employ]:
        biz = businesses[biz_idx % len(businesses)]
        role = random.choice(OCCUPATIONS)
        salary = biz.base_salary * random.uniform(0.8, 1.3)

        emp = Employment(
            citizen_id=citizen.id,
            business_id=biz.id,
            role=role,
            salary=salary,
        )
        db.add(emp)

        citizen.occupation = role
        citizen.salary = salary
        citizen.workplace_id = biz.location_id

        stats["employments"] += 1
        biz_idx += 1

    await db.flush()
    await db.commit()

    log.info("city_generated", **stats)
    return stats


async def grow_city(db: AsyncSession, additional_population: int, seed: int = 43) -> dict:
    """Add more residents to an already-generated city without touching what's there —
    existing citizens, their relationships, conversations, and history are untouched.
    Adds enough new residential locations/businesses to house and employ the newcomers,
    then generates additional_population new citizens on top."""
    from sqlalchemy import select

    random.seed(seed)
    Faker.seed(seed)

    stats = {"locations": 0, "buildings": 0, "businesses": 0, "citizens": 0, "employments": 0}

    districts_result = await db.execute(select(District))
    db_districts = list(districts_result.scalars().all())
    if not db_districts:
        raise ValueError("grow_city requires an existing city — run generate_city first")

    locations_result = await db.execute(select(Location))
    all_locations = list(locations_result.scalars().all())

    businesses_result = await db.execute(select(Business))
    businesses = list(businesses_result.scalars().all())

    # --- New residential locations, spread proportionally across districts ---
    new_locs_per_district = max(2, additional_population // (len(db_districts) * 60))
    new_residential: list[Location] = []
    for district in db_districts:
        for i in range(new_locs_per_district):
            offset_x = random.uniform(-district.radius, district.radius) * 0.8
            offset_y = random.uniform(-district.radius, district.radius) * 0.8
            loc = Location(
                name=f"{district.name} Residential Extension {i+1}",
                location_type=LocationType.RESIDENTIAL,
                district_id=district.id,
                x=district.center_x + offset_x,
                y=district.center_y + offset_y,
                capacity=random.randint(40, 250),
            )
            db.add(loc)
            all_locations.append(loc)
            new_residential.append(loc)
            stats["locations"] += 1

            building = Building(
                name=f"{loc.name} Building",
                building_type=BuildingType.APARTMENT,
                location=loc,
                floors=random.randint(3, 20),
                rent_cost=random.uniform(300, 2000),
            )
            db.add(building)
            stats["buildings"] += 1

    # --- A few more businesses so new citizens have somewhere to work ---
    new_businesses: list[Business] = []
    for district in db_districts:
        for _ in range(max(1, additional_population // (len(db_districts) * 100))):
            template = random.choice(BUSINESS_TEMPLATES[:6])
            district_locs = [l for l in all_locations if l.district_id == district.id]
            loc = random.choice(district_locs) if district_locs else all_locations[0]
            biz = Business(
                name=f"{fake.company()} {template['name']}",
                business_type=template["type"],
                location_id=loc.id,
                max_employees=random.randint(5, template["max_emp"]),
                base_salary=template["salary"] * random.uniform(0.8, 1.2),
                balance=random.uniform(10000, 200000),
            )
            db.add(biz)
            businesses.append(biz)
            new_businesses.append(biz)
            stats["businesses"] += 1

    await db.flush()

    # --- New citizens ---
    residential_locs = [l for l in all_locations if l.location_type == LocationType.RESIDENTIAL]
    citizens: list[Citizen] = []

    for _ in range(additional_population):
        gender = random.choice(list(Gender))
        name = fake.name_male() if gender == Gender.MALE else fake.name_female()
        if gender == Gender.NON_BINARY:
            name = fake.name()

        age = random.choices(
            range(18, 85),
            weights=[max(0.1, 1.0 - abs(a - 35) / 50.0) for a in range(18, 85)],
        )[0]

        education = random.choices(
            list(EducationLevel),
            weights=[0.05, 0.3, 0.35, 0.2, 0.1],
        )[0]

        personality = {trait: round(random.uniform(0.1, 0.9), 2) for trait in PERSONALITY_TRAITS}
        home = random.choice(residential_locs) if residential_locs else all_locations[0]

        citizen = Citizen(
            name=name,
            age=age,
            gender=gender,
            education=education,
            personality_traits=personality,
            goals=random.sample(
                ["earn_money", "find_love", "stay_healthy", "get_promoted", "learn_new_skill",
                 "travel", "start_business", "retire_early", "help_community"],
                k=random.randint(1, 3),
            ),
            happiness=round(random.uniform(0.4, 0.9), 2),
            stress=round(random.uniform(0.1, 0.5), 2),
            health=round(random.uniform(0.6, 1.0), 2),
            energy=round(random.uniform(0.5, 1.0), 2),
            hunger=round(random.uniform(0.0, 0.3), 2),
            social_need=round(random.uniform(0.2, 0.7), 2),
            balance=round(random.uniform(500, 50000), 2),
            transport_preference=random.choice(list(TransportPreference)),
            political_opinion=round(random.uniform(0.0, 1.0), 3),
            home_location_id=home.id,
            current_location_id=home.id,
        )
        db.add(citizen)
        citizens.append(citizen)
        stats["citizens"] += 1

    await db.flush()

    # --- Assign employment ---
    employable = [c for c in citizens if 18 <= c.age < 65]
    random.shuffle(employable)
    to_employ = int(len(employable) * 0.85)

    biz_idx = 0
    for citizen in employable[:to_employ]:
        if not businesses:
            break
        biz = businesses[biz_idx % len(businesses)]
        role = random.choice(OCCUPATIONS)
        salary = biz.base_salary * random.uniform(0.8, 1.3)

        emp = Employment(citizen_id=citizen.id, business_id=biz.id, role=role, salary=salary)
        db.add(emp)

        citizen.occupation = role
        citizen.salary = salary
        citizen.workplace_id = biz.location_id

        stats["employments"] += 1
        biz_idx += 1

    await db.flush()
    await db.commit()

    log.info("city_grown", additional_population=additional_population, **stats)
    return {"new_citizens": citizens, **stats}


# New districts placed clearly outside the original 8's footprint (which spans roughly
# x:[-1500,2000], y:[-1500,1500]) — this actually grows the city's map, rather than
# just packing more buildings into the same area the way grow_city's residential
# extensions do.
NEW_DISTRICTS = [
    {"name": "Riverside Heights", "center_x": -2300, "center_y": -800, "radius": 550, "wealth": 0.65, "safety": 0.75},
    {"name": "Tech Park", "center_x": 2700, "center_y": -300, "radius": 500, "wealth": 0.75, "safety": 0.65},
    {"name": "Old Quarter", "center_x": -600, "center_y": 2400, "radius": 500, "wealth": 0.4, "safety": 0.5},
    {"name": "Sunset Hills", "center_x": -2400, "center_y": 1700, "radius": 550, "wealth": 0.85, "safety": 0.9},
]


async def expand_city(db: AsyncSession, seed: int = 44) -> dict:
    """Grow the city's physical footprint with brand-new districts (not just denser
    existing ones), each seeded with a starter set of buildings the same way
    generate_city seeds the original 8 — non-destructive, nothing existing is touched
    or removed. Call grow_city afterward to populate them (and densify existing
    districts) with actual residents."""
    from sqlalchemy import select

    random.seed(seed)

    existing_result = await db.execute(select(District.name))
    existing_names = {n for (n,) in existing_result.all()}
    to_add = [d for d in NEW_DISTRICTS if d["name"] not in existing_names]

    stats = {"districts": 0, "locations": 0, "buildings": 0}
    db_districts: list[District] = []
    for d in to_add:
        district = District(
            name=d["name"], center_x=d["center_x"], center_y=d["center_y"],
            radius=d["radius"], wealth_index=d["wealth"], safety_index=d["safety"],
        )
        db.add(district)
        db_districts.append(district)
        stats["districts"] += 1
    await db.flush()

    building_map = {
        LocationType.RESIDENTIAL: BuildingType.APARTMENT,
        LocationType.COMMERCIAL: BuildingType.SHOP,
        LocationType.ENTERTAINMENT: BuildingType.RESTAURANT,
    }
    for district in db_districts:
        loc_types = [(LocationType.RESIDENTIAL, 6), (LocationType.COMMERCIAL, 3), (LocationType.ENTERTAINMENT, 2)]
        for loc_type, count in loc_types:
            for i in range(count):
                offset_x = random.uniform(-district.radius, district.radius) * 0.8
                offset_y = random.uniform(-district.radius, district.radius) * 0.8
                loc = Location(
                    name=f"{district.name} {loc_type.value.title()} {i + 1}",
                    location_type=loc_type,
                    district_id=district.id,
                    x=district.center_x + offset_x,
                    y=district.center_y + offset_y,
                    capacity=random.randint(20, 200),
                )
                db.add(loc)
                stats["locations"] += 1

                building = Building(
                    name=f"{loc.name} Building",
                    building_type=building_map.get(loc_type, BuildingType.OFFICE),
                    location=loc,
                    floors=random.randint(1, 15),
                    rent_cost=random.uniform(300, 2000),
                )
                db.add(building)
                stats["buildings"] += 1

    await db.flush()
    await db.commit()

    log.info("city_expanded", **stats)
    return {"new_districts": [d.name for d in db_districts], **stats}
