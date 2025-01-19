from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Date

# Database connection string
DATABASE_URI = "postgresql+psycopg2://postgres:Janiv123@localhost:5433/real_estate"

# Create the database engine
engine = create_engine(DATABASE_URI)

# Initialize metadata
metadata = MetaData()

# Define the 'buildings' table
buildings = Table(
    "buildings", metadata,
    Column("building_id", String(10), primary_key=True),
    Column("city", String(100)),
    Column("address", String(255)),
    Column("country", String(100)),
    Column("region", String(100)),
    Column("size", Float),
    Column("floors", Integer),
    Column("purpose", String(50)),
    Column("ownership", String(50)),
    Column("year_built", Integer),
    Column("market_rate", Float),
    Column("employee_capacity", Integer),
    Column("energy_target", Float),
    Column("leed_certified", Boolean)
)

# Define the 'financials' table
financials = Table(
    "financials", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("building_id", String(10), ForeignKey("buildings.building_id"), nullable=False),
    Column("date", Date, nullable=False),
    Column("lease_cost", Float),
    Column("total_operating_expense", Float),
    Column("energy_costs", Float),
    Column("utilities_costs", Float),
    Column("maintenance_costs", Float),
    Column("catering_costs", Float),
    Column("cleaning_costs", Float),
    Column("security_costs", Float),
    Column("insurance_costs", Float),
    Column("waste_disposal_costs", Float),
    Column("other_costs", Float)
)

# Define the 'floor_occupancy' table
floor_occupancy = Table(
    "floor_occupancy", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("building_id", String(10), ForeignKey("buildings.building_id"), nullable=False),
    Column("floor", Integer, nullable=False),
    Column("max_capacity", Integer, nullable=False)
)

# Define the 'floor_utilization' table
floor_utilization = Table(
    "floor_utilization", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("building_id", String(10), ForeignKey("buildings.building_id"), nullable=False),
    Column("floor", Integer, nullable=False),
    Column("time", DateTime, nullable=False),
    Column("occupancy", Integer, nullable=False)
)

# Define the 'energy_consumption' table
energy_consumption = Table(
    "energy_consumption", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("building_id", String(10), ForeignKey("buildings.building_id"), nullable=False),
    Column("floor", Integer, nullable=False),
    Column("time", DateTime, nullable=False),
    Column("energy", Float, nullable=False)
)

# Create all tables in the database
metadata.create_all(engine)

print("Tables successfully created in the PostgreSQL database.")
